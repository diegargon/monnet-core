"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - core

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
from monnet_agent import agent_config, info_linux
from monnet_agent.datastore import Datastore
from monnet_agent.event_processor import EventProcessor
from monnet_agent.handle_signals import handle_signal
from monnet_agent.notifications import send_notification, send_request, validate_response
from shared.app_context import AppContext
from shared.mconfig import update_config


class MonnetAgent:
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.running = True
        ctx.set_var("running", True)
        self.config = ctx.get_config()
        self.datastore = Datastore(ctx)
        self.event_processor = EventProcessor(ctx)
        self.last_cpu_times = psutil.cpu_times()


    def initialize(self):
        """Initialize the Monnet Agent"""
        self.logger.debug("Starting Agent Core")

        if not self.config:
            self.logger.err("Cant load config. Finishing")
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
            self.logger.err("Initialization failed. Exiting...")
            return False

        while self.running:
            current_time = time.time()
            system_metrics = self._collect_system_data()

            try:
                host_logs = self.logger.pop_logs(count=10)
            except Exception as e:
                self.logger.err(f"Error while collecting host logs: {e}")
                host_logs = []

            # Ensure system_metrics and host_logs are not empty before merging
            data_values = {}
            if system_metrics:
                data_values.update(system_metrics)
            if host_logs:
                data_values['host_logs_count'] = len(host_logs)
                data_values["host_logs"] = host_logs

            self._send_ping(data_values)
            self._process_events()

            self.running = self.ctx.get_var("running")
            self._sleep_interval(current_time)

        self.logger.notice("Agent run core finish")

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
        system_metrics = {}

        # Get system info
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
            system_metrics.update(current_load_avg)

        # Check and update memory info
        if current_memory_info is not None and current_memory_info != self.datastore.get_data("last_memory_info"):
            self.datastore.update_data("last_memory_info", current_memory_info)
            system_metrics.update(current_memory_info)

        # Check and update disk info
        if current_disk_info is not None and current_disk_info != self.datastore.get_data("last_disk_info"):
            self.datastore.update_data("last_disk_info", current_disk_info)
            system_metrics.update(current_disk_info)

        # Get IOwait
        current_cpu_times = psutil.cpu_times()
        current_iowait = info_linux.get_iowait(self.last_cpu_times, current_cpu_times)
        current_iowait = round(current_iowait, 2)
        if current_iowait != self.datastore.get_data("last_iowait"):
            self.datastore.update_data("last_iowait", current_iowait)
            system_metrics.update({'iowait': current_iowait})
        self.last_cpu_times = current_cpu_times

        return system_metrics

    def _send_ping(self, data_values: Dict[str, Any]):
        """Send ping to server with collected data"""
        self.logger.log("Preparing to send ping to server", "debug")

        if not data_values:
            data_values = {}

        self.logger.log(f"Ping data: {data_values}", "debug")
        response = send_request(self.ctx, cmd="ping", data=data_values)

        if response:
            self.logger.log(f"Response received: {response}", "debug")
            valid_response = validate_response(self.ctx, response, self.config["token"])
            if valid_response:
                self.logger.log("Valid response received. Handling response...", "debug")
                self._handle_valid_response(valid_response)
            else:
                self.logger.log("Invalid response received", "warning")
        else:
            self.logger.log("No response received from server", "err")

    def _handle_valid_response(self, response: Dict[str, Any]):
        """Handle valid server response"""
        data = response.get("data", {})
        new_interval = response.get("refresh")

        if new_interval and self.config['interval'] != int(new_interval):
            self.config["interval"] = new_interval
            self.logger.log(f"Interval updated to {self.config['interval']} seconds", "info")

        if isinstance(data, dict) and "config" in data:
            new_config = data["config"]
            if isinstance(new_config, dict):
                # Add or update config values
                for key, value in new_config.items():
                    if key in self.config:
                        self.logger.debug(f"Updating config key '{key}' with new value: {value}")
                    else:
                        self.logger.debug(f"Adding new config key '{key}' with value: {value}")
                    self.config[key] = value
                update_config(self.config)
                self.logger.log(f"Config updated: {self.config}", "info")
        """
        if isinstance(data, dict) and "something" in data:
            try:
                pass
            except ValueError:
                self.logger.log("Invalid command", "warning")
        """

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
        for timer_name, timer in agent_config.timers.items():
            if timer:
                timer.cancel()
        self.logger.log("Agent stopped and timers cleaned up.", "info")
