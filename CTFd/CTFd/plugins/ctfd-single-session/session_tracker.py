"""Core session tracking logic."""

import datetime
import hashlib

from flask import current_app

from CTFd.cache import cache
from CTFd.plugins._lifecycle import lifecycle_lock
from CTFd.models import db
from CTFd.utils import get_config

from .config import (
    HEARTBEAT_INTERVAL_KEY,
    MODE_BLOCK,
    MODE_KEY,
)
from .models import SSMSession


def hash_session_id(session_id):
    """Create a SHA-256 hash of a session ID. Never store raw SIDs."""
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def get_session_lifetime():
    """Return the configured session lifetime in seconds."""
    lifetime = current_app.config.get("PERMANENT_SESSION_LIFETIME", 604800)
    if hasattr(lifetime, "total_seconds"):
        return int(lifetime.total_seconds())
    return int(lifetime)


def get_app_lifecycle_id():
    """
    Return an identifier for the current application lifecycle.
    By hashing the SECRET_KEY, we automatically tie the lifecycle to cookie validity.
    If CTFd restarts and generates a new SECRET_KEY, old cookies become invalid,
    and this ID changes, allowing us to safely prune the orphaned Redis sessions.
    """
    secret = current_app.config.get("SECRET_KEY", "")
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    elif isinstance(secret, bytes):
        pass
    else:
        secret = str(secret).encode("utf-8")
    return hashlib.sha256(secret).hexdigest()


