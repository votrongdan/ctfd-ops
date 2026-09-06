"""Test session tracker module."""

import datetime
from unittest.mock import MagicMock, patch
from CTFd.plugins.ctfd_single_session.session_tracker import SessionTracker, hash_session_id

@patch('CTFd.plugins.ctfd_single_session.session_tracker.db')
@patch('CTFd.plugins.ctfd_single_session.session_tracker.get_config')
@patch('CTFd.plugins.ctfd_single_session.session_tracker.get_session_lifetime')
def test_register_session(mock_lifetime, mock_get_config, mock_db):
    mock_get_config.return_value = "true"
    mock_lifetime.return_value = 604800
    
    with patch('CTFd.plugins.ctfd_single_session.session_tracker.SSMSession') as mock_session_model:
        SessionTracker.register_session(1, "test-session-id")
        
        mock_session_model.assert_called_once()
        args, kwargs = mock_session_model.call_args
        assert kwargs['user_id'] == 1
        assert kwargs['session_hash'] == hash_session_id("test-session-id")
        assert kwargs['cache_key'] == "sessiontest-session-id"
        assert kwargs['is_active'] is True
        
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()

@patch('CTFd.plugins.ctfd_single_session.session_tracker.db')
def test_remove_session_by_sid(mock_db):
    with patch('CTFd.plugins.ctfd_single_session.session_tracker.SSMSession') as mock_session_model:
        mock_query = mock_session_model.query.filter_by.return_value
        mock_query.update.return_value = 1
        
        result = SessionTracker.remove_session_by_sid("test-session-id")
        
        assert result is True
        mock_session_model.query.filter_by.assert_called_once_with(
            session_hash=hash_session_id("test-session-id"), is_active=True
        )
        mock_query.update.assert_called_once_with({"is_active": False})
        mock_db.session.commit.assert_called_once()
