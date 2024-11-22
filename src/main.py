import argparse
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

import yaml
from elem6_logger import Elem6Logger
from simple_salesforce.exceptions import SalesforceError

from .config.loader import load_config
from .config.templates import create_config_template
from .salesforce_manager import sfdc_manager

logger = Elem6Logger.get_logger(__name__)


def check_permission_set_exists(permission_set_name: str) -> bool:
    try:
        with sfdc_manager.connect() as connection:
            result = connection.query(
                f"SELECT Id FROM PermissionSet WHERE Name = '{permission_set_name}'"
            )
            return bool(result["totalSize"])
    except Exception as e:
        logger.error(f"Error checking permission set existence: {str(e)}")
        return False


def get_record_types(object_name: str) -> List[Dict]:
    try:
        with sfdc_manager.connect() as connection:
            query = f"""
                SELECT Id, Name, DeveloperName, IsActive
                FROM RecordType
                WHERE SobjectType = '{object_name}'
                AND IsActive = true
            """
            result = connection.query(query)
            return result["records"]
    except Exception as e:
        logger.error(f"Error getting record types: {str(e)}")
        return []


def create_object_config_template(object_name: str) -> None:
    try:
        logger.info(f"Creating configuration template for {object_name}")

        record_types = get_record_types(object_name)
        if record_types:
            logger.info(f"Found record types for {object_name}:")
            for rt in record_types:
                logger.info(f"  {rt['DeveloperName']}")
        else:
            logger.info(f"No record types found for {object_name}, using 'Master'")

        config_path = create_config_template(object_name, record_types)
        logger.info(f"Configuration template created at {config_path}")

    except Exception as e:
        logger.error(f"Error creating configuration template: {str(e)}")


def load_object_config(object_name: str) -> Dict:
    config_path = os.path.join("config", f"{object_name}.yaml")
    try:
        logger.info(f"Loading configuration from {config_path}")
        if not os.path.exists(config_path):
            logger.error(f"Configuration file {config_path} not found")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        config = load_config(config_path)
        logger.debug(f"Configuration successfully loaded: {config}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error loading YAML file: {str(e)}")
        raise


def get_all_objects() -> List[str]:
    try:
        logger.info("Getting list of all objects")
        with sfdc_manager.connect() as connection:
            describe = connection.describe()
            objects = [obj["name"] for obj in describe["sobjects"]]
            logger.info(f"Found {len(objects)} objects")
            return objects
    except Exception as e:
        logger.error(f"Error getting list of objects: {str(e)}")
        raise


def get_custom_objects() -> List[str]:
    try:
        logger.info("Getting list of custom objects")
        with sfdc_manager.connect() as connection:
            describe = connection.describe()
            objects = [obj["name"] for obj in describe["sobjects"] if obj["custom"]]
            logger.info(f"Found {len(objects)} custom objects")
            return objects
    except Exception as e:
        logger.error(f"Error getting list of custom objects: {str(e)}")
        raise


def setup_permissions(connection, object_name: str, config: Dict) -> None:
    """Setup permissions for a Salesforce object based on configuration."""
    try:
        # Create read permission set
        read_permission_set = connection.PermissionSet.create(
            {"Name": f"{object_name}_read_Permissions", "Label": f"{object_name} Read Permissions"}
        )

        # Create edit permission set
        edit_permission_set = connection.PermissionSet.create(
            {"Name": f"{object_name}_edit_Permissions", "Label": f"{object_name} Edit Permissions"}
        )

        # Set field permissions
        for field in config.get("fields", {}).get("read", []):
            connection.FieldPermissions.create(
                {
                    "ParentId": read_permission_set["id"],
                    "SobjectType": object_name,
                    "Field": f"{object_name}.{field}",
                    "PermissionsRead": True,
                    "PermissionsEdit": False,
                }
            )

        for field in config.get("fields", {}).get("edit", []):
            connection.FieldPermissions.create(
                {
                    "ParentId": edit_permission_set["id"],
                    "SobjectType": object_name,
                    "Field": f"{object_name}.{field}",
                    "PermissionsRead": True,
                    "PermissionsEdit": True,
                }
            )

    except Exception as e:
        raise Exception(f"Error setting up permissions: {str(e)}")


