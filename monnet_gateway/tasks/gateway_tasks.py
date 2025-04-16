"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

import threading
from time import sleep, time

DEFAULT_INTERVAL = 60

# Local
from shared.app_context import AppContext
from monnet_gateway.tasks.discovery import DiscoveryHostsTask
from monnet_gateway.tasks.known_checker import HostsCheckerTask
from monnet_gateway.tasks.ansible_runner import AnsibleTask

class TaskSched:
    """Clase para ejecutar una tarea periódica."""
    def __init__(self, ctx: AppContext):
        self.logger = ctx.get_logger()
        try:
            self.logger.info("Initialice TaskSched...")
            if not ctx.has_var("task_interval"):
                ctx.set_var("task_interval", DEFAULT_INTERVAL)
                self.logger.warning(
                    f"TaskSched interval not set. Using default: {DEFAULT_INTERVAL}"
                )

            self.stop_event = ctx.get_var("stop_event")

            self.task_intervals = {
                "discovery_hosts":  60,
                "hosts_checker":  60,
                "ansible": 60,
            }

            self.last_run_time = {
                "discovery_hosts": 0,
                "hosts_checker": 0,
                "ansible": 0,
            }

            # Avoid parallel task
            self.task_locks = {
                "discovery_hosts": threading.Lock(),
                "hosts_checker": threading.Lock(),
                "ansible": threading.Lock(),
            }

            self.discovery_hosts = DiscoveryHostsTask(ctx)
            self.hosts_checker = HostsCheckerTask(ctx)
            self.ansible = AnsibleTask(ctx)

            # Launch Thread
            self.thread = threading.Thread(target=self.run_task, daemon=True)
            self.logger.debug("TaskSched thread created.")
        except Exception as e:
            self.logger.error(f"Error initialice TaskSched: {e}")

    def start(self):
        """Inicia el hilo de la tarea periódica."""
        self.logger.debug("Starting TaskSched...")
        self.thread.start()

    def run_task(self):
        """
        Método que ejecuta la tarea periódica.

        Tiene que ejecutar:
            monnet-cli
            monnet-discovery
            Ansible Tasks
        """
        while not self.stop_event.is_set():
            current_time = time()

            # Ejecutar DiscoveryTask si ha pasado el intervalo
            if current_time - self.last_run_time["discovery_hosts"] >= self.task_intervals["discovery_hosts"]:
                if self.task_locks["discovery_hosts"].acquire(blocking=False):
                    try:
                        self.logger.debug("Running DiscoveryHostsTask...")
                        self.discovery_hosts.run()
                        self.last_run_time["discovery_hosts"] = current_time
                    finally:
                        self.task_locks["discovery_hosts"].release()

            # Ejecutar HostCheckerTask si ha pasado el intervalo
            if current_time - self.last_run_time["hosts_checker"] >= self.task_intervals["hosts_checker"]:
                if self.task_locks["hosts_checker"].acquire(blocking=False):
                    try:
                        self.logger.debug("Running HostsCheckerTask...")
                        self.hosts_checker.run()
                        self.last_run_time["hosts_checker"] = current_time
                    finally:
                        self.task_locks["hosts_checker"].release()

            # Ejecutar AnsibleTask si ha pasado el intervalo
            if current_time - self.last_run_time["ansible"] >= self.task_intervals["ansible"]:
                if self.task_locks["ansible"].acquire(blocking=False):
                    try:
                        self.logger.debug("Running AnsibleTask...")
                        self.ansible.run()
                        self.last_run_time["ansible"] = current_time
                    finally:
                        self.task_locks["ansible"].release()

            sleep(1)

    def stop(self):
        """Detiene la tarea periódica."""
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join()
        self.logger.info("TaskSched stopped.")
