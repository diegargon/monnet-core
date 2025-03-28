"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent
"""

# Std
import signal
import sys

# Local
import info_linux
from shared.logger import log
from monnet_agent import agent_globals
from monnet_agent.notifications import send_notification
from constants import LogLevel, EventType


def handle_signal(signum, frame, config):
    """
    Signal Handler

    Returns:
        None
    """
    global running

    signal_name = None
    msg = None

    if signum == signal.SIGTERM:
        signal_name = 'SIGTERM'
    elif signum == signal.SIGHUP:
        signal_name = 'SIGHUP'
    else:
        signal_name = signum

    log(f"Receive Signal {signal_name}  Stopping app...", "notice")

    # Cancel all timers
    for name, timer in agent_globals.timers.items():
        log(f"Clearing timer: {name}")
        timer.cancel()
    agent_globals.timers.clear()

    # Build notification if detect agent or system shutdown
    if info_linux.is_system_shutting_down():
        notification_type = "system_shutdown"
        msg = "System shutdown or reboot"
        log_level = LogLevel.ALERT
        event_type = EventType.SYSTEM_SHUTDOWN
    else:
        notification_type = "agent_shutdown"
        msg = f"Signal receive: {signal_name}. Closing application."
        log_level = LogLevel.ALERT
        event_type = EventType.AGENT_SHUTDOWN

    # Send
    data = {"msg": msg, "log_level": log_level, "event_type": event_type}
    send_notification(config, notification_type, data)
    running = False
    sys.exit(0)
