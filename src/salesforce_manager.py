import os
from contextlib import contextmanager
from itertools import groupby
from operator import itemgetter
from typing import Any, Dict, List, Optional, Tuple

from elem6_logger import Elem6Logger
from simple_salesforce import Salesforce

logger = Elem6Logger.get_logger(__name__)


class SalesforceManager:
    """
    Manages Salesforce connections and operations.
    """

    def __init__(self):
        self.connection: Optional[Salesforce] = None

    def create_connection(self) -> Salesforce:
        """Create a new Salesforce connection."""
        return Salesforce(
            username=os.getenv("SF_USERNAME"),
            password=os.getenv("SF_PASSWORD"),
            security_token=os.getenv("SF_SECURITY_TOKEN"),
            instance=os.getenv("SF_DOMAIN"),
        )

    @contextmanager
    def connect(self):
        """Context manager for handling Salesforce connection."""
        try:
            logger.info("Establishing Salesforce connection...")
            self.connection = self.create_connection()
            logger.info("Salesforce connection established successfully")
            yield self.connection
        except Exception as e:
            logger.error("Failed to connect to Salesforce", exc_info=True)
            raise
        finally:
            self.connection = None

    def get_api_usage(self) -> Tuple[int, int]:
        """
        Získá aktuální využití API limitů ze Salesforce.

        Returns:
            Tuple[int, int]: (použité limity, celkové limity)
        """
        if not self.connection:
            raise RuntimeError("No active Salesforce connection")

        try:
            limits = self.connection.limits()
            daily_api_requests = limits["DailyApiRequests"]
            return daily_api_requests["Remaining"], daily_api_requests["Max"]
        except Exception as e:
            logger.error(f"Failed to get API usage: {e}", exc_info=True)
            raise Exception(f"Failed to get API usage: {str(e)}")

    def create_permission_set(self, object_name: str, record_type: str) -> str:
        """
        Create a permission set for a given Salesforce object and record type.

        Args:
            object_name (str): Name of the Salesforce object
            record_type (str): Record type ('basic' or 'edit')

        Returns:
            str: ID of the created permission set

        Raises:
            Exception: If permission set creation fails
        """
        if not self.connection:
            raise RuntimeError("No active Salesforce connection")

        try:
            permission_set_name = f"{object_name}_{record_type}_Permissions"
            logger.info(f"Creating permission set {permission_set_name}")

            result = self.connection.PermissionSet.create(
                {
                    "Name": permission_set_name,
                    "Label": f"{object_name} {record_type} Permissions",
                    "Description": f"Permission set for {object_name} with record type {record_type}",
                }
            )

            if result.get("success"):
                logger.info(f"Permission set {permission_set_name} successfully created")
                return result.get("id")
            else:
                raise Exception(f"Failed to create permission set: {result.get('errors')}")

        except Exception as e:
            logger.error(f"Error creating permission set: {str(e)}")
            raise

    def set_field_permissions(
        self,
        permission_set_name: str,
        object_name: str,
        fields: List[str],
        access_level: str = "read",
    ) -> None:
        """
        Set field permissions for a given permission set.

        Args:
            permission_set_name (str): ID of the permission set
            object_name (str): Name of the Salesforce object
            fields (List[str]): List of fields to set permissions for
            access_level (str, optional): Access level ('read' or 'edit'). Defaults to 'read'.

        Raises:
            Exception: If setting field permissions fails
            ValueError: If invalid access_level is provided
        """
        if not self.connection:
            raise RuntimeError("No active Salesforce connection")

        if access_level not in ["read", "edit"]:
            raise ValueError("access_level must be either 'read' or 'edit'")

        try:
            logger.info(f"Setting permissions for {len(fields)} fields in object {object_name}")

            for field in fields:
                field_permission = {
                    "Field": f"{object_name}.{field}",
                    "PermissionsRead": True if access_level in ["read", "edit"] else False,
                    "PermissionsEdit": True if access_level == "edit" else False,
                    "ParentId": permission_set_name,
                }

                result = self.connection.FieldPermissions.create(field_permission)

                if result.get("success"):
                    logger.debug(f"Permissions for field {field} successfully set")
                else:
                    raise Exception(
                        f"Failed to set permissions for field {field}: {result.get('errors')}"
                    )

            logger.info(f"Permissions for all fields successfully set")

        except Exception as e:
            logger.error(f"Error setting permissions: {str(e)}")
            raise

    def create_edit_permission_set(self, object_name: str) -> str:
        """
        Create an edit permission set for a given Salesforce object.
        This is a convenience function that creates a permission set with edit access.

        Args:
            object_name (str): Name of the Salesforce object

        Returns:
            str: ID of the created edit permission set

        Raises:
            Exception: If permission set creation fails
        """
        return self.create_permission_set(object_name, "edit")


# Create a singleton instance
sfdc_manager = SalesforceManager()
