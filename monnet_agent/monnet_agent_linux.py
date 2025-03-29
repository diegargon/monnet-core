"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

Main agent loop

"""

# Standard
import sys
from pathlib import Path
import argparse

# Third Party
import daemon

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from shared.clogger import Logger
from shared.app_context import AppContext
from monnet_agent.core.agent import MonnetAgent

def main():
    parser = argparse.ArgumentParser(description="Monnet Agent")
    parser.add_argument('--no-daemon', action='store_true', help='Run without daemonizing')
    parser.add_argument(
        "--working-dir", type=str,
        default="/opt/monnet-core",
        help="Working directory"
    )
    args = parser.parse_args()

    workdir = args.working_dir

    ctx = AppContext(workdir)
    logger = Logger()
    ctx.set_logger(logger)

    logger.log("Init Monnet Agent service...", "info")

    agent = MonnetAgent(ctx)

    if args.no_daemon:
        logger.log("Running in foreground mode", "info")
        with daemon.DaemonContext(
            detach_process=False,   # Avoid background
        ):
            agent.run()
    else:
        with daemon.DaemonContext():
            logger.log("Running in daemon mode", "info")
            agent.run()

if __name__ == "__main__":
    main()
