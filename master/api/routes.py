"""REST API contract for Agent Pi and admin web interactions."""

from flask import Blueprint, request

from master.services.auth_service import AuthService
from master.services.booking_service import BookingService
from master.services.map_service import MapService
from master.services.payment_service import PaymentService
from master.services.report_service import ReportService
from master.services.scooter_service import ScooterService
from master.utils.auth import get_request_user, logout_current_token, require_roles
from master.utils.constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_ENGINEER
from master.utils.response import error_response

api_bp = Blueprint("api", __name__)

auth_service = AuthService()
booking_service = BookingService()
scooter_service = ScooterService()
report_service = ReportService()
map_service = MapService()
payment_service = PaymentService()


@api_bp.post("/register")
def register():
    return auth_service.register_customer(request.get_json(silent=True) or {})


@api_bp.post("/login")
def login():
    return auth_service.login(request.get_json(silent=True) or {})


@api_bp.post("/logout")
def logout():
    _token, logout_error = logout_current_token()
    if logout_error:
        return logout_error
    return auth_service.logout()


@api_bp.get("/scooters")
@require_roles(ROLE_ADMIN)
def list_scooters():
    return scooter_service.list_scooters()


@api_bp.get("/scooters/available")
def list_available_scooters():
    return scooter_service.list_available_scooters()


@api_bp.get("/scooters/<scooter_id>")
def get_scooter(scooter_id):
    return scooter_service.get_scooter(scooter_id)


@api_bp.post("/scooters")
@require_roles(ROLE_ADMIN)
def create_scooter():
    return scooter_service.create_scooter(request.get_json(silent=True) or {})


@api_bp.put("/scooters/<scooter_id>")
@require_roles(ROLE_ADMIN)
def update_scooter(scooter_id):
    payload = request.get_json(silent=True) or {}
    return scooter_service.update_scooter(scooter_id, payload)


@api_bp.delete("/scooters/<scooter_id>")
@require_roles(ROLE_ADMIN)
def delete_scooter(scooter_id):
    return scooter_service.delete_scooter(scooter_id)


@api_bp.put("/scooters/<scooter_id>/status")
@require_roles(ROLE_ADMIN)
def update_scooter_status(scooter_id):
    payload = request.get_json(silent=True) or {}
    return scooter_service.update_scooter_status(scooter_id, payload)


@api_bp.post("/bookings")
@require_roles(ROLE_CUSTOMER)
def book_scooter():
    payload = request.get_json(silent=True) or {}
    payload["user_id"] = get_request_user()["id"]
    return booking_service.book_scooter(payload)


@api_bp.post("/bookings/<int:booking_id>/cancel")
@require_roles(ROLE_CUSTOMER)
def cancel_booking(booking_id):
    payload = request.get_json(silent=True) or {}
    payload["user_id"] = get_request_user()["id"]
    return booking_service.cancel_booking(booking_id, payload)


@api_bp.post("/scooters/<scooter_id>/unlock")
@require_roles(ROLE_CUSTOMER, ROLE_ENGINEER)
def unlock_scooter(scooter_id):
    payload = request.get_json(silent=True) or {}
    payload["scooter_id"] = scooter_id
    payload["user_id"] = get_request_user()["id"]
    payload["role"] = get_request_user()["role"]
    return booking_service.unlock_scooter(payload)


@api_bp.post("/scooters/<scooter_id>/credential-unlock")
def unlock_scooter_with_credentials(scooter_id):
    payload = request.get_json(silent=True) or {}
    payload["scooter_id"] = scooter_id
    return booking_service.unlock_scooter_with_credentials(payload)


@api_bp.post("/scooters/<scooter_id>/credential-lock")
def lock_scooter_with_credentials(scooter_id):
    payload = request.get_json(silent=True) or {}
    payload["scooter_id"] = scooter_id
    return booking_service.lock_scooter_with_credentials(payload)


@api_bp.post("/bookings/qr-unlock")
@require_roles(ROLE_CUSTOMER)
def unlock_scooter_with_qr():
    payload = request.get_json(silent=True) or {}
    payload["user_id"] = get_request_user()["id"]
    payload["role"] = get_request_user()["role"]
    return booking_service.unlock_scooter_with_qr(payload)


