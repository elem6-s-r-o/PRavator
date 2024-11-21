import unittest
from unittest.mock import Mock, patch, mock_open
from src.main import (
    load_config,
    get_all_objects,
    get_custom_objects,
    process_objects,
    main
)

class TestMain(unittest.TestCase):
    def setUp(self):
        """Nastavení před každým testem"""
        self.mock_sf = Mock()
        self.test_config = {
            'record_types': ['Customer', 'Partner'],
            'fields': {
                'read': ['Name', 'Description'],
                'edit': ['Status']
            }
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
        
        with patch('builtins.open', mock_open(read_data=mock_yaml)):
            config = load_config('Account')
            
            self.assertEqual(config['record_types'], ['Customer', 'Partner'])
            self.assertEqual(config['fields']['read'], ['Name', 'Description'])
            self.assertEqual(config['fields']['edit'], ['Status'])

    def test_load_config_file_not_found(self):
        """Test načtení konfigurace - soubor neexistuje"""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = FileNotFoundError()
            
            with self.assertRaises(FileNotFoundError):
                load_config('NonexistentObject')

    def test_get_all_objects_success(self):
        """Test získání všech objektů"""
        self.mock_sf.describe.return_value = {
            'sobjects': [
                {'name': 'Account'},
                {'name': 'Contact'},
                {'name': 'Custom__c'}
            ]
        }
        
        result = get_all_objects(self.mock_sf)
        
        self.assertEqual(result, ['Account', 'Contact', 'Custom__c'])
        self.mock_sf.describe.assert_called_once()

    def test_get_custom_objects_success(self):
        """Test získání custom objektů"""
        self.mock_sf.describe.return_value = {
            'sobjects': [
                {'name': 'Account', 'custom': False},
                {'name': 'Contact', 'custom': False},
                {'name': 'Custom__c', 'custom': True}
            ]
        }
        
        result = get_custom_objects(self.mock_sf)
        
        self.assertEqual(result, ['Custom__c'])
        self.mock_sf.describe.assert_called_once()

    @patch('src.main.load_config')
    @patch('src.main.create_permission_set')
    @patch('src.main.set_field_permissions')
    def test_process_objects_success(self, mock_set_permissions, mock_create_ps, mock_load_config):
        """Test úspěšného zpracování objektů"""
        mock_load_config.return_value = self.test_config
        mock_create_ps.return_value = 'PS_ID'
        
        process_objects(self.mock_sf, ['Account'])
        
        # Ověření volání funkcí
        mock_load_config.assert_called_once_with('Account')
        self.assertEqual(mock_create_ps.call_count, 2)  # Pro každý record type
        self.assertEqual(mock_set_permissions.call_count, 4)  # Pro každou kombinaci record type a access level

    @patch('src.main.load_config')
    def test_process_objects_config_error(self, mock_load_config):
        """Test zpracování objektů - chyba při načítání konfigurace"""
        mock_load_config.side_effect = FileNotFoundError()
        
        # Nemělo by vyhodit výjimku, ale pokračovat na další objekt
        process_objects(self.mock_sf, ['Account', 'Contact'])

    @patch('src.main.connect_to_salesforce')
    @patch('src.main.get_all_objects')
    @patch('src.main.process_objects')
    @patch('src.main.load_dotenv')
    def test_main_all_objects(self, mock_load_dotenv, mock_process, mock_get_all, mock_connect):
        """Test hlavní funkce - zpracování všech objektů"""
        mock_connect.return_value = self.mock_sf
        mock_get_all.return_value = ['Account', 'Contact']
        
        with patch('sys.argv', ['script.py', '--all']):
            main()
            
            mock_connect.assert_called_once()
            mock_get_all.assert_called_once()
            mock_process.assert_called_once_with(self.mock_sf, ['Account', 'Contact'])

if __name__ == '__main__':
    unittest.main()
