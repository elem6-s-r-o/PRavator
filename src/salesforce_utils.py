from elem6_logger import Elem6Logger
from simple_salesforce import Salesforce

logger = Elem6Logger.get_logger(__name__)


def connect_to_salesforce(
    username: str, password: str, security_token: str, domain: str
) -> Salesforce:
    """
    Establish a connection to Salesforce.

    Args:
        username (str): Salesforce username
        password (str): Salesforce password
        security_token (str): Salesforce security token
        domain (str): Salesforce domain (e.g., 'test' or 'login')

    Returns:
        Salesforce: Authenticated Salesforce instance

    Raises:
        Exception: If connection fails
    """
    try:
        logger.info(f"Připojování k Salesforce s uživatelem {username}")
        sf = Salesforce(
            username=username, password=password, security_token=security_token, domain=domain
        )
        logger.info("Úspěšně připojeno k Salesforce")
        return sf
    except Exception as e:
        logger.error(f"Chyba při připojování k Salesforce: {str(e)}")
        raise


def create_permission_set(sf: Salesforce, object_name: str, record_type: str) -> str:
    """
    Create a permission set for a given Salesforce object and record type.

    Args:
        sf (Salesforce): Authenticated Salesforce instance
        object_name (str): Name of the Salesforce object
        record_type (str): Record type ('basic' or 'edit')

    Returns:
        str: ID of the created permission set

    Raises:
        Exception: If permission set creation fails
    """
    try:
        permission_set_name = f"{object_name}_{record_type}_Permissions"
        logger.info(f"Vytváření permission setu {permission_set_name}")

        result = sf.PermissionSet.create(
            {
                "Name": permission_set_name,
                "Label": f"{object_name} {record_type} Permissions",
                "Description": f"Permission set pro {object_name} s record typem {record_type}",
            }
        )

        if result.get("success"):
            logger.info(f"Permission set {permission_set_name} úspěšně vytvořen")
            return result.get("id")
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
    access_level: str = "read",
) -> None:
    """
    Set field permissions for a given permission set.

    Args:
        sf (Salesforce): Authenticated Salesforce instance
        permission_set_name (str): ID of the permission set
        object_name (str): Name of the Salesforce object
        fields (list[str]): List of fields to set permissions for
        access_level (str, optional): Access level ('read' or 'edit'). Defaults to 'read'.

    Raises:
        Exception: If setting field permissions fails
        ValueError: If invalid access_level is provided
    """
    if access_level not in ["read", "edit"]:
        raise ValueError("access_level must be either 'read' or 'edit'")

    try:
        logger.info(f"Nastavování oprávnění pro {len(fields)} polí v objektu {object_name}")

        for field in fields:
            field_permission = {
                "Field": f"{object_name}.{field}",
                "PermissionsRead": True if access_level in ["read", "edit"] else False,
                "PermissionsEdit": True if access_level == "edit" else False,
                "ParentId": permission_set_name,
            }

            result = sf.FieldPermissions.create(field_permission)

            if result.get("success"):
                logger.debug(f"Oprávnění pro pole {field} úspěšně nastaveno")
            else:
                raise Exception(
                    f"Nepodařilo se nastavit oprávnění pro pole {field}: {result.get('errors')}"
                )

        logger.info(f"Oprávnění pro všechna pole úspěšně nastavena")

    except Exception as e:
        logger.error(f"Chyba při nastavování oprávnění: {str(e)}")
        raise


def create_edit_permission_set(sf: Salesforce, object_name: str) -> str:
    """
    Create an edit permission set for a given Salesforce object.
    This is a convenience function that creates a permission set with edit access.

    Args:
        sf (Salesforce): Authenticated Salesforce instance
        object_name (str): Name of the Salesforce object

    Returns:
        str: ID of the created edit permission set

    Raises:
        Exception: If permission set creation fails
    """
    return create_permission_set(sf, object_name, "edit")
