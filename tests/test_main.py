import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_modules():
    mock_loader = MagicMock()
    mock_templates = MagicMock()
    mock_sfdc_manager = MagicMock()
    mock_sfdc_manager.connect.return_value.__enter__.return_value = MagicMock()
    mock_sfdc_manager.connect.return_value.__exit__.return_value = None
    mock_sfdc_manager.get_api_usage.return_value = (100, 200)  # (remaining, max_requests)

    with patch("src.main.load_config", mock_loader), patch(
        "src.main.create_config_template", mock_templates
    ), patch("src.main.sfdc_manager", mock_sfdc_manager):
        yield {
            "loader": mock_loader,
            "templates": mock_templates,
            "sfdc_manager": mock_sfdc_manager,
        }


class TestMain:
    def test_get_all_objects_success(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.describe.return_value = {
            "sobjects": [{"name": "Account"}, {"name": "Contact"}]
        }

        from src.main import get_all_objects

        result = get_all_objects()
        assert result == ["Account", "Contact"]
        mock_connection.describe.assert_called_once()

    def test_get_all_objects_failure(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.describe.side_effect = Exception("API Error")

        from src.main import get_all_objects

        with pytest.raises(Exception) as exc_info:
            get_all_objects()
        assert str(exc_info.value) == "API Error"

    def test_get_custom_objects_success(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.describe.return_value = {
            "sobjects": [
                {"name": "Account", "custom": False},
                {"name": "Custom__c", "custom": True},
            ]
        }

        from src.main import get_custom_objects

        result = get_custom_objects()
        assert result == ["Custom__c"]
        mock_connection.describe.assert_called_once()

    def test_get_custom_objects_failure(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.describe.side_effect = Exception("API Error")

        from src.main import get_custom_objects

        with pytest.raises(Exception) as exc_info:
            get_custom_objects()
        assert str(exc_info.value) == "API Error"

    def test_load_object_config_success(self, mock_modules, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "Account.yaml"
        config_file.write_text(
            """
record_types:
  - Customer
  - Partner
  - Supplier
fields:
  read:
    - Name
    - Description
    - Industry
    - Type
    - Website
    - Phone
    - BillingAddress
    - ShippingAddress
    - AccountNumber
    - Site
    - AccountSource
    - AnnualRevenue
    - NumberOfEmployees
    - Ownership
    - TickerSymbol
    - Rating
    - ParentId
    - CreatedDate
    - LastModifiedDate
  edit:
    - Name
    - Description
    - Industry
    - Type
    - Website
    - Phone
    - BillingStreet
    - BillingCity
    - BillingState
    - BillingPostalCode
    - BillingCountry
    - ShippingStreet
    - ShippingCity
    - ShippingState
    - ShippingPostalCode
    - ShippingCountry
    - AccountSource
    - AnnualRevenue
    - NumberOfEmployees
    - Rating
restricted_fields:
  - OwnerId
  - SystemModstamp
  - LastActivityDate
  - Jigsaw
  - JigsawCompanyId
  - CleanStatus
"""
        )

        expected_config = {
            "record_types": ["Customer", "Partner", "Supplier"],
            "fields": {
                "read": [
                    "Name",
                    "Description",
                    "Industry",
                    "Type",
                    "Website",
                    "Phone",
                    "BillingAddress",
                    "ShippingAddress",
                    "AccountNumber",
                    "Site",
                    "AccountSource",
                    "AnnualRevenue",
                    "NumberOfEmployees",
                    "Ownership",
                    "TickerSymbol",
                    "Rating",
                    "ParentId",
                    "CreatedDate",
                    "LastModifiedDate",
                ],
                "edit": [
                    "Name",
                    "Description",
                    "Industry",
                    "Type",
                    "Website",
                    "Phone",
                    "BillingStreet",
                    "BillingCity",
                    "BillingState",
                    "BillingPostalCode",
                    "BillingCountry",
                    "ShippingStreet",
                    "ShippingCity",
                    "ShippingState",
                    "ShippingPostalCode",
                    "ShippingCountry",
                    "AccountSource",
                    "AnnualRevenue",
                    "NumberOfEmployees",
                    "Rating",
                ],
            },
            "restricted_fields": [
                "OwnerId",
                "SystemModstamp",
                "LastActivityDate",
                "Jigsaw",
                "JigsawCompanyId",
                "CleanStatus",
            ],
        }

        mock_modules["loader"].return_value = expected_config
        with patch("src.main.os.getcwd", return_value=str(tmp_path)):
            from src.main import load_object_config

            result = load_object_config("Account")
            assert result == expected_config

    def test_load_object_config_file_not_found(self, mock_modules):
        from src.main import load_object_config

        with pytest.raises(FileNotFoundError):
            load_object_config("NonExistentObject")

    def test_load_object_config_invalid_yaml(self, mock_modules, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "Invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        mock_modules["loader"].side_effect = Exception("Invalid YAML")
        with patch("src.main.os.getcwd", return_value=str(tmp_path)):
            from src.main import load_object_config

            with pytest.raises(Exception):
                load_object_config("Invalid")

    def test_setup_permissions_success(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.PermissionSet.create.return_value = {"success": True, "id": "123"}
        mock_connection.FieldPermissions.create.return_value = {"success": True}

        config = {"fields": {"read": ["Name", "Description"], "edit": ["Status"]}}

        from src.main import setup_permissions

        setup_permissions(mock_connection, "Account", config)
        assert mock_connection.PermissionSet.create.call_count == 2
        assert mock_connection.FieldPermissions.create.call_count >= 3

    def test_setup_permissions_failure(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.PermissionSet.create.side_effect = Exception("Permission Set Error")

        config = {"fields": {"read": ["Name"], "edit": ["Status"]}}

        from src.main import setup_permissions

        with pytest.raises(Exception) as exc_info:
            setup_permissions(mock_connection, "Account", config)
        assert str(exc_info.value) == "Error setting up permissions: Permission Set Error"

    def test_process_objects_success(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.PermissionSet.create.return_value = {"success": True, "id": "123"}

        objects = ["Account"]
        config = {"fields": {"read": ["Name"], "edit": ["Status"]}}

        mock_modules["loader"].return_value = config
        from src.main import process_objects

        process_objects(mock_connection, objects)
        mock_connection.PermissionSet.create.assert_called()

    def test_process_objects_config_error(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        objects = ["Account", "Invalid"]

        mock_modules["loader"].side_effect = FileNotFoundError
        from src.main import process_objects

        process_objects(mock_connection, objects)
        mock_connection.PermissionSet.create.assert_not_called()

    def test_main_all_objects(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.describe.return_value = {
            "sobjects": [{"name": "Account"}, {"name": "Contact"}]
        }
        mock_connection.PermissionSet.create.return_value = {"success": True, "id": "123"}

        config = {"fields": {"read": ["Name"], "edit": ["Status"]}}

        mock_modules["loader"].return_value = config
        with patch("sys.argv", ["main.py", "--all"]):
            from src.main import main

            main()
            mock_connection.describe.assert_called()

    def test_main_custom_objects(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.describe.return_value = {
            "sobjects": [
                {"name": "Account", "custom": False},
                {"name": "Custom__c", "custom": True},
            ]
        }
        mock_connection.PermissionSet.create.return_value = {"success": True, "id": "123"}

        config = {"fields": {"read": ["Name"], "edit": ["Status"]}}

        mock_modules["loader"].return_value = config
        with patch("sys.argv", ["main.py", "--custom-all"]):
            from src.main import main

            main()
            mock_connection.describe.assert_called()

    def test_main_specific_objects(self, mock_modules):
        mock_connection = mock_modules["sfdc_manager"].connect.return_value.__enter__.return_value
        mock_connection.PermissionSet.create.return_value = {"success": True, "id": "123"}

        config = {"fields": {"read": ["Name"], "edit": ["Status"]}}

        mock_modules["loader"].return_value = config
        with patch("sys.argv", ["main.py", "--objects", "Account", "Contact"]):
            from src.main import main

            main()
            mock_connection.PermissionSet.create.assert_called()

    def test_main_no_objects(self, mock_modules):
        with patch("sys.argv", ["main.py"]):
            from src.main import main

            with pytest.raises(SystemExit):
                main()
            mock_modules["sfdc_manager"].describe.assert_not_called()
