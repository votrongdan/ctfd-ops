"""Security event creation with deduplication via cooldown."""

import datetime

from CTFd.models import Users, db
from CTFd.utils import get_config

from .config import EVENT_COOLDOWN_KEY, EVENT_LOGIN_BLOCKED, EVENT_MULTIPLE_SESSIONS
from .models import SSMEvent


class EventService:
    """Creates and queries security events with per-user cooldown."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_in_cooldown(user_id, event_type):
        """Return True if a recent event of the same type exists for this user."""
        cooldown = int(get_config(EVENT_COOLDOWN_KEY, "300"))
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=cooldown)
        return (
            SSMEvent.query
            .filter(
                SSMEvent.user_id == user_id,
                SSMEvent.event_type == event_type,
                SSMEvent.created_at > cutoff,
            )
            .first()
            is not None
        )

    @staticmethod
    def _get_username(user_id):
        user = Users.query.get(user_id)
        return user.name if user else f"User#{user_id}"

    # ------------------------------------------------------------------
    # Event creation
    # ------------------------------------------------------------------

    @staticmethod
    def create_multi_session_event(user_id, active_sessions):
        """
        Create an event when multiple active sessions are detected.
        Skipped if still in cooldown to avoid event flooding.
        """
        if EventService._is_in_cooldown(user_id, EVENT_MULTIPLE_SESSIONS):
            return None

        sessions_info = [
            {
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
            }
            for s in active_sessions
        ]

        event = SSMEvent(
            user_id=user_id,
            username=EventService._get_username(user_id),
            event_type=EVENT_MULTIPLE_SESSIONS,
            session_count=len(active_sessions),
            sessions_info=sessions_info,
            created_at=datetime.datetime.utcnow(),
        )
        db.session.add(event)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return event

    @staticmethod
    def create_login_blocked_event(user_id):
        """
        Create an event when Block Mode rejects a login attempt.
        Skipped if still in cooldown to avoid event flooding.
        """
        if EventService._is_in_cooldown(user_id, EVENT_LOGIN_BLOCKED):
            return None

        event = SSMEvent(
            user_id=user_id,
            username=EventService._get_username(user_id),
            event_type=EVENT_LOGIN_BLOCKED,
            session_count=1,
            sessions_info=[],
            created_at=datetime.datetime.utcnow(),
        )
        db.session.add(event)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return event

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_events(page=1, per_page=50, event_type=None, resolved=None):
        """Paginated list of security events for admin view."""
        query = SSMEvent.query
        if event_type:
            query = query.filter_by(event_type=event_type)
        if resolved is not None:
            query = query.filter_by(resolved=resolved)
        query = query.order_by(SSMEvent.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_unresolved_count():
        """Count of unresolved events (for badge display)."""
        return SSMEvent.query.filter_by(resolved=False).count()

    # ------------------------------------------------------------------
    # Admin actions
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_event(event_id, admin_user_id):
        """Mark an event as resolved by the given admin."""
        event = SSMEvent.query.get(event_id)
        if not event:
            return False
        event.resolved = True
        event.resolved_at = datetime.datetime.utcnow()
        event.resolved_by = admin_user_id
        db.session.commit()
        return True
