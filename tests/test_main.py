import os
from unittest.mock import MagicMock, patch

import pytest

from src.main import (
    get_all_objects,
    get_custom_objects,
    load_config,
    main,
    process_objects,
    setup_permissions,
)


class TestMain:
    @pytest.fixture
    def mock_sf(self):
        mock = MagicMock()
        mock.describe.return_value = {"sobjects": [{"name": "Account"}, {"name": "Contact"}]}
        return mock

    def test_get_all_objects_success(self, mock_sf):
        result = get_all_objects(mock_sf)
        assert result == ["Account", "Contact"]
        mock_sf.describe.assert_called_once()

    def test_get_all_objects_failure(self, mock_sf):
        mock_sf.describe.side_effect = Exception("API Error")
        with pytest.raises(Exception) as exc_info:
            get_all_objects(mock_sf)
        assert str(exc_info.value) == "API Error"

    def test_get_custom_objects_success(self, mock_sf):
        mock_sf.describe.return_value = {
            "sobjects": [
                {"name": "Account", "custom": False},
                {"name": "Custom__c", "custom": True},
            ]
        }
        result = get_custom_objects(mock_sf)
        assert result == ["Custom__c"]
        mock_sf.describe.assert_called_once()

    def test_get_custom_objects_failure(self, mock_sf):
        mock_sf.describe.side_effect = Exception("API Error")
        with pytest.raises(Exception) as exc_info:
            get_custom_objects(mock_sf)
        assert str(exc_info.value) == "API Error"

    def test_load_config_success(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir.parent / "config" / "Account.yaml"
        config_file.write_text(
            """# Configuration for Account object permissions
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
  - CleanStatus"""
        )

        with patch("src.main.os.getcwd", return_value=str(tmp_path)):
            result = load_config("Account")
            expected = {
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
            assert result == expected

    def test_load_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("NonExistentObject")

    def test_load_config_invalid_yaml(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir.parent / "config" / "Invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        with patch("src.main.os.getcwd", return_value=str(tmp_path)):
            with pytest.raises(Exception):
                load_config("Invalid")

    def test_setup_permissions_success(self, mock_sf):
        config = {
            "fields": {
                "read": ["Name", "Description"],
                "edit": ["Status"],
            }
        }
        mock_sf.PermissionSet.create.return_value = {"success": True, "id": "123"}
        mock_sf.FieldPermissions.create.return_value = {"success": True}

        setup_permissions(mock_sf, "Account", config)

        assert mock_sf.PermissionSet.create.call_count == 2
        assert mock_sf.FieldPermissions.create.call_count >= 3

    def test_setup_permissions_failure(self, mock_sf):
        config = {
            "fields": {
                "read": ["Name"],
                "edit": ["Status"],
            }
        }
        mock_sf.PermissionSet.create.side_effect = Exception("Permission Set Error")

        with pytest.raises(Exception) as exc_info:
            setup_permissions(mock_sf, "Account", config)
        assert str(exc_info.value) == "Permission Set Error"

    def test_process_objects_success(self, mock_sf):
        objects = ["Account"]
        config = {
            "fields": {
                "read": ["Name"],
                "edit": ["Status"],
            }
        }

        with patch("src.main.load_config", return_value=config):
            process_objects(mock_sf, objects)

        mock_sf.PermissionSet.create.assert_called()

    def test_process_objects_config_error(self, mock_sf):
        objects = ["Account", "Invalid"]

        with patch("src.main.load_config", side_effect=FileNotFoundError):
            process_objects(mock_sf, objects)

        mock_sf.PermissionSet.create.assert_not_called()

    def test_main_all_objects(self, mock_sf):
        with patch("src.main.connect_to_salesforce", return_value=mock_sf), patch(
            "src.main.load_dotenv"
        ), patch("sys.argv", ["main.py", "--all"]):
            main()

        mock_sf.describe.assert_called()

    def test_main_custom_objects(self, mock_sf):
        mock_sf.describe.return_value = {
            "sobjects": [
                {"name": "Account", "custom": False},
                {"name": "Custom__c", "custom": True},
            ]
        }
        with patch("src.main.connect_to_salesforce", return_value=mock_sf), patch(
            "src.main.load_dotenv"
        ), patch("sys.argv", ["main.py", "--custom-all"]):
            main()

        mock_sf.describe.assert_called()

    def test_main_specific_objects(self, mock_sf):
        with patch("src.main.connect_to_salesforce", return_value=mock_sf), patch(
            "src.main.load_dotenv"
        ), patch("sys.argv", ["main.py", "--objects", "Account", "Contact"]):
            main()

        mock_sf.PermissionSet.create.assert_called()

    def test_main_no_objects(self, mock_sf):
        with patch("src.main.connect_to_salesforce", return_value=mock_sf), patch(
            "src.main.load_dotenv"
        ), patch("sys.argv", ["main.py"]):
            main()

        mock_sf.describe.assert_not_called()
