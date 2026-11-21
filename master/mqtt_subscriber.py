"""MQTT subscriber that listens for safety/security events from Agent Pis.

Uses the public test broker by default. Needs a valid HMAC signature from Config.SECRET_KEY.
"""

import json
import threading

import paho.mqtt.client as mqtt

from master.config import Config
from master.services.safety_service import SafetyService
from shared.safety_topics import (
    EVENT_CRASH,
    EVENT_THEFT,
    TOPIC_PATTERN_SAFETY,
    TOPIC_PATTERN_SECURITY,
    verify_payload,
)

class MQTTSubscriber:
    def __init__(self, safety_service=None, client=None):
        self.safety_service = safety_service or SafetyService()
        self.client = client or mqtt.Client(
            client_id=Config.MQTT_CLIENT_ID,
            clean_session=True,
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
    def _on_connect(self, client, _userdata, _flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected to {Config.MQTT_HOST}:{Config.MQTT_PORT}")
            client.subscribe([(TOPIC_PATTERN_SAFETY, 1), (TOPIC_PATTERN_SECURITY, 1)])
            print(
                f"[MQTT] Subscribed to {TOPIC_PATTERN_SAFETY} and {TOPIC_PATTERN_SECURITY}"
            )
        else:
            print(f"[MQTT] Connection failed rc={rc}")
    def _on_disconnect(self, _client, _userdata, rc):
        print(f"[MQTT] Disconnected rc={rc}")
    def _on_message(self, _client, _userdata, msg):
        try:
            self.handle_raw_message(msg.topic, msg.payload)
        except Exception as error:
            print(f"[MQTT][ERROR] handler crashed on {msg.topic}: {error}")
    def handle_raw_message(self, topic, raw_payload):
        if isinstance(raw_payload, (bytes, bytearray)):
            try:
                raw_payload = raw_payload.decode("utf-8")
            except UnicodeDecodeError as error:
                print(f"[MQTT][REJECT] non-utf8 payload on {topic}: {error}")
                return
        try:
            payload = json.loads(raw_payload)
        except ValueError as error:
            print(f"[MQTT][REJECT] non-json payload on {topic}: {error}")
            return
        if not verify_payload(payload, Config.SECRET_KEY):
            print(f"[MQTT][REJECT] invalid signature on {topic}")
            return
        event_type = payload.get("event")
        if event_type == EVENT_CRASH:
            result = self.safety_service.handle_crash_event(payload)
            self._log_dispatch(topic, event_type, result)
        elif event_type == EVENT_THEFT:
            result = self.safety_service.handle_theft_event(payload)
            self._log_dispatch(topic, event_type, result)
        else:
            print(f"[MQTT][REJECT] unknown event '{event_type}' on {topic}")
    def _log_dispatch(self, topic, event, result):
        body = result[0] if isinstance(result, tuple) else result
        status_code = result[1] if isinstance(result, tuple) else 200
        success = body.get("success") if isinstance(body, dict) else None
        print(f"[MQTT] event={event} topic={topic} success={success} status={status_code}")
    def start(self):
        self.client.connect(Config.MQTT_HOST, Config.MQTT_PORT, keepalive=Config.MQTT_KEEPALIVE)
        self.client.loop_forever()
def start_mqtt_subscriber():
    MQTTSubscriber().start()
def start_mqtt_subscriber_in_thread():
    thread = threading.Thread(target=start_mqtt_subscriber, daemon=True)
    thread.start()
    return thread
if __name__ == "__main__":
    start_mqtt_subscriber()
