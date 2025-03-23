"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Ansible

"""

import threading
from time import sleep

DEFAULT_INTERVAL = 60

# Local
from monnet_gateway.utils.context import AppContext
from shared.logger import log

class TaskSched:
    """Clase para ejecutar una tarea periódica."""
    def __init__(self, ctx: AppContext):
        try:
            log("Initialice TaskSched...")
            if not ctx.has_var("task_interval"):
                ctx.set_var("task_interval", DEFAULT_INTERVAL)
                log(
                    f"TaskSched interval not set. Using default: {DEFAULT_INTERVAL}",
                    "warning"
                )
            self.interval = ctx.get_var("task_interval")

            self.stop_event = ctx.get_var("stop_event")
            # Launch Thread
            self.thread = threading.Thread(target=self.run_task, daemon=True)
            log("TaskSched thread created.", "debug")
        except Exception as e:
            log(f"Error initialice TaskSched: {e}", "err")

    def start(self):
        """Inicia el hilo de la tarea periódica."""
        log("Starting TaskSched...", "debug")
        self.thread.start()

    def run_task(self):
        """Método que ejecuta la tarea periódica."""
        while not self.stop_event.is_set():
            log(f"TaskSched: Running... interval: {self.interval}", "debug")
            sleep(self.interval)

    def stop(self):
        """Detiene la tarea periódica."""
        self.stop_event.set()
        self.thread.join()
        log("TaskSched stopped.")
