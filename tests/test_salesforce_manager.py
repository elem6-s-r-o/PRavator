import os
from unittest.mock import MagicMock, patch

import pytest

from src.salesforce_manager import SalesforceManager


class TestSalesforceManager:
    @pytest.fixture
    def manager(self):
        return SalesforceManager()

    @pytest.fixture
    def mock_env(self):
        env = {
            "SF_USERNAME": "test@example.com",
            "SF_PASSWORD": "password123",
            "SF_SECURITY_TOKEN": "token123",
            "SF_DOMAIN": "test.salesforce.com",
        }
        with patch.dict(os.environ, env):
            yield env

    def test_create_connection(self, manager, mock_env):
        with patch("src.salesforce_manager.Salesforce") as mock_sf:
            connection = manager.create_connection()
            mock_sf.assert_called_once_with(
                username=mock_env["SF_USERNAME"],
                password=mock_env["SF_PASSWORD"],
                security_token=mock_env["SF_SECURITY_TOKEN"],
                instance=mock_env["SF_DOMAIN"],
            )
            assert connection == mock_sf.return_value

    def test_connect_context_manager(self, manager):
        mock_connection = MagicMock()
        with patch.object(manager, "create_connection", return_value=mock_connection):
            with manager.connect() as conn:
                assert conn == mock_connection
                assert manager.connection == mock_connection
            assert manager.connection is None

    def test_connect_error_handling(self, manager):
        with patch.object(manager, "create_connection", side_effect=Exception("Connection error")):
            with pytest.raises(Exception) as exc_info:
                with manager.connect():
                    pass
            assert str(exc_info.value) == "Connection error"
            assert manager.connection is None

    def test_get_api_usage(self, manager):
        mock_connection = MagicMock()
        mock_connection.limits.return_value = {
            "DailyApiRequests": {"Remaining": 15000, "Max": 50000}
        }
        manager.connection = mock_connection

        remaining, max_requests = manager.get_api_usage()
        assert remaining == 15000
        assert max_requests == 50000
        mock_connection.limits.assert_called_once()

    def test_get_api_usage_no_connection(self, manager):
        with pytest.raises(RuntimeError) as exc_info:
            manager.get_api_usage()
        assert str(exc_info.value) == "No active Salesforce connection"

    def test_get_api_usage_error(self, manager):
        mock_connection = MagicMock()
        mock_connection.limits.side_effect = Exception("API error")
        manager.connection = mock_connection

        with pytest.raises(Exception) as exc_info:
            manager.get_api_usage()
        assert str(exc_info.value) == "Failed to get API usage: API error"

    def test_create_permission_set_success(self, manager):
        mock_connection = MagicMock()
        mock_connection.PermissionSet.create.return_value = {"success": True, "id": "0PS1234567890"}
        manager.connection = mock_connection

        result = manager.create_permission_set("Account", "basic")
        assert result == "0PS1234567890"
        mock_connection.PermissionSet.create.assert_called_once()

    def test_create_permission_set_no_connection(self, manager):
        with pytest.raises(RuntimeError) as exc_info:
            manager.create_permission_set("Account", "basic")
        assert str(exc_info.value) == "No active Salesforce connection"

    def test_create_permission_set_failure(self, manager):
        mock_connection = MagicMock()
        mock_connection.PermissionSet.create.return_value = {
            "success": False,
            "errors": ["Permission set already exists"],
        }
        manager.connection = mock_connection

        with pytest.raises(Exception) as exc_info:
            manager.create_permission_set("Account", "basic")
        assert "Failed to create permission set" in str(exc_info.value)

    def test_set_field_permissions_success(self, manager):
        mock_connection = MagicMock()
        mock_connection.FieldPermissions.create.return_value = {"success": True}
        manager.connection = mock_connection

        fields = ["Name", "Description"]
        manager.set_field_permissions("PS_ID", "Account", fields, "read")

        assert mock_connection.FieldPermissions.create.call_count == len(fields)

    def test_set_field_permissions_no_connection(self, manager):
        with pytest.raises(RuntimeError) as exc_info:
            manager.set_field_permissions("PS_ID", "Account", ["Name"], "read")
        assert str(exc_info.value) == "No active Salesforce connection"

    def test_set_field_permissions_invalid_access_level(self, manager):
        manager.connection = MagicMock()
        with pytest.raises(ValueError) as exc_info:
            manager.set_field_permissions("PS_ID", "Account", ["Name"], "invalid")
        assert str(exc_info.value) == "access_level must be either 'read' or 'edit'"

    def test_set_field_permissions_failure(self, manager):
        mock_connection = MagicMock()
        mock_connection.FieldPermissions.create.return_value = {
            "success": False,
            "errors": ["Invalid field"],
        }
        manager.connection = mock_connection

        with pytest.raises(Exception) as exc_info:
            manager.set_field_permissions("PS_ID", "Account", ["InvalidField"], "read")
        assert "Failed to set permissions for field" in str(exc_info.value)

    def test_create_edit_permission_set(self, manager):
        mock_connection = MagicMock()
        mock_connection.PermissionSet.create.return_value = {"success": True, "id": "0PS1234567890"}
        manager.connection = mock_connection

        result = manager.create_edit_permission_set("Account")
        assert result == "0PS1234567890"
        mock_connection.PermissionSet.create.assert_called_once()
