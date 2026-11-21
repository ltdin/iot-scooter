"""Google Calendar integration for scooter bookings."""

import json
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from master.config import Config

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:  # pragma: no cover - depends on installed requirements
    service_account = None
    build = None
    HttpError = None


class CalendarService:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, calendar_id=None):
        self.calendar_id = calendar_id or Config.GOOGLE_CALENDAR_ID
        self._client = None

    def _is_mock_mode(self):
        return Config.GOOGLE_CALENDAR_MOCK_MODE or not Config.GOOGLE_CALENDAR_CREDENTIALS_FILE

    def _timezone(self):
        try:
            return ZoneInfo(Config.GOOGLE_CALENDAR_TIMEZONE)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    def _format_google_error(self, error):
        if HttpError is None or not isinstance(error, HttpError):
            return str(error)

        try:
            error_payload = json.loads(error.content.decode("utf-8"))
            details = error_payload.get("error", {})
            reason = details.get("errors", [{}])[0].get("reason")
            message = details.get("message", str(error))
        except Exception:
            reason = None
            message = str(error)

        if reason == "accessNotConfigured":
            return (
                "Google Calendar API is not enabled for the Google Cloud project "
                "used by this service account. Enable Google Calendar API in "
                "Google Cloud Console, wait a few minutes, then retry."
            )
        if reason == "notFound":
            return (
                "Google Calendar was not found. Check GOOGLE_CALENDAR_ID and make "
                "sure the calendar is shared with the service account client_email."
            )
        if reason in {"forbidden", "insufficientPermissions"}:
            return (
                "Service account does not have permission to modify this calendar. "
                "Share the calendar with the service account using 'Make changes to events'."
            )
        return message

    def _get_client(self):
        if self._client is not None:
            return self._client
        if service_account is None or build is None:
            raise RuntimeError("Google Calendar packages are not installed")
        if not Config.GOOGLE_CALENDAR_CREDENTIALS_FILE:
            raise RuntimeError("GOOGLE_CALENDAR_CREDENTIALS_FILE is not configured")

        credentials = service_account.Credentials.from_service_account_file(
            Config.GOOGLE_CALENDAR_CREDENTIALS_FILE,
            scopes=self.SCOPES,
        )
        self._client = build("calendar", "v3", credentials=credentials)
        return self._client

    def _event_times(self, duration_minutes):
        start_time = datetime.now(self._timezone()).replace(microsecond=0)
        end_time = start_time + timedelta(minutes=duration_minutes)
        return start_time, end_time

    def _build_event_body(self, user, scooter, duration_minutes):
        start_time, end_time = self._event_times(duration_minutes)
        scooter_id = scooter["id"]
        summary = f"Scooter booking - {scooter_id}"
        description = (
            f"Customer: {user['first_name']} {user['last_name']} ({user['username']})\n"
            f"Scooter: {scooter_id} - {scooter['make']} {scooter['colour']}\n"
            f"Cost per minute: {scooter['cost_per_minute']}\n"
            f"Default duration: {duration_minutes} minutes"
        )
        return {
            "summary": summary,
            "location": scooter.get("location", ""),
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": Config.GOOGLE_CALENDAR_TIMEZONE,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": Config.GOOGLE_CALENDAR_TIMEZONE,
            },
            "extendedProperties": {
                "private": {
                    "scooter_id": scooter_id,
                    "user_id": str(user["id"]),
                    "duration_minutes": str(duration_minutes),
                }
            },
        }

    def create_booking_event(self, user, scooter, duration_minutes=10):
        event_body = self._build_event_body(user, scooter, duration_minutes)

        if self._is_mock_mode():
            event_id = f"mock_calendar_{uuid4().hex}"
            return {
                "event_id": event_id,
                "event_link": None,
                "provider": "google_calendar_mock",
                "mock_mode": True,
                "summary": event_body["summary"],
                "start_time": event_body["start"]["dateTime"],
                "end_time": event_body["end"]["dateTime"],
            }

        try:
            event = (
                self._get_client()
                .events()
                .insert(calendarId=self.calendar_id, body=event_body)
                .execute()
            )
        except Exception as error:
            raise RuntimeError(self._format_google_error(error)) from error

        return {
            "event_id": event["id"],
            "event_link": event.get("htmlLink"),
            "provider": "google_calendar",
            "mock_mode": False,
            "summary": event.get("summary"),
            "start_time": event.get("start", {}).get("dateTime"),
            "end_time": event.get("end", {}).get("dateTime"),
        }

    def cancel_booking_event(self, event_id):
        if not event_id:
            return {
                "calendar_event_deleted": False,
                "calendar_message": "Booking has no calendar event id",
            }

        if self._is_mock_mode() or str(event_id).startswith("mock_calendar_"):
            return {
                "event_deleted": True,
                "event_id": event_id,
                "provider": "google_calendar_mock",
                "mock_mode": True,
            }

        try:
            self._get_client().events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
            ).execute()
        except Exception as error:
            raise RuntimeError(self._format_google_error(error)) from error

        return {
            "event_deleted": True,
            "event_id": event_id,
            "provider": "google_calendar",
            "mock_mode": False,
        }
