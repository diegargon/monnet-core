"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

This code is just a basic/preliminary draft.

"""

import traceback
import socket
import subprocess
import json
import signal
import sys
import os
import threading
import argparse
from pathlib import Path
from time import sleep

# Third party
import daemon

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.server import run_server
from utils.context import AppContext
from shared.log_linux import log, logpo
from config import HOST, PORT, PORT_TEST, VERSION, MINOR_VERSION, ALLOWED_COMMANDS

def signal_handler(sig, frame):
    """Manejador de señales para capturar la terminación del servicio"""
    log("Monnet Gateway server shuttdown...", "info")
    stop_event.set()
    sys.exit(0)

"""
Run
"""
def run(ctx):
    server_thread = threading.Thread(target=run_server, args=(ctx,), daemon=False)
    server_thread.start()
    stop_event = ctx.get_var('stop_event')

    try:
        while not stop_event.is_set():
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        log("Stopping server...", "info")
        server_thread.join()

"""
    Main
"""

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    log("Iniciando el servicio Monnet Gateway...", "info")

    stop_event = threading.Event()

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-daemon", action="store_true", help="Run without daemonizing")
    parser.add_argument("--working-dir", type=str, default="/opt/monnet-core", help="Working directory")
    parser.add_argument("--test", action="store_true", help="Run the server on the test port.")
    args = parser.parse_args()

    workdir = args.working_dir

    if not os.path.exists(workdir):
        raise FileNotFoundError(f"Working direcotry not found: {workdir}")

    ctx = AppContext(workdir)
    ctx.set_var('test', 1)
    ctx.set_var('stop_event', stop_event)

    if args.no_daemon:
        run(ctx)
    else:
        with daemon.DaemonContext(working_directory=workdir):
            run(ctx)
