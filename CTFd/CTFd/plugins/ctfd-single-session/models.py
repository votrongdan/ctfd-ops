"""Database models for session tracking and security events."""

import datetime

from CTFd.models import db


class SSMSession(db.Model):
    """Tracks active login sessions per user."""

    __tablename__ = "ssm_sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_hash = db.Column(db.String(64), nullable=False, unique=True)
    cache_key = db.Column(db.String(128), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    last_seen_at = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    user = db.relationship("Users", foreign_keys=[user_id], lazy="select")

    __table_args__ = (
        db.Index("idx_ssm_sessions_user_active", "user_id", "is_active"),
    )

    @property
    def is_expired(self):
        """Check whether this session has exceeded the configured lifetime."""
        from flask import current_app

        lifetime = current_app.config.get("PERMANENT_SESSION_LIFETIME", 604800)
        if hasattr(lifetime, "total_seconds"):
            seconds = int(lifetime.total_seconds())
        else:
            seconds = int(lifetime)
        expiry = self.created_at + datetime.timedelta(seconds=seconds)
        return datetime.datetime.utcnow() > expiry

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.name if self.user else f"User#{self.user_id}",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<SSMSession user={self.user_id} active={self.is_active}>"


class SSMEvent(db.Model):
    """Security events for admin notification."""

    __tablename__ = "ssm_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    username = db.Column(db.String(128), nullable=False)
    event_type = db.Column(db.String(32), nullable=False)
    session_count = db.Column(db.Integer, nullable=False, default=0)
    sessions_info = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user = db.relationship("Users", foreign_keys=[user_id], lazy="select")
    resolver = db.relationship("Users", foreign_keys=[resolved_by], lazy="select")

    __table_args__ = (
        db.Index("idx_ssm_events_user_type", "user_id", "event_type"),
        db.Index("idx_ssm_events_created", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "event_type": self.event_type,
            "session_count": self.session_count,
            "sessions_info": self.sessions_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
        }

    def __repr__(self):
        return f"<SSMEvent type={self.event_type} user={self.username}>"
