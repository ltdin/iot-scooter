"""Safety and security incident handlers driven by MQTT events from Agent Pis.
"""

from master.config import Config
from master.repositories.booking_repository import BookingRepository
from master.repositories.scooter_repository import ScooterRepository
from master.repositories.user_repository import UserRepository
from master.services.email_service import EmailService
from master.utils.response import error_response, success_response


class SafetyService:
    def __init__(
        self,
        email_service=None,
        scooter_repository=None,
        booking_repository=None,
        user_repository=None,
    ):
        self.email_service = email_service or EmailService()
        self.scooter_repository = scooter_repository or ScooterRepository()
        self.booking_repository = booking_repository or BookingRepository()
        self.user_repository = user_repository or UserRepository()
    def handle_crash_event(self, payload):
        scooter_id = payload.get("scooter_id")
        if not scooter_id:
            return error_response("scooter_id is required in crash event", 400)
        if payload.get("event") != "crash_detected":
            return error_response("Unsupported event for crash handler", 400)

        scooter = self._safe_lookup("scooter", lambda: self.scooter_repository.find_by_id(scooter_id))
        active_booking = (
            self._safe_lookup("booking", lambda: self.booking_repository.find_active_for_scooter(scooter_id))
            if scooter is not None
            else None
        )
        rider = None
        if active_booking and active_booking.get("user_id"):
            rider = self._safe_lookup(
                "rider",
                lambda: self.user_repository.find_by_id(active_booking["user_id"]),
            )
        subject = f"[Scooter Share] Crash Detected on Scooter {scooter_id}"
        body = self._format_crash_email(payload, scooter, active_booking, rider)
        recipients = self._crash_alert_recipients(rider)
        email_result = self.email_service.send_email(recipients, subject, body)
        return success_response(
            "Crash event processed",
            {
                "scooter_id": scooter_id,
                "booking_id": active_booking["id"] if active_booking else None,
                "rider_id": rider["id"] if rider else None,
                "alert_recipients": recipients,
                "scooter_status": (scooter or {}).get("status"),
                "incident_type": "crash",
                "email": email_result,
            },
        )
    def handle_theft_event(self, payload):
        scooter_id = payload.get("scooter_id")
        if not scooter_id:
            return error_response("scooter_id is required in theft event", 400)
        if payload.get("event") != "theft_suspected":
            return error_response("Unsupported event for theft handler", 400)
        scooter = self._safe_lookup("scooter", lambda: self.scooter_repository.find_by_id(scooter_id))
        active_booking = (
            self._safe_lookup("booking", lambda: self.booking_repository.find_active_for_scooter(scooter_id))
            if scooter is not None
            else None
        )
        booker = None
        if active_booking and active_booking.get("user_id"):
            booker = self._safe_lookup(
                "booker",
                lambda: self.user_repository.find_by_id(active_booking["user_id"]),
            )
        subject = f"[Scooter Share] Suspected Theft on Scooter {scooter_id}"
        body = self._format_theft_email(payload, scooter, active_booking, booker)
        recipients = self._theft_alert_recipients(booker)
        email_result = self.email_service.send_email(recipients, subject, body)
        return success_response(
            "Theft event processed",
            {
                "scooter_id": scooter_id,
                "booking_id": active_booking["id"] if active_booking else None,
                "booker_id": booker["id"] if booker else None,
                "alert_recipients": recipients,
                "scooter_status": (scooter or {}).get("status"),
                "incident_type": "theft",
                "email": email_result,
            },
        )
    def _theft_alert_recipients(self, booker):
        recipients = []
        if Config.SAFETY_ALERT_EMAIL:
            recipients.append(Config.SAFETY_ALERT_EMAIL)
        if booker and booker.get("email") and booker["email"] not in recipients:
            recipients.append(booker["email"])
        return recipients
    def _format_theft_email(self, payload, scooter, booking, booker):
        scooter_line = (
            f"Scooter: {scooter['make']} {scooter['colour']} at {scooter['location']}"
            if scooter
            else "Scooter: unknown (not found in registry)"
        )
        booker_line = (
            f"Booker: {booker['first_name']} {booker['last_name']} <{booker['email']}> "
            f"(phone {booker['phone']})"
            if booker
            else "Booker: none (scooter was Available, not booked by anyone)"
        )
        booking_line = (
            f"Booking ID: {booking['id']} (still in {booking.get('status', 'Active')} state)"
            if booking
            else "Booking ID: none"
        )
        location_line = self._format_location(payload, scooter)
        return (
            "SECURITY ALERT: A scooter is being moved without an authorised rider.\n\n"
            f"Scooter ID:        {payload.get('scooter_id')}\n"
            f"Detected at:       {payload.get('timestamp')}\n"
            f"Status at trigger: {payload.get('current_status')}\n"
            f"Motion magnitude:  {payload.get('motion_magnitude')} G (mean)\n"
            f"Sustained for:     {payload.get('window_seconds')} s\n"
            f"{scooter_line}\n"
            f"{booker_line}\n"
            f"{booking_line}\n"
            f"{location_line}\n\n"
            "Action required: the scooter is being moved while no one has\n"
            "unlocked it. Investigate the location and contact the booker if\n"
            "any. Consider revoking the booking and dispatching recovery.\n"
            "\n"
            "-- Scooter Share automated security alert\n"
        )
    def _safe_lookup(self, label, lookup):
        try:
            return lookup()
        except Exception as error:
            print(f"[SAFETY] {label} lookup failed, continuing without it: {error}")
            return None
    def _crash_alert_recipients(self, rider):
        recipients = []
        if Config.SAFETY_ALERT_EMAIL:
            recipients.append(Config.SAFETY_ALERT_EMAIL)
        if rider and rider.get("emergency_contact_email"):
            contact = rider["emergency_contact_email"]
            if contact not in recipients:
                recipients.append(contact)
        return recipients
    def _format_crash_email(self, payload, scooter, booking, rider):
        scooter_line = (
            f"Scooter: {scooter['make']} {scooter['colour']} at {scooter['location']}"
            if scooter
            else "Scooter: unknown (not found in registry)"
        )
        rider_line = (
            f"Rider: {rider['first_name']} {rider['last_name']} "
            f"(phone {rider['phone']}, email {rider['email']})"
            if rider
            else "Rider: unknown (no active booking at time of impact)"
        )
        if rider and rider.get("emergency_contact_email"):
            contact_name = rider.get("emergency_contact_name") or "registered contact"
            emergency_line = (
                f"Emergency contact: {contact_name} <{rider['emergency_contact_email']}>"
            )
        elif rider:
            emergency_line = "Emergency contact: not set on the rider's profile"
        else:
            emergency_line = "Emergency contact: none (no rider identified)"
        booking_line = (
            f"Booking ID: {booking['id']} (started {booking['unlock_time']})"
            if booking and booking.get("unlock_time")
            else f"Booking ID: {booking['id']}" if booking else "Booking ID: none"
        )
        location_line = self._format_location(payload, scooter)
        return (
            "URGENT: A crash has been detected on a scooter operated by\n"
            "Scooter Share Platform. This alert is being sent to the rider's\n"
            "emergency contact so they can act quickly.\n\n"
            f"Scooter ID:        {payload.get('scooter_id')}\n"
            f"Detected at:       {payload.get('timestamp')}\n"
            f"Peak G-force:      {payload.get('g_force')} G\n"
            f"Orientation delta: {payload.get('orientation_delta_deg')} deg\n"
            f"{scooter_line}\n"
            f"{rider_line}\n"
            f"{emergency_line}\n"
            f"{booking_line}\n"
            f"{location_line}\n\n"
            "What to do: try to reach the rider on the phone number above. If\n"
            "you cannot reach them, please contact local emergency services\n"
            "and share the scooter's last known location (Google Maps link).\n"
            "\n"
            "-- Scooter Share Platform automated safety alert\n"
        )
    def _format_location(self, payload, scooter):
        latitude = None
        longitude = None
        location = payload.get("location") or {}
        if isinstance(location, dict):
            latitude = location.get("lat")
            longitude = location.get("lng")
        if (latitude is None or longitude is None) and scooter:
            latitude = scooter.get("latitude")
            longitude = scooter.get("longitude")
        if latitude is not None and longitude is not None:
            url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            return f"Location:          {latitude}, {longitude}\nGoogle Maps:       {url}"
        return "Location:          unknown"
