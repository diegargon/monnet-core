"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Send Mail Service

This code is just a basic/preliminary draft.

"""

# Std
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

# Local
from shared.app_context import AppContext

class SendMailService:
    def __init__(self, ctx: AppContext, smtp_server: str, smtp_port: int, username: str, password: str, use_ssl: bool = False):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.logger = ctx.get_logger()

    def send_email(self, sender: str, recipient: str, subject: str, body: str):
        """
        Sends an email using the configured SMTP server.

        :param sender: Email address of the sender.
        :param recipient: Email address of the recipient.
        :param subject: Subject of the email.
        :param body: Body of the email.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            if self.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()  # Upgrade the connection to secure
                    server.login(self.username, self.password)
                    server.send_message(msg)

        except Exception as e:
            self.logger.err(f"Failed to send email: {e}")