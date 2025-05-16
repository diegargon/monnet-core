"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

Notifications
    send_notification
    send_request
    validate_response
    get_meta
"""
# Std
import ssl
import http.client
import json
import uuid

# Local
import info_linux
from monnet_shared.app_context import AppContext
import monnet_shared.time_utils as time_utils
from monnet_agent import agent_config

def get_meta(ctx: AppContext):
    """
    Build metadata.

    Args:
        ctx (AppContext): Context.
    Returns:
        dict: Dictionary with metadata.
    """

    timestamp = time_utils.date_now()
    local_timezone = time_utils.get_local_timezone()
    hostname = info_linux.get_hostname()
    nodename = info_linux.get_nodename()
    if hostname:
        ip_address = info_linux.get_ip_address(hostname)
    else:
        ip_address = None

    _uuid = str(uuid.uuid4())

    meta = {
        "timestamp": timestamp,                       # Timestamp  UTC
        "timezone": str(local_timezone),              # Timezone
        "hostname": hostname,
        "nodename": nodename,
        "ip_address": ip_address,
        "agent_version": str(agent_config.AGENT_VERSION),
        "uuid": _uuid                                 # ID uniq
    }
    # log(f"Metadata: {meta}", "debug")
    return meta

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

        data["name"] = name

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
                We don't want to keep that key due to interference with dict comparison current/last.
                TODO: Find a safe way.
                WARNING: Do not modify the data here if it will be compared later.
            """
            if "name" in data:
                data.pop("name")

            logger.debug("Notification process completed")
    except Exception as e:
        logger.err(f"Unexpected error in send_notification: {e}")

def send_request(ctx: AppContext, cmd="ping", data=None):
    """
    Send a request to the server.

    Args:
        ctx (AppContext): Context.
        cmd (str): Command.
        data (dict): Extra data.

    Returns:
        dict or None: Server response or None if an error occurs.
    """
    config = ctx.get_config()
    logger = ctx.get_logger()

    # Get base config
    try:
        token = config["token"]
        idx = config["id"]
        interval = config["interval"]
        ignore_cert = config["ignore_cert"]
        server_host = config["server_host"]
        server_endpoint = config["server_endpoint"]
    except KeyError as e:
        logger.err(f"Missing configuration key: {e}")
        return None

    meta = get_meta(ctx)
    payload = {
        "id": idx,
        "cmd": cmd,
        "token": token,
        "interval": interval,
        "version": agent_config.AGENT_VERSION,
        "name": cmd,
        "data": data or {},
        "meta": meta
    }

    connection = None
    try:
        logger.debug(f"Attempting to send request to {server_host} with endpoint {server_endpoint}")
        logger.debug(f"Payload: {payload}")

        # Accept all certs
        context = ssl._create_unverified_context() if ignore_cert else None

        connection = http.client.HTTPSConnection(server_host, context=context)
        headers = {"Content-Type": "application/json"}
        connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)

        # Response
        response = connection.getresponse()
        raw_data = response.read().decode()
        logger.debug(f"Response status: {response.status}, reason: {response.reason}")
        logger.debug(f"Raw response: {raw_data}")

        if response.status == 200:
            if raw_data:
                try:
                    return json.loads(raw_data)
                except json.JSONDecodeError as e:
                    logger.err(f"Error decoding JSON response: {e} Raw data: {raw_data}")
        else:
            logger.err(f"HTTP Error: {response.status} {response.reason}, Raw data: {raw_data}")

    except http.client.HTTPException as e:
        logger.err(f"HTTP exception occurred: {e}")
    except Exception as e:
        logger.err(f"Unexpected error on request: {e}")
    finally:
        if connection:
            try:
                connection.close()
            except Exception as e:
                logger.err(f"Error closing connection: {e}")

    return None

def validate_response(ctx: AppContext, response, token):
    """
    Basic response validation.

    Args:
        ctx (AppContext): Context.
        response (dict): Response from the server.
        token (str): Token.
    Returns:
        None.
    """
    logger = ctx.get_logger()

    if response and response.get("cmd") == "pong" and response.get("token") == token:
        return response
    logger.warning("Invalid response from server or wrong token.")

    return None
