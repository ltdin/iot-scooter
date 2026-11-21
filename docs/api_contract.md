# Master Pi REST API Contract

Base URL:

```text
http://127.0.0.1:5000
```

Protected endpoints use the access token returned by login:

```text
Authorization: Bearer <access_token>
```

`X-User-Id` and `X-Role` are not accepted for protected APIs. The server
identifies the caller from the verified access token.

The access token is a signed, time-limited bearer token. It may look different
between users because the serializer can compress some payloads. Always copy the
entire token string and send it as one header value.

## Login

Customer login from Agent Pi:

```http
POST /api/login
```

```json
{
  "username": "alice",
  "password": "Alice123!",
  "source": "AP"
}
```

Admin login from Master Pi:

```json
{
  "username": "admin",
  "password": "Admin123!",
  "source": "MP"
}
```

Successful response:

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "<signed-token>",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 3,
      "username": "alice",
      "role": "customer",
      "source": "AP"
    }
  }
}
```

## Public/Auth

```text
GET  /health
POST /api/register
POST /api/login
POST /api/logout
GET  /api/scooters/available
GET  /api/scooters/<scooter_id>
POST /api/scooters/<scooter_id>/credential-unlock
```

Logout:

```http
POST /api/logout
Authorization: Bearer <access_token>
```

The backend revokes the current token. After logout, using the same token on a
protected API returns `401 Access token has been revoked`. The current
implementation stores revoked tokens in memory, which is enough for local demos;
if the backend process restarts, users should log in again to get a fresh token.

## Admin Token

```text
Authorization: Bearer <admin_access_token>
```

```text
GET    /api/scooters
GET    /api/admin/scooters
POST   /api/scooters
PUT    /api/scooters/<scooter_id>
DELETE /api/scooters/<scooter_id>
PUT    /api/scooters/<scooter_id>/status
GET    /api/admin/customers
GET    /api/admin/usage-history
GET    /api/admin/usage-report?group_by=day
GET    /api/admin/usage-report?group_by=week
GET    /api/reports
PUT    /api/reports/<report_id>/status
GET    /api/maps/config
GET    /api/maps/available-scooters
GET    /api/maps/reported-scooters
```

Admin usage visualization report:

```http
GET /api/admin/usage-report?group_by=day
GET /api/admin/usage-report?group_by=week
```

Response is chart-ready:

```json
{
  "group_by": "day",
  "summary": {
    "period_count": 2,
    "trip_count": 5,
    "total_duration_minutes": 42,
    "total_cost": 21.0,
    "charged_amount": 21.0,
    "unpaid_amount": 0.0
  },
  "series": [
    {
      "period": "2026-05-17",
      "trip_count": 3,
      "customer_count": 2,
      "scooter_count": 2,
      "total_duration_minutes": 25,
      "total_cost": "12.50",
      "charged_amount": "12.50",
      "unpaid_amount": "0.00"
    }
  ]
}
```

## Customer Token

```text
Authorization: Bearer <customer_access_token>
```

```text
POST /api/bookings
POST /api/bookings/<booking_id>/cancel
POST /api/scooters/<scooter_id>/unlock
POST /api/bookings/qr-unlock
POST /api/scooters/<scooter_id>/lock
POST /api/reports
GET  /api/maps/config
GET  /api/maps/available-scooters
POST /api/payments/top-up
POST /api/payments/top-up/mock-confirm
```

Book scooter:

```json
{
  "scooter_id": "S001"
}
```

Successful booking creates a Google Calendar event for the default 10 minute
booking duration and stores `calendar_event_id` on the booking row.

Booking response includes:

```json
{
  "unlock_code": "BK-7K2F9A8M1Q",
  "unlock_methods": ["credentials", "qr"],
  "qr_payload": {
    "type": "customer_unlock",
    "booking_id": 17,
    "scooter_id": "S001",
    "unlock_code": "BK-7K2F9A8M1Q"
  },
  "calendar_event_id": "event_id_or_mock_id",
  "calendar": {
    "event_id": "event_id_or_mock_id",
    "event_link": "https://calendar.google.com/...",
    "provider": "google_calendar",
    "mock_mode": false,
    "summary": "Scooter booking - S001",
    "start_time": "2026-05-16T12:54:39Z",
    "end_time": "2026-05-16T13:04:39Z"
  }
}
```

Cancel booking deletes the matching Google Calendar event and changes the
booking status to `Canceled` instead of deleting the row.

Customer unlock rules:

```text
scooter must be Booked
active booking must belong to the token user
customer balance must cover the default 10 minute booking duration
sets booking.unlock_time
calculates max_usage_minutes from balance / cost_per_minute
sets booking.auto_lock_at
updates scooter status to Occupying
```

Credential unlock:

```http
POST /api/scooters/<scooter_id>/credential-unlock
```

```json
{
  "username": "alice",
  "password": "Alice123!"
}
```

This matches the AP console flow where the customer types credentials at the
scooter. The backend verifies the credentials, then checks the active booking
belongs to that customer.

Token unlock is also supported for already logged-in AP/web clients:

```http
POST /api/scooters/<scooter_id>/unlock
Authorization: Bearer <customer_access_token>
```

QR unlock:

```http
POST /api/bookings/qr-unlock
Authorization: Bearer <customer_access_token>
```

```json
{
  "unlock_code": "BK-7K2F9A8M1Q"
}
```

The QR code should contain the booking `qr_payload` returned by the booking API.
The backend still verifies the customer token, so only the booking owner can
unlock the scooter even if another customer scans the same QR code.

Customer lock rules:

```text
scooter must be Occupying
active booking must belong to the token user
sets booking.lock_time
updates booking status to Completed
updates scooter status to Available
calculates duration from unlock_time to lock_time
if requested lock time is after auto_lock_at, billing uses auto_lock_at as the effective lock time
deducts up to the customer's remaining balance
does not allow negative balance
creates a usage_history row
```

Create report:

```json
{
  "scooter_id": "S001",
  "issue_description": "Brake issue"
}
```

Creating a report marks the scooter as `To Be Repaired` and sends an email
notification to all engineers. The email includes the scooter details and Google
Maps links.

Local email mock mode:

```env
SMTP_MOCK_MODE=true
```

Real SMTP mode:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=true
SMTP_MOCK_MODE=false
```

