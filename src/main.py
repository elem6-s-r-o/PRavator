import argparse
import os
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv
from elem6_logger import Elem6Logger

from src.salesforce_utils import (
    connect_to_salesforce,
    create_edit_permission_set,
    create_permission_set,
    set_field_permissions,
)

logger = Elem6Logger.get_logger(__name__)


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


def setup_permissions(sf, object_name: str, config: Dict[str, Any]) -> None:
    """
    Set up permissions for a Salesforce object.

    Args:
        sf: Authenticated Salesforce instance
        object_name (str): Name of the Salesforce object
        config (Dict[str, Any]): Configuration data for the object

    Raises:
        Exception: If setting up permissions fails
    """
    try:
        logger.info(f"Setting up permissions for object {object_name}")

        # Create basic permission set
        basic_ps_id = create_permission_set(sf, object_name, "basic")

        # Create edit permission set
        edit_ps_id = create_edit_permission_set(sf, object_name)

        # Set field permissions according to configuration
        fields = config.get("fields", {})

        # Set read permissions
        if "read" in fields:
            set_field_permissions(sf, basic_ps_id, object_name, fields["read"], "read")
            set_field_permissions(sf, edit_ps_id, object_name, fields["read"], "read")

        # Set edit permissions
        if "edit" in fields:
            set_field_permissions(sf, edit_ps_id, object_name, fields["edit"], "edit")

        logger.info(f"Permissions for object {object_name} successfully set")

    except Exception as e:
        logger.error(f"Error setting permissions for object {object_name}: {str(e)}")
        raise


def process_objects(sf, objects: List[str]) -> None:
    """
    Process a list of objects and set up their permissions.

    Args:
        sf: Authenticated Salesforce instance
        objects (List[str]): List of objects to process

    Note:
        If processing of one object fails, it continues with the next object
    """
    for object_name in objects:
        try:
            logger.info(f"Processing object {object_name}")
            config = load_config(object_name)
            setup_permissions(sf, object_name, config)
            logger.info(f"Object {object_name} successfully processed")
        except Exception as e:
            logger.error(f"Error processing object {object_name}: {str(e)}")
            continue


def main():
    """
    Main function to set up permissions for Salesforce objects.
    Supports processing all objects, all custom objects, or specific objects.
    """
    parser = argparse.ArgumentParser(description="PRavator: Salesforce Permission Manager")
    parser.add_argument("-a", "--all", action="store_true", help="Process all objects")
    parser.add_argument(
        "-ca", "--custom-all", action="store_true", help="Process all custom objects"
    )
    parser.add_argument("-o", "--objects", nargs="+", help="Specific objects to process")

    args = parser.parse_args()

    try:
        # Load environment variables
        load_dotenv()

        # Connect to Salesforce
        sf = connect_to_salesforce(
            os.getenv("SF_USERNAME"),
            os.getenv("SF_PASSWORD"),
            os.getenv("SF_SECURITY_TOKEN"),
            os.getenv("SF_DOMAIN"),
        )

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
        process_objects(sf, objects)

        logger.info("Program successfully completed")

    except Exception as e:
        logger.error(f"Critical program error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
