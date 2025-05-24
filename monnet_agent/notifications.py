"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Notifications
"""
# Std
import ssl
import http.client
import json

# Local
from monnet_agent.meta import get_meta
from monnet_shared.app_context import AppContext
from monnet_agent import agent_config

def send_notification(ctx: AppContext, name: str, data: dict):
    """
    Send notification to the server.

    Args:
        ctx (AppContext): Context.
        name (str): Name of the notification.
        data (dict): Extra data to send.
    Returns:
        None.
    """
    config = ctx.get_config()
    logger = ctx.get_logger()

    try:
        token = config.get("token")
        idx = config.get("id")
        ignore_cert = config.get("ignore_cert")
        server_host = config.get("server_host")
        server_endpoint = config.get("server_endpoint")
        meta = get_meta(ctx)

        payload = {
            "id": idx,
            "cmd": "notification",
            "token": token,
            "version": agent_config.AGENT_VERSION,
            "name": name,
            "data": data or {},
            "meta": meta
        }
        logger.debug(f"Notification payload: {payload}")
        connection = None
        try:
            context = ssl._create_unverified_context() if ignore_cert else None
            connection = http.client.HTTPSConnection(server_host, context=context)
            headers = {"Content-Type": "application/json"}
            connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)
            response = connection.getresponse()

            if response.status == 200:
                # Successfully sent notification, need to handle response?
                pass
            elif response.status == 204:
                # Successfully sent notification, no content to return
                pass
            else:
                logger.err(f"Notification response error: {response.status} {response.reason}")

            logger.debug(f"Notification response: {response.status} {response.reason}")
        except Exception as e:
            logger.err(f"Error sending notification to {server_host}: {e}")
        finally:
            if connection:
                connection.close()

            logger.debug("Notification process completed")
    except Exception as e:
        logger.err(f"Unexpected error in send_notification: {e}")


