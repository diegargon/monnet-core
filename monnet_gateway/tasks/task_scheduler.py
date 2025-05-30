"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Task Scheduler

"""

import threading
from time import sleep, time, mktime
import syslog
from datetime import datetime

# Local
from monnet_gateway.database.dbmanager import DBManager
from monnet_shared.app_context import AppContext
from monnet_gateway.tasks.discovery import DiscoveryHostsTask
from monnet_gateway.tasks.known_checker import HostsCheckerTask
from monnet_gateway.tasks.ansible_task import AnsibleTask
from monnet_gateway.tasks.prune_task import PruneTask
from monnet_gateway.tasks.weekly_task import WeeklyTask
from monnet_gateway.tasks.hourly_task import HourlyTask
from monnet_gateway.tasks.agents_check import AgentsCheckTask

class TaskSched:
    """Class to execute a periodic task."""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config.file_config)
        current_time = time()

        try:
            self.logger.debug("Initialize TaskSched...")
            self.stop_event = ctx.get_var("stop_event")

            self.task_intervals = {
                # Default 20 seconds
                "send_logs": float(self.config.get("gw_send_logs_intvl", 20)),
                # Default 22 minutes
                "discovery_hosts": float(self.config.get("gw_discover_host_intvl", 60 * 22)),
                # Default 5 minutes
                "hosts_checker": float(self.config.get("gw_host_checker_intvl", 60 * 5)),
                # Default 1 minute
                "ansible_task": float(self.config.get("gw_ansible_tasks_intvl", 60)),
                # Default 1 day
                "prune": float(self.config.get("gw_prune_intvl", 60 * 60 * 24)),
                # Default 1 week
                "weekly_task": float(60 * 60 * 24 * 7),
                "hourly_task": float(60 * 60),
                # Default 1 minute
                "agents_check": float(self.config.get("gw_agents_check_intvl", 60)),  # Default 60s
            }

            self.last_run_time = {
                "send_logs": self._to_timestamp(self.config.get("last_send_logs", current_time)),
                "discovery_hosts": self._to_timestamp(self.config.get("last_discovery_hosts", current_time)),
                "hosts_checker": self._to_timestamp(self.config.get("last_host_checker", current_time)),
                "ansible_task": self._to_timestamp(self.config.get("last_ansible_task", current_time)),
                "prune": self._to_timestamp(self.config.get("last_prune", current_time)),
                "weekly_task": self._to_timestamp(self.config.get("last_weekly_task", current_time)),
                "hourly_task": current_time,
                "agents_check": self._to_timestamp(self.config.get("last_agents_check", current_time)),
            }

            # Avoid parallel task
            self.task_locks = {
                "send_logs": threading.Lock(),
                "discovery_hosts": threading.Lock(),
                "hosts_checker": threading.Lock(),
                "ansible_task": threading.Lock(),
                "prune": threading.Lock(),
                "weekly_task": threading.Lock(),
                "hourly_task": threading.Lock(),
                "agents_check": threading.Lock(),
            }

            self.discovery_hosts = DiscoveryHostsTask(ctx)
            self.hosts_checker = HostsCheckerTask(ctx)
            self.ansible_task = AnsibleTask(ctx)
            self.prune_task = PruneTask(ctx)
            self.weekly_task = WeeklyTask(ctx)
            self.hourly_task = HourlyTask(ctx)
            self.agents_check = AgentsCheckTask(ctx)

            # Launch Thread
            self.thread = threading.Thread(target=self.run_task, daemon=True)
            self.logger.debug("TaskSched thread created.")
        except KeyError as e:
            self.logger.error(f"KeyError during TaskSched initialization: {e}")
        except AttributeError as e:
            self.logger.error(f"AttributeError during TaskSched initialization: {e}")
        except Exception as e:
            self.logger.error(f"Error initialice TaskSched: {e}")

    def start(self):
        """Starts the periodic task thread."""
        self.logger.debug("Starting TaskSched...")
        self.thread.start()

    def _ensure_db_connection(self):
        """Ensure the database connection is active and reconnect if necessary."""
        try:
            if not self.db.is_connected():
                self.logger.warning("TaskSched: DB connection lost. Reconnecting...")
                self.db.close()
                self.db = DBManager(self.config.file_config)
        except Exception as e:
            self.logger.error(f"TaskSched: Failed to reconnect to the database: {e}")
            raise

    def run_task(self):
        """
        Method that executes the periodic task.

        It must execute:
            monnet-cli
            monnet-discovery
            Ansible Tasks
        """
        self.logger.debug("TaskSched runner...")
        while not self.stop_event.is_set():
            current_time = time()

            try:
                # Ensure DB connection before running tasks
                self._ensure_db_connection()

                # Insert logs in system_logs table
                self._run_task("send_logs", self._send_store_logs, current_time)
                # Run DiscoveryTask
                self._run_task("discovery_hosts", self.discovery_hosts.run, current_time)
                # Run HostCheckerTask
                self._run_task("hosts_checker", self.hosts_checker.run, current_time)
                # Run AnsibleTask
                self._run_task("ansible_task", self.ansible_task.run, current_time)
                # Run PruneTask
                self._run_task("prune", self.prune_task.run, current_time)
                # Run WeeklyTask
                self._run_task("weekly_task", self.weekly_task.run, current_time)
                # Run HourlyTask
                self._run_task("hourly_task", self.hourly_task.run, current_time)
                # Run AgentsCheckTask
                self._run_task("agents_check", self.agents_check.run, current_time)

                sleep(1)
            except Exception as e:
                self.logger.error(f"Error in TaskSched run: {e}")
                # Delay to avoid spamming logs when trying reconnecting
                sleep(5)

    def _run_task(self, task_name, task_function, current_time):
        """
        Helper method to run a specific task

        Args:
            task_name (str): The name of the task.
            task_function (callable): The function to execute the task.
            current_time (float): The current time.
        """
        if current_time - self.last_run_time[task_name] >= self.task_intervals[task_name]:
            if self.task_locks[task_name].acquire(blocking=False):
                try:
                    self.logger.debug(f"Running {task_name}...")
                    task_function()
                    self.last_run_time[task_name] = current_time
                    # Persist last run time v75, except for last_agents_check TODO temporaly
                    if self.config.get("db_monnet_version") >= 0.75 and task_name != "agents_check":
                        try:
                            self.config.update_db_key(f"last_{task_name}", current_time)
                        except Exception as e:
                            self.logger.error(f"Failed to persist last_{task_name} to config: {e}")
                except Exception as e:
                    self.logger.error(f"Error during {task_name}: {e}")
                    raise # Propagate to run_task to try reconnect
                finally:
                    self.task_locks[task_name].release()
            else:
                self.logger.info(f"TaskSched: {task_name} task locked..")

    def _send_store_logs(self, num_pop: int = 10):
        """
        Collects logs from the Logger and inserts them into the system_logs table.
        """
        # self.logger.debug("Storing logs in system_logs table...")
        try:
            logs = self.logger.pop_logs(num_pop)
            if logs:
                with self.db.transaction():
                    cursor = self.db.cursor
                    for log in logs:
                        if "level" not in log or "message" not in log:
                            self.logger.error(f"Invalid log entry: {log}")
                            continue
                        cursor.execute(
                            "INSERT INTO system_logs (level, msg) VALUES (%s, %s)",
                            (log["level"], log["message"])
                        )
                    self.logger.info(f"Inserted {len(logs)} logs into system_logs table.")
        except KeyError as e:
            self.logger.error(f"KeyError while processing logs: {e}")
        except AttributeError as e:
            self.logger.error(f"AttributeError in _send_store_logs: {e}")
        except Exception as e:
            # Log errors directly to syslog to avoid recursive logging issues
            syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
            syslog.syslog(syslog.LOG_ERR, f"Error storing logs in system_logs table: {e}")

    def _to_timestamp(self, value):
        if isinstance(value, (float, int)):
            return float(value)
        if isinstance(value, str):
            try:
                dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                return mktime(dt.timetuple())
            except Exception:
                self.logger.warning(f"Failed to parse timestamp from string: {value}")
                # if failed to parse, return current time
                return time()
        return time()

    def stop(self):
        """Stops the periodic task."""
        self.stop_event.set()
        try:
            if self.thread.is_alive():
                self.thread.join(timeout=20)
            # Ensure all logs are sent before stopping
            self._send_store_logs(50)
            self.db.close()
            self.logger.info("TaskSched stopped.")
        except Exception as e:
            self.logger.error(f"Error stopping TaskSched: {e}")
