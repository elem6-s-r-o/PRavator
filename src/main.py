import argparse
import os
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from elem6_logger import Elem6Logger

try:
    from src.salesforce_manager import sfdc_manager
except ImportError:
    from salesforce_manager import sfdc_manager

logger = Elem6Logger.get_logger(__name__)


def get_permission_set(sf, permission_set_name: str) -> Optional[Dict[str, Any]]:
    """
    Check if permission set exists.

    Args:
        sf: Authenticated Salesforce instance
        permission_set_name (str): Name of the permission set

    Returns:
        Optional[Dict[str, Any]]: Permission set data if exists, None otherwise
    """
    try:
        query = f"SELECT Id, Name FROM PermissionSet WHERE Name = '{permission_set_name}'"
        result = sf.query(query)
        return result["records"][0] if result["totalSize"] > 0 else None
    except Exception as e:
        logger.error(f"Error checking permission set existence: {str(e)}")
        raise


def get_record_types(sf, object_name: str) -> List[Dict[str, Any]]:
    """
    Get record types for an object.

    Args:
        sf: Authenticated Salesforce instance
        object_name (str): Name of the Salesforce object

    Returns:
        List[Dict[str, Any]]: List of record types
    """
    try:
        query = (
            f"SELECT Id, Name, DeveloperName FROM RecordType WHERE SObjectType = '{object_name}'"
        )
        result = sf.query(query)
        return result["records"]
    except Exception as e:
        logger.error(f"Error getting record types: {str(e)}")
        raise


def create_config_template(sf, object_name: str) -> None:
    """
    Create a YAML configuration template for a Salesforce object.

    Args:
        sf: Authenticated Salesforce instance
        object_name (str): Name of the Salesforce object
    """
    try:
        logger.info(f"Creating configuration template for {object_name}")

        # Get object description
        describe = sf.Order6__c.describe()

        # Get record types
        record_types = get_record_types(sf, object_name)
        if record_types:
            logger.info(f"Found record types for {object_name}:")
            for rt in record_types:
                logger.info(f"  {rt['DeveloperName']}")
        else:
            logger.info(f"No record types found for {object_name}, using 'Master'")
            record_types = [{"DeveloperName": "Master"}]

        # Get all field names
        fields = [field["name"] for field in describe["fields"]]

        # Get standard fields that should be restricted
        standard_restricted = [
            "Id",
            "OwnerId",
            "IsDeleted",
            "SystemModstamp",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "LastActivityDate",
        ]

        # Create template configuration
        template = {
            f"# Configuration for {object_name} object permissions": None,
            "record_types": [rt["DeveloperName"] for rt in record_types],
            "fields": [field for field in fields if field not in standard_restricted],
            "restricted_fields": standard_restricted,
        }

        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)

        # Write template to file
        config_path = f"config/{object_name}.yaml"
        with open(config_path, "w") as f:
            yaml.dump(template, f, sort_keys=False, default_flow_style=False)

        logger.info(f"Configuration template created at {config_path}")

    except Exception as e:
        logger.error(f"Error creating configuration template: {str(e)}")
        raise


def load_config(object_name: str) -> Dict[str, Any]:
    """
    Load configuration for a Salesforce object from a YAML file.

    Args:
        object_name (str): Name of the Salesforce object

    Returns:
        Dict[str, Any]: Configuration data for the object

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If there's an error parsing the YAML file
    """
    try:
        config_path = f"config/{object_name}.yaml"
        logger.info(f"Loading configuration from {config_path}")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        logger.debug(f"Configuration successfully loaded: {config}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error loading YAML file: {str(e)}")
        raise


def get_all_objects(sf) -> List[str]:
    """
    Get a list of all objects in Salesforce.

    Args:
        sf: Authenticated Salesforce instance

    Returns:
        List[str]: List of object names

    Raises:
        Exception: If retrieving objects fails
    """
    try:
        logger.info("Getting list of all objects")
        describe = sf.describe()
        objects = [obj["name"] for obj in describe["sobjects"]]
        logger.info(f"Found {len(objects)} objects")
        return objects
    except Exception as e:
        logger.error(f"Error getting list of objects: {str(e)}")
        raise


def get_custom_objects(sf) -> List[str]:
    """
    Get a list of all custom objects in Salesforce.

    Args:
        sf: Authenticated Salesforce instance

    Returns:
        List[str]: List of custom object names

    Raises:
        Exception: If retrieving custom objects fails
    """
    try:
        logger.info("Getting list of custom objects")
        describe = sf.describe()
        objects = [obj["name"] for obj in describe["sobjects"] if obj["custom"]]
        logger.info(f"Found {len(objects)} custom objects")
        return objects
    except Exception as e:
        logger.error(f"Error getting list of custom objects: {str(e)}")
        raise


