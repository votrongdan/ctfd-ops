"""Tests for the Single Session Monitor API endpoints."""

from unittest.mock import patch, MagicMock

def test_api_sessions_live_admin(client, admin_user):
    """Test that an admin can access the live sessions API."""
    with client.session_transaction() as sess:
        sess["id"] = admin_user.id
        sess["nonce"] = "1234"
        sess["type"] = "admin"

    with patch("CTFd.plugins.ctfd_single_session.routes.SessionTracker.get_all_active_sessions") as mock_get_sessions:
        mock_pagination = MagicMock()
        mock_pagination.items = []
        mock_pagination.pages = 1
        mock_pagination.page = 1
        mock_get_sessions.return_value = mock_pagination
        
        response = client.get("/plugins/ctfd-single-session/api/sessions/live", headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "sessions" in data

def test_api_sessions_live_user(client, user):
    """Test that a regular user cannot access the live sessions API."""
    with client.session_transaction() as sess:
        sess["id"] = user.id
        sess["nonce"] = "1234"
        sess["type"] = "user"

    response = client.get("/plugins/ctfd-single-session/api/sessions/live", headers={"Content-Type": "application/json"})
    assert response.status_code == 403

def test_api_events_live_admin(client, admin_user):
    """Test that an admin can access the live events API."""
    with client.session_transaction() as sess:
        sess["id"] = admin_user.id
        sess["nonce"] = "1234"
        sess["type"] = "admin"

    with patch("CTFd.plugins.ctfd_single_session.routes.EventService.get_events") as mock_get_events, \
         patch("CTFd.plugins.ctfd_single_session.routes.EventService.get_unresolved_count") as mock_unresolved:
        mock_pagination = MagicMock()
        mock_pagination.items = []
        mock_pagination.pages = 1
        mock_pagination.page = 1
        mock_get_events.return_value = mock_pagination
        mock_unresolved.return_value = 0
        
        response = client.get("/plugins/ctfd-single-session/api/events/live")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "events" in data
