"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Requests
"""

import http
import json
import ssl
from monnet_agent import agent_config
from monnet_agent.meta import get_meta
from monnet_shared.app_context import AppContext


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
        token = config.get("token")
        idx = config.get("id")
        interval = config.get("interval")
        ignore_cert = config.get("ignore_cert")
        server_host = config.get("server_host")
        server_endpoint = config.get("server_endpoint")
    except KeyError as e:
        logger.err(f"Missing configuration key: {e}")
        return None

    meta = get_meta(ctx)
    # TODO: Remove version: is in meta
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
