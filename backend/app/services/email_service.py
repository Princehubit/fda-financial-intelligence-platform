
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_notification_email(
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    """
    Send a notification email using configured SMTP settings.

    Returns False when SMTP is not configured or delivery fails.
    """

    settings = get_settings()

    required_settings = (
        settings.smtp_host,
        settings.smtp_from_email,
    )

    if not all(required_settings):
        logger.info("SMTP is not configured. Email was not sent.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=15,
        ) as server:

            server.ehlo()

            if settings.smtp_use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()

            if settings.smtp_username and settings.smtp_password:
                server.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )

            server.send_message(message)

        logger.info("Notification email sent successfully.")
        return True

    except (smtplib.SMTPException, OSError, ssl.SSLError):
        logger.exception("Notification email delivery failed.")
        return False
