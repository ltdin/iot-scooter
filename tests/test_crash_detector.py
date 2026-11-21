import unittest

from agent.crash_detector import CrashDetector


def accel(x=0.0, y=0.0, z=1.0):
    return {"x": x, "y": y, "z": z}
def orientation(pitch=0.0, roll=0.0, yaw=0.0):
    return {"pitch": pitch, "roll": roll, "yaw": yaw}

class FakeClock:
    def __init__(self, start=0.0):
        self.now = start
    def advance(self, seconds):
        self.now += seconds
    def __call__(self):
        return self.now
    
class CrashDetectorTests(unittest.TestCase):
    def _detector(self, clock):
        return CrashDetector(
            g_force_threshold=2.5,
            orientation_delta_threshold_deg=45.0,
            window_seconds=0.5,
            cooldown_seconds=30.0,
            time_provider=clock,
        )
    def test_idle_riding_does_not_trigger(self):
        clock = FakeClock()
        detector = self._detector(clock)
        for _ in range(10):
            self.assertIsNone(detector.submit_sample(accel(z=1.0), orientation()))
            clock.advance(0.05)
    def test_high_g_without_orientation_change_does_not_trigger(self):
        clock = FakeClock()
        detector = self._detector(clock)
        self.assertIsNone(detector.submit_sample(accel(z=3.5), orientation()))
        clock.advance(0.05)
        self.assertIsNone(detector.submit_sample(accel(z=1.0), orientation()))
    def test_orientation_change_without_high_g_does_not_trigger(self):
        clock = FakeClock()
        detector = self._detector(clock)
        self.assertIsNone(detector.submit_sample(accel(z=1.0), orientation(roll=0.0)))
        clock.advance(0.2)
        self.assertIsNone(detector.submit_sample(accel(z=1.0), orientation(roll=80.0)))
    def test_high_g_and_orientation_change_within_window_triggers(self):
        clock = FakeClock()
        detector = self._detector(clock)
        self.assertIsNone(detector.submit_sample(accel(z=1.0), orientation(roll=0.0)))
        clock.advance(0.1)
        detection = detector.submit_sample(accel(x=3.0, z=1.5), orientation(roll=60.0))
        self.assertIsNotNone(detection)
        self.assertGreaterEqual(detection["peak_g_force"], 2.5)
        self.assertGreaterEqual(detection["orientation_delta_deg"], 45.0)
    def test_cooldown_suppresses_duplicate_alert(self):
        clock = FakeClock()
        detector = self._detector(clock)
        detector.submit_sample(accel(z=1.0), orientation(roll=0.0))
        clock.advance(0.1)
        first = detector.submit_sample(accel(x=3.0, z=1.5), orientation(roll=60.0))
        self.assertIsNotNone(first)
        clock.advance(0.1)
        second = detector.submit_sample(accel(x=3.0, z=1.5), orientation(roll=60.0))
        self.assertIsNone(second)
    def test_cooldown_expires_and_allows_new_alert(self):
        clock = FakeClock()
        detector = self._detector(clock)
        detector.submit_sample(accel(z=1.0), orientation(roll=0.0))
        clock.advance(0.1)
        detector.submit_sample(accel(x=3.0, z=1.5), orientation(roll=60.0))
        clock.advance(31.0)
        detector.submit_sample(accel(z=1.0), orientation(roll=0.0))
        clock.advance(0.1)
        detection = detector.submit_sample(accel(x=3.0, z=1.5), orientation(roll=60.0))
        self.assertIsNotNone(detection)
    def test_orientation_wrap_around_handled(self):
        clock = FakeClock()
        detector = self._detector(clock)
        detector.submit_sample(accel(z=1.0), orientation(yaw=350.0))
        clock.advance(0.1)
        detection = detector.submit_sample(accel(x=3.0, z=1.5), orientation(yaw=50.0))
        self.assertIsNotNone(detection)
        self.assertLess(detection["orientation_delta_deg"], 180.0)
if __name__ == "__main__":
    unittest.main()
