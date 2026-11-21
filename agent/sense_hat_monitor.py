"""Hardware-backed Sense HAT IMU loop for crash detection.
"""

import time

from sense_hat import SenseHat

from agent.crash_detector import CrashDetector
from agent.theft_detector import TheftDetector

class SenseHatCrashMonitor:
    SAMPLE_HZ = 50
    def __init__(self, on_crash, sense_hat=None, detector=None, sample_hz=None):
        self.sense = sense_hat or SenseHat()
        self.detector = detector or CrashDetector()
        self.on_crash = on_crash
        self.sample_hz = sample_hz or self.SAMPLE_HZ
        self._running = False
    def run(self):
        self._running = True
        interval = 1.0 / self.sample_hz
        while self._running:
            cycle_start = time.monotonic()
            accel = self._read_accel()
            orientation = self.sense.get_orientation_degrees()
            detection = self.detector.submit_sample(accel, orientation)
            if detection:
                self._render_sos()
                self.on_crash(detection)
            elapsed = time.monotonic() - cycle_start
            sleep_for = interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
    def stop(self):
        self._running = False
    def _read_accel(self):
        return self.sense.get_accelerometer_raw()
    def _render_sos(self):
        red = (255, 0, 0)
        self.sense.show_message("SOS", text_colour=red, scroll_speed=0.05)
        self.sense.clear()


class SenseHatSafetyMonitor:
    SAMPLE_HZ = 50
    def __init__(
        self,
        on_crash=None,
        on_theft=None,
        status_provider=None,
        sense_hat=None,
        crash_detector=None,
        theft_detector=None,
        sample_hz=None,
    ):
        self.sense = sense_hat or SenseHat()
        self.crash_detector = crash_detector or CrashDetector()
        self.theft_detector = theft_detector or TheftDetector()
        self.on_crash = on_crash
        self.on_theft = on_theft
        self.status_provider = status_provider
        self.sample_hz = sample_hz or self.SAMPLE_HZ
        self._running = False
    def run(self):
        self._running = True
        interval = 1.0 / self.sample_hz
        while self._running:
            cycle_start = time.monotonic()
            accel = self.sense.get_accelerometer_raw()
            orientation = self.sense.get_orientation_degrees()
            current_status = (
                self.status_provider.get_status() if self.status_provider else "Unknown"
            )
            if self.on_crash is not None:
                crash = self.crash_detector.submit_sample(accel, orientation)
                if crash:
                    self._render_sos()
                    self.on_crash(crash)
            if self.on_theft is not None:
                theft = self.theft_detector.submit_sample(accel, current_status)
                if theft:
                    self._render_theft_alert()
                    self.on_theft(theft)
            elapsed = time.monotonic() - cycle_start
            sleep_for = interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
    def stop(self):
        self._running = False
    def _render_sos(self):
        red = (255, 0, 0)
        self.sense.show_message("SOS", text_colour=red, scroll_speed=0.05)
        self.sense.clear()
    def _render_theft_alert(self):
        red = (255, 0, 0)
        self.sense.show_message("THEFT", text_colour=red, scroll_speed=0.06)
        self.sense.clear()
