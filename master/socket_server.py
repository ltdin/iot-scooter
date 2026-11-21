"""Socket server for request/response communication from Agent Pis."""

import json
import socket
import threading
from datetime import date, datetime
from decimal import Decimal

from master.config import Config
from master.services.auth_service import AuthService
from master.services.booking_service import BookingService
from master.services.payment_service import PaymentService
from master.services.report_service import ReportService
from master.services.scooter_service import ScooterService
from master.utils.constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_ENGINEER
from master.utils.response import error_response
from master.utils.token_utils import revoke_access_token, verify_access_token
from master.repositories.user_repository import UserRepository

auth_service = AuthService()
booking_service = BookingService()
report_service = ReportService()
payment_service = PaymentService()
scooter_service = ScooterService()
user_repository = UserRepository()

PUBLIC_ACTIONS = {
    "login",
    "register",
    "credential_unlock",
    "credential_lock",
    "qr_unlock",
    "qr_lock",
    "engineer_qr_unlock",
    "engineer_qr_lock",
    "list_available_scooters",
    "get_scooter",
}

ACTION_ROLES = {
    "get_current_user": {ROLE_ADMIN, ROLE_CUSTOMER, ROLE_ENGINEER},
    "book": {ROLE_CUSTOMER},
    "cancel_booking": {ROLE_CUSTOMER},
    "unlock": {ROLE_CUSTOMER, ROLE_ENGINEER},
    "qr_unlock": {ROLE_CUSTOMER},
    "qr_lock": {ROLE_CUSTOMER},
    "engineer_qr_unlock": {ROLE_ENGINEER},
    "engineer_qr_lock": {ROLE_ENGINEER},
    "lock": {ROLE_CUSTOMER, ROLE_ENGINEER},
    "report_issue": {ROLE_CUSTOMER, ROLE_ADMIN},
    "repair_result": {ROLE_ENGINEER},
    "list_reports": {ROLE_ENGINEER, ROLE_ADMIN},
    "update_report_status": {ROLE_ENGINEER},
    "top_up": {ROLE_CUSTOMER},
    "confirm_mock_top_up": {ROLE_CUSTOMER},
    "create_checkout_session": {ROLE_CUSTOMER},
    "confirm_checkout_session": {ROLE_CUSTOMER},
    "logout": {ROLE_ADMIN, ROLE_CUSTOMER, ROLE_ENGINEER},
}

SUPPORTED_ACTIONS = PUBLIC_ACTIONS | set(ACTION_ROLES)


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _normalize_service_response(service_response):
    if isinstance(service_response, tuple):
        response, status_code = service_response
        response["status_code"] = status_code
        return response
    service_response["status_code"] = 200
    return service_response


def _authenticated_payload(action, message):
    if action in PUBLIC_ACTIONS:
        return message.get("payload", {}), None

    token = message.get("token")
    if not token:
        return None, error_response("Socket token is required", 401)

    payload, token_error = verify_access_token(token)
    if token_error:
        return None, error_response(token_error, 401)

    user = user_repository.find_by_id(payload["user_id"])
    if not user:
        return None, error_response("Authenticated user not found", 401)
    if user["role"] != payload["role"]:
        return None, error_response("Access token role no longer matches user", 403)

    allowed_roles = ACTION_ROLES.get(action)
    if allowed_roles is None:
        return None, error_response(f"Unknown socket action: {action}", 400)
    if user["role"] not in allowed_roles:
        return None, error_response("Access denied for this socket action", 403)

    data = message.get("payload", {})
    data["user_id"] = user["id"]
    data["role"] = user["role"]
    if action == "report_issue":
        data["reported_by"] = user["id"]
    if action == "repair_result":
        data["engineer_id"] = user["id"]
    return data, None


def _validate_public_engineer_payload(payload):
    if payload.get("role") != ROLE_ENGINEER:
        return error_response("Only engineers can use this QR repair flow", 403)

    user_id = payload.get("user_id")
    if not user_id:
        return error_response("Missing required fields: user_id", 400)

    user = user_repository.find_by_id(user_id)
    if not user:
        return error_response("Engineer not found", 404)

    if user["role"] != ROLE_ENGINEER:
        return error_response("Only engineers can use this QR repair flow", 403)

    if not payload.get("scooter_id"):
        return error_response("Missing required fields: scooter_id", 400)

    return None


