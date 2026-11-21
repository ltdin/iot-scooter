"""Pure-Python crash classifier kept free of hardware imports.

The detector accepts IMU samples (accelerometer + orientation) one at a
time and decides whether the recent window indicates a crash. Two
conditions must both hold within the same rolling window:
"""

import math
import time


class CrashDetector:
    def __init__(
        self,
        g_force_threshold=2.5,
        orientation_delta_threshold_deg=45.0,
        window_seconds=0.5,
        cooldown_seconds=30.0,
        time_provider=None,
    ):
        self.g_force_threshold = g_force_threshold
        self.orientation_delta_threshold_deg = orientation_delta_threshold_deg
        self.window_seconds = window_seconds
        self.cooldown_seconds = cooldown_seconds
        self._time_provider = time_provider or time.monotonic
        self._samples = []
        self._last_alert_at = None

    def submit_sample(self, accel, orientation):
        now = self._time_provider()
        g_force = self._magnitude(accel)
        self._samples.append((now, g_force, dict(orientation)))
        self._prune_window(now)
        if self._in_cooldown(now):
            return None
        peak_g = max(sample[1] for sample in self._samples)
        if peak_g < self.g_force_threshold:
            return None
        orientation_delta = self._max_orientation_delta()
        if orientation_delta < self.orientation_delta_threshold_deg:
            return None
        self._last_alert_at = now
        return {
            "peak_g_force": peak_g,
            "orientation_delta_deg": orientation_delta,
            "window_seconds": self.window_seconds,
        }
    def reset(self):
        self._samples = []
        self._last_alert_at = None
    def _prune_window(self, now):
        cutoff = now - self.window_seconds
        self._samples = [sample for sample in self._samples if sample[0] >= cutoff]
    def _in_cooldown(self, now):
        if self._last_alert_at is None:
            return False
        return (now - self._last_alert_at) < self.cooldown_seconds
    def _magnitude(self, accel):
        return math.sqrt(accel["x"] ** 2 + accel["y"] ** 2 + accel["z"] ** 2)
    def _max_orientation_delta(self):
        if len(self._samples) < 2:
            return 0.0
        first = self._samples[0][2]
        last = self._samples[-1][2]
        return max(
            abs(_wrap_180(last["pitch"] - first["pitch"])),
            abs(_wrap_180(last["roll"] - first["roll"])),
            abs(_wrap_180(last["yaw"] - first["yaw"])),
        )
def _wrap_180(angle):
    return (angle + 180.0) % 360.0 - 180.0
