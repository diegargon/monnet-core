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
        token = config["token"]
        idx = config["id"]
        ignore_cert = config["ignore_cert"]
        server_host = config["server_host"]
        server_endpoint = config["server_endpoint"]
        meta = get_meta(ctx)

        # TODO DEL data["name"] = name

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
            """
            TODO: Test Check if the response is JSON and contains the expected keys.
            if response.status == 200:
                if raw_data:
                    try:
                        parsed_data = json.loads(raw_data)
                        if "expected_key" not in parsed_data:
                            logger.err("Missing 'expected_key' in response data.")
                            return None
                        return parsed_data
                    except json.JSONDecodeError as e:
                        logger.err(f"Error decoding JSON response: {e} Raw data: {raw_data}")
                        return None
            else:
                logger.err(f"HTTP Error: {response.status} {response.reason},
            """
            logger.debug(f"Notification response: {response.status} {response.reason}")
        except Exception as e:
            logger.err(f"Error sending notification to {server_host}: {e}")
        finally:
            if connection:
                connection.close()
            """
                TODO: DEL THIS ALREADY REMOVE AND TESTING
                We don't want to keep that key due to interference with dict comparison current/last.
                TODO: Find a safe way.
                WARNING: Do not modify the data here if it will be compared later.
            """
            #if "name" in data:
            #    data.pop("name")

            logger.debug("Notification process completed")
    except Exception as e:
        logger.err(f"Unexpected error in send_notification: {e}")