def create_permission_set(sf, object_name: str, permission_type: str) -> str:
    """
    Create a permission set for a Salesforce object.

    Args:
        sf: Authenticated Salesforce instance
        object_name (str): Name of the Salesforce object
        permission_type (str): Type of permission set (e.g., 'basic', 'edit')

    Returns:
        str: ID of the created permission set

    Raises:
        Exception: If permission set creation fails
    """
    try:
        permission_set_name = f"{object_name}_{permission_type}"

        # Check if permission set already exists
        existing_ps = get_permission_set(sf, permission_set_name)
        if existing_ps:
            logger.info(f"Permission set {permission_set_name} already exists")
            return existing_ps["Id"]

        logger.info(f"Creating permission set {permission_set_name}")

        result = sf.PermissionSet.create(
            {
                "Name": permission_set_name,
                "Label": f"{object_name} {permission_type} Permissions",
                "Description": f"Permission set for {object_name}",
            }
        )

        if result.get("success"):
            logger.info(f"Permission set {permission_set_name} created successfully")
            return result.get("id")
        else:
            raise Exception(f"Failed to create permission set: {result.get('errors')}")

    except Exception as e:
        logger.error(f"Error creating permission set: {str(e)}")
        raise


def set_field_permissions(sf, permission_set_id: str, object_name: str, fields: List[str]) -> None:
    """
    Set field permissions for a permission set.

    Args:
        sf: Authenticated Salesforce instance
        permission_set_id (str): ID of the permission set
        object_name (str): Name of the Salesforce object
        fields (List[str]): List of fields to set permissions for

    Raises:
        Exception: If setting field permissions fails
    """
    try:
        logger.info(f"Setting field permissions for {len(fields)} fields")

        for field in fields:
            field_permission = {
                "Field": f"{object_name}.{field}",
                "PermissionsRead": True,
                "PermissionsEdit": False,
                "ParentId": permission_set_id,
            }

            result = sf.FieldPermissions.create(field_permission)

            if result.get("success"):
                logger.debug(f"Field permission set for {field}")
            else:
                raise Exception(f"Failed to set field permission: {result.get('errors')}")

        logger.info("Field permissions set successfully")

    except Exception as e:
        logger.error(f"Error setting field permissions: {str(e)}")
        raise


def process_objects(
    sf, objects: List[str], verbose: bool = False, create_template: bool = False
) -> None:
    """
    Process a list of objects and set up their permissions.

    Args:
        sf: Authenticated Salesforce instance
        objects (List[str]): List of objects to process
        verbose (bool): Whether to show detailed information
        create_template (bool): Whether to create configuration templates
    """
    for object_name in objects:
        try:
            logger.info(f"Processing object {object_name}")

            # Get record types
            record_types = get_record_types(sf, object_name)
            if record_types:
                logger.info(f"Found record types for {object_name}:")
                for rt in record_types:
                    logger.info(f"  {rt['DeveloperName']}")
            else:
                logger.info(f"No record types found for {object_name}, using 'Master'")

            if create_template:
                create_config_template(sf, object_name)
                continue

            # Load configuration
            config = load_config(object_name)

            # Create basic permission set
            permission_set_id = create_permission_set(sf, object_name, "basic")

            # Set field permissions
            allowed_fields = [
                field
                for field in config.get("fields", [])
                if field not in config.get("restricted_fields", [])
            ]
            set_field_permissions(sf, permission_set_id, object_name, allowed_fields)

            if verbose:
                # Show object details
                describe = sf.Order6__c.describe()
                logger.info("Object details:")
                logger.info(f"  Label: {describe['label']}")
                logger.info(f"  API Name: {describe['name']}")
                logger.info(f"  Custom: {describe['custom']}")
                logger.info(f"  Number of fields: {len(describe['fields'])}")
                logger.info(f"  Allowed fields: {len(allowed_fields)}")
                logger.info(f"  Restricted fields: {len(config.get('restricted_fields', []))}")

            logger.info(f"Object {object_name} successfully processed")

        except Exception as e:
            logger.error(f"Error processing object {object_name}: {str(e)}")
            continue


def main():
    """
    Main function to set up Salesforce object permissions.
    Supports processing all objects, all custom objects, or specific objects.
    """
    parser = argparse.ArgumentParser(description="PRavator: Salesforce Permission Manager")
    parser.add_argument("-a", "--all", action="store_true", help="Process all objects")
    parser.add_argument(
        "-ca", "--custom-all", action="store_true", help="Process all custom objects"
    )
    parser.add_argument("-o", "--objects", nargs="+", help="Specific objects to process")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed information")
    parser.add_argument(
        "-t",
        "--create-template",
        action="store_true",
        help="Create YAML configuration templates for objects",
    )

    args = parser.parse_args()

    try:
        # Load environment variables
        load_dotenv()

        # Connect to Salesforce using context manager
        with sfdc_manager.connect() as sf:
            # Get API usage
            remaining, max_requests = sfdc_manager.get_api_usage()
            logger.info(f"API Usage: {remaining}/{max_requests} requests remaining")

            # Determine objects to process
            if args.all:
                objects = get_all_objects(sf)
            elif args.custom_all:
                objects = get_custom_objects(sf)
            elif args.objects:
                objects = args.objects
            else:
                logger.error("No objects specified for processing")
                parser.print_help()
                return

            # Process objects
            process_objects(sf, objects, args.verbose, args.create_template)

            logger.info("Program successfully completed")

    except Exception as e:
        logger.error(f"Critical program error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
