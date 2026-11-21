import unittest

from shared.safety_topics import (
    build_crash_payload,
    build_safety_topic,
    build_security_topic,
    sign_payload,
    verify_payload,
)

SECRET = "unit-test-secret"

class SafetyTopicsTests(unittest.TestCase):
    def test_topics_include_project_prefix_and_scooter_id(self):
        self.assertEqual(build_safety_topic("S001"), "cosc2790-g8/scooter/S001/safety")
        self.assertEqual(build_security_topic("S001"), "cosc2790-g8/scooter/S001/security")
    def test_sign_and_verify_round_trip(self):
        payload = build_crash_payload("S001", g_force=3.2, orientation_delta_deg=78.4)
        signed = sign_payload(payload, SECRET)
        self.assertIn("signature", signed)
        self.assertTrue(verify_payload(signed, SECRET))
    def test_tampered_payload_fails_verification(self):
        payload = build_crash_payload("S001", g_force=3.2, orientation_delta_deg=78.4)
        signed = sign_payload(payload, SECRET)
        signed["g_force"] = 99.0
        self.assertFalse(verify_payload(signed, SECRET))
    def test_missing_signature_fails_verification(self):
        payload = build_crash_payload("S001", g_force=3.2, orientation_delta_deg=78.4)
        self.assertFalse(verify_payload(payload, SECRET))
    def test_wrong_secret_fails_verification(self):
        payload = build_crash_payload("S001", g_force=3.2, orientation_delta_deg=78.4)
        signed = sign_payload(payload, SECRET)
        self.assertFalse(verify_payload(signed, "different-secret"))
if __name__ == "__main__":
    unittest.main()
