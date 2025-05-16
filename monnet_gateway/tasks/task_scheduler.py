"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Task Scheduler

"""

import threading
from time import sleep, time
import syslog

# Local
from monnet_gateway.database.dbmanager import DBManager
from monnet_shared.app_context import AppContext
from monnet_gateway.tasks.discovery import DiscoveryHostsTask
from monnet_gateway.tasks.known_checker import HostsCheckerTask
from monnet_gateway.tasks.ansible_task import AnsibleTask
from monnet_gateway.tasks.prune_task import PruneTask
from monnet_gateway.tasks.weekly_task import WeeklyTask

class TaskSched:
    """Class to execute a periodic task."""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config)
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
            }

            # TODO save last run time in DB? and apply here
            self.last_run_time = {
                "send_logs": current_time,
                "discovery_hosts": current_time,
                "hosts_checker": current_time,
                "ansible_task": current_time,
                "prune": current_time,
                "weekly_task": current_time,
            }

            # Avoid parallel task
            self.task_locks = {
                "send_logs": threading.Lock(),
                "discovery_hosts": threading.Lock(),
                "hosts_checker": threading.Lock(),
                "ansible_task": threading.Lock(),
                "prune": threading.Lock(),
                "weekly_task": threading.Lock(),
            }

            self.discovery_hosts = DiscoveryHostsTask(ctx)
            self.hosts_checker = HostsCheckerTask(ctx)
            self.ansible_task = AnsibleTask(ctx)
            self.prune_task = PruneTask(ctx)
            self.weekly_task = WeeklyTask(ctx)

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
                self.logger.warning("TaskSched: Database connection lost. Forcing reconnection.")
                self.db.close()
                self.db = DBManager(self.config)
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
                # Run DiscoveryTask if the interval has passed
                self._run_task("discovery_hosts", self.discovery_hosts.run, current_time)
                # Run HostCheckerTask if the interval has passed
                self._run_task("hosts_checker", self.hosts_checker.run, current_time)
                # Run AnsibleTask if the interval has passed
                self._run_task("ansible_task", self.ansible_task.run, current_time)
                # Run PruneTask if the interval has passed
                self._run_task("prune", self.prune_task.run, current_time)
                # Run WeeklyTask if the interval has passed
                self._run_task("weekly_task", self.weekly_task.run, current_time)

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
                except Exception as e:
                    self.logger.error(f"Error during {task_name}: {e}")
                    raise # Propagate to run_task to try reconnect
                finally:
                    self.task_locks[task_name].release()
            else:
                self.logger.info(f"TaskSched: {task_name} task locked..")

    def _send_store_logs(self):
        """
        Collects logs from the Logger and inserts them into the system_logs table.
        """
        # self.logger.debug("Storing logs in system_logs table...")
        try:
            logs = self.logger.pop_logs()
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

    def stop(self):
        """Stops the periodic task."""
        self.stop_event.set()
        try:
            if self.thread.is_alive():
                self.thread.join()
            self.db.close()
            self.logger.info("TaskSched stopped.")
        except Exception as e:
            self.logger.error(f"Error stopping TaskSched: {e}")
