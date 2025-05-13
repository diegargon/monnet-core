"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Handle Signals

@description Handle signals for the Monnet Agent. This module is responsible for handling
    signals such as SIGTERM and SIGHUP. It also checks if the system is shutting down and
    sends notifications accordingly.
"""

# Std
import signal
import subprocess
import sys

# Local
import info_linux
from shared.app_context import AppContext
from monnet_agent import agent_config
from monnet_agent.notifications import send_notification
from constants import LogLevel, EventType


def handle_signal(signum, frame, ctx: AppContext):
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

    logger.notice(f"Receive Signal {signal_name}  Stopping app...")

    # Cancel all timers
    for name, timer in agent_config.timers.items():
        logger.notice(f"Clearing timer: {name}")
        timer.cancel()
    agent_config.timers.clear()

    # Build notification if detect agent or system shutdown

    try:
        _is_system_shutdown = info_linux.is_system_shutting_down()
    except FileNotFoundError:
        logger.notice("Systemd not available - skipping shutdown check")
        _is_system_shutdown = False
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else "Unknown error while checking system status"
        logger.err(f"Failed to check system status: {error_message}")
        logger.debug(f"Command: {e.cmd}")
        logger.debug(f"Return code: {e.returncode}")
        _is_system_shutdown = False
    except Exception as e:
        logger.err(f"Unexpected error while checking system status: {str(e)}")
        logger.debug(f"Exception type: {type(e).__name__}")
        _is_system_shutdown = False

    if _is_system_shutdown:
        logger.notice("System shutdown detected")
        notification_type = "system_shutdown"
        msg = "System shutdown/reboot detected"
        log_level = LogLevel.ALERT
        event_type = EventType.SYSTEM_SHUTDOWN
    else:
        logger.notice("Agent shutdown detected")
        notification_type = "agent_shutdown"
        msg = f"Signal receive: {signal_name}. Closing application."
        log_level = LogLevel.ALERT
        event_type = EventType.AGENT_SHUTDOWN

    # Send
    data = {"msg": msg, "log_level": log_level, "event_type": event_type}
    send_notification(ctx, notification_type, data)
    ctx.set_var("running", False)
    sys.exit(0)
