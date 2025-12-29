"""
Google Calendar integration service.

This module provides functions for creating, updating, and deleting calendar events
linked to tasks.
"""

from datetime import datetime, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class CalendarService:
    """Service for interacting with Google Calendar API."""

    def __init__(self, access_token: str, refresh_token: str):
        """
        Initialize Calendar Service with OAuth credentials.

        Args:
            access_token: Google OAuth access token
            refresh_token: Google OAuth refresh token
        """
        # Create credentials object from tokens
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Will be set when needed
            client_secret=None,  # Will be set when needed
        )
        self.service = build("calendar", "v3", credentials=self.credentials)

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """
        Create a calendar event.

        Args:
            title: Event title
            start_time: Event start time (timezone-aware datetime)
            duration_minutes: Event duration in minutes
            description: Optional event description
            location: Optional event location

        Returns:
            dict: Created event object with 'id', 'htmlLink', etc.

        Raises:
            HttpError: If the API request fails
        """
        # Calculate end time
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Build event object
        event = {
            "summary": title,
            "description": description or "",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": str(start_time.tzinfo) if start_time.tzinfo else "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": str(end_time.tzinfo) if end_time.tzinfo else "UTC",
            },
        }

        if location:
            event["location"] = location

        try:
            # Insert event into primary calendar
            created_event = (
                self.service.events()
                .insert(calendarId="primary", body=event)
                .execute()
            )
            return created_event
        except HttpError as error:
            raise error

    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """
        Update an existing calendar event.

        Args:
            event_id: Google Calendar event ID
            title: Optional new title
            start_time: Optional new start time
            duration_minutes: Optional new duration in minutes
            description: Optional new description
            location: Optional new location

        Returns:
            dict: Updated event object

        Raises:
            HttpError: If the API request fails
        """
        try:
            # Get existing event
            event = (
                self.service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )

            # Update fields
            if title:
                event["summary"] = title

            if description is not None:
                event["description"] = description

            if location is not None:
                event["location"] = location

            if start_time and duration_minutes:
                end_time = start_time + timedelta(minutes=duration_minutes)
                event["start"] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": str(start_time.tzinfo) if start_time.tzinfo else "UTC",
                }
                event["end"] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": str(end_time.tzinfo) if end_time.tzinfo else "UTC",
                }

            # Update event
            updated_event = (
                self.service.events()
                .update(calendarId="primary", eventId=event_id, body=event)
                .execute()
            )
            return updated_event
        except HttpError as error:
            raise error

    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: Google Calendar event ID

        Returns:
            bool: True if deleted successfully

        Raises:
            HttpError: If the API request fails
        """
        try:
            self.service.events().delete(
                calendarId="primary", eventId=event_id
            ).execute()
            return True
        except HttpError as error:
            if error.resp.status == 404:
                # Event already deleted or doesn't exist
                return True
            raise error

    async def get_event(self, event_id: str) -> Optional[dict]:
        """
        Get a calendar event by ID.

        Args:
            event_id: Google Calendar event ID

        Returns:
            Optional[dict]: Event object or None if not found
        """
        try:
            event = (
                self.service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )
            return event
        except HttpError as error:
            if error.resp.status == 404:
                return None
            raise error
