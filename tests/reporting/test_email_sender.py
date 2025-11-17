import os
import unittest
from unittest.mock import patch

from analyst_service.reporting.email_sender import send_html_email


class SendHtmlEmailTests(unittest.TestCase):
    @patch("analyst_service.reporting.email_sender.smtplib.SMTP")
    def test_email_sender_uses_smtp_configuration(self, mock_smtp):
        env = {
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user",
            "SMTP_PASSWORD": "password",
            "REPORT_FROM": "reports@example.com",
            "REPORT_TO": "investor@example.com,team@example.com",
        }
        with patch.dict(os.environ, env, clear=True):
            smtp_instance = mock_smtp.return_value.__enter__.return_value

            send_html_email("Subject", "<p>Body</p>")

            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            smtp_instance.starttls.assert_called_once()
            smtp_instance.login.assert_called_once_with("user", "password")
            smtp_instance.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
