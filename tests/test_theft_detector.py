import unittest

from agent.theft_detector import TheftDetector


def accel(x=0.0, y=0.0, z=1.0):
    return {"x": x, "y": y, "z": z}
class FakeClock:
    def __init__(self, start=0.0):
        self.now = start
    def advance(self, seconds):
        self.now += seconds
    def __call__(self):
        return self.now
def _detector(clock):
    return TheftDetector(
        motion_threshold_g=0.3,
        window_seconds=2.0,
        sustained_seconds=1.5,
        cooldown_seconds=60.0,
        time_provider=clock,
    )
def _feed_motion(detector, clock, status, magnitude_g, seconds, step=0.1):
    samples_per_second = int(1.0 / step)
    first_detection = None
    for _ in range(int(seconds * samples_per_second)):
        detection = detector.submit_sample(accel(z=1.0 + magnitude_g), status)
        if detection and first_detection is None:
            first_detection = detection
        clock.advance(step)
    return first_detection

class TheftDetectorTests(unittest.TestCase):
    def test_idle_scooter_does_not_trigger(self):
        clock = FakeClock()
        detector = _detector(clock)
        for _ in range(50):
            self.assertIsNone(detector.submit_sample(accel(z=1.0), "Booked"))
            clock.advance(0.1)
    def test_occupying_status_never_triggers(self):
        clock = FakeClock()
        detector = _detector(clock)
        last = _feed_motion(detector, clock, "Occupying", magnitude_g=0.5, seconds=5.0)
        self.assertIsNone(last)
    def test_under_repair_status_never_triggers(self):
        clock = FakeClock()
        detector = _detector(clock)
        last = _feed_motion(detector, clock, "Under Repair", magnitude_g=0.5, seconds=5.0)
        self.assertIsNone(last)
    def test_brief_bump_while_booked_does_not_trigger(self):
        clock = FakeClock()
        detector = _detector(clock)
        last = _feed_motion(detector, clock, "Booked", magnitude_g=0.6, seconds=0.4)
        self.assertIsNone(last)
    def test_sustained_motion_while_booked_triggers(self):
        clock = FakeClock()
        detector = _detector(clock)
        last = _feed_motion(detector, clock, "Booked", magnitude_g=0.5, seconds=2.0)
        self.assertIsNotNone(last)
        self.assertGreaterEqual(last["mean_magnitude_g"], 0.3)
        self.assertEqual(last["current_status"], "Booked")
    def test_sustained_motion_while_available_triggers(self):
        clock = FakeClock()
        detector = _detector(clock)
        last = _feed_motion(detector, clock, "Available", magnitude_g=0.5, seconds=2.0)
        self.assertIsNotNone(last)
        self.assertEqual(last["current_status"], "Available")
    def test_sustained_low_motion_below_threshold_does_not_trigger(self):
        clock = FakeClock()
        detector = _detector(clock)
        last = _feed_motion(detector, clock, "Booked", magnitude_g=0.1, seconds=3.0)
        self.assertIsNone(last)
    def test_cooldown_suppresses_duplicate_alert(self):
        clock = FakeClock()
        detector = _detector(clock)
        first = _feed_motion(detector, clock, "Booked", magnitude_g=0.5, seconds=2.0)
        self.assertIsNotNone(first)
        second = _feed_motion(detector, clock, "Booked", magnitude_g=0.5, seconds=2.0)
        self.assertIsNone(second)
    def test_cooldown_expires_and_allows_new_alert(self):
        clock = FakeClock()
        detector = _detector(clock)
        first = _feed_motion(detector, clock, "Booked", magnitude_g=0.5, seconds=2.0)
        self.assertIsNotNone(first)
        clock.advance(61.0)
        second = _feed_motion(detector, clock, "Booked", magnitude_g=0.5, seconds=2.0)
        self.assertIsNotNone(second)
    def test_status_transition_to_occupying_resets_window(self):
        clock = FakeClock()
        detector = _detector(clock)
        _feed_motion(detector, clock, "Booked", magnitude_g=0.5, seconds=1.0)
        self.assertIsNone(detector.submit_sample(accel(z=1.0), "Occupying"))
        last = _feed_motion(detector, clock, "Booked", magnitude_g=0.5, seconds=0.5)
        self.assertIsNone(last)
if __name__ == "__main__":
    unittest.main()
