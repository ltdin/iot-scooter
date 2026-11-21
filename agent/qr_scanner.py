import json
import time

import requests
from picamera2 import Picamera2
from pyzbar.pyzbar import decode


AGENT_GATEWAY_BASE_URL = "http://127.0.0.1:7000"
DEFAULT_CUSTOMER_ROLE = "customer"
DEFAULT_ENGINEER_ROLE = "engineer"


def parse_qr_data(qr_text):
    """
    Parse customer and engineer QR codes.

    Customer QR formats:
    UNLOCK|BK-XXXXXXXXXXXX|3
    LOCK|BK-XXXXXXXXXXXX|3

    Engineer QR formats:
    ENGINEER_UNLOCK|S004|5
    ENGINEER_LOCK|S004|5
    """

    qr_text = qr_text.strip()

    if not qr_text:
        print("QR detected, but it is empty.")
        return None

    parts = qr_text.split("|")

    if len(parts) != 3:
        print("QR detected, but format is invalid.")
        print("Expected formats:")
        print("  UNLOCK|BK-XXXXXXXXXXXX|3")
        print("  LOCK|BK-XXXXXXXXXXXX|3")
        print("  ENGINEER_UNLOCK|S004|5")
        print("  ENGINEER_LOCK|S004|5")
        print("Raw QR content:", qr_text)
        return None

    action = parts[0].strip().upper()
    value = parts[1].strip()
    user_id = parts[2].strip()

    if not user_id:
        print("QR detected, but user_id is missing.")
        print("Raw QR content:", qr_text)
        return None

    if action in {"UNLOCK", "LOCK"}:
        if not value.startswith("BK-"):
            print("QR detected, but customer unlock_code is invalid.")
            print("unlock_code should start with BK-")
            print("Raw QR content:", qr_text)
            return None

        return {
            "qr_type": "customer",
            "action": action,
            "unlock_code": value,
            "user_id": user_id,
            "role": DEFAULT_CUSTOMER_ROLE,
        }

    if action in {"ENGINEER_UNLOCK", "ENGINEER_LOCK"}:
        if not value:
            print("QR detected, but scooter_id is missing.")
            print("Raw QR content:", qr_text)
            return None

        return {
            "qr_type": "engineer",
            "action": action,
            "scooter_id": value,
            "user_id": user_id,
            "role": DEFAULT_ENGINEER_ROLE,
        }

    print("QR detected, but action is invalid.")
    print("Valid actions: UNLOCK, LOCK, ENGINEER_UNLOCK, ENGINEER_LOCK")
    print("Raw QR content:", qr_text)
    return None


def send_customer_qr_request(qr_data):
    """
    Send customer QR unlock or QR lock request to Agent Gateway.
    """

    if qr_data["action"] == "UNLOCK":
        endpoint = "/agent/bookings/qr-unlock"
    else:
        endpoint = "/agent/bookings/qr-lock"

    url = f"{AGENT_GATEWAY_BASE_URL}{endpoint}"

    payload = {
        "unlock_code": qr_data["unlock_code"],
        "user_id": qr_data["user_id"],
        "role": qr_data["role"],
    }

    print("\nSending customer QR request...")
    print("Action:", qr_data["action"])
    print("POST", url)
    print("Payload:", payload)

    return send_post_request(url, payload)


def send_engineer_qr_request(qr_data):
    """
    Send engineer QR unlock or QR lock request to Agent Gateway.
    """

    if qr_data["action"] == "ENGINEER_UNLOCK":
        endpoint = "/agent/engineer/qr-unlock"
    else:
        endpoint = "/agent/engineer/qr-lock"

    url = f"{AGENT_GATEWAY_BASE_URL}{endpoint}"

    payload = {
        "scooter_id": qr_data["scooter_id"],
        "user_id": qr_data["user_id"],
        "role": qr_data["role"],
    }

    print("\nSending engineer QR request...")
    print("Action:", qr_data["action"])
    print("POST", url)
    print("Payload:", payload)

    return send_post_request(url, payload)


def send_post_request(url, payload):
    """
    Send POST request and print the server response.
    """

    try:
        response = requests.post(url, json=payload, timeout=10)

        try:
            result = response.json()
        except ValueError:
            print("\nServer did not return JSON.")
            print("Server response status:", response.status_code)
            print("Raw response:", response.text)
            return None

        print("\nServer response status:", response.status_code)
        print("Server response JSON:")
        print(json.dumps(result, indent=2))

        return result

    except requests.RequestException as error:
        print("Request failed:", error)
        return None


def send_qr_request(qr_data):
    """
    Route customer and engineer QR requests to the correct endpoint.
    """

    if qr_data["qr_type"] == "customer":
        return send_customer_qr_request(qr_data)

    if qr_data["qr_type"] == "engineer":
        return send_engineer_qr_request(qr_data)

    print("Unknown QR type:", qr_data.get("qr_type"))
    return None


def scan_qr_code():
    """
    Open Raspberry Pi Camera Module, scan QR code,
    and call the correct Agent Gateway endpoint.
    """

    print("Starting QR scanner...")
    print("Show a customer or engineer QR code in front of the camera.")
    print("Expected QR formats:")
    print("  UNLOCK|BK-XXXXXXXXXXXX|3")
    print("  LOCK|BK-XXXXXXXXXXXX|3")
    print("  ENGINEER_UNLOCK|S004|5")
    print("  ENGINEER_LOCK|S004|5")
    print("Press Ctrl+C to stop.\n")

    camera = Picamera2()

    camera_config = camera.create_preview_configuration(
        main={"size": (1280, 720), "format": "RGB888"}
    )

    camera.configure(camera_config)
    camera.start()

    time.sleep(1)

    last_qr_text = None

    try:
        while True:
            frame = camera.capture_array()
            qr_codes = decode(frame)

            for qr_code in qr_codes:
                qr_text = qr_code.data.decode("utf-8").strip()

                if qr_text == last_qr_text:
                    continue

                last_qr_text = qr_text

                print("\nQR detected:", qr_text)

                qr_data = parse_qr_data(qr_text)

                if qr_data is not None:
                    print("Valid QR.")
                    print("QR Type:", qr_data["qr_type"])
                    print("Action:", qr_data["action"])

                    if qr_data["qr_type"] == "customer":
                        print("Unlock Code:", qr_data["unlock_code"])
                    else:
                        print("Scooter ID:", qr_data["scooter_id"])

                    print("User ID:", qr_data["user_id"])
                    print("Role:", qr_data["role"])

                    send_qr_request(qr_data)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping QR scanner...")

    finally:
        camera.stop()
        print("Camera stopped.")


if __name__ == "__main__":
    scan_qr_code()