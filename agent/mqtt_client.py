import paho.mqtt.client as mqtt
from master.config import Config
from sense_hat import SenseHat
import datetime as dt
import json, time
from agent.sensehat_controller import SensehatController
from shared.rsa_utils import verify_signature
from agent.socket_client import send_to_master
from shared.socket_messages import build_socket_message
from shared.display_variables import Color

SCOOTER_ID = "S099"

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_SUBS_SCOOTER_STATUS = f"scooter_status/"
MQTT_SUBS_LOCK_STATUS = f"lock_status/"

MQTT_PUBL_EVENT = f"scooter/{SCOOTER_ID}/sensor"
MQTT_PUBL_STATUS = f"scooter/{SCOOTER_ID}/status"
MQTT_PUBL_LOCK = f"scooter/{SCOOTER_ID}/lock"

def display_scooter_status(scooter_id):
    response = send_to_master(
        build_socket_message(
            action="get_scooter",
            agent_id="local-agent",
            scooter_id=SCOOTER_ID
        ),
        master_host="127.0.0.1"
    )
    if not response.get("success"): print("Failed to get scooter status")
    sensehat_controller = SensehatController()
    sensehat_controller.display_status(response["data"].get("status", Color.WHITE.value))

class MQTTClient:
    def __init__(self, scooter_id=None, broker=MQTT_HOST, port=MQTT_PORT, alive=60):
        self.scooter_id = scooter_id if scooter_id is not None else SCOOTER_ID
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.scooter_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_default

        self.client.message_callback_add(MQTT_SUBS_SCOOTER_STATUS + self.scooter_id, self.on_status_update)
        self.client.message_callback_add(MQTT_SUBS_LOCK_STATUS + self.scooter_id, self.on_lock_status_update)

        self.broker = broker
        self.port = port

        self.sensehat_controller = SensehatController()

        self.client.connect(broker, port, alive)

    def on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            print(f"Connection: {str(rc)}. To {self.broker} at port {self.port}.")

            self.client.subscribe(MQTT_SUBS_SCOOTER_STATUS + self.scooter_id)
            self.client.subscribe(MQTT_SUBS_LOCK_STATUS + self.scooter_id)

        else:
            print(f"Connection: {str(rc)}. To {self.broker} at port {self.port}.")
            
    def on_default(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        print(f"{topic}: {payload}")

    def on_status_update(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        data = json.loads(payload)
        status = data.get("status")
        signature = data.get("signature")

        if signature is None or not verify_signature(status, signature):
            print(f"Invalid signature. Message ignored.")
        else:
            self.sensehat_controller.display_status(status)
            self.publish_status(status)

    def on_lock_status_update(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        data = json.loads(payload)
        lock_status = data.get("lock_status")
        signature = data.get("signature")

        if signature is None or not verify_signature(lock_status, signature):
            print(f"Invalid signature. Message ignored.")
        else:
            print("Scooter Locked" if lock_status == "Locked" else "Scooter Unlocked")
            self.publish_lock_status(lock_status)

    def publish_sensor_data(self, interval=20):

        while True:
            temp = self.sensehat_controller.collect_temperature()
            humidity = self.sensehat_controller.collect_humidity()
            current = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            payload = {
                "time": current,
                "temp": round(temp, 2),
                "humid": round(humidity, 2)
            }
            msg = json.dumps(payload)

            self.client.publish(MQTT_PUBL_EVENT, msg)
            time.sleep(interval)

    def publish_lock_status(self, status):

        current = dt.datetime.now().strftime("%y-%m-%d %H:%M:%S")
        payload = {
            "time": current,
            "status": status
        }
        msg = json.dumps(payload)

        self.client.publish(MQTT_PUBL_LOCK, msg)

    def publish_status(self, status):

        current = dt.datetime.now().strftime("%y-%m-%d %H:%M:%S")
        payload = {
            "time": current,
            "status": status
        }
        msg = json.dumps(payload)

        self.client.publish(MQTT_PUBL_STATUS, msg)

    def start(self):
        try:
            self.client.loop_start()
            self.publish_sensor_data()
            
        except KeyboardInterrupt:
            print(f"Shutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    client = MQTTClient(SCOOTER_ID, MQTT_HOST, MQTT_PORT)
    display_scooter_status(SCOOTER_ID)
    client.start()

        