def process_objects(
    connection, objects: List[str], verbose: bool = False, create_template: bool = False
) -> None:
    for object_name in objects:
        try:
            logger.info(f"Processing object {object_name}")

            if create_template:
                create_object_config_template(object_name)
                continue

            try:
                config = load_object_config(object_name)
            except FileNotFoundError:
                logger.error(f"Configuration file not found for {object_name}")
                continue

            record_types = get_record_types(object_name)
            if record_types:
                logger.info(f"Found record types for {object_name}:")
                for rt in record_types:
                    logger.info(f"  {rt['DeveloperName']}")
            else:
                logger.info(f"No record types found for {object_name}, using 'Master'")

            if verbose:
                describe = connection.describe()
                logger.info("Object details:")
                logger.info(f"  Label: {describe['label']}")
                logger.info(f"  API Name: {describe['name']}")
                logger.info(f"  Custom: {describe['custom']}")
                logger.info(f"  Number of fields: {len(describe['fields'])}")

                allowed_fields = [
                    f
                    for f in describe["fields"]
                    if f["name"] not in config.get("restricted_fields", [])
                ]
                logger.info(f"  Allowed fields: {len(allowed_fields)}")
                logger.info(f"  Restricted fields: {len(config.get('restricted_fields', []))}")

            setup_permissions(connection, object_name, config)
            logger.info(f"Object {object_name} successfully processed")

        except SalesforceError as e:
            logger.error(f"Error processing object {object_name}: {str(e)}")


def main():
    try:
        parser = argparse.ArgumentParser(
            description="PRavator: Salesforce Permission Manager",
            epilog="Example usage:\n"
            "  Process all objects:           python main.py --all\n"
            "  Process custom objects:        python main.py --custom-all\n"
            "  Process specific objects:      python main.py --objects Account Contact\n"
            "  Create config templates:       python main.py --objects Account --create-template\n"
            "  Debug mode with verbose:       python main.py --objects Account --debug --verbose",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Process all Salesforce objects (standard and custom). This option will analyze and process permissions for every object in your org.",
        )
        parser.add_argument(
            "-ca",
            "--custom-all",
            action="store_true",
            help="Process all custom Salesforce objects only. This excludes standard objects and focuses only on custom objects in your org.",
        )
        parser.add_argument(
            "-o",
            "--objects",
            nargs="+",
            help="Specify one or more Salesforce objects to process. Example: --objects Account Contact Lead",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Set verbosity level: -v for WARNING, -vv for ERROR, -vvv for CRITICAL. Each additional v increases the logging detail.",
        )
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Enable debug mode with maximum logging detail. Useful for troubleshooting issues.",
        )
        parser.add_argument(
            "-t",
            "--create-template",
            action="store_true",
            help="Generate YAML configuration templates for specified objects. These templates can be customized for permission management.",
        )

        args = parser.parse_args()

        # Set logging level based on arguments
        if args.debug:
            logger.setLevel(logging.DEBUG)
        elif args.verbose == 1:
            logger.setLevel(logging.WARNING)
        elif args.verbose == 2:
            logger.setLevel(logging.ERROR)
        elif args.verbose >= 3:
            logger.setLevel(logging.CRITICAL)
        else:
            logger.setLevel(logging.INFO)

        try:
            with sfdc_manager.connect() as connection:
                api_usage = sfdc_manager.get_api_usage()
                if not isinstance(api_usage, tuple) or len(api_usage) != 2:
                    raise ValueError("Invalid API usage format")
                remaining, max_requests = api_usage
                logger.info(f"API Usage: {remaining}/{max_requests} requests remaining")

                if args.all:
                    objects = get_all_objects()
                elif args.custom_all:
                    objects = get_custom_objects()
                elif args.objects:
                    objects = args.objects
                else:
                    logger.error("No objects specified for processing")
                    sys.exit(1)

                process_objects(
                    connection, objects, args.verbose > 0 or args.debug, args.create_template
                )
                logger.info("Program successfully completed")

        except Exception as e:
            logger.error(f"Critical program error: {str(e)}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Critical program error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
