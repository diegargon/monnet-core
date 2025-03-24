import ssl
import http.client
import json
import time_utils
import info_linux
import uuid
# Local
from shared.logger import log
from monnet_agent import agent_globals

def get_meta():
    """
    Builds metadata
    Returns:
        dict: Dict with metadata
    """

    timestamp = time_utils.get_datetime()
    local_timezone = time_utils.get_local_timezone()
    hostname = info_linux.get_hostname()
    nodename = info_linux.get_nodename()
    if (hostname):
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
        "agent_version": str(agent_globals.AGENT_VERSION),
        "uuid": _uuid                                 # ID uniq
    }
    log(f"Metadata: {meta}", "debug")
    return meta

def send_notification(config: dict, name: str, data: dict):
    """
        Send notification to server.

        Return:
        None
    """
    try:
        token = config["token"]
        idx = config["id"]
        ignore_cert = config["ignore_cert"]
        server_host = config["server_host"]
        server_endpoint = config["server_endpoint"]
        meta = get_meta()
        if name == 'starting':
            data["msg"] = data["msg"].strftime("%H:%M:%S")
        data["name"] = name

        payload = {
            "id": idx,
            "cmd": "notification",
            "token": token,
            "version": agent_globals.AGENT_VERSION,
            "name": name,
            "data":  data or {},
            "meta": meta
        }
        log(f"Notification payload: {payload}", "debug")
        connection = None
        try:
            if ignore_cert:
                context = ssl._create_unverified_context()
            else:
                context = None
            connection = http.client.HTTPSConnection(server_host, context=context)
            headers = {"Content-Type": "application/json"}
            connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)
            log(f"Notification sent: {payload}", "debug")
        except Exception as e:
            log(f"Error sending notification: {e}", "err")
        finally:
            if connection:
                connection.close()
            """
                We dont want keep that key due interference with dict comparison current/last
                TODO: find a safe way
                WARNING: No modify the data here of something that going to have a comparison
            """
            if "name" in data:
                data.pop("name")

            log("Notification process completed", "debug")
    except Exception as e:
        log(f"Unexpected error in send_notification: {e}", "err")

def send_request(config, cmd="ping", data=None):
    """
    Send request to server.

    Args:
        config (dict): Configuration dictionary
        cmd (str): Command
        data (dict): Extra data

    Returns:
        dict or None: Server response or None if error
    """

    # Get base config
    token = config["token"]
    idx = config["id"]
    interval = config["interval"]
    ignore_cert = config["ignore_cert"]
    server_host = config["server_host"]
    server_endpoint = config["server_endpoint"]
    meta = get_meta()
    payload = {
        "id": idx,
        "cmd": cmd,
        "token": token,
        "interval": interval,
        "version": agent_globals.AGENT_VERSION,
        "name": cmd,
        "data": data or {},
        "meta": meta
    }

    connection = None
    try:
        # Accept all certs
        if ignore_cert:
            context = ssl._create_unverified_context()
        else:
            context = None

        connection = http.client.HTTPSConnection(server_host, context=context)
        headers = {"Content-Type": "application/json"}
        log(f"Payload: {payload}", "debug")
        connection.request("POST", server_endpoint, body=json.dumps(payload), headers=headers)
        # Response
        response = connection.getresponse()
        raw_data = response.read().decode()
        log(f"Raw response: {raw_data}", "debug")

        if response.status == 200:
            if raw_data:
                return json.loads(raw_data)
            log("Empty response from server", "err")
        else:
            log(f"Error HTTP: {response.status} {response.reason}, Respuesta: {raw_data}", "err")

    except Exception as e:
        log(f"Error on request: {e}", "err")
    finally:
        if connection:
            connection.close()

    return None

def validate_response(response, token):
    """
    Basic response validation

    Returns:
    None
    """
    if response and response.get("cmd") == "pong" and response.get("token") == token:
        return response
    log("Invalid response from server or wrong token.", "warning")
    return None
