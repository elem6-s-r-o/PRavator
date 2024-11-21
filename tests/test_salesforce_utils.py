import unittest
from unittest.mock import Mock, patch
from src.salesforce_utils import connect_to_salesforce, create_permission_set, set_field_permissions

class TestSalesforceUtils(unittest.TestCase):
    def setUp(self):
        """Nastavení před každým testem"""
        self.mock_sf = Mock()
        self.test_username = "test@example.com"
        self.test_password = "password123"
        self.test_token = "security_token"
        self.test_domain = "test.salesforce.com"

    @patch('src.salesforce_utils.Salesforce')
    def test_connect_to_salesforce_success(self, mock_salesforce):
        """Test úspěšného připojení k Salesforce"""
        mock_salesforce.return_value = self.mock_sf
        
        result = connect_to_salesforce(
            self.test_username,
            self.test_password,
            self.test_token,
            self.test_domain
        )
        
        mock_salesforce.assert_called_once_with(
            username=self.test_username,
            password=self.test_password,
            security_token=self.test_token,
            domain=self.test_domain
        )
        self.assertEqual(result, self.mock_sf)

    @patch('src.salesforce_utils.Salesforce')
    def test_connect_to_salesforce_failure(self, mock_salesforce):
        """Test neúspěšného připojení k Salesforce"""
        mock_salesforce.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception):
            connect_to_salesforce(
                self.test_username,
                self.test_password,
                self.test_token,
                self.test_domain
            )

    def test_create_permission_set_success(self):
        """Test úspěšného vytvoření permission setu"""
        self.mock_sf.PermissionSet.create.return_value = {
            'success': True,
            'id': '0PS1234567890'
        }
        
        result = create_permission_set(
            self.mock_sf,
            'Account',
            'Customer'
        )
        
        self.mock_sf.PermissionSet.create.assert_called_once()
        self.assertEqual(result, '0PS1234567890')

    def test_create_permission_set_failure(self):
        """Test neúspěšného vytvoření permission setu"""
        self.mock_sf.PermissionSet.create.return_value = {
            'success': False,
            'errors': ['Permission set already exists']
        }
        
        with self.assertRaises(Exception):
            create_permission_set(
                self.mock_sf,
                'Account',
                'Customer'
            )

    def test_set_field_permissions_success(self):
        """Test úspěšného nastavení oprávnění pro pole"""
        self.mock_sf.FieldPermissions.create.return_value = {
            'success': True
        }
        
        fields = ['Name', 'Description']
        
        set_field_permissions(
            self.mock_sf,
            'PS_ID',
            'Account',
            fields,
            'read'
        )
        
        # Ověření, že create byl volán pro každé pole
        self.assertEqual(
            self.mock_sf.FieldPermissions.create.call_count,
            len(fields)
        )

    def test_set_field_permissions_failure(self):
        """Test neúspěšného nastavení oprávnění pro pole"""
        self.mock_sf.FieldPermissions.create.return_value = {
            'success': False,
            'errors': ['Invalid field']
        }
        
        with self.assertRaises(Exception):
            set_field_permissions(
                self.mock_sf,
                'PS_ID',
                'Account',
                ['InvalidField'],
                'read'
            )

if __name__ == '__main__':
    unittest.main()
