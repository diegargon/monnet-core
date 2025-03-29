"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

"""

import threading
from time import sleep

DEFAULT_INTERVAL = 60

# Local
from shared.app_context import AppContext
from monnet_gateway.tasks.discovery import DiscoveryTask
from monnet_gateway.tasks.known_checker import HostCheckerTask
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
            self.interval = ctx.get_var("task_interval")
            self.stop_event = ctx.get_var("stop_event")

            self.discovery = DiscoveryTask(ctx)
            self.checker = HostCheckerTask(ctx)
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
            self.logger.debug(f"TaskSched: Running... interval: {self.interval}")
            self.discovery.run()
            self.checker.run()
            self.ansible.run()
            sleep(self.interval)

    def stop(self):
        """Detiene la tarea periódica."""
        self.stop_event.set()
        self.thread.join()
        self.logger.info("TaskSched stopped.")
