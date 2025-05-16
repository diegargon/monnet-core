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

from monnet_gateway import mgateway_config
from monnet_shared.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_shared.app_context import AppContext
from monnet_shared.clogger import Logger
from monnet_gateway.services.ansible_service import AnsibleService
from monnet_gateway.server import run_server, stop_server
from monnet_gateway.tasks.task_scheduler import TaskSched

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
    logger.warning(f"Monnet Gateway server shutdown... signal received {sig}")
    logger.debug(f"File: {frame.f_code.co_filename}, Line: {frame.f_lineno}")
    logger.debug(f"Function: {frame.f_code.co_name}, Locals: {frame.f_locals}")
    try:
        if not stop_event.is_set():
            stop_event.set()
            stop_server()

        if server_thread is not None:
            server_thread.join()

        if task_thread is not None:
            task_thread.stop()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

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

    try:
        timeout = 5
        waited = 0
        while ctx.get_var('server_ready', None) is not True or stop_event.is_set():
            sleep(0.1)
            waited += 0.1
            if waited >= timeout:
                logger.error("Timeout waiting for server to be ready.")
                stop_event.set()
                return
    except Exception as e:
        logger.error(f"Error waiting for server to be ready: {e}")
        stop_event.set()
        return

    task_thread = TaskSched(ctx)
    task_thread.start()

    try:
        while not stop_event.is_set():
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Stopping Gateway server...")
    finally:
        stop_event.set()
        if server_thread is not None:
            server_thread.join()
        if task_thread is not None:
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
    ctx.set_var('version', mgateway_config.GW_F_VERSION)
    # Initialize Logger
    logger = Logger()
    ctx.set_logger(logger)

    # Initialize Config
    config = Config(ctx, mgateway_config.CONFIG_DB_PATH)
    ctx.set_config(config)

    # Setting up signal handlers
    signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler(sig, frame, ctx))
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, ctx))

    # Initialize AnsibleService
    ansible_service = AnsibleService(ctx, None)

    # Scan Ansible Playbooks Directory and save it in the context
    ansible_service.extract_pb_metadata()

    # Run the server on the test port if specified
    if args.test_port:  # Cambiado de args.test a args.test_port
        ctx.set_var('test-port', 1)

    logger.notice(f"Starting Monnet Gateway in {'foreground' if args.no_daemon else 'daemon'} mode...")

    if args.no_daemon:
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
            run(ctx)

if __name__ == "__main__":
    main()
