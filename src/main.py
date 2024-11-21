import argparse
import os
from typing import List

from dotenv import load_dotenv
from elem6_logger import Elem6Logger

from src.salesforce_manager import sfdc_manager

logger = Elem6Logger.get_logger(__name__)


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
        print("Getting list of all objects")
        describe = sf.describe()
        objects = [obj["name"] for obj in describe["sobjects"]]
        print(f"Found {len(objects)} objects")
        return objects
    except Exception as e:
        print(f"Error getting list of objects: {str(e)}")
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
        print("Getting list of custom objects")
        describe = sf.describe()
        objects = [obj["name"] for obj in describe["sobjects"] if obj["custom"]]
        print(f"Found {len(objects)} custom objects")
        return objects
    except Exception as e:
        print(f"Error getting list of custom objects: {str(e)}")
        raise


def process_objects(sf, objects: List[str], verbose: bool = False) -> None:
    """
    Process a list of objects and display their details.

    Args:
        sf: Authenticated Salesforce instance
        objects (List[str]): List of objects to process
        verbose (bool): Whether to show detailed information
    """
    for object_name in objects:
        try:
            print(f"\nProcessing object {object_name}")

            # Get object description
            describe = sf.Order6__c.describe()
            print("\nObject details:")
            print(f"  Label: {describe['label']}")
            print(f"  API Name: {describe['name']}")
            print(f"  Custom: {describe['custom']}")
            print(f"  Createable: {describe['createable']}")
            print(f"  Updateable: {describe['updateable']}")
            print(f"  Deletable: {describe['deletable']}")
            print(f"  Number of fields: {len(describe['fields'])}")

            if verbose:
                # Show field details in verbose mode
                print("\nField details:")
                for field in describe["fields"]:
                    print(f"\n  {field['name']}:")
                    print(f"    Label: {field['label']}")
                    print(f"    Type: {field['type']}")
                    print(f"    Custom: {field['custom']}")
                    print(f"    Createable: {field['createable']}")
                    print(f"    Updateable: {field['updateable']}")
                    print(f"    Nillable: {field['nillable']}")

            # Get some records
            query = f"SELECT Id, Name FROM {object_name} LIMIT 5"
            print(f"\nExecuting query: {query}")
            result = sf.query(query)

            print(f"Found {result['totalSize']} records")
            if verbose:
                for record in result["records"]:
                    print(f"  Record ID: {record['Id']}, Name: {record.get('Name', 'N/A')}")

            print(f"\nObject {object_name} successfully processed")

        except Exception as e:
            print(f"Error processing object {object_name}: {str(e)}")
            continue


def main():
    """
    Main function to explore Salesforce objects.
    Supports processing all objects, all custom objects, or specific objects.
    """
    parser = argparse.ArgumentParser(description="PRavator: Salesforce Object Explorer")
    parser.add_argument("-a", "--all", action="store_true", help="Process all objects")
    parser.add_argument(
        "-ca", "--custom-all", action="store_true", help="Process all custom objects"
    )
    parser.add_argument("-o", "--objects", nargs="+", help="Specific objects to process")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed information")

    args = parser.parse_args()

    try:
        # Load environment variables
        load_dotenv()

        # Connect to Salesforce using context manager
        with sfdc_manager.connect() as sf:
            # Get API usage
            remaining, max_requests = sfdc_manager.get_api_usage()
            print(f"\nAPI Usage: {remaining}/{max_requests} requests remaining")

            # Determine objects to process
            if args.all:
                objects = get_all_objects(sf)
            elif args.custom_all:
                objects = get_custom_objects(sf)
            elif args.objects:
                objects = args.objects
            else:
                print("No objects specified for processing")
                parser.print_help()
                return

            # Process objects
            process_objects(sf, objects, args.verbose)

            print("\nProgram successfully completed")

    except Exception as e:
        print(f"Critical program error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
