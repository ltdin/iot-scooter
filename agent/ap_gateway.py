"""HTTP gateway on Agent Pi that forwards browser requests to Master Pi socket.

"""

import os

from flask import Flask, jsonify, request

from agent.socket_client import send_to_master
from shared.socket_messages import build_socket_message


def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


MASTER_HOST = os.getenv("MASTER_HOST", "127.0.0.1")
MASTER_SOCKET_PORT = _env_int("MASTER_SOCKET_PORT", os.getenv("SOCKET_PORT", "9000"))
AGENT_ID = os.getenv("AGENT_ID", "agent-pi-01")
AGENT_GATEWAY_HOST = os.getenv("AGENT_GATEWAY_HOST", "0.0.0.0")
AGENT_GATEWAY_PORT = _env_int("AGENT_GATEWAY_PORT", "7000")

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = os.getenv("AGENT_CORS_ORIGIN", "*")
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/agent/<path:_path>", methods=["OPTIONS"])
@app.route("/agent", methods=["OPTIONS"])
def cors_preflight(_path=None):
    return ("", 204)


def _json_payload():
    return request.get_json(silent=True) or {}


def _bearer_token():
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return None


def _forward(action, payload=None, scooter_id=None, token=None):
    message = build_socket_message(
        action=action,
        agent_id=AGENT_ID,
        scooter_id=scooter_id,
        token=token or _bearer_token(),
        payload=payload or {},
    )
    response = send_to_master(
        message,
        master_host=MASTER_HOST,
        master_port=MASTER_SOCKET_PORT,
    )
    return jsonify(response), response.get("status_code", 200)


@app.get("/agent/health")
def health():
    return jsonify(
        {
            "success": True,
            "message": "Agent gateway is running",
            "data": {
                "agent_id": AGENT_ID,
                "master_host": MASTER_HOST,
                "master_socket_port": MASTER_SOCKET_PORT,
            },
        }
    )


@app.get("/agent/me")
def current_user():
    return _forward("get_current_user")


@app.post("/agent/socket")
def generic_socket_action():
    body = _json_payload()
    action = body.get("action")
    if not action:
        return jsonify({"success": False, "message": "Missing required field: action", "data": None}), 400

    return _forward(
        action=action,
        payload=body.get("payload", {}),
        scooter_id=body.get("scooter_id"),
        token=body.get("token") or _bearer_token(),
    )


@app.post("/agent/register")
def register():
    return _forward("register", _json_payload())


@app.post("/agent/login")
def login():
    payload = _json_payload()
    payload.setdefault("source", "AP")
    return _forward("login", payload)


@app.post("/agent/logout")
def logout():
    return _forward("logout", _json_payload())


@app.post("/agent/bookings")
def book():
    payload = _json_payload()
    return _forward("book", payload, scooter_id=payload.get("scooter_id"))


@app.get("/agent/scooters/available")
def list_available_scooters():
    return _forward("list_available_scooters")


@app.get("/agent/scooters/<scooter_id>")
def get_scooter(scooter_id):
    return _forward("get_scooter", {"scooter_id": scooter_id}, scooter_id=scooter_id)


@app.post("/agent/bookings/<int:booking_id>/cancel")
def cancel_booking(booking_id):
    payload = _json_payload()
    payload["booking_id"] = booking_id
    return _forward("cancel_booking", payload)


@app.post("/agent/bookings/qr-unlock")
def qr_unlock():
    return _forward("qr_unlock", _json_payload())


@app.post("/agent/bookings/qr-lock")
def qr_lock():
    return _forward("qr_lock", _json_payload())


@app.post("/agent/engineer/qr-unlock")
def engineer_qr_unlock():
    payload = _json_payload()
    return _forward(
        "engineer_qr_unlock",
        payload,
        scooter_id=payload.get("scooter_id"),
    )


@app.post("/agent/engineer/qr-lock")
def engineer_qr_lock():
    payload = _json_payload()
    return _forward(
        "engineer_qr_lock",
        payload,
        scooter_id=payload.get("scooter_id"),
    )


@app.post("/agent/scooters/<scooter_id>/unlock")
def unlock(scooter_id):
    payload = _json_payload()
    payload["scooter_id"] = scooter_id
    return _forward("unlock", payload, scooter_id=scooter_id)


@app.post("/agent/scooters/<scooter_id>/credential-unlock")
def credential_unlock(scooter_id):
    payload = _json_payload()
    payload["scooter_id"] = scooter_id
    return _forward("credential_unlock", payload, scooter_id=scooter_id)


@app.post("/agent/scooters/<scooter_id>/credential-lock")
def credential_lock(scooter_id):
    payload = _json_payload()
    payload["scooter_id"] = scooter_id
    return _forward("credential_lock", payload, scooter_id=scooter_id)


@app.post("/agent/scooters/<scooter_id>/lock")
def lock(scooter_id):
    payload = _json_payload()
    payload["scooter_id"] = scooter_id
    return _forward("lock", payload, scooter_id=scooter_id)


@app.post("/agent/reports")
def report_issue():
    payload = _json_payload()
    return _forward("report_issue", payload, scooter_id=payload.get("scooter_id"))


@app.get("/agent/reports")
def list_reports():
    return _forward("list_reports")


@app.put("/agent/reports/<int:report_id>/status")
def update_report_status(report_id):
    payload = _json_payload()
    payload["report_id"] = report_id
    return _forward("update_report_status", payload)


@app.post("/agent/engineer/repair-results")
def repair_result():
    payload = _json_payload()
    return _forward("repair_result", payload, scooter_id=payload.get("scooter_id"))


@app.post("/agent/payments/top-up")
def top_up():
    return _forward("top_up", _json_payload())


@app.post("/agent/payments/top-up/mock-confirm")
def confirm_mock_top_up():
    return _forward("confirm_mock_top_up", _json_payload())


@app.post("/agent/payments/checkout-session")
def create_checkout_session():
    return _forward("create_checkout_session", _json_payload())


@app.post("/agent/payments/checkout-session/confirm")
def confirm_checkout_session():
    return _forward("confirm_checkout_session", _json_payload())


def main():
    print(
        "Agent gateway listening on "
        f"{AGENT_GATEWAY_HOST}:{AGENT_GATEWAY_PORT}; "
        f"forwarding socket messages to {MASTER_HOST}:{MASTER_SOCKET_PORT}"
    )
    app.run(host=AGENT_GATEWAY_HOST, port=AGENT_GATEWAY_PORT, debug=False)


if __name__ == "__main__":
    main()