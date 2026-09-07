"""Tests for session lifecycle recovery after CTFd restarts."""

import datetime
import uuid
from unittest.mock import patch

from CTFd.models import db
from CTFd.plugins.ctfd_single_session.models import SSMSession
from CTFd.plugins.ctfd_single_session.session_tracker import SessionTracker

def test_session_reconciliation_clears_stale_records(app, user):
    """
    Test that when the cache is wiped (simulating a restart),
    previously active database sessions are correctly identified as stale
    and do not count as active.
    """
    with app.app_context():
        # Insert a fake session that is marked active in the DB
        # but does NOT exist in the cache.
        record = SSMSession(
            user_id=user.id,
            session_hash=uuid.uuid4().hex,
            cache_key="sessionfake_id",
            created_at=datetime.datetime.utcnow(),
            last_seen_at=datetime.datetime.utcnow(),
            is_active=True,
        )
        db.session.add(record)
        db.session.commit()

        # Verify it's in the DB
        assert SSMSession.query.filter_by(user_id=user.id, is_active=True).count() == 1

        # Simulate cache wipe by mocking cache.get to return None
        with patch("CTFd.plugins.ctfd_single_session.session_tracker.cache.get", return_value=None):
            # Checking for active sessions should lazily validate against the cache
            # Since the cache is empty, it should return False and mark the DB record inactive
            has_active = SessionTracker.has_active_session(user.id)
            assert has_active is False

            # Verify the record was actually updated to inactive
            updated_record = SSMSession.query.filter_by(user_id=user.id).first()
            assert updated_record.is_active is False

def test_session_reconciliation_keeps_valid_records(app, user):
    """
    Test that if the cache backend persists across restarts (e.g. Redis persistence),
    valid sessions are NOT incorrectly invalidated.
    """
    with app.app_context():
        record = SSMSession(
            user_id=user.id,
            session_hash=uuid.uuid4().hex,
            cache_key="sessionvalid_id",
            created_at=datetime.datetime.utcnow(),
            last_seen_at=datetime.datetime.utcnow(),
            is_active=True,
        )
        db.session.add(record)
        db.session.commit()

        # Mock cache.get to return fake session data (simulating persistence)
        from CTFd.plugins.ctfd_single_session.session_tracker import get_app_lifecycle_id
        record.lifecycle = get_app_lifecycle_id()
        cached = app.session_interface.serializer.dumps({"id": user.id})
        with patch("CTFd.plugins.ctfd_single_session.session_tracker.cache.get", return_value=cached):
            has_active = SessionTracker.has_active_session(user.id)
            assert has_active is True

            # Verify the record remains active
            updated_record = SSMSession.query.filter_by(user_id=user.id).first()
            assert updated_record.is_active is True

def test_block_mode_allows_login_if_cache_wiped(client, user):
    """
    Test that a new login attempt is ALLOWED in Block Mode if the
    existing active DB session is actually stale (cache wiped).
    """
    with client.application.app_context():
        # Setup plugin config to BLOCK
        from CTFd.utils import set_config
        set_config("ssm:mode", "block")

        record = SSMSession(
            user_id=user.id,
            session_hash=uuid.uuid4().hex,
            cache_key="sessionstale_id",
            created_at=datetime.datetime.utcnow(),
            last_seen_at=datetime.datetime.utcnow(),
            is_active=True,
        )
        db.session.add(record)
        db.session.commit()

    # The stale record has no cache entry. Do not mock all cache reads: that
    # would erase the login request's CSRF session and test a different failure.
    from tests.plugin_regression.fixtures import login
    r = login(client, user.name)
    assert r.status_code == 302
    assert r.location.endswith("/challenges")
