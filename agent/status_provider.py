"""Background poller that caches the Master Pi view of a scooter's status.

The theft detector uses the cached status to decide whether motion is a
legitimate ride (Occupying) or a security event (Available / Booked).
"""

import json
import sys
import threading
import urllib.error
import urllib.request


class StatusProvider:
    UNKNOWN = "Unknown"
    def __init__(self, mp_base_url, scooter_id, poll_interval=10.0, request_timeout=5.0):
        self.mp_base_url = mp_base_url.rstrip("/")
        self.scooter_id = scooter_id
        self.poll_interval = poll_interval
        self.request_timeout = request_timeout
        self._status = self.UNKNOWN
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
    def start(self):
        if self._thread is not None:
            return
        self.refresh_once()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
    def stop(self):
        self._stop.set()
    def get_status(self):
        with self._lock:
            return self._status
    def set_status(self, status):
        with self._lock:
            self._status = status
    def refresh_once(self):
        url = f"{self.mp_base_url}/api/scooters/{self.scooter_id}"
        try:
            with urllib.request.urlopen(url, timeout=self.request_timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            print(f"[STATUS] poll failed for {self.scooter_id}: {error}", file=sys.stderr)
            return False
        if not data.get("success"):
            print(f"[STATUS] MP rejected lookup for {self.scooter_id}: {data.get('message')}", file=sys.stderr)
            return False
        payload = data.get("data") or {}
        status = payload.get("status")
        if status:
            self.set_status(status)
            return True
        return False
    def _poll_loop(self):
        while not self._stop.wait(self.poll_interval):
            self.refresh_once()
