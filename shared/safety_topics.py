"""MQTT topic structure and payload signing for safety/security events.
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone


TOPIC_PREFIX = "scooter"
TOPIC_PATTERN_SAFETY = f"{TOPIC_PREFIX}/+/safety"
TOPIC_PATTERN_SECURITY = f"{TOPIC_PREFIX}/+/security"

EVENT_CRASH = "crash_detected"
EVENT_THEFT = "theft_suspected"

def build_safety_topic(scooter_id):
    return f"{TOPIC_PREFIX}/{scooter_id}/safety"
def build_security_topic(scooter_id):
    return f"{TOPIC_PREFIX}/{scooter_id}/security"
def _canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
def sign_payload(payload, secret_key):
    body = {k: v for k, v in payload.items() if k != "signature"}
    digest = hmac.new(secret_key.encode("utf-8"), _canonical(body), hashlib.sha256).hexdigest()
    body["signature"] = digest
    return body
def verify_payload(payload, secret_key):
    if not isinstance(payload, dict):
        return False
    received = payload.get("signature")
    if not isinstance(received, str) or not received:
        return False
    body = {k: v for k, v in payload.items() if k != "signature"}
    expected = hmac.new(secret_key.encode("utf-8"), _canonical(body), hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)
def build_crash_payload(
    scooter_id,
    g_force,
    orientation_delta_deg,
    booking_id=None,
    rider_id=None,
    location=None,
    timestamp=None,
):
    return {
        "event": EVENT_CRASH,
        "scooter_id": scooter_id,
        "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "g_force": round(float(g_force), 3),
        "orientation_delta_deg": round(float(orientation_delta_deg), 2),
        "booking_id": booking_id,
        "rider_id": rider_id,
        "location": location,
    }
def build_theft_payload(
    scooter_id,
    motion_magnitude,
    current_status,
    window_seconds,
    location=None,
    timestamp=None,
):
    return {
        "event": EVENT_THEFT,
        "scooter_id": scooter_id,
        "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "motion_magnitude": round(float(motion_magnitude), 3),
        "window_seconds": round(float(window_seconds), 2),
        "current_status": current_status,
        "location": location,
    }
