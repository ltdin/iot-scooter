"""Thin paho-mqtt publisher used by Agent Pis to emit safety/security events."""

import json
import threading

import paho.mqtt.client as mqtt

from shared.safety_topics import sign_payload


class MQTTPublisher:
    def __init__(self, host, port, secret_key, client_id=None, keepalive=60):
        self.host = host
        self.port = port
        self.secret_key = secret_key
        self.keepalive = keepalive
        self.client = mqtt.Client(client_id=client_id, clean_session=True)
        self._lock = threading.Lock()
        self._connected = False
    def connect(self):
        with self._lock:
            if self._connected:
                return
            self.client.connect(self.host, self.port, keepalive=self.keepalive)
            self.client.loop_start()
            self._connected = True
    def disconnect(self):
        with self._lock:
            if not self._connected:
                return
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False
    def publish(self, topic, payload, qos=1, publish_timeout=5):
        if not self._connected:
            self.connect()
        signed = sign_payload(payload, self.secret_key)
        info = self.client.publish(topic, json.dumps(signed), qos=qos)
        info.wait_for_publish(timeout=publish_timeout)
        return info.is_published()
