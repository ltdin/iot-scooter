import paho.mqtt.client as mqtt
from master.config import Config
import datetime as dt
import time, json, os, threading
from shared.rsa_utils import sign_message, generate_keys

from master.config import Config
from master.services.safety_service import SafetyService
from shared.safety_topics import (
    EVENT_CRASH,
    EVENT_THEFT,
    TOPIC_PATTERN_SAFETY,
    TOPIC_PATTERN_SECURITY,
    verify_payload,
)

MQTT_CLIENT_DATA = "scooter/#"
MQTT_CLIENT_STATUS = "scooter/+/status"
MQTT_CLIENT_SENSOR = "scooter/+/sensor"
MQTT_CLIENT_LOCK = "scooter/+/lock"

class MQTTServer:
    def __init__(self, broker=Config.MQTT_HOST, port=Config.MQTT_PORT, alive=60):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_default
        self.client.on_disconnect = self.on_disconnect

        self.broker = broker
        self.port = port
        self.alive = alive

        self.safety_service = SafetyService()

        self.client.message_callback_add(TOPIC_PATTERN_SAFETY, self.on_incident_detected)
        self.client.message_callback_add(TOPIC_PATTERN_SECURITY, self.on_incident_detected)
        self.client.message_callback_add(MQTT_CLIENT_STATUS, self.on_status_update)
        self.client.message_callback_add(MQTT_CLIENT_LOCK, self.on_lock_status_update)
        self.client.message_callback_add(MQTT_CLIENT_SENSOR, self.on_sensor_update)

    def generate_rsa_keys(self):
        print("Generating RSA keys...")
        if os.path.exists("shared/private_key.pem") and os.path.exists("shared/public_key.pem"):
            print("RSA keys detected. Skipping generation.")
        else:
            print("No RSA keys found. Generating new keys...")
            generate_keys()

    def on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            print(f"[MQTT] Connected to {Config.MQTT_HOST}:{Config.MQTT_PORT}")

            self.client.subscribe(MQTT_CLIENT_DATA)
        else:
            print(f"[MQTT] Connection failed rc={rc}")

    def on_default(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        print(f"{topic}: {payload}")

    def on_sensor_update(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        payload = json.loads(payload)
        time = payload.get("time", "")
        temp = payload.get("temp", "")
        humid = payload.get("humid", "")
        unit = topic.split("/")[1] if "/" in topic else "unknown"

        print(f"[MQTT][SENSOR][{unit}] {time} Temperature: {temp}  Humidity: {humid}")

    def on_status_update(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        payload = json.loads(payload)
        time = payload.get("time", "")
        status = payload.get("status", "")
        unit = topic.split("/")[1] if "/" in topic else "unknown"

        print(f"[MQTT][STATUS][{unit}] {time} Status: {status}")

    def on_lock_status_update(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        payload = json.loads(payload)
        time = payload.get("time", "")
        status = payload.get("status", "")
        unit = topic.split("/")[1] if "/" in topic else "unknown"

        print(f"[MQTT][LOCK][{unit}] {time} Lock status: {status}")

    def on_disconnect(self,client, userdata, disconnect_flags, rc, properties):
        print(f"[MQTT] Disconnected rc={rc}")

    def on_incident_detected(self, client, userdata, msg):
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
        time = payload.get("timestamp", "")
        if event_type == EVENT_CRASH:
            result = self.safety_service.handle_crash_event(payload)
            self._log_dispatch(topic, event_type, result, time)
        elif event_type == EVENT_THEFT:
            result = self.safety_service.handle_theft_event(payload)
            self._log_dispatch(topic, event_type, result, time)
        else:
            print(f"[MQTT][REJECT] unknown event '{event_type}' on {topic}")

    def _log_dispatch(self, topic, event, result, time):
        body = result[0] if isinstance(result, tuple) else result
        status_code = result[1] if isinstance(result, tuple) else 200
        success = body.get("success") if isinstance(body, dict) else None
        unit = topic.split("/")[1] if "/" in topic else "unknown"
        print(f"[MQTT][INCIDENT][{unit}] {time} event={event} topic={topic} success={success} status={status_code}")

    def publish_scooter_status(self, scooter_id, status):
        self.client.connect(self.broker, self.port, 20)
        
        publish_topic = f"scooter_status/{scooter_id}"
        signature = sign_message(status)

        payload = {
            "status": status,
            "signature": signature.hex()
        }
        msg = json.dumps(payload, indent=4)

        self.client.publish(publish_topic, msg)

    def publish_lock_status(self, scooter_id, lock_status):
        self.client.connect(self.broker, self.port, 20)
        publish_topic = f"lock_status/{scooter_id}"
        signature = sign_message(lock_status)

        payload = {
            "lock_status": lock_status,
            "signature": signature.hex()
        }
        msg = json.dumps(payload, indent=4)

        self.client.publish(publish_topic, msg)

    def start(self):
        self.client.connect(self.broker, self.port, self.alive)

        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print(f"Shutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client.disconnect()

if __name__ == "__main__":
    server = MQTTServer(Config.MQTT_HOST, Config.MQTT_PORT)
    server.generate_rsa_keys()
    server.start()
