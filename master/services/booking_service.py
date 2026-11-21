import secrets

from master.repositories.booking_repository import BookingRepository
from master.repositories.scooter_repository import ScooterRepository
from master.repositories.user_repository import UserRepository
from master.services.billing_service import BillingService
from master.services.calendar_service import CalendarService
from master.utils.constants import (
    BOOKING_STATUS_ACTIVE,
    BOOKING_STATUS_CANCELED,
    ROLE_CUSTOMER,
    ROLE_ENGINEER,
    SCOOTER_STATUS_AVAILABLE,
    SCOOTER_STATUS_BOOKED,
    SCOOTER_STATUS_OCCUPYING,
    SCOOTER_STATUS_TO_BE_REPAIRED,
    SCOOTER_STATUS_UNDER_REPAIR,
)
from master.utils.password_utils import verify_password
from master.utils.response import error_response, success_response
from master.utils.validators import require_fields
from master.mqtt_server import MQTTServer

class BookingService:
    DEFAULT_BOOKING_MINUTES = 10

    def __init__(
        self,
        booking_repository=None,
        scooter_repository=None,
        user_repository=None,
        billing_service=None,
        calendar_service=None,
    ):
        self.booking_repository = booking_repository or BookingRepository()
        self.scooter_repository = scooter_repository or ScooterRepository()
        self.user_repository = user_repository or UserRepository()
        self.billing_service = billing_service or BillingService()
        self.calendar_service = calendar_service or CalendarService()
        self.mqtt_server = MQTTServer()

    def book_scooter(self, data):
        missing = require_fields(data, ["user_id", "scooter_id"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        user = self.user_repository.find_by_id(data["user_id"])
        if not user:
            return error_response("Customer not found", 404)
        if user["role"] != ROLE_CUSTOMER:
            return error_response("Only customers can book scooters", 403)

        scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        if not scooter:
            return error_response("Scooter not found", 404)
        if scooter["status"] != SCOOTER_STATUS_AVAILABLE:
            return error_response("Scooter is not available for booking", 409)

        minimum_required = float(scooter["cost_per_minute"]) * self.DEFAULT_BOOKING_MINUTES
        if float(user["balance"]) < minimum_required:
            return error_response(
                "Insufficient balance for the default booking duration",
                409,
                {"minimum_required": round(minimum_required, 2), "balance": user["balance"]},
            )

        if self.booking_repository.find_active_for_scooter(data["scooter_id"]):
            return error_response("Scooter already has an active booking", 409)

        try:
            calendar_result = self.calendar_service.create_booking_event(
                user,
                scooter,
                self.DEFAULT_BOOKING_MINUTES,
            )
        except Exception as error:
            return error_response(f"Could not create Google Calendar event: {error}", 502)

        unlock_code = self._generate_unlock_code()
        booking = self.booking_repository.create_booking_and_mark_scooter_booked(
            {
                "user_id": data["user_id"],
                "scooter_id": data["scooter_id"],
                "status": BOOKING_STATUS_ACTIVE,
                "calendar_event_id": calendar_result["event_id"],
                "unlock_code": unlock_code,
            }
        )
        self.mqtt_server.publish_scooter_status(data["scooter_id"], SCOOTER_STATUS_BOOKED)
        return success_response(
            "Scooter booked",
            {
                **booking,
                "scooter_status": SCOOTER_STATUS_BOOKED,
                "default_duration_minutes": self.DEFAULT_BOOKING_MINUTES,
                "unlock_methods": ["credentials", "qr"],
                "qr_payload": self._build_qr_payload(booking),
                "calendar": calendar_result,
            },
            201,
        )

    def cancel_booking(self, booking_id, data):
        missing = require_fields(data, ["user_id"])
        if missing:
            return error_response("Missing required fields: user_id", 400)

        booking = self.booking_repository.find_by_id(booking_id)
        if not booking:
            return error_response("Booking not found", 404)
        if str(booking["user_id"]) != str(data["user_id"]):
            return error_response("Only the booking owner can cancel this booking", 403)
        if booking["status"] != BOOKING_STATUS_ACTIVE:
            return error_response("Only active bookings can be canceled", 409)
        if booking["unlock_time"] is not None:
            return error_response("Cannot cancel a booking after scooter is unlocked", 409)

        scooter = self.scooter_repository.find_by_id(booking["scooter_id"])
        if not scooter:
            return error_response("Scooter not found for this booking", 404)

        if scooter["status"] not in {SCOOTER_STATUS_BOOKED, SCOOTER_STATUS_AVAILABLE}:
            return error_response("Scooter cannot be canceled in its current state", 409)

        try:
            calendar_result = self.calendar_service.cancel_booking_event(
                booking.get("calendar_event_id")
            )
        except Exception as error:
            return error_response(f"Could not delete Google Calendar event: {error}", 502)

        canceled_booking = self.booking_repository.cancel_booking_and_mark_scooter_available(
            booking_id
        )
        self.mqtt_server.publish_scooter_status(booking["scooter_id"], SCOOTER_STATUS_AVAILABLE)
        return success_response(
            "Booking canceled",
            {
                **canceled_booking,
                "scooter_status": SCOOTER_STATUS_AVAILABLE,
                "calendar_event_id": booking.get("calendar_event_id"),
                "calendar": calendar_result,
            },
        )

    def unlock_scooter(self, data):
        missing = require_fields(data, ["user_id", "scooter_id", "role"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        if data["role"] == ROLE_ENGINEER:
            return self._unlock_scooter_for_engineer(data)
        return self._unlock_scooter_for_customer(data)

    def lock_scooter(self, data):
        missing = require_fields(data, ["user_id", "scooter_id", "role"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        if data["role"] == ROLE_ENGINEER:
            return self._lock_scooter_for_engineer(data)
        return self._lock_scooter_for_customer(data)

    def unlock_scooter_with_qr(self, data):
        missing = require_fields(data, ["user_id", "role", "unlock_code"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)
        if data["role"] != ROLE_CUSTOMER:
            return error_response("Only customers can use QR unlock", 403)

        booking = self.booking_repository.find_active_by_unlock_code(data["unlock_code"])
        if not booking:
            return error_response("Invalid or inactive unlock QR code", 404)

        return self._unlock_scooter_for_customer(
            {
                "user_id": data["user_id"],
                "role": data["role"],
                "scooter_id": booking["scooter_id"],
                "unlock_code": data["unlock_code"],
                "unlock_method": "qr",
            }
        )

    def lock_scooter_with_qr(self, data):
        missing = require_fields(data, ["user_id", "role", "unlock_code"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        if data["role"] != ROLE_CUSTOMER:
            return error_response("Only customers can use QR lock", 403)

        booking = self.booking_repository.find_active_by_unlock_code(data["unlock_code"])
        if not booking:
            return error_response("Invalid or inactive return QR code", 404)

        return self._lock_scooter_for_customer(
            {
                "user_id": data["user_id"],
                "role": data["role"],
                "scooter_id": booking["scooter_id"],
                "unlock_code": data["unlock_code"],
                "lock_method": "qr",
            }
        )

    def unlock_scooter_with_credentials(self, data):
        missing = require_fields(data, ["username", "password", "scooter_id"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        user = self.user_repository.find_by_username(data["username"])
        if not user or not verify_password(data["password"], user["password_hash"]):
            return error_response("Invalid username or password", 401)
        if user["role"] != ROLE_CUSTOMER:
            return error_response("Only customers can use credential unlock", 403)

        return self._unlock_scooter_for_customer(
            {
                "user_id": user["id"],
                "role": user["role"],
                "scooter_id": data["scooter_id"],
                "unlock_method": "credentials",
            }
        )

    def lock_scooter_with_credentials(self, data):
        missing = require_fields(data, ["username", "password", "scooter_id"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        user = self.user_repository.find_by_username(data["username"])
        if not user or not verify_password(data["password"], user["password_hash"]):
            return error_response("Invalid username or password", 401)
        if user["role"] != ROLE_CUSTOMER:
            return error_response("Only customers can use credential lock", 403)

        return self._lock_scooter_for_customer(
            {
                "user_id": user["id"],
                "role": user["role"],
                "scooter_id": data["scooter_id"],
                "lock_method": "credentials",
            }
        )

    def list_usage_history(self):
        usage_history = self.booking_repository.list_usage_history()
        return success_response("Usage history retrieved", usage_history)

    def get_usage_report(self, group_by="day"):
        group_by = str(group_by or "day").lower()
        if group_by not in {"day", "week"}:
            return error_response("group_by must be day or week", 400)

        raw_series = (
            self.booking_repository.usage_report_by_week()
            if group_by == "week"
            else self.booking_repository.usage_report_by_day()
        )
        series = [self._format_usage_report_row(row) for row in raw_series]
        summary = {
            "period_count": len(series),
            "trip_count": sum(int(row["trip_count"]) for row in series),
            "customer_count": sum(int(row["customer_count"]) for row in series),
            "scooter_count": sum(int(row["scooter_count"]) for row in series),
            "total_duration_minutes": sum(int(row["total_duration_minutes"]) for row in series),
            "total_cost": sum(float(row["total_cost"]) for row in series),
            "charged_amount": sum(float(row["charged_amount"]) for row in series),
            "unpaid_amount": sum(float(row["unpaid_amount"]) for row in series),
        }
        return success_response(
            "Usage report retrieved",
            {
                "group_by": group_by,
                "summary": summary,
                "series": series,
            },
        )

    def _format_usage_report_row(self, row):
        formatted = dict(row)
        for date_key in ("period", "start_date", "end_date"):
            if date_key in formatted and formatted[date_key] is not None:
                formatted[date_key] = str(formatted[date_key])
        for count_key in (
            "trip_count",
            "customer_count",
            "scooter_count",
            "total_duration_minutes",
        ):
            formatted[count_key] = int(formatted[count_key])
        for money_key in ("total_cost", "charged_amount", "unpaid_amount"):
            formatted[money_key] = float(formatted[money_key])
        return formatted

    def _generate_unlock_code(self):
        for _attempt in range(5):
            unlock_code = f"BK-{secrets.token_urlsafe(9).replace('_', '').replace('-', '').upper()[:12]}"
            if not self.booking_repository.find_active_by_unlock_code(unlock_code):
                return unlock_code
        return f"BK-{secrets.token_hex(8).upper()}"

    def _build_qr_payload(self, booking):
        return {
            "type": "customer_unlock",
            "booking_id": booking["id"],
            "scooter_id": booking["scooter_id"],
            "unlock_code": booking["unlock_code"],
            "user_id": booking["user_id"],
            "role": ROLE_CUSTOMER,
        }

    def _unlock_scooter_for_customer(self, data):
        user = self.user_repository.find_by_id(data["user_id"])
        if not user:
            return error_response("Customer not found", 404)
        if user["role"] != ROLE_CUSTOMER:
            return error_response("Only customers can use this unlock flow", 403)

        scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        if not scooter:
            return error_response("Scooter not found", 404)
        if scooter["status"] != SCOOTER_STATUS_BOOKED:
            return error_response("Scooter must be booked before customer unlock", 409)

        booking = self.booking_repository.find_active_for_scooter(data["scooter_id"])
        if not booking:
            return error_response("No active booking found for this scooter", 404)
        if str(booking["user_id"]) != str(data["user_id"]):
            return error_response("Only the booking owner can unlock this scooter", 403)
        if booking["unlock_time"] is not None:
            return error_response("Scooter is already unlocked for this booking", 409)

        minimum_required = float(scooter["cost_per_minute"]) * self.DEFAULT_BOOKING_MINUTES
        if float(user["balance"]) < minimum_required:
            return error_response(
                "Insufficient balance to unlock scooter",
                409,
                {"minimum_required": round(minimum_required, 2), "balance": user["balance"]},
            )

        usage_limit = self.billing_service.calculate_usage_limit(
            user["balance"],
            scooter["cost_per_minute"],
            self.billing_service.current_time(),
        )
        unlocked_booking = self.booking_repository.unlock_booking_and_mark_scooter_occupying(
            booking["id"],
            usage_limit,
        )
        self.mqtt_server.publish_lock_status(data["scooter_id"], "Unlocked")
        self.mqtt_server.publish_scooter_status(data["scooter_id"], SCOOTER_STATUS_OCCUPYING)
        return success_response(
            "Scooter unlocked",
            {
                **unlocked_booking,
                "scooter_status": SCOOTER_STATUS_OCCUPYING,
                "unlock_method": data.get("unlock_method", "credentials"),
                "max_usage_minutes": usage_limit["max_usage_minutes"],
                "auto_lock_at": usage_limit["auto_lock_at"],
            },
        )

    def _lock_scooter_for_customer(self, data):
        user = self.user_repository.find_by_id(data["user_id"])
        if not user:
            return error_response("Customer not found", 404)
        if user["role"] != ROLE_CUSTOMER:
            return error_response("Only customers can use this lock flow", 403)

        scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        if not scooter:
            return error_response("Scooter not found", 404)
        if scooter["status"] != SCOOTER_STATUS_OCCUPYING:
            return error_response("Scooter is not currently occupying", 409)

        booking = self.booking_repository.find_active_for_scooter(data["scooter_id"])
        if not booking:
            return error_response("No active booking found for this scooter", 404)
        if str(booking["user_id"]) != str(data["user_id"]):
            return error_response("Only the active rider can lock this scooter", 403)
        if booking["unlock_time"] is None:
            return error_response("Scooter has not been unlocked yet", 409)
        if booking["lock_time"] is not None:
            return error_response("Scooter is already locked for this booking", 409)

        requested_lock_time = self.billing_service.current_time()
        auto_lock_at = booking.get("auto_lock_at")
        auto_lock_applied = bool(auto_lock_at and requested_lock_time >= auto_lock_at)
        effective_lock_time = auto_lock_at if auto_lock_applied else requested_lock_time

        billing = self.billing_service.calculate_cost(
            booking["unlock_time"],
            effective_lock_time,
            float(scooter["cost_per_minute"]),
        )
        payment = self.billing_service.apply_balance_cap(
            billing["total_cost"],
            user["balance"],
            auto_lock_applied=auto_lock_applied,
        )
        completed = self.booking_repository.complete_booking_with_billing(
            booking["id"],
            {
                "start_time": booking["unlock_time"],
                "end_time": billing["end_time"],
                "duration_minutes": billing["duration_minutes"],
                "total_cost": billing["total_cost"],
                "charged_amount": payment["charged_amount"],
                "unpaid_amount": payment["unpaid_amount"],
                "payment_status": payment["payment_status"],
            },
        )
        updated_user = self.user_repository.find_by_id(data["user_id"])
        self.mqtt_server.publish_lock_status(data["scooter_id"], "Locked")
        self.mqtt_server.publish_scooter_status(data["scooter_id"], SCOOTER_STATUS_AVAILABLE)
        return success_response(
            "Scooter locked",
            {
                **completed["booking"],
                "scooter_status": SCOOTER_STATUS_AVAILABLE,
                "bill": {
                    "usage_id": completed["usage"]["id"],
                    "duration_minutes": completed["usage"]["duration_minutes"],
                    "total_cost": completed["usage"]["total_cost"],
                    "charged_amount": completed["usage"]["charged_amount"],
                    "unpaid_amount": completed["usage"]["unpaid_amount"],
                    "payment_status": completed["usage"]["payment_status"],
                    "balance_after": updated_user["balance"],
                    "auto_lock_applied": auto_lock_applied,
                    "requested_lock_time": requested_lock_time,
                    "effective_lock_time": effective_lock_time,
                },
            },
        )

    def _unlock_scooter_for_engineer(self, data):
        user = self.user_repository.find_by_id(data["user_id"])
        if not user:
            return error_response("Engineer not found", 404)
        if user["role"] != ROLE_ENGINEER:
            return error_response("Only engineers can use this repair unlock flow", 403)

        scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        if not scooter:
            return error_response("Scooter not found", 404)

        previous_status = scooter["status"]

        updated_scooter = self.scooter_repository.update_status(
            data["scooter_id"],
            SCOOTER_STATUS_UNDER_REPAIR,
        )
        self.mqtt_server.publish_lock_status(data["scooter_id"], "Unlocked")
        self.mqtt_server.publish_scooter_status(data["scooter_id"], SCOOTER_STATUS_UNDER_REPAIR)
        return success_response(
            "Engineer unlocked scooter for repair",
            {
                "scooter": updated_scooter,
                "charged": False,
                "previous_status": previous_status,
                "scooter_status": SCOOTER_STATUS_UNDER_REPAIR,
            },
        )

    def _lock_scooter_for_engineer(self, data):
        user = self.user_repository.find_by_id(data["user_id"])
        if not user:
            return error_response("Engineer not found", 404)
        if user["role"] != ROLE_ENGINEER:
            return error_response("Only engineers can use this repair lock flow", 403)

        scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        if not scooter:
            return error_response("Scooter not found", 404)
        self.mqtt_server.publish_lock_status(data["scooter_id"], "Locked")
        return success_response(
            "Engineer locked scooter after repair work",
            {
                "scooter": scooter,
                "charged": False,
                "scooter_status": scooter["status"],
                "next_step": "Submit repair result to mark the scooter available",
            },
        )