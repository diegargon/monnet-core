"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

"""

# Standard
import ssl
import sys
import time
import json
import signal
import uuid
import http.client
from datetime import datetime
from pathlib import Path

# Third Party
import psutil
import daemon

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
import globals
import info_linux
import time_utils
import tasks
from datastore import Datastore
from event_processor import EventProcessor
from agent_config import load_config
from constants import LogLevel, EventType
from shared.logger import log, logpo


# Config file
CONFIG_FILE_PATH = "/etc/monnet/agent-config"

# Global Var

running = True
config = None

def get_meta():
    """
    Builds metadata
    Returns:
        dict: Dict with metadata
    """

    timestamp = time_utils.get_datatime()
    local_timezone = time_utils.get_local_timezone()
    hostname = info_linux.get_hostname()
    nodename = info_linux.get_nodename()
    ip_address = info_linux.get_ip_address(hostname)
    _uuid = str(uuid.uuid4())

    return {
        "timestamp": timestamp,                 # Timestamp  UTC
        "timezone": str(local_timezone),        # Timezone
        "hostname": hostname,
        "nodename": nodename,
        "ip_address": ip_address,
        "agent_version": str(globals.AGENT_VERSION),
        "uuid": _uuid                           # ID uniq
    }

def send_notification(name: str, data: dict):
    """
        Send notification to server.

        Return:
        None
    """
    global config

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
        "version": globals.AGENT_VERSION,
        "data":  data or {},
        "meta": meta
    }

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
        """
            We dont want keep that key due interference with dict comparation current/last
            TODO: find a safe way
            WARNING: No modify the data here of something that going to have a comporation
        """
        if "name" in data:
            data.pop("name")
        connection.close()

def send_request(cmd="ping", data=None):
    """
    Send request to server.

    Args:
        cmd (str): Command
        data (dict): Extra data

    Returns:
        dict or None: Server response o None if error
    """
    global config

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
        "version": globals.AGENT_VERSION,
        "data": data or {},
        "meta": meta
    }

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
        # Close
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

def handle_signal(signum, frame):
    """
    Signal Handler

    Returns:
    None
    """
    global running
    global config

    signal_name = None
    msg = None

    for name, timer in globals.timers.items():
        log(f"Cancelando timer: {name}")
        timer.cancel()
    globals.timers.clear()

    if signum == signal.SIGTERM:
        signal_name = 'SIGTERM'
    elif signum == signal.SIGHUP:
        signal_name = 'SIGHUP'
    else:
        signal_name = signum

    if info_linux.is_system_shutting_down():
        notification_type = "system_shutdown"
        msg = "System shutdown or reboot"
        log_level = LogLevel.ALERT
        event_type = EventType.SYSTEM_SHUTDOWN
    else:
        notification_type = "app_shutdown"
        msg = f"Signal receive: {signal_name}. Closing application."
        log_level = LogLevel.ALERT
        event_type = EventType.APP_SHUTDOWN

    log(f"Receive Signal {signal_name}  Stopping app...", "notice")

    data = {"msg": msg, "log_level": log_level, "event_type": event_type}
    send_notification(notification_type, data)
    running = False
    sys.exit(0)

def validate_config():
    """
    Validates that all required keys exist in the config and are not empty.

    :param config: dict containing configuration values.
    :param required_keys: list of keys to validate.
    :return: Tue or Raises ValueError if validation fails.
    """
    global config

    required_keys = [
        "token",
        "id",
        "default_interval",
        "ignore_cert",
        "server_host",
        "server_endpoint"
    ]

    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")
    log("Configuration is valid", "debug")

    return True

def run():
    global running
    global config

    datastore = Datastore()
    event_processor = EventProcessor()

    # Used for iowait
    last_cpu_times = psutil.cpu_times()

    log("Init monnet linux agent", "info")
    # Cargar la configuracion desde el archivo
    config = load_config(CONFIG_FILE_PATH)
    if not config:
        log("Cant load config. Finishing", "err")
        return

    try:
        validate_config()
    except ValueError as e:
        log(str(e), "err")
        return

    token = config["token"]
    config["interval"] = config["default_interval"]

    # Signal Handle
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    starting_data = {
        'msg': datetime.now().time(),
        'ncpu': info_linux.get_cpus(),
        'uptime': info_linux.get_uptime(),
        'log_level': LogLevel.NOTICE,
        'event_type': EventType.STARTING
    }
    send_notification('starting', starting_data)

    # Timer functions
    tasks.check_listen_ports(datastore, send_notification, startup=1)
    tasks.send_stats(datastore, send_notification)

    while running:
        extra_data = {}
        current_load_avg = info_linux.get_load_avg()
        current_memory_info = info_linux.get_memory_info()
        current_disk_info = info_linux.get_disks_info()

        current_time = time.time()

        # Check and update load average
        if current_load_avg != datastore.get_data("last_load_avg"):
            datastore.update_data("last_load_avg", current_load_avg)
            extra_data.update(current_load_avg)

        # Check and update memory info
        if current_memory_info != datastore.get_data("last_memory_info"):
            datastore.update_data("last_memory_info", current_memory_info)
            extra_data.update(current_memory_info)

        # Check and update disk info
        if current_disk_info != datastore.get_data("last_disk_info"):
            datastore.update_data("last_disk_info", current_disk_info)
            extra_data.update(current_disk_info)

        # Get IOwait
        current_cpu_times = psutil.cpu_times()
        current_iowait = info_linux.get_iowait(last_cpu_times, current_cpu_times)
        current_iowait = round(current_iowait, 2)
        if current_iowait != datastore.get_data("last_iowait"):
            datastore.update_data("last_iowait", current_iowait)
            extra_data.update({'iowait': current_iowait})
        last_cpu_times = current_cpu_times

        log("Sending ping to server. " + str(globals.AGENT_VERSION), "debug")
        response = send_request(cmd="ping", data=extra_data)

        events = event_processor.process_changes(datastore)
        for event in events:
            logpo("Sending event:", event, "debug")
            send_notification(event["name"], event["data"])

        if response:
            log("Response receive... validating", "debug")
            valid_response = validate_response(response, token)
            if valid_response:
                data = valid_response.get("data", {})
                new_interval = valid_response.get("refresh")
                if new_interval and config['interval'] != int(new_interval):
                    config["interval"] = new_interval
                    log(f"Interval update to {config['interval']} seconds", "info")
                if isinstance(data, dict) and "something" in data:
                    # example
                    try:
                        pass
                    except ValueError:
                        log("invalid", "warning")
            else:
                log("Invalid response receive", "warning")

        end_time = time.time()
        duration = end_time - current_time
        log(f"Tiempo bucle {duration:.2f} + Sleeping {config['interval']} (segundos).", "debug")
        time.sleep(config["interval"])

if __name__ == "__main__":
    log("Iniciando el servicio Monnet Agent...", "info")
    with daemon.DaemonContext():
        run()