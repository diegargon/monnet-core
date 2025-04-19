"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Test DB Config
"""

from monnet_gateway.tests_cli.common_cli import init_context
from monnet_gateway.services.send_mail import SendMailService

ctx = init_context("/opt/monnet-core")
ctx.get_logger().log("Starting test_mail CLI", "info")

# Initialize the SendMailService
send_mail_service = SendMailService(ctx)

# Send a test email
try:
    send_mail_service.send_email(
        sender=None,  # Use default sender from configuration
        recipient="diego@envigo.net",
        subject="Test Email",
        body="This is a test email from Monnet Gateway."
    )
    ctx.get_logger().log("Test email sent successfully.", "info")
except Exception as e:
    ctx.get_logger().err(f"Failed to send test email: {e}")
