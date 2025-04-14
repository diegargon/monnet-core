"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

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
from monnet_gateway.handlers.handler_ansible import extract_pb_metadata
from shared.app_context import AppContext
from shared.clogger import Logger
from monnet_gateway.mgateway_config import TASK_INTERVAL
from monnet_gateway.server import run_server, stop_server
from monnet_gateway.tasks.gateway_tasks import TaskSched

stop_event = threading.Event()
server_thread = None
task_thread = None

def signal_handler(sig: signal.Signals, frame: types.FrameType, ctx: AppContext) -> None:
    """
    Manejador de señales para capturar la terminación del servicio

    Args:
        sig (signal.Signals):
        frame (types.FrameType):
        ctx (AppContext): Context
    """
    logger = ctx.get_logger()
    logger.log(f"Monnet Gateway server shutdown... signal received {sig}", "info")
    logger.log(f"File: {frame.f_code.co_filename}, Line: {frame.f_lineno}", "debug")
    logger.log(f"Function: {frame.f_code.co_name}, Locals: {frame.f_locals}", "debug")
    if not stop_event.is_set():
        stop_event.set()
        stop_server()

    if server_thread is not None:
        server_thread.join()

def run(ctx: AppContext):
    """
    Start Server Thread
    Args:
        ctx (AppContext): context
    """
    global server_thread, task_thread

    logger = ctx.get_logger()

    server_thread = threading.Thread(target=run_server, args=(ctx,), daemon=False)
    server_thread.start()

    task_thread = TaskSched(ctx)
    task_thread.start()

    try:
        while not stop_event.is_set():
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.log("Stopping server...", "info")
    finally:
        stop_event.set()
        server_thread.join()
        task_thread.stop()

def main():
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
        "--test-port",
        action="store_true",
        help="Run the server on the test port."
    )
    args = parser.parse_args()

    workdir = args.working_dir

    if not os.path.exists(workdir):
        sys.stderr.write(f"Error: Working directory not found: {workdir}\n")
        sys.exit(1)

    ctx = AppContext(workdir)
    ctx.set_var('stop_event', stop_event)
    ctx.set_var('task_interval', TASK_INTERVAL)

    logger = Logger()
    ctx.set_logger(logger)

    # Setting up signal handlers
    signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler(sig, frame, ctx))
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, ctx))

    # Escan Ansible Playbooks Directory and save it in the context
    extract_pb_metadata(ctx)

    # Run the server on the test port if specified
    if args.test_port:  # Cambiado de args.test a args.test_port
        ctx.set_var('test-port', 1)

    logger.log("Starting Monnet Gateway...", "info")

    if args.no_daemon:
        logger.log("Running in foreground mode", "info")
        with daemon.DaemonContext(
            detach_process=False,   # Avoid background
            stdout=sys.stdout,      # Redirect stdout to the console
            stderr=sys.stderr,      # Redirect stderr to the console
            stdin=sys.stdin,        # Terminal input
            files_preserve=[sys.stdout.fileno(), sys.stderr.fileno()]
        ):
            run(ctx)
    else:
        with daemon.DaemonContext(working_directory=workdir):
            logger.log("Running in daemon mode", "info")
            run(ctx)

if __name__ == "__main__":
    main()