@api_bp.post("/scooters/<scooter_id>/lock")
@require_roles(ROLE_CUSTOMER, ROLE_ENGINEER)
def lock_scooter(scooter_id):
    payload = request.get_json(silent=True) or {}
    payload["scooter_id"] = scooter_id
    payload["user_id"] = get_request_user()["id"]
    payload["role"] = get_request_user()["role"]
    return booking_service.lock_scooter(payload)


@api_bp.post("/reports")
@require_roles(ROLE_CUSTOMER, ROLE_ADMIN)
def create_report():
    payload = request.get_json(silent=True) or {}
    payload["reported_by"] = get_request_user()["id"]
    return report_service.create_report(payload)


@api_bp.get("/reports")
@require_roles(ROLE_ADMIN, ROLE_ENGINEER)
def list_reports():
    return report_service.list_reports()


@api_bp.put("/reports/<int:report_id>/status")
@require_roles(ROLE_ADMIN, ROLE_ENGINEER)
def update_report_status(report_id):
    return report_service.update_report_status(report_id, request.get_json(silent=True) or {})


@api_bp.post("/engineer/repair-results")
@require_roles(ROLE_ENGINEER)
def report_repair_result():
    payload = request.get_json(silent=True) or {}
    payload["engineer_id"] = get_request_user()["id"]
    return report_service.report_repair_result(payload)


@api_bp.get("/admin/scooters")
@require_roles(ROLE_ADMIN)
def list_scooters_for_admin():
    return scooter_service.list_scooters()


@api_bp.get("/admin/customers")
@require_roles(ROLE_ADMIN)
def list_customers_for_admin():
    return auth_service.list_customers()


@api_bp.get("/admin/usage-history")
@require_roles(ROLE_ADMIN)
def list_usage_history_for_admin():
    return booking_service.list_usage_history()


@api_bp.get("/admin/usage-report")
@require_roles(ROLE_ADMIN)
def get_usage_report_for_admin():
    return booking_service.get_usage_report(request.args.get("group_by", "day"))


@api_bp.get("/maps/config")
@require_roles(ROLE_ADMIN, ROLE_CUSTOMER, ROLE_ENGINEER)
def get_maps_config():
    return map_service.get_config()


@api_bp.get("/maps/available-scooters")
@require_roles(ROLE_CUSTOMER, ROLE_ADMIN)
def list_available_scooter_map_markers():
    return map_service.list_available_scooter_markers()


@api_bp.get("/maps/reported-scooters")
@require_roles(ROLE_ENGINEER, ROLE_ADMIN)
def list_reported_scooter_map_markers():
    return map_service.list_reported_scooter_markers()


@api_bp.post("/payments/top-up")
@require_roles(ROLE_CUSTOMER)
def create_top_up():
    payload = request.get_json(silent=True) or {}
    payload["user_id"] = get_request_user()["id"]
    return payment_service.create_top_up(payload)


@api_bp.post("/payments/checkout-session")
@require_roles(ROLE_CUSTOMER)
def create_checkout_session():
    payload = request.get_json(silent=True) or {}
    payload["user_id"] = get_request_user()["id"]
    return payment_service.create_checkout_session(payload)


@api_bp.post("/payments/checkout-session/confirm")
def confirm_checkout_session():
    return payment_service.confirm_checkout_session(
        request.get_json(silent=True) or {}
    )


@api_bp.get("/payments/config")
@require_roles(ROLE_CUSTOMER)
def get_payment_config():
    return payment_service.get_config()


@api_bp.get("/payments/top-ups")
@require_roles(ROLE_CUSTOMER)
def list_top_ups():
    return payment_service.list_user_top_ups(get_request_user()["id"])


@api_bp.get("/payments/top-ups/<payment_intent_id>")
@require_roles(ROLE_CUSTOMER)
def get_top_up(payment_intent_id):
    return payment_service.get_user_top_up(
        get_request_user()["id"],
        payment_intent_id,
    )


@api_bp.post("/payments/top-up/mock-confirm")
@require_roles(ROLE_CUSTOMER)
def confirm_mock_top_up():
    return payment_service.confirm_mock_top_up(request.get_json(silent=True) or {})


@api_bp.post("/payments/stripe/webhook")
def stripe_webhook():
    return payment_service.handle_stripe_webhook(
        request.get_data(),
        request.headers.get("Stripe-Signature", ""),
    )


@api_bp.errorhandler(404)
def not_found(_error):
    return error_response("API endpoint not found", 404)