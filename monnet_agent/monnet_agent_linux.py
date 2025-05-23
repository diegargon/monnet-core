"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Main agent loop

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
from monnet_shared.clogger import Logger
from monnet_shared.app_context import AppContext
from monnet_shared.file_config import FileConfig
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

    # Load configuration before instantiating MonnetAgent
    try:
        config = FileConfig(ctx, agent_config.CONFIG_AGENT_PATH)
        config.validate_agent_config()
    except Exception as e:
        logger.err(f"Error loading or validating config: {e}")
        sys.exit(1)

    agent_log_level = config.get("agent_log_level", "INFO")
    logger.info(f"Setting log level to: {agent_log_level}")
    logger.set_min_log_level(agent_log_level)
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
