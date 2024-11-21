import unittest
from unittest.mock import Mock, call, mock_open, patch

from src.main import (
    get_all_objects,
    get_custom_objects,
    load_config,
    main,
    process_objects,
    setup_permissions,
)


class TestMain(unittest.TestCase):
    def setUp(self):
        """Nastavení před každým testem"""
        self.mock_sf = Mock()
        self.test_config = {
            "record_types": ["Customer", "Partner"],
            "fields": {"read": ["Name", "Description"], "edit": ["Status"]},
        }

    def test_load_config_success(self):
        """Test úspěšného načtení konfigurace"""
        mock_yaml = """
        record_types:
          - Customer
          - Partner
        fields:
          read:
            - Name
            - Description
          edit:
            - Status
        """

        with patch("builtins.open", mock_open(read_data=mock_yaml)):
            config = load_config("Account")

            self.assertEqual(config["record_types"], ["Customer", "Partner"])
            self.assertEqual(config["fields"]["read"], ["Name", "Description"])
            self.assertEqual(config["fields"]["edit"], ["Status"])

    def test_load_config_file_not_found(self):
        """Test načtení konfigurace - soubor neexistuje"""
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = FileNotFoundError()

            with self.assertRaises(FileNotFoundError):
                load_config("NonexistentObject")

    def test_get_all_objects_success(self):
        """Test získání všech objektů"""
        self.mock_sf.describe.return_value = {
            "sobjects": [{"name": "Account"}, {"name": "Contact"}, {"name": "Custom__c"}]
        }

        result = get_all_objects(self.mock_sf)

        self.assertEqual(result, ["Account", "Contact", "Custom__c"])
        self.mock_sf.describe.assert_called_once()

    def test_get_custom_objects_success(self):
        """Test získání custom objektů"""
        self.mock_sf.describe.return_value = {
            "sobjects": [
                {"name": "Account", "custom": False},
                {"name": "Contact", "custom": False},
                {"name": "Custom__c", "custom": True},
            ]
        }

        result = get_custom_objects(self.mock_sf)

        self.assertEqual(result, ["Custom__c"])
        self.mock_sf.describe.assert_called_once()

    @patch("src.main.load_config")
    @patch("src.main.create_permission_set")
    @patch("src.main.create_edit_permission_set")
    @patch("src.main.set_field_permissions")
    def test_setup_permissions_success(
        self, mock_set_permissions, mock_create_edit_ps, mock_create_ps, mock_load_config
    ):
        """Test úspěšného nastavení oprávnění"""
        mock_create_ps.return_value = "BASIC_PS_ID"
        mock_create_edit_ps.return_value = "EDIT_PS_ID"

        config = {"fields": {"read": ["Name", "Description"], "edit": ["Status"]}}

        setup_permissions(self.mock_sf, "Account", config)

        # Ověření volání funkcí
        mock_create_ps.assert_called_once_with(self.mock_sf, "Account", "basic")
        mock_create_edit_ps.assert_called_once_with(self.mock_sf, "Account")

        # Ověření volání set_field_permissions
        expected_calls = [
            call(self.mock_sf, "BASIC_PS_ID", "Account", ["Name", "Description"], "read"),
            call(self.mock_sf, "EDIT_PS_ID", "Account", ["Name", "Description"], "read"),
            call(self.mock_sf, "EDIT_PS_ID", "Account", ["Status"], "edit"),
        ]

        self.assertEqual(mock_set_permissions.call_count, 3)
        mock_set_permissions.assert_has_calls(expected_calls)

    @patch("src.main.load_config")
    def test_process_objects_config_error(self, mock_load_config):
        """Test zpracování objektů - chyba při načítání konfigurace"""
        mock_load_config.side_effect = FileNotFoundError()

        # Nemělo by vyhodit výjimku, ale pokračovat na další objekt
        process_objects(self.mock_sf, ["Account", "Contact"])

    @patch("src.main.connect_to_salesforce")
    @patch("src.main.get_all_objects")
    @patch("src.main.process_objects")
    @patch("src.main.load_dotenv")
    def test_main_all_objects(self, mock_load_dotenv, mock_process, mock_get_all, mock_connect):
        """Test hlavní funkce - zpracování všech objektů"""
        mock_connect.return_value = self.mock_sf
        mock_get_all.return_value = ["Account", "Contact"]

        with patch("sys.argv", ["script.py", "--all"]):
            main()

            mock_connect.assert_called_once()
            mock_get_all.assert_called_once()
            mock_process.assert_called_once_with(self.mock_sf, ["Account", "Contact"])


if __name__ == "__main__":
    unittest.main()
