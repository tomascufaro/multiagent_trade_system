"""Email sender for HTML portfolio reports."""
import os
import smtplib
from email.message import EmailMessage
from typing import List


def _get_required_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value


def _parse_recipients(to_value: str) -> List[str]:
    recipients = [address.strip() for address in to_value.split(",") if address.strip()]
    if not recipients:
        raise ValueError("No recipients provided in REPORT_TO")
    return recipients


def send_html_email(subject: str, html_body: str) -> None:
    """Send an HTML email using SMTP settings from environment variables."""
    server = _get_required_env("SMTP_SERVER")
    port = int(_get_required_env("SMTP_PORT"))
    from_address = _get_required_env("REPORT_FROM")
    to_value = _get_required_env("REPORT_TO")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    recipients = _parse_recipients(to_value)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = ", ".join(recipients)
    message.set_content("This email requires an HTML-capable client.")
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(server, port) as smtp:
        smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)
