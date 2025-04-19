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
from monnet_gateway.mgateway_config import CONFIG_DB_PATH
from shared.app_context import AppContext
from monnet_gateway.services.config import Config

class SendMailService:
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()

        # Load configuration using Config class
        if ctx.has_config():
            config = ctx.get_config()
            print("Config loaded from context:", config)
        else:
            config = Config(ctx, CONFIG_DB_PATH)
            ctx.set_config(config)

        self.smtp_server = config.get('mail_host', 'localhost')
        self.smtp_port = config.get('mail_port', 25)
        self.username = config.get('mail_username', '')
        self.password = config.get('mail_password', '')
        self.mail_auth_type = config.get('mail_auth_type', {'LOGIN': 1})
        self.smtp_security = config.get('smtp_security', {'STARTTLS': 1})
        self.mail_from = config.get('mail_from', 'no-reply@example.com')

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
            msg['From'] = sender or self.mail_from
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Determine the security method
            if self.smtp_security.get('SMTPS', 0) == 1:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    self._authenticate(server)
                    server.send_message(msg)
            elif self.smtp_security.get('STARTTLS', 0) == 1:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    self._authenticate(server)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    self._authenticate(server)
                    server.send_message(msg)

        except Exception as e:
            self.logger.err(f"Failed to send email: {e}")

    def _authenticate(self, server):
        """
        Authenticate with the SMTP server using the configured authentication type.

        :param server: The SMTP server connection.
        """
        if self.mail_auth_type.get('LOGIN', 0) == 1 or self.mail_auth_type.get('PLAIN', 0) == 1:
            # Use login for both LOGIN and PLAIN authentication
            server.login(self.username, self.password)
        else:
            raise ValueError("Unsupported authentication type. Only LOGIN and PLAIN are supported.")

    """
    def _dump_config(self):
        return {
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'username': self.username,
            'password': self.password,
            'mail_auth_type': self.mail_auth_type,
            'smtp_security': self.smtp_security,
            'mail_from': self.mail_from,
        }
    """
