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


# Create a singleton instance
sfdc_manager = SalesforceManager()
