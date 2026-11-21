"""Pure-Python theft classifier; no hardware imports.
"""

import math
import time


class TheftDetector:
    GUARDED_STATUSES = {"Available", "Booked"}
    def __init__(
        self,
        motion_threshold_g=0.3,
        window_seconds=2.0,
        sustained_seconds=1.5,
        cooldown_seconds=60.0,
        time_provider=None,
    ):
        self.motion_threshold_g = motion_threshold_g
        self.window_seconds = window_seconds
        self.sustained_seconds = sustained_seconds
        self.cooldown_seconds = cooldown_seconds
        self._time_provider = time_provider or time.monotonic
        self._samples = []
        self._last_alert_at = None
    def submit_sample(self, accel, current_status):
        if current_status not in self.GUARDED_STATUSES:
            self._samples = []
            return None
        now = self._time_provider()
        magnitude = self._gravity_normalised_magnitude(accel)
        self._samples.append((now, magnitude))
        self._prune_window(now)
        if self._in_cooldown(now):
            return None
        if not self._is_sustained_motion():
            return None
        mean = sum(s[1] for s in self._samples) / len(self._samples)
        self._last_alert_at = now
        return {
            "mean_magnitude_g": mean,
            "sustained_seconds": self._samples[-1][0] - self._samples[0][0],
            "window_seconds": self.window_seconds,
            "current_status": current_status,
        }
    def reset(self):
        self._samples = []
        self._last_alert_at = None
    def _gravity_normalised_magnitude(self, accel):
        total = math.sqrt(accel["x"] ** 2 + accel["y"] ** 2 + accel["z"] ** 2)
        return abs(total - 1.0)
    def _prune_window(self, now):
        cutoff = now - self.window_seconds
        self._samples = [s for s in self._samples if s[0] >= cutoff]
    def _in_cooldown(self, now):
        if self._last_alert_at is None:
            return False
        return (now - self._last_alert_at) < self.cooldown_seconds
    def _is_sustained_motion(self):
        if not self._samples:
            return False
        span = self._samples[-1][0] - self._samples[0][0]
        if span < self.sustained_seconds:
            return False
        mean = sum(s[1] for s in self._samples) / len(self._samples)
        return mean >= self.motion_threshold_g