Report response includes:

```json
{
  "report": {
    "id": 1,
    "scooter_id": "S001",
    "google_maps_url": "https://www.google.com/maps/search/?api=1&query=-37.8081,144.9632"
  },
  "email": {
    "sent": true,
    "mock_mode": true,
    "recipients": ["engineer@example.com"]
  },
  "scooter_status": "To Be Repaired"
}
```

Top up with Stripe test mode:

```json
{
  "amount": 20.00,
  "currency": "aud"
}
```

The response includes `payment_intent_id` and `client_secret`. If
`STRIPE_MOCK_MODE=true`, call the mock confirmation endpoint with:

```json
{
  "payment_intent_id": "pi_mock_xxx"
}
```

## Engineer Token

```text
Authorization: Bearer <engineer_access_token>
```

```text
GET  /api/reports
PUT  /api/reports/<report_id>/status
POST /api/scooters/<scooter_id>/unlock
POST /api/scooters/<scooter_id>/lock
POST /api/engineer/repair-results
GET  /api/maps/config
GET  /api/maps/reported-scooters
```

Engineer unlock/lock rules:

```text
engineer can unlock scooters marked To Be Repaired or Under Repair
unlock updates scooter status to Under Repair
engineer is not charged
lock keeps scooter Under Repair until repair result is submitted
repair result resolves the report and updates scooter status to Available
```

Repair result:

```json
{
  "scooter_id": "S001",
  "report_id": 1,
  "result": "Brake fixed"
}
```

Successful repair result response includes:

```json
{
  "repair_log": {
    "id": 1,
    "engineer_id": 2,
    "scooter_id": "S001",
    "report_id": 1,
    "result": "Brake fixed"
  },
  "report_status": "Resolved",
  "scooter_status": "Available"
}
```

## Socket Request Format

Agent Pi sends request/response messages to the Master Pi socket server.

Public login message:

```json
{
  "action": "login",
  "agent_id": "agent-pi-1",
  "payload": {
    "username": "alice",
    "password": "Alice123!",
    "source": "AP"
  }
}
```

Protected action message:

```json
{
  "action": "book",
  "agent_id": "agent-pi-1",
  "scooter_id": "S001",
  "token": "<access_token>",
  "payload": {
    "scooter_id": "S001"
  }
}
```

Supported socket actions:

```text
login
register
credential_unlock
book
cancel_booking
unlock
qr_unlock
lock
report_issue
repair_result
top_up
confirm_mock_top_up
logout
```

## Google Maps

The backend stores scooter location as `location`, `latitude`, and `longitude`.
Scooter and report responses include `google_maps_url` so the AP/MP web pages can
open the marker in Google Maps.

```http
GET /api/maps/config
GET /api/maps/available-scooters
GET /api/maps/reported-scooters
```

## Google Calendar

The backend creates a Google Calendar event when a customer books a scooter and
deletes that event when the booking is canceled.

Environment:

```env
GOOGLE_CALENDAR_ID=primary
GOOGLE_CALENDAR_CREDENTIALS_FILE=secrets/google-calendar-service-account.json
GOOGLE_CALENDAR_TIMEZONE=Asia/Ho_Chi_Minh
GOOGLE_CALENDAR_MOCK_MODE=false
```

For local demos without Google credentials, keep:

```env
GOOGLE_CALENDAR_MOCK_MODE=true
```

Mock mode still stores a `mock_calendar_xxx` `calendar_event_id` so the booking
and cancel flow can be tested end to end without calling Google.

## Stripe Test Mode

Environment:

```env
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_CURRENCY=aud
STRIPE_MOCK_MODE=false
```

Customer top-up:

```http
POST /api/payments/top-up
```

A real AP/web UI confirms the returned `client_secret` with Stripe.js in test
mode. Stripe then calls:

```http
POST /api/payments/stripe/webhook
```

For local demos without a public webhook, keep `STRIPE_MOCK_MODE=true` and call:

```http
POST /api/payments/top-up/mock-confirm
```
