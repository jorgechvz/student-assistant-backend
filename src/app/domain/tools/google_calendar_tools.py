"""Google Calendar Integration Tools for LangChain agents.

Provides a comprehensive set of tools for managing Google Calendar events,
including creating, updating, deleting, and querying events with proper
timezone handling.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from langchain.tools import tool

_logger = logging.getLogger(__name__)


class GoogleCalendarHelper:
    """Shared utilities for Google Calendar tools."""

    CALENDAR_BASE = "/calendar/v3/calendars/primary/events"
    SETTINGS_TIMEZONE = "/calendar/v3/users/me/settings/timezone"

    def __init__(self, google_service, user_id: str):
        self.google_service = google_service
        self.user_id = user_id
        self._cached_timezone: str | None = None

    async def get_user_timezone(self) -> str:
        """Fetch the user's timezone from Google Calendar settings.

        Caches the result so subsequent calls are instant.
        Falls back to 'America/New_York' if the API call fails.
        """
        if self._cached_timezone:
            return self._cached_timezone
        try:
            response = await self.google_service.make_google_request(
                user_id=self.user_id,
                method="GET",
                endpoint=self.SETTINGS_TIMEZONE,
            )
            tz = response.get("value", "America/New_York")
            self._cached_timezone = tz
            return tz
        except Exception as e:
            _logger.warning("Failed to fetch user timezone: %s", e)
            return "America/New_York"

    async def resolve_timezone(self, provided_tz: str | None) -> str:
        """Use provided timezone or auto-detect from Google Calendar."""
        if provided_tz and provided_tz != "auto":
            return provided_tz
        return await self.get_user_timezone()

    async def api_get(
        self,
        endpoint: str | None = None,
        params: dict | None = None,
    ) -> dict:
        """GET request to Google Calendar API."""
        endpoint = endpoint or self.CALENDAR_BASE
        return await self.google_service.make_google_request(
            user_id=self.user_id,
            method="GET",
            endpoint=endpoint,
            params=params,
        )

    async def api_post(
        self,
        data: dict,
        endpoint: str | None = None,
        params: dict | None = None,
    ) -> dict:
        """POST request to Google Calendar API."""
        endpoint = endpoint or self.CALENDAR_BASE
        return await self.google_service.make_google_request(
            user_id=self.user_id,
            method="POST",
            endpoint=endpoint,
            data=data,
            params=params,
        )

    async def api_patch(
        self,
        event_id: str,
        data: dict,
    ) -> dict:
        """PATCH request to update an event."""
        endpoint = f"{self.CALENDAR_BASE}/{event_id}"
        return await self.google_service.make_google_request(
            user_id=self.user_id,
            method="PATCH",
            endpoint=endpoint,
            data=data,
        )

    async def api_delete(self, event_id: str) -> dict:
        """DELETE request to remove an event."""
        endpoint = f"{self.CALENDAR_BASE}/{event_id}"
        return await self.google_service.make_google_request(
            user_id=self.user_id,
            method="DELETE",
            endpoint=endpoint,
        )

    @staticmethod
    def format_event(event: dict) -> str:
        """Format a single event into a human-readable line."""
        summary = event.get("summary", "No title")
        start = event.get("start", {})
        end = event.get("end", {})
        location = event.get("location", "")
        status = event.get("status", "")
        event_id = event.get("id", "")

        if "date" in start:
            date_str = start["date"]
            end_date = end.get("date", "")
            if end_date and end_date != date_str:
                line = f"{summary} — {date_str} → {end_date} (all day)"
            else:
                line = f"{summary} — {date_str} (all day)"
        else:
            dt_str = start.get("dateTime", "")
            end_dt_str = end.get("dateTime", "")
            try:
                dt = datetime.fromisoformat(dt_str)
                start_fmt = dt.strftime("%Y-%m-%d %I:%M %p %Z")
            except (ValueError, AttributeError):
                start_fmt = dt_str
            try:
                end_dt = datetime.fromisoformat(end_dt_str)
                end_fmt = end_dt.strftime("%I:%M %p %Z")
            except (ValueError, AttributeError):
                end_fmt = end_dt_str
            line = f"{summary} — {start_fmt} to {end_fmt}"

        if location:
            line += f" | 📍 {location}"
        if status == "cancelled":
            line += " [CANCELLED]"

        line += f"  (id: {event_id})"
        return line

    @staticmethod
    def format_event_list(events: list, header: str) -> str:
        """Format a list of events with a header."""
        if not events:
            return f"{header}\nNo events found."
        lines = [f"{header}\n"]
        for event in events:
            lines.append(GoogleCalendarHelper.format_event(event))
        return "\n".join(lines)


def create_google_calendar_tools(google_service, user_id: str) -> list:
    """Create Google Calendar tools for LangChain agent.

    Args:
        google_service: GoogleService instance (async-capable)
        user_id: Authenticated user's ID

    Returns:
        List of LangChain tools for Google Calendar operations
    """
    helper = GoogleCalendarHelper(google_service, user_id)

    @tool("get_user_timezone")
    async def get_user_timezone() -> str:
        """Get the user's timezone from their Google Calendar settings.

        **CRITICAL: Call this FIRST before ANY scheduling operation.**
        The result is cached for the session.

        Use when:
        - You need to create/schedule any event
        - You need to interpret times (e.g., "2pm" → what timezone?)
        - The user asks "What's my timezone?"

        Returns:
            The user's IANA timezone (e.g., 'America/New_York', 'Europe/London').
        """
        try:
            tz = await helper.get_user_timezone()
            return (
                f"User's timezone: {tz}\n"
                f"Use this timezone for all scheduling unless the user "
                f"explicitly requests a different one."
            )
        except Exception as e:
            _logger.error("get_user_timezone failed: %s", e, exc_info=True)
            return f"❌ Failed to detect timezone: {e}"

    @tool("get_current_datetime_info")
    async def get_current_datetime_info() -> str:
        """Get the current date, time, day of week, and upcoming dates.

        **CRITICAL: Call this when the user mentions relative dates.**

        Use when the user asks:
        - "What's today's date?"
        - "Create a study plan for THIS WEEK"    → Need to know what "this week" means
        - "Schedule something for tomorrow"       → Need to know tomorrow's date
        - "What events do I have next Monday?"    → Need to map "next Monday" to a date
        - "Plan my week"                          → Need current week boundaries

        Returns:
            - Current UTC time
            - User's timezone
            - Today's day of week
            - Dates for remaining days this week
            - Dates for next week
            - Warning to never schedule events in the past
        """
        try:
            tz_name = await helper.get_user_timezone()
            now_utc = datetime.now(timezone.utc)

            weekday = now_utc.weekday()
            days_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            today_name = days_names[weekday]

            remaining_days = []
            for i in range(7 - weekday):
                future = now_utc + timedelta(days=i)
                remaining_days.append(
                    f"  {days_names[(weekday + i) % 7]}: "
                    f"{future.strftime('%Y-%m-%d')}"
                )

            next_week_start = now_utc + timedelta(days=(7 - weekday))
            next_week_days = []
            for i in range(7):
                future = next_week_start + timedelta(days=i)
                next_week_days.append(
                    f"  {days_names[i]}: {future.strftime('%Y-%m-%d')}"
                )

            return (
                f"Current UTC time: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"User's timezone: {tz_name}\n"
                f"Today is: {today_name}\n\n"
                f"Remaining days THIS week (including today):\n"
                + "\n".join(remaining_days)
                + f"\n\nNext week:\n"
                + "\n".join(next_week_days)
                + f"\n\nIMPORTANT: Always use dates from {now_utc.strftime('%Y-%m-%d')} "
                f"onwards. NEVER schedule events in the past."
            )
        except Exception as e:
            _logger.error("get_current_datetime_info failed: %s", e, exc_info=True)
            return f"❌ Failed to get current datetime: {e}"

    @tool("list_upcoming_events")
    async def list_upcoming_events(
        days: int = 7,
        max_results: int = 25,
    ) -> str:
        """List upcoming events from Google Calendar.

        Use when the user asks:
        - "What's on my calendar?"
        - "Show me my upcoming events"
        - "What do I have this week?"             → days=7
        - "What's on my calendar next month?"     → days=30
        - "Show me the next 3 days"               → days=3

        Args:
            days: Number of days to look ahead (default: 7, max: 90)
            max_results: Maximum events to return (default: 25)

        Returns:
            Formatted list of events with dates, times, locations, and IDs.
        """
        try:
            days = min(max(days, 1), 90)
            time_min = datetime.now(timezone.utc).isoformat()
            time_max = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

            params = {
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": str(max_results),
            }

            response = await helper.api_get(params=params)
            events = response.get("items", [])
            return helper.format_event_list(
                events, f"Upcoming events (next {days} days):"
            )
        except Exception as e:
            _logger.error("list_upcoming_events failed: %s", e, exc_info=True)
            return f"❌ Failed to retrieve calendar events: {e}"

    @tool("get_events_for_date")
    async def get_events_for_date(date: str) -> str:
        """Get all events for a specific date.

        Use when the user asks:
        - "What do I have on February 14?"        → date="2026-02-14"
        - "Show me my schedule for Monday"        → (after calling get_current_datetime_info)
        - "What's on my calendar tomorrow?"       → (calculate tomorrow's date first)
        - "Am I busy on the 20th?"               → date="2026-02-20"

        **IMPORTANT: Always call get_current_datetime_info first to convert
        relative dates ("tomorrow", "next Friday") to YYYY-MM-DD format.**

        Args:
            date: Date in YYYY-MM-DD format (e.g., '2026-02-14')

        Returns:
            All events scheduled for that date (including all-day events).
        """
        try:
            start = f"{date}T00:00:00Z"
            end_date = (
                datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")
            end = f"{end_date}T00:00:00Z"

            params = {
                "timeMin": start,
                "timeMax": end,
                "singleEvents": "true",
                "orderBy": "startTime",
            }

            response = await helper.api_get(params=params)
            events = response.get("items", [])
            return helper.format_event_list(events, f"Events on {date}:")
        except Exception as e:
            _logger.error("get_events_for_date failed: %s", e, exc_info=True)
            return f"❌ Failed to retrieve events for {date}: {e}"

    @tool("search_events")
    async def search_events(query: str, max_results: int = 10) -> str:
        """Search for events in Google Calendar by keyword.

        Searches across event titles, descriptions, and locations.

        Use when the user asks:
        - "Find my dentist appointment"           → query="dentist"
        - "Show me all study sessions"            → query="study"
        - "When is my CS497 meeting?"            → query="CS497"
        - "Search for events with 'interview'"    → query="interview"

        Args:
            query: Search text (matches title, description, location)
            max_results: Maximum number of results (default: 10)

        Returns:
            List of matching events with dates, times, and event IDs.
        """
        try:
            params = {
                "q": query,
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": str(max_results),
            }

            response = await helper.api_get(params=params)
            events = response.get("items", [])
            return helper.format_event_list(events, f"Events matching '{query}':")
        except Exception as e:
            _logger.error("search_events failed: %s", e, exc_info=True)
            return f"❌ Failed to search events: {e}"

    @tool("create_calendar_event")
    async def create_calendar_event(
        title: str,
        start_datetime: str,
        end_datetime: str,
        timezone_str: str = "auto",
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        """Create a new timed event in Google Calendar.

        **IMPORTANT: Timezone is auto-detected. Only specify timezone_str if the
        user explicitly requests a different timezone.**

        Use when the user asks:
        - "Create an event called 'Team Meeting' tomorrow at 2pm for 1 hour"
        - "Schedule 'Dentist Appointment' on Feb 14 at 3pm"
        - "Add 'Coffee with Sarah' on Friday at 10am to 11am"

        **Before calling this tool:**
        1. Call get_current_datetime_info to get the correct date
        2. Call get_user_timezone to confirm timezone (if needed)
        3. Convert times to ISO format: YYYY-MM-DDTHH:MM:SS

        Example flow:
        - User: "Create a meeting tomorrow at 2pm for 1 hour"
        - You: Call get_current_datetime_info → tomorrow is 2026-02-13
        - You: Call create_calendar_event(
            title="Meeting",
            start_datetime="2026-02-13T14:00:00",
            end_datetime="2026-02-13T15:00:00"
          )

        Args:
            title: Event title/summary
            start_datetime: Start in ISO format (e.g., '2026-02-14T10:00:00')
            end_datetime: End in ISO format (e.g., '2026-02-14T11:00:00')
            timezone_str: IANA timezone or 'auto' to detect (default: 'auto')
            description: Optional event description/notes
            location: Optional event location (address, room number, etc.)

        Returns:
            Confirmation with event link and ID.
        """
        try:
            tz = await helper.resolve_timezone(timezone_str)

            event_body: dict = {
                "summary": title,
                "start": {
                    "dateTime": start_datetime,
                    "timeZone": tz,
                },
                "end": {
                    "dateTime": end_datetime,
                    "timeZone": tz,
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 1440},
                        {"method": "popup", "minutes": 60},
                    ],
                },
            }

            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location

            response = await helper.api_post(data=event_body)
            event_link = response.get("htmlLink", "")
            event_id = response.get("id", "")

            return (
                f"Event created successfully!\n"
                f"Title: {title}\n"
                f"Start: {start_datetime} ({tz})\n"
                f"End: {end_datetime} ({tz})\n"
                + (f"Description: {description}\n" if description else "")
                + (f"Location: {location}\n" if location else "")
                + (f"Link: {event_link}\n" if event_link else "")
                + f"Event ID: {event_id}"
            )
        except Exception as e:
            _logger.error("create_calendar_event failed: %s", e, exc_info=True)
            return f"❌ Failed to create calendar event: {e}"

    @tool("create_all_day_event")
    async def create_all_day_event(
        title: str,
        start_date: str,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        """Create an all-day event in Google Calendar.

        Use when the user asks:
        - "Mark February 14 as 'Valentine's Day'"
        - "Create an all-day event for 'Spring Break' from March 10 to March 17"
        - "Block out next Monday as 'Day Off'"
        - "Add 'Conference' as an all-day event on the 20th"

        **Note: For multi-day events, Google uses exclusive end dates.
        For a 1-day event on Feb 14, use start='2026-02-14' end='2026-02-15'.**

        Args:
            title: Event title
            start_date: Start date in YYYY-MM-DD format (e.g., '2026-02-14')
            end_date: End date in YYYY-MM-DD format (optional, defaults to start_date + 1 day)
            description: Optional event description
            location: Optional location

        Returns:
            Confirmation with event link and ID.
        """
        try:
            if not end_date:
                end_dt = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)
                end_date = end_dt.strftime("%Y-%m-%d")

            event_body: dict = {
                "summary": title,
                "start": {"date": start_date},
                "end": {"date": end_date},
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 1440},
                    ],
                },
            }

            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location

            response = await helper.api_post(data=event_body)
            event_link = response.get("htmlLink", "")
            event_id = response.get("id", "")

            return (
                f"All-day event created!\n"
                f"Title: {title}\n"
                f"Date: {start_date}\n"
                + (f"Description: {description}\n" if description else "")
                + (f"Location: {location}\n" if location else "")
                + (f"Link: {event_link}\n" if event_link else "")
                + f"Event ID: {event_id}"
            )
        except Exception as e:
            _logger.error("create_all_day_event failed: %s", e, exc_info=True)
            return f"❌ Failed to create all-day event: {e}"

    @tool("schedule_assignment_due_date")
    async def schedule_assignment_due_date(
        title: str,
        due_datetime: str,
        timezone_str: str = "auto",
        course_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Schedule an assignment due date as a calendar event with reminders.

        Creates a 30-minute deadline event ending at the due time.
        Adds reminders at 24 hours and 1 hour before due.
        Timezone is auto-detected from user's Google Calendar settings.

        Use when the user asks:
        - "Add the W06 Reflection due date to my calendar"
        - "Remind me about the CS497 project deadline"
        - "Schedule the quiz due date on Feb 20 at 11:59pm"
        - "Put all my assignment deadlines on my calendar"

        **Before calling this tool:**
        1. Get assignment details from Canvas (due date, course, description)
        2. Convert Canvas due_at to ISO format
        3. Call this tool with the data

        Args:
            title: Assignment title (e.g., 'W06 Reflection: Weekly Progress Report')
            due_datetime: Due date/time in ISO format (e.g., '2026-02-14T23:59:00')
            timezone_str: IANA timezone or 'auto' to detect (default: 'auto')
            course_name: Optional course name to prefix the title (e.g., 'GS497.003')
            description: Optional description (points, submission type, etc.)

        Returns:
            Confirmation with event link and ID.
        """
        try:
            tz = await helper.resolve_timezone(timezone_str)
            due_dt = datetime.fromisoformat(due_datetime)
            start_dt = due_dt - timedelta(minutes=30)

            summary = f"DUE: {title}"
            if course_name:
                summary = f"[{course_name}] DUE: {title}"

            event_body: dict = {
                "summary": summary,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": tz,
                },
                "end": {
                    "dateTime": due_dt.isoformat(),
                    "timeZone": tz,
                },
                "colorId": "11",
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 60},
                        {"method": "popup", "minutes": 1440},
                    ],
                },
            }

            if description:
                event_body["description"] = description

            response = await helper.api_post(data=event_body)
            event_link = response.get("htmlLink", "")
            event_id = response.get("id", "")

            return (
                f"Assignment due date scheduled!\n"
                f"Title: {summary}\n"
                f"Due: {due_datetime} ({tz})\n"
                + (f"Description: {description}\n" if description else "")
                + (f"Link: {event_link}\n" if event_link else "")
                + f"Event ID: {event_id}"
            )
        except Exception as e:
            _logger.error("schedule_assignment_due_date failed: %s", e, exc_info=True)
            return f"❌ Failed to schedule assignment: {e}"

    @tool("schedule_study_session")
    async def schedule_study_session(
        title: str,
        start_datetime: str,
        duration_hours: float = 1.0,
        timezone_str: str = "auto",
        course_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Schedule a study session in Google Calendar.

        Creates a blue-colored study block with a 30-minute reminder.
        Timezone is auto-detected from user's Google Calendar settings.

        Use when the user asks:
        - "Schedule a study session for CS497 tomorrow at 2pm for 2 hours"
        - "Block out 3 hours on Saturday to study for the quiz"
        - "Add a study session for the W06 project on Friday afternoon"

        **Before calling this tool:**
        1. Call get_current_datetime_info to resolve relative dates
        2. Call check_availability to find free time slots (optional but recommended)
        3. Convert times to ISO format

        Example flow:
        - User: "Schedule 2 hours to study for the quiz on Saturday"
        - You: Call get_current_datetime_info → Saturday is 2026-02-15
        - You: Call check_availability(date="2026-02-15") → Free 2pm-4pm
        - You: Call schedule_study_session(
            title="Quiz",
            start_datetime="2026-02-15T14:00:00",
            duration_hours=2.0
          )

        Args:
            title: Study topic or assignment name
            start_datetime: Start time in ISO format (e.g., '2026-02-14T14:00:00')
            duration_hours: Duration in hours (default: 1.0, can be 0.5, 1.5, 2.0, etc.)
            timezone_str: IANA timezone or 'auto' to detect (default: 'auto')
            course_name: Optional course name (e.g., 'GS497')
            description: Optional study plan, topics to cover, resources, etc.

        Returns:
            Confirmation with event link and ID.
        """
        try:
            tz = await helper.resolve_timezone(timezone_str)
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = start_dt + timedelta(hours=duration_hours)

            summary = f"Study: {title}"
            if course_name:
                summary = f"[{course_name}] Study: {title}"

            event_body: dict = {
                "summary": summary,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": tz,
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": tz,
                },
                "colorId": "9",
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 1440},
                        {"method": "popup", "minutes": 60},
                    ],
                },
            }

            if description:
                event_body["description"] = description

            response = await helper.api_post(data=event_body)
            event_link = response.get("htmlLink", "")
            event_id = response.get("id", "")

            return (
                f"Study session scheduled!\n"
                f"Title: {summary}\n"
                f"Start: {start_datetime} ({tz})\n"
                f"Duration: {duration_hours}h\n"
                + (f"Description: {description}\n" if description else "")
                + (f"Link: {event_link}\n" if event_link else "")
                + f"Event ID: {event_id}"
            )
        except Exception as e:
            _logger.error("schedule_study_session failed: %s", e, exc_info=True)
            return f"❌ Failed to schedule study session: {e}"

    @tool("update_calendar_event")
    async def update_calendar_event(
        event_id: str,
        title: Optional[str] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        timezone_str: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        """Update an existing calendar event. Only provided fields are changed.

        Use when the user asks:
        - "Change the meeting title to 'Project Review'"     → title="Project Review"
        - "Move my 2pm appointment to 3pm"                   → start_datetime="..T15:00:00"
        - "Update the description of event abc123"           → event_id="abc123", description="..."
        - "Change the location to 'Room 305'"                → location="Room 305"

        **Before calling this tool:**
        1. Get the event_id by searching (use search_events or list_upcoming_events)
        2. Only provide the fields that should change (others remain unchanged)

        Args:
            event_id: The Google Calendar event ID (get from search/list tools)
            title: New event title (optional)
            start_datetime: New start in ISO format (optional)
            end_datetime: New end in ISO format (optional)
            timezone_str: IANA timezone for new times (optional)
            description: New description (optional)
            location: New location (optional)

        Returns:
            Confirmation with updated event title and ID.
        """
        try:
            patch_data: dict = {}

            if title:
                patch_data["summary"] = title
            if description is not None:
                patch_data["description"] = description
            if location is not None:
                patch_data["location"] = location

            tz = timezone_str or "America/New_York"
            if start_datetime:
                patch_data["start"] = {
                    "dateTime": start_datetime,
                    "timeZone": tz,
                }
            if end_datetime:
                patch_data["end"] = {
                    "dateTime": end_datetime,
                    "timeZone": tz,
                }

            if not patch_data:
                return "No fields to update. " "Provide at least one field to change."

            response = await helper.api_patch(event_id, patch_data)
            updated_summary = response.get("summary", title or "Event")
            return (
                f"Event '{updated_summary}' updated successfully! " f"(ID: {event_id})"
            )
        except Exception as e:
            _logger.error("update_calendar_event failed: %s", e, exc_info=True)
            return f"❌ Failed to update event: {e}"

    @tool("delete_calendar_event")
    async def delete_calendar_event(event_id: str) -> str:
        """Delete an event from Google Calendar.

        **WARNING: This permanently deletes the event. Cannot be undone.**

        Use when the user asks:
        - "Delete my dentist appointment"         → (search first, then delete)
        - "Remove the event with ID abc123"       → event_id="abc123"
        - "Cancel my 2pm meeting"                 → (search first, then delete)

        **Before calling this tool:**
        1. Search for the event using search_events or list_upcoming_events
        2. Get the event_id from the search results
        3. Ask user to confirm deletion (optional but recommended)

        Args:
            event_id: The Google Calendar event ID to delete

        Returns:
            Confirmation message.
        """
        try:
            await helper.api_delete(event_id)
            return f"✅ Event deleted successfully! (ID: {event_id})"
        except Exception as e:
            _logger.error("delete_calendar_event failed: %s", e, exc_info=True)
            return f"❌ Failed to delete event: {e}"

    @tool("check_availability")
    async def check_availability(
        date: str,
        start_hour: int = 8,
        end_hour: int = 22,
    ) -> str:
        """Check free time slots on a specific date by analyzing existing events.

        Use when the user asks:
        - "When am I free tomorrow?"                          → date=tomorrow's date
        - "What time slots are available on Friday?"          → date=Friday's date
        - "Check my availability on Feb 14 between 9am-5pm"   → start_hour=9, end_hour=17
        - "Find a good time to schedule a 2-hour study session" → check availability first

        **This tool helps find the best time to schedule new events.**

        Args:
            date: Date in YYYY-MM-DD format
            start_hour: Start of the window to check (24-hour format, default: 8 = 8am)
            end_hour: End of the window to check (24-hour format, default: 22 = 10pm)

        Returns:
            - List of busy time slots (existing events)
            - List of free time slots with durations
        """
        try:
            time_min = f"{date}T{start_hour:02d}:00:00Z"
            end_date = (
                date
                if end_hour < 24
                else (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                )
            )
            time_max = f"{end_date}T{end_hour % 24:02d}:00:00Z"

            params = {
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": "true",
                "orderBy": "startTime",
            }

            response = await helper.api_get(params=params)
            events = response.get("items", [])

            if not events:
                return (
                    f"You're free all day on {date} "
                    f"between {start_hour:02d}:00 and {end_hour:02d}:00!"
                )

            busy_slots = []
            for event in events:
                start = event.get("start", {})
                end = event.get("end", {})
                summary = event.get("summary", "Busy")

                if "dateTime" in start:
                    s = datetime.fromisoformat(start["dateTime"])
                    e = datetime.fromisoformat(end["dateTime"])
                    busy_slots.append((s, e, summary))

            lines = [
                f"Schedule for {date} " f"({start_hour:02d}:00–{end_hour:02d}:00):\n"
            ]
            lines.append("Busy slots:")
            for s, e, name in busy_slots:
                lines.append(
                    f"{s.strftime('%I:%M %p')} – " f"{e.strftime('%I:%M %p')}: {name}"
                )

            if busy_slots:
                busy_sorted = sorted(busy_slots, key=lambda x: x[0])
                free_slots = []
                window_start = datetime.fromisoformat(f"{date}T{start_hour:02d}:00:00")
                for s, e, _ in busy_sorted:
                    if s > window_start:
                        free_slots.append((window_start, s))
                    window_start = max(window_start, e)
                window_end = datetime.fromisoformat(
                    f"{end_date}T{end_hour % 24:02d}:00:00"
                )
                if window_start < window_end:
                    free_slots.append((window_start, window_end))

                if free_slots:
                    lines.append("\nFree slots:")
                    for s, e in free_slots:
                        duration = (e - s).total_seconds() / 3600
                        lines.append(
                            f"{s.strftime('%I:%M %p')} – "
                            f"{e.strftime('%I:%M %p')} ({duration:.1f}h)"
                        )
                else:
                    lines.append("\n No free slots in this window.")

            return "\n".join(lines)
        except Exception as e:
            _logger.error("check_availability failed: %s", e, exc_info=True)
            return f"❌ Failed to check availability: {e}"

    @tool("get_todays_schedule")
    async def get_todays_schedule() -> str:
        """Get today's full schedule from Google Calendar.

        Use when the user asks:
        - "What's on my calendar today?"
        - "Show me today's schedule"
        - "What do I have today?"
        - "Am I free today?"

        Returns:
            All events scheduled for today (timed and all-day events).
        """
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            time_min = f"{today}T00:00:00Z"
            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime(
                "%Y-%m-%d"
            )
            time_max = f"{tomorrow}T00:00:00Z"

            params = {
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": "true",
                "orderBy": "startTime",
            }

            response = await helper.api_get(params=params)
            events = response.get("items", [])
            return helper.format_event_list(events, f"Today's schedule ({today}):")
        except Exception as e:
            _logger.error("get_todays_schedule failed: %s", e, exc_info=True)
            return f"❌ Failed to retrieve today's schedule: {e}"

    return [
        get_user_timezone,
        get_current_datetime_info,
        list_upcoming_events,
        get_events_for_date,
        search_events,
        get_todays_schedule,
        check_availability,
        create_calendar_event,
        create_all_day_event,
        schedule_assignment_due_date,
        schedule_study_session,
        update_calendar_event,
        delete_calendar_event,
    ]
