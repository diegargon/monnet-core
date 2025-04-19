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

from shared.file_config import load_file_config, validate_agent_config

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from shared.clogger import Logger
from shared.app_context import AppContext
from monnet_agent.core.agent import MonnetAgent
from monnet_agent import agent_config

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

    logger.info(f"Init Monnet Agent service... {agent_config.AGENT_VERSION}")

    # Cargar configuración antes de instanciar MonnetAgent
    try:
        config = load_file_config(agent_config.CONFIG_AGENT_PATH)
    except RuntimeError as e:
        logger.err(f"Error loading config: {e}")
        sys.exit(1)

    try:
        validate_agent_config(config)
    except ValueError as e:
        logger.err(f"Validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.err(f"Unexpected error during validation: {e}")
        sys.exit(1)

    log_level = config.get("log_level", "info")
    logger.info(f"Setting log level to: {log_level}")
    logger.set_min_log_level(log_level)
    ctx.set_config(config)

    agent = MonnetAgent(ctx)

    if args.no_daemon:
        logger.info("Running in foreground mode")
        with daemon.DaemonContext(
            detach_process=False,   # Avoid background
        ):
            agent.run()
    else:
        with daemon.DaemonContext():
            logger.info("Running in daemon mode")
            agent.run()

if __name__ == "__main__":
    main()
