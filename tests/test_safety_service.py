import unittest

from master.services.safety_service import SafetyService

class FakeEmailService:
    def __init__(self):
        self.calls = []
    def send_email(self, recipients, subject, body):
        record = {
            "recipients": list(recipients),
            "subject": subject,
            "body": body,
        }
        self.calls.append(record)
        return {"sent": True, "mock_mode": True, "recipients": list(recipients)}
class FakeRepo:
    def __init__(self, items=None):
        self.items = items or {}
    def find_by_id(self, key):
        return self.items.get(key)
class FakeScooterRepo(FakeRepo):
    def __init__(self, items=None):
        super().__init__(items)
        self.status_updates = []
    def update_status(self, key, status):
        item = self.items.get(key)
        if item is None:
            return None
        updated = dict(item, status=status)
        self.items[key] = updated
        self.status_updates.append((key, status))
        return updated
class FakeBookingRepo:
    def __init__(self, by_scooter=None):
        self.by_scooter = by_scooter or {}

    def find_active_for_scooter(self, scooter_id):
        return self.by_scooter.get(scooter_id)
SCOOTER = {
    "id": "S001",
    "make": "Xiaomi",
    "colour": "Black",
    "location": "RMIT Building 80",
    "latitude": -37.808,
    "longitude": 144.964,
}
RIDER = {
    "id": 7,
    "first_name": "Alice",
    "last_name": "Nguyen",
    "email": "alice@example.com",
    "phone": "0400000000",
    "emergency_contact_name": "Bob Nguyen",
    "emergency_contact_email": "bob.nguyen@example.com",
}
ACTIVE_BOOKING = {
    "id": 42,
    "user_id": 7,
    "scooter_id": "S001",
    "unlock_time": "2026-05-19T10:00:00",
}

def _crash_payload(**overrides):
    payload = {
        "event": "crash_detected",
        "scooter_id": "S001",
        "timestamp": "2026-05-19T10:05:30Z",
        "g_force": 3.4,
        "orientation_delta_deg": 71.0,
        "location": {"lat": -37.808, "lng": 144.964},
    }
    payload.update(overrides)
    return payload


def _theft_payload(**overrides):
    payload = {
        "event": "theft_suspected",
        "scooter_id": "S001",
        "timestamp": "2026-05-19T12:00:00Z",
        "motion_magnitude": 0.42,
        "window_seconds": 1.8,
        "current_status": "Booked",
        "location": {"lat": -37.808, "lng": 144.964},
    }
    payload.update(overrides)
    return payload
def _build_service(email=None, scooter=SCOOTER, booking=ACTIVE_BOOKING, rider=RIDER):
    email_service = email or FakeEmailService()
    scooter_repo = FakeScooterRepo({SCOOTER["id"]: scooter} if scooter else {})
    service = SafetyService(
        email_service=email_service,
        scooter_repository=scooter_repo,
        booking_repository=FakeBookingRepo({"S001": booking} if booking else {}),
        user_repository=FakeRepo({RIDER["id"]: rider} if rider else {}),
    )
    service._test_scooter_repo = scooter_repo
    return service

