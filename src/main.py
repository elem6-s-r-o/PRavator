import os
import yaml
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from elem6_logger import get_logger
from salesforce_utils import connect_to_salesforce, create_permission_set, set_field_permissions

logger = get_logger(__name__)

def load_config(object_name: str) -> Dict[str, Any]:
    """
    Načtení konfigurace pro daný objekt z YAML souboru.

    Args:
        object_name (str): Název Salesforce objektu

    Returns:
        Dict[str, Any]: Konfigurace objektu

    Raises:
        FileNotFoundError: Pokud konfigurační soubor neexistuje
        yaml.YAMLError: Pokud se nepodaří načíst YAML soubor
    """
    try:
        config_path = f"config/{object_name}.yaml"
        logger.info(f"Načítání konfigurace z {config_path}")
        
        with open(config_path, 'r') as f:
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
    Získání seznamu všech objektů v Salesforce.

    Args:
        sf: Instance Salesforce připojení

    Returns:
        List[str]: Seznam názvů objektů
    """
    try:
        logger.info("Získávání seznamu všech objektů")
        describe = sf.describe()
        objects = [obj['name'] for obj in describe['sobjects']]
        logger.info(f"Nalezeno {len(objects)} objektů")
        return objects
    except Exception as e:
        logger.error(f"Chyba při získávání seznamu objektů: {str(e)}")
        raise

def get_custom_objects(sf) -> List[str]:
    """
    Získání seznamu všech custom objektů v Salesforce.

    Args:
        sf: Instance Salesforce připojení

    Returns:
        List[str]: Seznam názvů custom objektů
    """
    try:
        logger.info("Získávání seznamu custom objektů")
        describe = sf.describe()
        objects = [obj['name'] for obj in describe['sobjects'] if obj['custom']]
        logger.info(f"Nalezeno {len(objects)} custom objektů")
        return objects
    except Exception as e:
        logger.error(f"Chyba při získávání seznamu custom objektů: {str(e)}")
        raise

def process_objects(sf, objects: List[str]) -> None:
    """
    Zpracování seznamu objektů a nastavení jejich oprávnění.

    Args:
        sf: Instance Salesforce připojení
        objects (List[str]): Seznam objektů ke zpracování
    """
    for object_name in objects:
        try:
            logger.info(f"Zpracovávání objektu {object_name}")
            
            # Načtení konfigurace pro objekt
            config = load_config(object_name)
            
            # Vytvoření permission setu pro každý record type
            for record_type in config.get('record_types', ['']):
                permission_set_id = create_permission_set(sf, object_name, record_type)
                
                # Nastavení oprávnění pro pole
                fields = config.get('fields', {})
                for access_level, field_list in fields.items():
                    set_field_permissions(
                        sf,
                        permission_set_id,
                        object_name,
                        field_list,
                        access_level
                    )
                    
            logger.info(f"Objekt {object_name} úspěšně zpracován")
            
        except Exception as e:
            logger.error(f"Chyba při zpracování objektu {object_name}: {str(e)}")
            continue

def main():
    """
    Hlavní funkce programu.
    """
    parser = argparse.ArgumentParser(description="PRavator: Salesforce Permission Manager")
    parser.add_argument("-a", "--all", action="store_true", help="Zpracovat všechny objekty")
    parser.add_argument("-ca", "--custom-all", action="store_true", help="Zpracovat všechny custom objekty")
    parser.add_argument("-o", "--objects", nargs="+", help="Konkrétní objekty ke zpracování")
    
    args = parser.parse_args()

    try:
        # Načtení proměnných prostředí
        load_dotenv()
        
        # Připojení k Salesforce
        sf = connect_to_salesforce(
            os.getenv('SF_USERNAME'),
            os.getenv('SF_PASSWORD'),
            os.getenv('SF_SECURITY_TOKEN'),
            os.getenv('SF_DOMAIN')
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
