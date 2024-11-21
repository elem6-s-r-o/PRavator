from simple_salesforce import Salesforce
from elem6_logger import get_logger

logger = get_logger(__name__)

def connect_to_salesforce(username: str, password: str, security_token: str, domain: str) -> Salesforce:
    """
    Připojení k Salesforce instanci.

    Args:
        username (str): Salesforce uživatelské jméno
        password (str): Salesforce heslo
        security_token (str): Salesforce security token
        domain (str): Salesforce doména (např. 'test.salesforce.com' nebo 'login.salesforce.com')

    Returns:
        Salesforce: Instance Salesforce připojení

    Raises:
        Exception: Pokud se nepodaří připojit k Salesforce
    """
    try:
        logger.info(f"Připojování k Salesforce s uživatelem {username}")
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain
        )
        logger.info("Úspěšně připojeno k Salesforce")
        return sf
    except Exception as e:
        logger.error(f"Chyba při připojování k Salesforce: {str(e)}")
        raise

def create_permission_set(sf: Salesforce, object_name: str, record_type: str) -> str:
    """
    Vytvoření permission setu pro daný objekt a record type.

    Args:
        sf (Salesforce): Instance Salesforce připojení
        object_name (str): Název Salesforce objektu
        record_type (str): Název record typu

    Returns:
        str: ID vytvořeného permission setu

    Raises:
        Exception: Pokud se nepodaří vytvořit permission set
    """
    try:
        permission_set_name = f"{object_name}_{record_type}_Permissions"
        logger.info(f"Vytváření permission setu {permission_set_name}")
        
        result = sf.PermissionSet.create({
            'Name': permission_set_name,
            'Label': f"{object_name} {record_type} Permissions",
            'Description': f"Permission set pro {object_name} s record typem {record_type}"
        })
        
        if result.get('success'):
            logger.info(f"Permission set {permission_set_name} úspěšně vytvořen")
            return result.get('id')
        else:
            raise Exception(f"Nepodařilo se vytvořit permission set: {result.get('errors')}")
            
    except Exception as e:
        logger.error(f"Chyba při vytváření permission setu: {str(e)}")
        raise

def set_field_permissions(
    sf: Salesforce,
    permission_set_name: str,
    object_name: str,
    fields: list[str],
    access_level: str = 'read'
) -> None:
    """
    Nastavení oprávnění pro pole objektu v permission setu.

    Args:
        sf (Salesforce): Instance Salesforce připojení
        permission_set_name (str): Název permission setu
        object_name (str): Název Salesforce objektu
        fields (list[str]): Seznam polí pro nastavení oprávnění
        access_level (str, optional): Úroveň přístupu ('read' nebo 'edit'). Výchozí je 'read'.

    Raises:
        Exception: Pokud se nepodaří nastavit oprávnění
    """
    try:
        logger.info(f"Nastavování oprávnění pro {len(fields)} polí v objektu {object_name}")
        
        for field in fields:
            field_permission = {
                'Field': f"{object_name}.{field}",
                'PermissionsRead': True if access_level in ['read', 'edit'] else False,
                'PermissionsEdit': True if access_level == 'edit' else False,
                'ParentId': permission_set_name
            }
            
            result = sf.FieldPermissions.create(field_permission)
            
            if result.get('success'):
                logger.debug(f"Oprávnění pro pole {field} úspěšně nastaveno")
            else:
                raise Exception(f"Nepodařilo se nastavit oprávnění pro pole {field}: {result.get('errors')}")
                
        logger.info(f"Oprávnění pro všechna pole úspěšně nastavena")
        
    except Exception as e:
        logger.error(f"Chyba při nastavování oprávnění: {str(e)}")
        raise
