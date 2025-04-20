"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Task Scheduler

"""

import threading
from time import sleep, time
import syslog  # Add this import for direct syslog logging

DEFAULT_INTERVAL = 60

# Local
from monnet_gateway.database.dbmanager import DBManager
from shared.app_context import AppContext
from monnet_gateway.tasks.discovery import DiscoveryHostsTask
from monnet_gateway.tasks.known_checker import HostsCheckerTask
from monnet_gateway.tasks.ansible_runner import AnsibleTask
from monnet_gateway.tasks.prune_task import PruneTask
from monnet_gateway.tasks.weekly_task import WeeklyTask

class TaskSched:
    """Class to execute a periodic task."""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config)

        try:
            self.logger.info("Initialize TaskSched...")
            if not ctx.has_var("task_interval"):
                ctx.set_var("task_interval", DEFAULT_INTERVAL)
                self.logger.warning(
                    f"TaskSched interval not set. Using default: {DEFAULT_INTERVAL}"
                )

            self.stop_event = ctx.get_var("stop_event")

            self.task_intervals = {
                "send_logs": 20,                    # 20 seconds
                "discovery_hosts":  60 * 22,        # 22 minutes
                "hosts_checker":  60 * 5,           # 5 minutes
                "ansible": 60,                      # 1 minute
                "prune": 60 * 60 * 24,              # 1 day
                "weekly_task": 60 * 60 * 24 * 7,    # 1 week
            }

            self.last_run_time = {
                "send_logs": 0,
                "discovery_hosts": 0,
                "hosts_checker": 0,
                "ansible": 0,
                "prune": 0,
                "weekly_task": 0,
            }

            # Avoid parallel task
            self.task_locks = {
                "send_logs": threading.Lock(),
                "discovery_hosts": threading.Lock(),
                "hosts_checker": threading.Lock(),
                "ansible": threading.Lock(),
                "prune": threading.Lock(),
                "weekly_task": threading.Lock(),
            }

            self.discovery_hosts = DiscoveryHostsTask(ctx)
            self.hosts_checker = HostsCheckerTask(ctx)
            self.ansible = AnsibleTask(ctx)
            self.prune_task = PruneTask(ctx)
            self.weekly_task = WeeklyTask(ctx)

            # Launch Thread
            #self.thread = threading.Thread(target=self.run_task, daemon=True)
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

    def run_task(self):
        """
        Method that executes the periodic task.

        It must execute:
            monnet-cli
            monnet-discovery
            Ansible Tasks
        """
        while not self.stop_event.is_set():
            current_time = time()

            try:
                # Insert logs in system_logs table
                if current_time - self.last_run_time["send_logs"] >= self.task_intervals["send_logs"]:
                    if self.task_locks["send_logs"].acquire(blocking=False):
                        try:
                            self._send_store_logs()
                            self.last_run_time["send_logs"] = current_time
                        finally:
                            self.task_locks["send_logs"].release()

                # Run DiscoveryTask if the interval has passed
                if current_time - self.last_run_time["discovery_hosts"] >= self.task_intervals["discovery_hosts"]:
                    if self.task_locks["discovery_hosts"].acquire(blocking=False):
                        try:
                            self.logger.notice("Running DiscoveryHostsTask...")
                            self.discovery_hosts.run()
                            self.last_run_time["discovery_hosts"] = current_time
                        finally:
                            self.task_locks["discovery_hosts"].release()
                            self.logger.notice("Finish DiscoveryHostsTask...")

                # Run HostCheckerTask if the interval has passed
                if current_time - self.last_run_time["hosts_checker"] >= self.task_intervals["hosts_checker"]:
                    if self.task_locks["hosts_checker"].acquire(blocking=False):
                        try:
                            self.logger.notice("Running known host checker...")
                            self.hosts_checker.run()
                            self.last_run_time["hosts_checker"] = current_time
                        finally:
                            self.task_locks["hosts_checker"].release()
                            self.logger.notice("Finish known host checker...")

                # Run AnsibleTask if the interval has passed
                if current_time - self.last_run_time["ansible"] >= self.task_intervals["ansible"]:
                    if self.task_locks["ansible"].acquire(blocking=False):
                        try:
                            self.logger.debug("Running AnsibleTask...")
                            # self.ansible.run()
                            self.last_run_time["ansible"] = current_time
                        finally:
                            self.task_locks["ansible"].release()

                # Run PruneTask if the interval has passed
                if current_time - self.last_run_time["prune"] >= self.task_intervals["prune"]:
                    if self.task_locks["prune"].acquire(blocking=False):
                        try:
                            self.logger.debug("Running PruneTask...")
                            self.prune_task.run()
                            self.last_run_time["prune"] = current_time
                        finally:
                            self.task_locks["prune"].release()

                # Run WeeklyTask if the interval has passed
                if current_time - self.last_run_time["weekly_task"] >= self.task_intervals["weekly_task"]:
                    if self.task_locks["weekly_task"].acquire(blocking=False):
                        try:
                            self.logger.debug("Running WeeklyTask...")
                            self.weekly_task.run()
                            self.last_run_time["weekly_task"] = current_time
                        finally:
                            self.task_locks["weekly_task"].release()

                sleep(1)
            except Exception as e:
                self.logger.error(f"Error in TaskSched: {e}")

        """
        New run_task method with task scheduling
        self._run_task("send_logs", self._send_store_logs)
        self._run_task("discovery_hosts", self.discovery_hosts.run)
        self._run_task("hosts_checker", self.hosts_checker.run)
        self._run_task("ansible", self.ansible.run)
        self._run_task("prune", self.prune_task.run)


        def _run_task(self, task_name, task_function):
            if current_time - self.last_run_time[task_name] >= self.task_intervals[task_name]:
                if self.task_locks[task_name].acquire(blocking=False):
                    try:
                        self.logger.debug(f"Running {task_name}...")
                        task_function()
                        self.last_run_time[task_name] = current_time
                    except Exception as e:
                        self.logger.error(f"Error during {task_name}: {e}")
                    finally:
                        self.task_locks[task_name].release()
        """

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
            self.logger.info("TaskSched stopped.")
        except Exception as e:
            self.logger.error(f"Error stopping TaskSched: {e}")

