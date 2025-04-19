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
                "discovery_hosts":  60 * 20,    # 20 minutes
                "hosts_checker":  60 * 5,       # 5 minutes
                "ansible": 60,                  # 1 minute
                "prune": 86400,                 # 1 day
                "weekly_task": 604800,          # 7 days
            }

            self.last_run_time = {
                "discovery_hosts": 0,
                "hosts_checker": 0,
                "ansible": 0,
                "prune": 0,
                "weekly_task": 0,
            }

            # Avoid parallel task
            self.task_locks = {
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

            # Collect and store logs
            self._store_logs()
            try:
                # Run DiscoveryTask if the interval has passed
                if current_time - self.last_run_time["discovery_hosts"] >= self.task_intervals["discovery_hosts"]:
                    if self.task_locks["discovery_hosts"].acquire(blocking=False):
                        try:
                            self.logger.debug("Running DiscoveryHostsTask...")
                            # self.discovery_hosts.run()
                            self.last_run_time["discovery_hosts"] = current_time
                        finally:
                            self.task_locks["discovery_hosts"].release()

                # Run HostCheckerTask if the interval has passed
                if current_time - self.last_run_time["hosts_checker"] >= self.task_intervals["hosts_checker"]:
                    if self.task_locks["hosts_checker"].acquire(blocking=False):
                        try:
                            self.logger.debug("Running HostsCheckerTask...")
                            # self.hosts_checker.run()
                            self.last_run_time["hosts_checker"] = current_time
                        finally:
                            self.task_locks["hosts_checker"].release()

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

    def _store_logs(self):
        """
        Collects logs from the Logger and inserts them into the system_logs table.
        """
        self.logger.debug("Storing logs in system_logs table...")
        try:
            logs = self.logger.pop_logs()
            if logs:
                db = self
                cursor = db.cursor()
                for log in logs:
                    cursor.execute(
                        "INSERT INTO system_logs (level, msg) VALUES (%s, %s)",
                        (log["level"], log["message"])
                    )
                db.commit()
        except Exception as e:
            # Log errors directly to syslog to avoid recursive logging issues
            syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
            syslog.syslog(syslog.LOG_ERR, f"Error storing logs in system_logs table: {e}")

    def stop(self):
        """Stops the periodic task."""
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join()
        self.logger.info("TaskSched stopped.")

    def __del__(self):
        """Ensure the database connection is closed."""
        self.logger.info("Task sched destructor called.")
        if hasattr(self, 'db') and self.db:
            self.db.close()
