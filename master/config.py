"""Configuration values for the Master Pi."""

import os


def _clean_env_value(value):
    return str(value or "").strip().strip('"').strip("'")


def _clean_ascii_env_value(value):
    return _clean_env_value(value).encode("ascii", "ignore").decode("ascii").strip()


def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = _clean_env_value(value)

            if key.startswith("SMTP_"):
                os.environ[key] = _clean_ascii_env_value(value)
            else:
                os.environ.setdefault(key, value)


_load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-for-demo")
    TOKEN_MAX_AGE_SECONDS = int(os.getenv("TOKEN_MAX_AGE_SECONDS", "7200"))

    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    SOCKET_HOST = os.getenv("SOCKET_HOST", "0.0.0.0")
    SOCKET_PORT = int(os.getenv("SOCKET_PORT", "9000"))

    MQTT_HOST = os.getenv("MQTT_HOST", "test.mosquitto.org")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
    MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "cosc2790-g8-master")

    SAFETY_ALERT_EMAIL = os.getenv("SAFETY_ALERT_EMAIL", "s3938309@rmit.edu.vn")
    SAFETY_REPORTER_USER_ID = int(os.getenv("SAFETY_REPORTER_USER_ID", "1"))

    DB_HOST = os.getenv("DB_HOST", "")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    GOOGLE_CALENDAR_CREDENTIALS_FILE = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE", "")
    GOOGLE_CALENDAR_TIMEZONE = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "Asia/Ho_Chi_Minh")
    GOOGLE_CALENDAR_MOCK_MODE = os.getenv("GOOGLE_CALENDAR_MOCK_MODE", "true").lower() == "true"

    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

    SMTP_HOST = _clean_ascii_env_value(os.getenv("SMTP_HOST", ""))
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

    SMTP_USERNAME = _clean_ascii_env_value(
        os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER", "")
    )

    SMTP_PASSWORD = _clean_ascii_env_value(os.getenv("SMTP_PASSWORD", ""))

    SMTP_FROM_EMAIL = _clean_ascii_env_value(
        os.getenv("SMTP_FROM_EMAIL")
        or os.getenv("SMTP_FROM")
        or SMTP_USERNAME
    )

    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_MOCK_MODE = os.getenv("SMTP_MOCK_MODE", "true").lower() == "true"

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_CURRENCY = os.getenv("STRIPE_CURRENCY", "aud").lower()
    STRIPE_MOCK_MODE = os.getenv("STRIPE_MOCK_MODE", "true").lower() == "true"

    FRONTEND_BASE_URL = os.getenv(
        "FRONTEND_BASE_URL",
        "http://127.0.0.1:5500/frontend/agent",
    )