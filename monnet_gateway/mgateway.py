"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

This code is just a basic/preliminary draft.

"""

import signal
import sys
import os
import threading
import argparse
import types
from pathlib import Path
from time import sleep

# Third party
import daemon

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.server import run_server
from monnet_gateway.utils.context import AppContext
from shared.logging import log

stop_event = threading.Event()

def signal_handler(sig: signal.Signals, frame: types.FrameType) -> None:
    """
    Manejador de señales para capturar la terminación del servicio

    Args:
        sig (signal.Signals):
        frame (types.FrameType):
    """
    log(f"Monnet Gateway server shuttdown... signal receive {sig}", "info")
    log(f"File: {frame.f_code.co_filename}, Line: {frame.f_lineno}", "debug")
    log(f"Function: {frame.f_code.co_name}, Locals: {frame.f_locals}", "debug")
    stop_event.set()

def run(ctx: AppContext):
    """
    Start Server Thread
    Args:
        ctx (AppContext): context
    """
    server_thread = threading.Thread(target=run_server, args=(ctx,), daemon=False)
    server_thread.start()
    stop_event = ctx.get_var('stop_event')

    try:
        while not stop_event.is_set():
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        log("Stopping server...", "info")
    finally:
        stop_event.set()
        server_thread.join()

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    log("Iniciando el servicio Monnet Gateway...", "info")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-daemon",
        action="store_true",
        help="Run without daemonizing"
    )
    parser.add_argument(
        "--working-dir", type=str,
        default="/opt/monnet-core",
        help="Working directory"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the server on the test port."
    )
    args = parser.parse_args()

    workdir = args.working_dir

    if not os.path.exists(workdir):
        raise FileNotFoundError(f"Working direcotry not found: {workdir}")

    ctx = AppContext(workdir)
    if args.test:
        ctx.set_var('test', 1)

    ctx.set_var('stop_event', stop_event)

    if args.no_daemon:
        run(ctx)
    else:
        with daemon.DaemonContext(working_directory=workdir):
            run(ctx)
