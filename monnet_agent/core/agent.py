"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Core Agent Main Loop
"""

"""
TODO:
    info_linux: Manage exceptions

"""
from datetime import datetime
import signal
import time
from typing import Any, Dict

# Third Party
import psutil

# Local Shared
from monnet_shared.log_level import LogLevel
from monnet_shared.event_type import EventType
from monnet_shared.log_type import LogType
from monnet_shared.app_context import AppContext
# Local
from monnet_agent.agent_sched import AgentTaskSched
from monnet_agent import info_linux
from monnet_agent.datastore import Datastore
from monnet_agent.event_processor import EventProcessor
from monnet_agent.handle_signals import handle_signal
from monnet_agent.notifications import send_notification
from monnet_agent.requests import send_request, validate_response
from monnet_agent.agent_net_utils import get_mac_from_ip, get_own_mac
from monnet_shared.com_net_utils import send_wol, get_default_interface

class MonnetAgent:
    def __init__(self, ctx: AppContext):
        try:
            self.ctx = ctx
            self.logger = ctx.get_logger()
            ctx.set_var("agent_running", True)
            self.config = ctx.get_config()
            self.datastore = Datastore(ctx)
            self.event_processor = EventProcessor(ctx)
            self.last_cpu_times = psutil.cpu_times()
            self.task_scheduler = AgentTaskSched(self.ctx, self.datastore, send_notification)
        except Exception as e:
            self.logger.error(f"Error initializing MonnetAgent: {e}")
            return
        finally:
            self.logger.debug("Monnet Agent Core __init__ success.")

    def initialize(self):
        """Initialize the Monnet Agent."""
        self.logger.debug("Starting Agent Core")

        if not self.config:
            self.logger.error("Cannot load config. Exiting")
            return False

        # Initilize withthe default interval to ping the server
        self.config.set("interval", self.config.get("default_interval"))

        try:
            self._setup_handlers()
        except Exception as e:
            self.logger.error(f"Error setting up handlers: {e}")
            return False

        try:
            self._send_starting_notification()
        except Exception as e:
            self.logger.error(f"Error sending starting notification: {e}")
            return False

        try:
            self._setup_tasksched()
        except Exception as e:
            self.logger.error(f"Error setting up task scheduler: {e}")
            return False

        self.logger.debug("Agent Core initialized successfully.")

        return True

    def run(self):
        """Main agent loop."""
        self.logger.debug("Starting Agent core main loop")

        if not self.initialize():
            self.logger.err("Agent initialization failed. Exiting...")
            return False
        else:
            self.logger.info("Initialization successful. Starting main loop...")

        while self.ctx.get_var("agent_running"):
            current_time = time.time()

            # Collect data - System Data
            try:
                system_metrics = self._collect_system_data()
            except (FileNotFoundError, ValueError, OSError) as e:
                self.logger.warning(f"Error collecting system data: {e}")
                system_metrics = {}
            except Exception as e:
                self.logger.err(f"Unexpected error while collecting system data: {e}")
                system_metrics = {}

            self.logger.debug(f"System metrics collected: {system_metrics}")

            # Collect data - Logs
            try:
                host_logs = self.logger.pop_logs()
            except Exception as e:
                self.logger.err(f"Error while collecting host logs: {e}")
                host_logs = []

            # Check if we have any data to send
            data_values = {}
            if system_metrics:
                data_values.update(system_metrics)
            if host_logs:
                data_values['host_logs_count'] = len(host_logs)
                data_values["host_logs"] = host_logs

            # Add collect_macs if exists in datastore
            collect_macs = self.datastore.get_data("collect_macs")
            if collect_macs is not None:
                data_values["collect_macs"] = collect_macs
                # Clear the datastore entry after sending
                self.datastore.delete_data("collect_macs")

            self.logger.debug(f"Data values prepared for ping: {data_values}")
            self._send_ping(data_values)
            self._process_events()

            # Comprueba que el scheduler sigue vivo
            self.task_scheduler.ensure_running()

            self._sleep_interval(current_time)

        self.logger.notice("Agent run core finish")

        return True

    def _send_starting_notification(self):
        """Send initial notification with system info."""
        self.logger.info("Sending starting notification")
        try:
            uptime = info_linux.get_uptime()
        except (FileNotFoundError, ValueError, OSError) as e:
            self.logger.warning(f"Error getting uptime: {e}")
            uptime = None

        if uptime is None:
            self.logger.warning("Uptime not available")
            return

        # Obtener interfaz principal y su MAC
        interface = get_default_interface()
        mac = get_own_mac(interface) if interface else None

        # Obtener machine-id
        machine_id = info_linux.get_machine_id()

        date_now = datetime.now().time().strftime("%H:%M:%S")
        starting_data = {
            'msg': f'Agent starting {date_now}',
            'date': date_now,
            'ncpu': info_linux.get_cpus(),
            'uptime': uptime,
            'machine_id': machine_id,
            'log_level': LogLevel.NOTICE,
            'log_type': LogType.EVENT,
            'event_type': EventType.AGENT_STARTING,
            'interface': interface,
            'mac': mac
        }
        send_notification(self.ctx, 'starting', starting_data)

    def _collect_system_data(self) -> Dict[str, Any]:
        """Collect system metrics and return as a dictionary."""
        system_metrics = {}

        # Get system info
        # Load AVG
        try:
            current_load_avg = info_linux.get_load_avg()
        except (FileNotFoundError, ValueError, OSError) as e:
            self.logger.warning(f"Error load avg: {e}")
            current_load_avg = None
        # Memory
        try:
            current_memory_info = info_linux.get_memory_info()
        except (FileNotFoundError, ValueError, OSError) as e:
            self.logger.warning(f"Error memory info: {e}")
            current_memory_info = None
        # Disk
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

        # Get and Update IOwait
        current_cpu_times = psutil.cpu_times()
        current_iowait = info_linux.get_iowait(self.last_cpu_times, current_cpu_times)
        current_iowait = round(current_iowait, 2)
        if current_iowait != self.datastore.get_data("last_iowait"):
            self.datastore.update_data("last_iowait", current_iowait)
            system_metrics.update({'iowait': current_iowait})
        self.last_cpu_times = current_cpu_times

        return system_metrics

    def _send_ping(self, data_values: Dict[str, Any]):
        """Send ping to the server with collected data."""
        self.logger.debug("Preparing to send ping to server")

        if not data_values:
            self.logger.debug("No data values to send in ping")
            data_values = {}

        self.logger.debug(f"Ping data: {data_values}")
        response = send_request(self.ctx, cmd="ping", data=data_values)

        if response:
            self.logger.debug(f"Response received: {response}")
            valid_response = validate_response(self.ctx, response, self.config.get("token"))
            if valid_response:
                self.logger.debug("Valid response received. Handling response...")
                self._handle_valid_response(valid_response)
            else:
                self.logger.warning("Invalid response received")
        else:
            self.logger.err("No response received from server")

    def _handle_valid_response(self, response: Dict[str, Any]):
        """Handle valid server response."""
        data = response.get("data", {})
        new_interval = int(response.get("refresh"))

        if new_interval and int(self.config.get('interval')) != int(new_interval):
            self.config.set("interval", int(new_interval))
            self.logger.info(f"Interval updated to {self.config.get('interval')} seconds")

        if isinstance(data, dict) and "config" in data:
            new_config = data["config"]
            if isinstance(new_config, dict):
                # Add or update config values
                for key, value in new_config.items():
                    if key in self.config.file_config:
                        self.logger.debug(f"Updating config key '{key}' with new value: {value}")
                    else:
                        self.logger.debug(f"Adding new config key '{key}' with value: {value}")
                    self.config.set(key, value)
                    if key == "agent_log_level":
                        self.logger.set_min_log_level(value)
                        self.logger.info(f"Log level updated to: {value}")
                try:
                    self.config.update_file_key(key, value, create_key=True)
                except Exception as e:
                    self.logger.err(f"Error updating config file: {e}")
                    return
                self.logger.info(f"Config file updated: {self.config.file_config}")

        # sendwol
        if isinstance(data, dict) and "sendwol" in data:
            sendwol_data = data["sendwol"]
            if isinstance(sendwol_data, dict) and "mac" in sendwol_data:
                mac = sendwol_data["mac"]
                try:
                    result = send_wol(mac)
                    self.logger.info(f"sendwol: Magic packet sent to {mac}: {result}")
                except Exception as e:
                    self.logger.err(f"sendwol: Failed to send magic packet to {mac}: {e}")

        # collect_macs
        if isinstance(data, dict) and "collect_macs" in data:
            ip_list = data["collect_macs"]
            if isinstance(ip_list, list):
                macs_info = []
                for ip in ip_list:
                    mac = get_mac_from_ip(ip)
                    macs_info.append({"ip": ip, "mac": mac})
                if macs_info:
                    self.datastore.replace_data("collect_macs", macs_info)
                self.logger.debug(f"collect_macs: Stored {len(macs_info)} IP-MAC entries in datastore")

    def _process_events(self):
        """Process and send events."""
        events = self.event_processor.process_changes(self.datastore)
        for event in events:
            self.logger.logpo(f"Sending event: {event}", "debug")
            send_notification(self.ctx, event["name"], event["data"])

    def _setup_handlers(self):
        """Setup signal handlers."""
        signal.signal(signal.SIGINT, lambda signum, frame: handle_signal(signum, frame, self.ctx))
        signal.signal(signal.SIGTERM, lambda signum, frame: handle_signal(signum, frame, self.ctx))

    def _sleep_interval(self, start_time: float):
        """Sleep for the remaining interval time."""
        end_time = time.time()
        duration = end_time - start_time
        sleep_time = max(0, self.config.get("interval") - duration)
        self.logger.debug(
            f"Loop time {duration:.2f} + Sleeping {sleep_time:.2f} seconds."
        )
        time.sleep(sleep_time)

    def _setup_tasksched(self):
        """Setup Task Scheduler."""
        self.task_scheduler.start()

    def stop(self):
        """Stop the agent gracefully."""
        self.ctx.set_var("agent_running", False)
        if self.task_scheduler.is_running():
            self.task_scheduler.stop()

        self.logger.info("Agent stopped.")
