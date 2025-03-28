"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent
"""

# Std
import signal
import subprocess
import sys

# Local
import info_linux
from shared.app_context import AppContext
from monnet_agent import agent_globals
from monnet_agent.notifications import send_notification
from constants import LogLevel, EventType


def handle_signal(signum, frame, ctx: AppContext, config):
    """
    Signal Handler

    Returns:
        None
    """

    signal_name = None
    msg = None

    logger = ctx.get_logger()

    if signum == signal.SIGTERM:
        signal_name = 'SIGTERM'
    elif signum == signal.SIGHUP:
        signal_name = 'SIGHUP'
    else:
        signal_name = signum

    logger.log(f"Receive Signal {signal_name}  Stopping app...", "notice")

    # Cancel all timers
    for name, timer in agent_globals.timers.items():
        logger.log(f"Clearing timer: {name}")
        timer.cancel()
    agent_globals.timers.clear()

    # Build notification if detect agent or system shutdown

    try:
        _is_system_shutdown = info_linux.is_system_shutting_down()
    except FileNotFoundError:
        logger.log("Systemd not available - skipping shutdown check", "notice")
        _is_system_shutdown = False
    except subprocess.CalledProcessError as e:
        logger.log(f"Failed to check system status: {e.stderr}", "err")
        _is_system_shutdown = False

    if _is_system_shutdown:
        logger.log("System shutdown detected", "notice")
        notification_type = "system_shutdown"
        msg = "System shutdown or reboot"
        log_level = LogLevel.ALERT
        event_type = EventType.SYSTEM_SHUTDOWN
    else:
        logger.log("Agent shutdown detected", "notice")
        notification_type = "agent_shutdown"
        msg = f"Signal receive: {signal_name}. Closing application."
        log_level = LogLevel.ALERT
        event_type = EventType.AGENT_SHUTDOWN

    # Send
    data = {"msg": msg, "log_level": log_level, "event_type": event_type}
    send_notification(config, notification_type, data)
    ctx.set_var("running", False)
    sys.exit(0)