class SessionTracker:
    """Manages session lifecycle in the plugin's own database table."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @staticmethod
    def register_session(user_id, session_id):
        with lifecycle_lock("ssm-user-" + str(user_id)):
            return SessionTracker._register(user_id, session_id)

    @staticmethod
    def _register(user_id, session_id):
        now = datetime.datetime.utcnow()
        sid_hash = hash_session_id(session_id)
        record = SSMSession.query.filter_by(session_hash=sid_hash).first()
        if record is None:
            record = SSMSession(user_id=user_id, session_hash=sid_hash,
                                cache_key=current_app.session_interface.key_prefix + session_id,
                                created_at=now, last_seen_at=now)
            db.session.add(record)
        record.user_id = user_id
        record.is_active = True
        record.lifecycle = get_app_lifecycle_id()
        # An unsaved login is a reservation, not a dead session. The response
        # adapter must complete it before the deadline or discard the login.
        record.pending_until = now + datetime.timedelta(seconds=60)
        db.session.commit()
        return record

    @staticmethod
    def is_session_valid(record):
        if not record.is_active:
            return False
        lifecycle = record.lifecycle or cache.get("ssm:lifecycle:" + record.cache_key)
        if lifecycle != get_app_lifecycle_id():
            # Backfill legacy records only when this request proves cookie validity.
            from flask import has_request_context, session
            if not (record.lifecycle is None and has_request_context()
                    and getattr(session, "sid", None)
                    and record.session_hash == hash_session_id(session.sid)
                    and session.get("id") == record.user_id):
                return False
        # A request opened before cache expiry may legitimately refresh its
        # session, unless it was revoked or is an expired login reservation.
        from flask import has_request_context, session
        if (record.pending_until is None and has_request_context()
                and getattr(session, 'sid', None)
                and record.session_hash == hash_session_id(session.sid)
                and session.get('id') == record.user_id):
            return True
        raw = cache.get(record.cache_key)
        if raw is not None:
            try:
                data = current_app.session_interface.serializer.loads(raw)
                if data.get("id") == record.user_id:
                    return True
            except (ValueError, TypeError):
                pass
        return bool(record.pending_until and record.pending_until > datetime.datetime.utcnow())

    @staticmethod
    def register_session_atomic(user_id, session_id):
        with lifecycle_lock("ssm-user-" + str(user_id)):
            db.session.rollback()  # no stale snapshot from the pre-login gate
            if SessionTracker.has_active_session(user_id):
                return None, True
            return SessionTracker._register(user_id, session_id), False

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------

    @staticmethod
    def remove_session_by_sid(session_id):
        """Mark a session inactive using its raw session ID."""
        sid_hash = hash_session_id(session_id)
        updated = SSMSession.query.filter_by(
            session_hash=sid_hash, is_active=True
        ).update({"is_active": False})
        db.session.commit()
        return updated > 0

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_active_sessions(user_id):
        """Return all active, non-expired sessions for a user."""
        sessions = (
            SSMSession.query
            .filter(
                SSMSession.user_id == user_id,
                SSMSession.is_active == True,  # noqa: E712
            )
            .all()
        )
        valid = []
        modified = False
        for s in sessions:
            if SessionTracker.is_session_valid(s):
                valid.append(s)
            else:
                s.is_active = False
                modified = True
        
        if modified:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        
        return valid

    @staticmethod
    def has_active_session(user_id):
        """Fast boolean check: does this user have ≥1 active session?"""
        sessions = (
            SSMSession.query
            .filter(
                SSMSession.user_id == user_id,
                SSMSession.is_active == True,  # noqa: E712
            )
            .all()
        )
        modified = False
        has_active = False
        for s in sessions:
            if SessionTracker.is_session_valid(s):
                has_active = True
            else:
                s.is_active = False
                modified = True

        if modified:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        return has_active

    @staticmethod
    def get_all_active_sessions(page=1, per_page=50):
        """Paginated list of all active sessions (admin view). Reconciles the current page."""
        query = (
            SSMSession.query
            .filter(SSMSession.is_active == True)  # noqa: E712
            .order_by(SSMSession.last_seen_at.desc())
        )
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Reconcile just this page's sessions
        modified = False
        for s in pagination.items:
            if not SessionTracker.is_session_valid(s):
                s.is_active = False
                modified = True
                
        if modified:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                
        # Re-fetch the page if we modified it (to ensure items count is accurate and removed sessions disappear)
        if modified:
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
        return pagination

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    @staticmethod
    def update_last_seen(session_id):
        """Throttled last-seen update to avoid excessive DB writes."""
        sid_hash = hash_session_id(session_id)
        interval = int(get_config(HEARTBEAT_INTERVAL_KEY, "30"))

        throttle_key = f"ssm:hb:{sid_hash}"
        if cache.get(throttle_key):
            return False  # Already updated recently

        now = datetime.datetime.utcnow()
        updated = SSMSession.query.filter_by(
            session_hash=sid_hash, is_active=True
        ).update({"last_seen_at": now})

        if updated:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                return False
            cache.set(throttle_key, "1", timeout=interval)
            return True
        return False

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    @staticmethod
    def cleanup_expired():
        """Mark all expired sessions as inactive. Returns count cleaned."""
        count = 0
        for record in SSMSession.query.filter_by(is_active=True).all():
            if not SessionTracker.is_session_valid(record):
                record.is_active = False
                count += 1
        db.session.commit()
        return count

    # ------------------------------------------------------------------
    # Admin actions
    # ------------------------------------------------------------------

    @staticmethod
    def force_logout_session(session_record_id):
        record = SSMSession.query.get(session_record_id)
        if record is None:
            return False
        user_id = record.user_id
        with lifecycle_lock("ssm-user-" + str(user_id)):
            db.session.rollback()
            record = SSMSession.query.get(session_record_id)
            if not record or not record.is_active:
                return False
            cache.delete(record.cache_key)
            cache.delete("ssm:lifecycle:" + record.cache_key)
            record.is_active = False
            record.pending_until = None
            db.session.commit()
            return True

    @staticmethod
    def force_logout_all(user_id):
        with lifecycle_lock("ssm-user-" + str(user_id)):
            db.session.rollback()
            ids = [r.id for r in SSMSession.query.filter_by(user_id=user_id, is_active=True).all()]
            return sum(SessionTracker.force_logout_session(i) for i in ids)
