"""
Tests for the CTFd import adapter module.
Requires CTFd to be importable (run inside CTFd container or with CTFd on PYTHONPATH).
"""

import os
import sys
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

# For import adapter tests, we need CTFd on the path since the module
# imports from CTFd.models and CTFd.schemas directly.
# These tests should be run inside the CTFd Docker container.
_plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ctfd_root = os.path.dirname(os.path.dirname(os.path.dirname(_plugin_dir)))
if _ctfd_root not in sys.path:
    sys.path.insert(0, _ctfd_root)

from CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter import (
    ImportResult,
    import_users,
)


@dataclass
class MockParticipant:
    row_number: int = 1
    name: str = "Test User"
    username: str = "test_user"
    email: str = "test_user@ctf.local"
    password: str = "TestPass123"
    status: str = "valid"
    error: str = ""


class MockSchemaResponse:
    def __init__(self, data=None, errors=None):
        self.data = data
        self.errors = errors or {}


class TestImportUsers:

    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.db")
    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.UserSchema")
    def test_successful_import(self, MockSchema, mock_db):
        mock_user = MagicMock()
        mock_user.id = 42
        schema_instance = MagicMock()
        schema_instance.load.return_value = MockSchemaResponse(data=mock_user)
        MockSchema.return_value = schema_instance

        result = import_users([MockParticipant()])
        assert result.total_success == 1
        assert result.total_failed == 0
        assert result.successful[0].user_id == 42

    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.db")
    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.UserSchema")
    def test_schema_validation_failure(self, MockSchema, mock_db):
        schema_instance = MagicMock()
        schema_instance.load.return_value = MockSchemaResponse(errors={"email": ["Invalid"]})
        MockSchema.return_value = schema_instance

        result = import_users([MockParticipant()])
        assert result.total_success == 0
        assert result.total_failed == 1

    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.db")
    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.UserSchema")
    def test_db_commit_failure(self, MockSchema, mock_db):
        mock_user = MagicMock()
        mock_user.id = 1
        schema_instance = MagicMock()
        schema_instance.load.return_value = MockSchemaResponse(data=mock_user)
        MockSchema.return_value = schema_instance
        mock_db.session.commit.side_effect = Exception("DB error")

        result = import_users([MockParticipant()])
        assert result.total_success == 0
        assert result.total_failed == 1
        mock_db.session.rollback.assert_called()

    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.db")
    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.UserSchema")
    def test_invalid_participants_skipped(self, MockSchema, mock_db):
        result = import_users([MockParticipant(status="invalid")])
        assert result.total_success == 0
        assert result.total_failed == 0

    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.db")
    @patch("CTFd.plugins.ctfd_account_provisioning.services.ctfd_import_adapter.UserSchema")
    def test_correct_data_format(self, MockSchema, mock_db):
        mock_user = MagicMock()
        mock_user.id = 1
        schema_instance = MagicMock()
        schema_instance.load.return_value = MockSchemaResponse(data=mock_user)
        MockSchema.return_value = schema_instance

        p = MockParticipant(name="Nguyễn Văn An", email="nva@ctf.local", password="Pass1")
        import_users([p])
        call_args = schema_instance.load.call_args[0][0]
        assert call_args["name"] == "Nguyễn Văn An"
        assert call_args["email"] == "nva@ctf.local"
        assert call_args["password"] == "Pass1"
