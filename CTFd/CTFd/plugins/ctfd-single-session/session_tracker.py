"""Core session tracking logic."""

import datetime
import hashlib

from flask import current_app

from CTFd.cache import cache
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
        """Record a new session after successful login (Monitoring Mode)."""
        sid_hash = hash_session_id(session_id)
        ck = "session" + session_id

        now = datetime.datetime.utcnow()

        record = SSMSession(
            user_id=user_id,
            session_hash=sid_hash,
            cache_key=ck,
            created_at=now,
            last_seen_at=now,
            is_active=True,
        )
        db.session.add(record)
        try:
            db.session.commit()
            
            # Bind this session to the current application lifecycle
            cache.set(
                f"ssm:lifecycle:{ck}", 
                get_app_lifecycle_id(), 
                timeout=get_session_lifetime()
            )
        except Exception:
            db.session.rollback()
            raise
        return record

    @staticmethod
    def is_session_valid(session_record):
        """
        Determine if a tracked session is genuinely still active.
        This reconciles the plugin database state with CTFd's actual cache backend.
        If CTFd restarts and the cache is wiped, this correctly identifies stale DB records.
        """
        from flask import session
        
        now = datetime.datetime.utcnow()
        cutoff = now - datetime.timedelta(seconds=get_session_lifetime())
        if session_record.created_at <= cutoff:
            return False
            
        # If this is the session currently processing the request, it is definitely valid.
        # (Flask-Session hasn't saved it to Redis yet, so the cache lookup below would falsely fail).
        if hasattr(session, "sid") and session.sid:
            if session_record.session_hash == hash_session_id(session.sid):
                return True
                
        # Verify it belongs to the current app lifecycle (SECRET_KEY matches)
        # If SECRET_KEY changes on restart, old cookies (and their Redis sessions) are orphaned
        session_lifecycle = cache.get(f"ssm:lifecycle:{session_record.cache_key}")
        if session_lifecycle != get_app_lifecycle_id():
            return False
            
        # Verify the session still exists in CTFd's session store (Redis/Filesystem)
        return cache.get(session_record.cache_key) is not None

    @staticmethod
    def register_session_atomic(user_id, session_id):
        """
        Atomically check for existing active sessions and register a new one.

        Used in Block Mode to prevent race conditions where two simultaneous
        logins could both pass the before_request gate.

        Returns:
            (SSMSession, False) on success.
            (None, True) if an active session already exists (blocked).
        """
        sid_hash = hash_session_id(session_id)
        ck = "session" + session_id
        now = datetime.datetime.utcnow()

        # Attempt row-level locking (MySQL / PostgreSQL)
        try:
            existing = (
                SSMSession.query
                .filter_by(user_id=user_id, is_active=True)
                .with_for_update()
                .all()
            )
        except Exception:
            # SQLite does not support FOR UPDATE — fall back to plain query
            existing = (
                SSMSession.query
                .filter_by(user_id=user_id, is_active=True)
                .all()
            )

        # Reconcile stale sessions while we hold the lock
        active = []
        for s in existing:
            if not SessionTracker.is_session_valid(s):
                s.is_active = False
            else:
                active.append(s)

        if active:
            # Another session is still valid — reject this login
            db.session.commit()
            return None, True

        record = SSMSession(
            user_id=user_id,
            session_hash=sid_hash,
            cache_key=ck,
            created_at=now,
            last_seen_at=now,
            is_active=True,
        )
        db.session.add(record)
        try:
            db.session.commit()
            
            # Bind this session to the current application lifecycle
            cache.set(
                f"ssm:lifecycle:{ck}", 
                get_app_lifecycle_id(), 
                timeout=get_session_lifetime()
            )
        except Exception:
            db.session.rollback()
            raise
        return record, False

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
        now = datetime.datetime.utcnow()
        cutoff = now - datetime.timedelta(seconds=get_session_lifetime())
        updated = SSMSession.query.filter(
            SSMSession.is_active == True,  # noqa: E712
            SSMSession.created_at <= cutoff,
        ).update({"is_active": False})
        db.session.commit()
        return updated

    # ------------------------------------------------------------------
    # Admin actions
    # ------------------------------------------------------------------

    @staticmethod
    def force_logout_session(session_record_id):
        """Force-logout a single session by its DB id."""
        record = SSMSession.query.get(session_record_id)
        if not record or not record.is_active:
            return False
        cache.delete(record.cache_key)
        record.is_active = False
        db.session.commit()
        return True

    @staticmethod
    def force_logout_all(user_id):
        """Force-logout every active session for a user."""
        sessions = SSMSession.query.filter_by(
            user_id=user_id, is_active=True
        ).all()
        count = 0
        for s in sessions:
            cache.delete(s.cache_key)
            s.is_active = False
            count += 1
        db.session.commit()
        return count
