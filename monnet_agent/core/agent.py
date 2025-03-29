"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

"""


from datetime import datetime
import signal
import time
from typing import Any, Dict

# Third Party
import psutil

# Local
from constants.log_level import LogLevel
from constants.event_type import EventType
import monnet_agent.agent_tasks as agent_tasks
from monnet_agent import agent_globals, info_linux
from monnet_agent.datastore import Datastore
from monnet_agent.event_processor import EventProcessor
from monnet_agent.handle_signals import handle_signal
from monnet_agent.notifications import send_notification, send_request, validate_response
from shared.mconfig import load_config, validate_agent_config


class MonnetAgent:
    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.running = True
        ctx.set_var("running", True)
        self.config = None
        self.datastore = Datastore(ctx)
        self.event_processor = EventProcessor(ctx)
        self.last_cpu_times = psutil.cpu_times()


    def initialize(self):
        """Initialize the Monnet Agent"""
        self.logger.log("Init monnet linux agent", "info")

        # Load config from file
        try:
            self.config = load_config(agent_globals.CONFIG_FILE_PATH)
        except RuntimeError as e:
            self.logger.log(f"Error loading config: {e}", "err")
            return False

        if not self.config:
            self.logger.log("Cant load config. Finishing", "err")
            return False

        try:
            validate_agent_config(self.config)
        except ValueError as e:
            self.logger.log(f"Validation error: {e}", "err")
            return False
        except RuntimeError as e:
            self.logger.log(f"Unexpected error during validation: {e}", "err")
            return False

        self.config["interval"] = self.config["default_interval"]
        self.ctx.set_config(self.config)
        self._setup_handlers()
        self._setup_tasksched()
        self._send_starting_notification()

        return True

    def run(self):
        """Main agent loop"""
        if not self.initialize():
            self.logger.log("Initialization failed. Exiting...", "err")
            return False

        while self.running:
            current_time = time.time()
            extra_data = self._collect_system_data()

            self._send_ping(extra_data)
            self._process_events()

            self.running = self.ctx.get_var("running")
            self._sleep_interval(current_time)

        return True

    def _send_starting_notification(self):
        """Send initial notification with system info"""
        self.logger.log("Sending starting notification", "info")
        try:
            uptime = info_linux.get_uptime()
        except (FileNotFoundError, ValueError, OSError) as e:
            self.logger.warning(f"Error getting uptime: {e}")
            uptime = None

        if uptime is None:
            self.logger.log("Uptime not available", "warning")
            return

        starting_data = {
            'msg': datetime.now().time(),
            'ncpu': info_linux.get_cpus(),
            'uptime': uptime,
            'log_level': LogLevel.NOTICE,
            'event_type': EventType.STARTING
        }
        send_notification(self.ctx, 'starting', starting_data)

    def _collect_system_data(self) -> Dict[str, Any]:
        """Collect system metrics and return as dictionary"""
        extra_data = {}

        # Get system info from tasks/system_info.py
        try:
            current_load_avg = info_linux.get_load_avg()
        except (FileNotFoundError, ValueError, OSError) as e:
            self.logger.warning(f"Error load avg: {e}")
            current_load_avg = None

        try:
            current_memory_info = info_linux.get_memory_info()
        except (FileNotFoundError, ValueError, OSError) as e:
            self.logger.warning(f"Error memory info: {e}")
            current_memory_info = None

        try:
            current_disk_info = info_linux.get_disks_info()
        except (FileNotFoundError, ValueError, OSError) as e:
            self.logger.warning(f"Error memory info: {e}")
            current_disk_info = None

        # Check and update load average
        if current_load_avg is not None and current_load_avg != self.datastore.get_data("last_load_avg"):
            self.datastore.update_data("last_load_avg", current_load_avg)
            extra_data.update(current_load_avg)

        # Check and update memory info
        if current_memory_info is not None and current_memory_info != self.datastore.get_data("last_memory_info"):
            self.datastore.update_data("last_memory_info", current_memory_info)
            extra_data.update(current_memory_info)

        # Check and update disk info
        if current_disk_info is not None and current_disk_info != self.datastore.get_data("last_disk_info"):
            self.datastore.update_data("last_disk_info", current_disk_info)
            extra_data.update(current_disk_info)

        # Get IOwait
        current_cpu_times = psutil.cpu_times()
        current_iowait = info_linux.get_iowait(self.last_cpu_times, current_cpu_times)
        current_iowait = round(current_iowait, 2)
        if current_iowait != self.datastore.get_data("last_iowait"):
            self.datastore.update_data("last_iowait", current_iowait)
            extra_data.update({'iowait': current_iowait})
        self.last_cpu_times = current_cpu_times

        return extra_data

    def _send_ping(self, extra_data: Dict[str, Any]):
        """Send ping to server with collected data"""
        self.logger.log("Sending ping to server", "debug")
        response = send_request(self.ctx, cmd="ping", data=extra_data)

        if response:
            self.logger.log("Response received... validating", "debug")
            valid_response = validate_response(self.ctx, response, self.config["token"])
            if valid_response:
                self._handle_valid_response(valid_response)
            else:
                self.logger.log("Invalid response received", "warning")

    def _handle_valid_response(self, response: Dict[str, Any]):
        """Handle valid server response"""
        data = response.get("data", {})
        new_interval = response.get("refresh")

        if new_interval and self.config['interval'] != int(new_interval):
            self.config["interval"] = new_interval
            self.logger.log(f"Interval updated to {self.config['interval']} seconds", "info")

        if isinstance(data, dict) and "something" in data:
            # Handle specific commands from server
            try:
                pass  # Implement command handling
            except ValueError:
                self.logger.log("Invalid command", "warning")

    def _process_events(self):
        """Process and send events"""
        events = self.event_processor.process_changes(self.datastore)
        for event in events:
            self.logger.logpo(f"Sending event: {event}", "debug")
            send_notification(self.ctx, event["name"], event["data"])

    def _setup_handlers(self):
        """Setup signal handlers"""
        signal.signal(signal.SIGINT, lambda signum, frame: handle_signal(signum, frame, self.ctx))
        signal.signal(signal.SIGTERM, lambda signum, frame: handle_signal(signum, frame, self.ctx))

    def _sleep_interval(self, start_time: float):
        """Sleep for remaining interval time"""
        end_time = time.time()
        duration = end_time - start_time
        sleep_time = max(0, self.config["interval"] - duration)
        self.logger.log(
            f"Loop time {duration:.2f} + Sleeping {sleep_time:.2f} (seconds).",
            "debug"
        )
        time.sleep(sleep_time)

    def _setup_tasksched(self):
        """Setup Task Scheduler"""

        agent_tasks.check_listen_ports(self.ctx, self.datastore, send_notification, startup=1)
        agent_tasks.send_stats(self.ctx, self.datastore, send_notification)

    def stop(self):
        """Stop the agent gracefully"""
        self.running = False
        self.ctx.set_var("running", False)

        # Cancel all active timers
        for timer_name, timer in agent_globals.timers.items():
            if timer:
                timer.cancel()
        self.logger.log("Agent stopped and timers cleaned up.", "info")
