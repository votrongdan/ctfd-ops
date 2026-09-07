"""Observe the real CTFd session-save boundary without changing cache TTL policy."""
from CTFd.models import db
from CTFd.plugins._lifecycle import lifecycle_lock
from .models import SSMSession
from .session_tracker import SessionTracker, hash_session_id, get_app_lifecycle_id


class TrackedSessionInterface:
    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def save_session(self, app, session, response):
        if not session.modified:
            return self.delegate.save_session(app, session, response)
        sid = getattr(session, 'sid', None)
        if not sid:
            return self.delegate.save_session(app, session, response)
        record = SSMSession.query.filter_by(session_hash=hash_session_id(sid)).first()
        if record is None:
            return self.delegate.save_session(app, session, response)
        user_id, record_id = record.user_id, record.id
        with lifecycle_lock('ssm-user-' + str(user_id)):
            db.session.rollback()
            record = SSMSession.query.get(record_id)
            if session.get('id') and not SessionTracker.is_session_valid(record):
                # Revoked/expired reservation: never publish a late second login.
                session.clear()
            try:
                self.delegate.save_session(app, session, response)
            except Exception:
                record.is_active = False
                record.pending_until = None
                db.session.commit()
                raise
            record.pending_until = None
            record.is_active = session.get('id') == user_id
            record.lifecycle = get_app_lifecycle_id()
            db.session.commit()
