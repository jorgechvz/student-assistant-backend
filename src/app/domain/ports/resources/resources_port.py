"""Resources Port Interface."""

from abc import ABC, abstractmethod


class ResourcesPort(ABC):
    """Interface for Canvas LMS operations."""

    @abstractmethod
    def canvas_connection(self, access_token: str) -> None:
        """Create a connection to the Canvas LMS using the provided access token.

        Args:
            access_token (str): The access token for authenticating with Canvas LMS.
        """

    @abstractmethod
    def nootion_connection(self, access_token: str) -> None:
        """Create a connection to Notion using the provided access token.

        Args:
            access_token (str): The access token for authenticating with Notion.
        """

    @abstractmethod
    def google_calendar_connection(self, access_token: str) -> None:
        """Create a connection to Google Calendar using the provided access token.

        Args:
            access_token (str): The access token for authenticating with Google Calendar.
        """
