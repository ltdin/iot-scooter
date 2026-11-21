"""SMTP email notifications for engineer repair tasks."""

import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from master.config import Config


class EmailService:
    def _ascii_clean(self, value):
        return str(value or "").strip().encode("ascii", "ignore").decode("ascii").strip()

    def _is_mock_mode(self):
        return Config.SMTP_MOCK_MODE or not Config.SMTP_HOST

    def _sender(self):
        if Config.SMTP_FROM_EMAIL and Config.SMTP_FROM_EMAIL != "yourgmail@gmail.com":
            return self._ascii_clean(Config.SMTP_FROM_EMAIL)
        return self._ascii_clean(Config.SMTP_USERNAME) or "no-reply@scooter-share.local"

    def send_email(self, recipients, subject, body):
        recipients = [self._ascii_clean(email) for email in recipients if self._ascii_clean(email)]
        if not recipients:
            return {
                "sent": False,
                "mock_mode": self._is_mock_mode(),
                "message": "No recipients",
                "recipients": [],
            }

        if self._is_mock_mode():
            return {
                "sent": True,
                "mock_mode": True,
                "provider": "smtp_mock",
                "recipients": recipients,
                "subject": subject,
                "body_preview": body[:300],
            }

        message = EmailMessage()
        message["From"] = formataddr(("Scooter Share", self._sender()))
        message["To"] = ", ".join(recipients)
        message["Subject"] = str(subject)
        message.set_content(str(body), charset="utf-8")

        try:
            smtp_host = self._ascii_clean(Config.SMTP_HOST)
            smtp_username = self._ascii_clean(Config.SMTP_USERNAME)
            smtp_password = self._ascii_clean(Config.SMTP_PASSWORD).replace(" ", "")
            with smtplib.SMTP(
                smtp_host,
                Config.SMTP_PORT,
                local_hostname="localhost",
                timeout=15,
            ) as smtp:
                if Config.SMTP_USE_TLS:
                    smtp.starttls()
                if smtp_username and smtp_password:
                    smtp.login(smtp_username, smtp_password)
                smtp.send_message(message)
        except (smtplib.SMTPException, OSError, UnicodeError) as error:
            return {
                "sent": False,
                "mock_mode": False,
                "provider": "smtp",
                "recipients": recipients,
                "subject": subject,
                "message": str(error),
            }

        return {
            "sent": True,
            "mock_mode": False,
            "provider": "smtp",
            "recipients": recipients,
            "subject": subject,
        }
