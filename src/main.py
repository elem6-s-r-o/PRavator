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
        logger.info(f"Načítání konfigurace z {config_path}")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        logger.debug(f"Konfigurace úspěšně načtena: {config}")
        return config
    except FileNotFoundError:
        logger.error(f"Konfigurační soubor {config_path} nenalezen")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Chyba při načítání YAML souboru: {str(e)}")
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
        logger.info("Získávání seznamu všech objektů")
        describe = sf.describe()
        objects = [obj["name"] for obj in describe["sobjects"]]
        logger.info(f"Nalezeno {len(objects)} objektů")
        return objects
    except Exception as e:
        logger.error(f"Chyba při získávání seznamu objektů: {str(e)}")
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
        logger.info("Získávání seznamu custom objektů")
        describe = sf.describe()
        objects = [obj["name"] for obj in describe["sobjects"] if obj["custom"]]
        logger.info(f"Nalezeno {len(objects)} custom objektů")
        return objects
    except Exception as e:
        logger.error(f"Chyba při získávání seznamu custom objektů: {str(e)}")
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
        logger.info(f"Nastavování oprávnění pro objekt {object_name}")

        # Vytvoření základního permission setu
        basic_ps_id = create_permission_set(sf, object_name, "basic")

        # Vytvoření edit permission setu
        edit_ps_id = create_edit_permission_set(sf, object_name)

        # Nastavení oprávnění pro pole podle konfigurace
        fields = config.get("fields", {})

        # Nastavení read oprávnění
        if "read" in fields:
            set_field_permissions(sf, basic_ps_id, object_name, fields["read"], "read")
            set_field_permissions(sf, edit_ps_id, object_name, fields["read"], "read")

        # Nastavení edit oprávnění
        if "edit" in fields:
            set_field_permissions(sf, edit_ps_id, object_name, fields["edit"], "edit")

        logger.info(f"Oprávnění pro objekt {object_name} úspěšně nastavena")

    except Exception as e:
        logger.error(f"Chyba při nastavování oprávnění pro objekt {object_name}: {str(e)}")
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
            logger.info(f"Zpracovávání objektu {object_name}")
            config = load_config(object_name)
            setup_permissions(sf, object_name, config)
            logger.info(f"Objekt {object_name} úspěšně zpracován")
        except Exception as e:
            logger.error(f"Chyba při zpracování objektu {object_name}: {str(e)}")
            continue


def main():
    """
    Main function to set up permissions for Salesforce objects.
    Supports processing all objects, all custom objects, or specific objects.
    """
    parser = argparse.ArgumentParser(description="PRavator: Salesforce Permission Manager")
    parser.add_argument("-a", "--all", action="store_true", help="Zpracovat všechny objekty")
    parser.add_argument(
        "-ca", "--custom-all", action="store_true", help="Zpracovat všechny custom objekty"
    )
    parser.add_argument("-o", "--objects", nargs="+", help="Konkrétní objekty ke zpracování")

    args = parser.parse_args()

    try:
        # Načtení proměnných prostředí
        load_dotenv()

        # Připojení k Salesforce
        sf = connect_to_salesforce(
            os.getenv("SF_USERNAME"),
            os.getenv("SF_PASSWORD"),
            os.getenv("SF_SECURITY_TOKEN"),
            os.getenv("SF_DOMAIN"),
        )

        # Určení objektů ke zpracování
        if args.all:
            objects = get_all_objects(sf)
        elif args.custom_all:
            objects = get_custom_objects(sf)
        elif args.objects:
            objects = args.objects
        else:
            logger.error("Nebyl specifikován žádný objekt ke zpracování")
            parser.print_help()
            return

        # Zpracování objektů
        process_objects(sf, objects)

        logger.info("Program úspěšně dokončen")

    except Exception as e:
        logger.error(f"Kritická chyba programu: {str(e)}")
        raise


if __name__ == "__main__":
    main()