class SafetyServiceTests(unittest.TestCase):
    def test_missing_scooter_id_returns_400(self):
        service = _build_service()
        response, status = service.handle_crash_event({"event": "crash_detected"})
        self.assertEqual(status, 400)
        self.assertFalse(response["success"])
    def test_non_crash_event_rejected(self):
        service = _build_service()
        response, status = service.handle_crash_event(
            {"event": "other", "scooter_id": "S001"}
        )
        self.assertEqual(status, 400)
    def test_crash_event_sends_email_to_admin_and_emergency_contact(self):
        email = FakeEmailService()
        service = _build_service(email=email)
        response, status = service.handle_crash_event(_crash_payload())
        self.assertEqual(status, 200)
        self.assertTrue(response["success"])
        self.assertEqual(len(email.calls), 1)
        call = email.calls[0]
        self.assertIn("s3938309@rmit.edu.vn", call["recipients"])
        self.assertIn("bob.nguyen@example.com", call["recipients"])
        self.assertNotIn("alice@example.com", call["recipients"])
        self.assertIn("Crash Detected", call["subject"])
        self.assertIn("S001", call["subject"])
        self.assertIn("Alice Nguyen", call["body"])
        self.assertIn("Bob Nguyen", call["body"])
        self.assertIn("3.4", call["body"])
        self.assertIn("71.0", call["body"])
        self.assertIn("google.com/maps", call["body"])
    def test_crash_event_with_rider_but_no_emergency_contact_only_emails_admin(self):
        email = FakeEmailService()
        rider = dict(RIDER, emergency_contact_name=None, emergency_contact_email=None)
        service = _build_service(email=email, rider=rider)
        service.handle_crash_event(_crash_payload())
        recipients = email.calls[0]["recipients"]
        self.assertEqual(recipients, ["s3938309@rmit.edu.vn"])
        self.assertIn("Emergency contact: not set", email.calls[0]["body"])
    def test_crash_event_with_no_active_booking_still_emails_admin(self):
        email = FakeEmailService()
        service = _build_service(email=email, booking=None, rider=None)
        response, status = service.handle_crash_event(_crash_payload())
        self.assertEqual(status, 200)
        self.assertIn("s3938309@rmit.edu.vn", email.calls[0]["recipients"])
        self.assertNotIn("bob.nguyen@example.com", email.calls[0]["recipients"])
        self.assertIn("no active booking", email.calls[0]["body"])
    def test_crash_event_does_not_write_to_scooter_status(self):
        service = _build_service()
        response, _ = service.handle_crash_event(_crash_payload())
        self.assertEqual(response["data"]["incident_type"], "crash")
        self.assertEqual(service._test_scooter_repo.status_updates, [])
    def test_admin_email_only_listed_once_when_emergency_contact_matches(self):
        email = FakeEmailService()
        rider = dict(RIDER, emergency_contact_email="s3938309@rmit.edu.vn")
        service = _build_service(email=email, rider=rider)
        service.handle_crash_event(_crash_payload())
        recipients = email.calls[0]["recipients"]
        self.assertEqual(recipients.count("s3938309@rmit.edu.vn"), 1)
    def test_theft_event_missing_scooter_id_returns_400(self):
        service = _build_service()
        response, status = service.handle_theft_event({"event": "theft_suspected"})
        self.assertEqual(status, 400)
        self.assertFalse(response["success"])
    def test_theft_event_wrong_event_type_rejected(self):
        service = _build_service()
        response, status = service.handle_theft_event(
            {"event": "crash_detected", "scooter_id": "S001"}
        )
        self.assertEqual(status, 400)
    def test_theft_event_with_booker_sends_email_with_booker_details(self):
        email = FakeEmailService()
        service = _build_service(email=email)
        response, status = service.handle_theft_event(_theft_payload())
        self.assertEqual(status, 200)
        self.assertTrue(response["success"])
        call = email.calls[0]
        self.assertIn("s3938309@rmit.edu.vn", call["recipients"])
        self.assertIn("alice@example.com", call["recipients"])
        self.assertIn("Suspected Theft", call["subject"])
        self.assertIn("S001", call["subject"])
        self.assertIn("Alice Nguyen", call["body"])
        self.assertIn("Booked", call["body"])
        self.assertIn("0.42", call["body"])
        self.assertIn("google.com/maps", call["body"])
    def test_theft_event_with_no_booking_emails_admin_only(self):
        email = FakeEmailService()
        service = _build_service(email=email, booking=None, rider=None)
        response, status = service.handle_theft_event(
            _theft_payload(current_status="Available")
        )
        self.assertEqual(status, 200)
        recipients = email.calls[0]["recipients"]
        self.assertIn("s3938309@rmit.edu.vn", recipients)
        self.assertNotIn("alice@example.com", recipients)
        self.assertIn("Booker: none", email.calls[0]["body"])
    def test_theft_event_does_not_write_to_scooter_status(self):
        service = _build_service()
        response, _ = service.handle_theft_event(_theft_payload())
        self.assertEqual(response["data"]["incident_type"], "theft")
        self.assertEqual(service._test_scooter_repo.status_updates, [])
if __name__ == "__main__":
    unittest.main()