def dispatch_message(message):
    action = message.get("action")
    if action not in SUPPORTED_ACTIONS:
        return error_response(f"Unknown socket action: {action}", 400)

    payload, auth_error = _authenticated_payload(action, message)
    if auth_error:
        return auth_error

    if action == "login":
        return auth_service.login(payload)
    if action == "register":
        return auth_service.register_customer(payload)
    if action == "get_current_user":
        return auth_service.get_current_user(payload["user_id"])
    if action == "credential_unlock":
        if message.get("scooter_id") and "scooter_id" not in payload:
            payload["scooter_id"] = message["scooter_id"]
        return booking_service.unlock_scooter_with_credentials(payload)
    if action == "credential_lock":
        if message.get("scooter_id") and "scooter_id" not in payload:
            payload["scooter_id"] = message["scooter_id"]
        return booking_service.lock_scooter_with_credentials(payload)
    if action == "list_available_scooters":
        return scooter_service.list_available_scooters()
    if action == "get_scooter":
        scooter_id = message.get("scooter_id") or payload.get("scooter_id")
        return scooter_service.get_scooter(scooter_id)
    if action == "book":
        return booking_service.book_scooter(payload)
    if action == "cancel_booking":
        return booking_service.cancel_booking(payload.get("booking_id"), payload)
    if action == "unlock":
        return booking_service.unlock_scooter(payload)
    if action == "qr_unlock":
        return booking_service.unlock_scooter_with_qr(payload)
    if action == "qr_lock":
        return booking_service.lock_scooter_with_qr(payload)
    if action == "engineer_qr_unlock":
        validation_error = _validate_public_engineer_payload(payload)
        if validation_error:
            return validation_error
        return booking_service.unlock_scooter(payload)
    if action == "engineer_qr_lock":
        validation_error = _validate_public_engineer_payload(payload)
        if validation_error:
            return validation_error
        return booking_service.lock_scooter(payload)
    if action == "lock":
        return booking_service.lock_scooter(payload)
    if action == "report_issue":
        return report_service.create_report(payload)
    if action == "list_reports":
        return report_service.list_reports()
    if action == "update_report_status":
        return report_service.update_report_status(payload.get("report_id"), payload)
    if action == "repair_result":
        return report_service.report_repair_result(payload)
    if action == "top_up":
        return payment_service.create_top_up(payload)
    if action == "confirm_mock_top_up":
        return payment_service.confirm_mock_top_up(payload)
    if action == "create_checkout_session":
        return payment_service.create_checkout_session(payload)
    if action == "confirm_checkout_session":
        return payment_service.confirm_checkout_session(payload)
    if action == "logout":
        revoke_access_token(message["token"])
        return auth_service.logout()

    return error_response(f"Unknown socket action: {action}", 400)


def handle_client(connection, address):
    try:
        raw_data = connection.recv(4096)
        if not raw_data:
            return

        message = json.loads(raw_data.decode("utf-8"))
        response = _normalize_service_response(dispatch_message(message))
        print(
            "[SOCKET] "
            f"from={address[0]} "
            f"action={message.get('action')} "
            f"agent={message.get('agent_id')} "
            f"scooter={message.get('scooter_id')} "
            f"status={response.get('status_code')}"
        )
        connection.sendall(json.dumps(response, default=_json_default).encode("utf-8"))
    except Exception as error:
        response = {
            "success": False,
            "message": str(error),
            "data": {"address": str(address)},
            "status_code": 500,
        }
        print(f"[SOCKET][ERROR] from={address[0]} message={error}")
        connection.sendall(json.dumps(response, default=_json_default).encode("utf-8"))
    finally:
        connection.close()


def start_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((Config.SOCKET_HOST, Config.SOCKET_PORT))
    server.listen()
    print(f"Socket server listening on {Config.SOCKET_HOST}:{Config.SOCKET_PORT}")

    try:
        while True:
            connection, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(connection, address), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("Shutting down socket server...")


if __name__ == "__main__":
    start_socket_server()