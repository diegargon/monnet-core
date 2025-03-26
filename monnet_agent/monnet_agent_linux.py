"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

"""

# Standard
import sys
import time
import signal
from datetime import datetime
from pathlib import Path
import argparse

# Third Party
import psutil
import daemon

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
import info_linux
import tasks
import monnet_agent.agent_globals as agent_globals
from datastore import Datastore
from event_processor import EventProcessor
from shared.mconfig import load_config, validate_agent_config
from constants import LogLevel, EventType
from shared.logger import log, logpo
from monnet_agent.notifications import send_notification, validate_response, send_request
from monnet_agent.handle_signals import handle_signal

global running

def run():
    global running

    running = True
    config = None

    datastore = Datastore()
    event_processor = EventProcessor()

    # Used for iowait
    last_cpu_times = psutil.cpu_times()

    log("Init monnet linux agent", "info")
    # Cargar la configuracion desde el archivo
    config = load_config(agent_globals.CONFIG_FILE_PATH)
    if not config:
        log("Cant load config. Finishing", "err")
        return

    try:
        validate_agent_config(config)
    except ValueError as e:
        log(str(e), "err")
        return

    token = config["token"]
    config["interval"] = config["default_interval"]

    # Signal Handle
    signal.signal(signal.SIGINT, lambda signum, frame: handle_signal(signum, frame, config))
    signal.signal(signal.SIGTERM, lambda signum, frame: handle_signal(signum, frame, config))

    starting_data = {
        'msg': datetime.now().time(),
        'ncpu': info_linux.get_cpus(),
        'uptime': info_linux.get_uptime(),
        'log_level': LogLevel.NOTICE,
        'event_type': EventType.STARTING
    }

    send_notification(config, 'starting', starting_data)

    # Timer functions
    tasks.check_listen_ports(config, datastore, send_notification, startup=1)
    tasks.send_stats(config, datastore, send_notification)

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

        log("Sending ping to server. " + str(agent_globals.AGENT_VERSION), "debug")
        response = send_request(config, cmd="ping", data=extra_data)

        events = event_processor.process_changes(datastore)
        for event in events:
            logpo("Sending event:", event, "debug")
            send_notification(config, event["name"], event["data"])

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
    parser = argparse.ArgumentParser(description="Monnet Agent")
    parser.add_argument('--no-daemon', action='store_true', help='Run without daemonizing')
    args = parser.parse_args()

    log("Iniciando el servicio Monnet Agent...", "info")
    if args.no_daemon:
        run()
    else:
        with daemon.DaemonContext():
            run()
