"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Task Scheduler

Current Tasks Called:
    check_listen_ports
    send_stats
"""

# Standard
import threading
from time import sleep, time

# Local
from monnet_agent.agent_tasks import check_listen_ports, send_stats

class AgentTaskSched:
    """Agent Task Scheduler (single thread, robust, inspired by gateway)"""
    def __init__(self, ctx, datastore, notify_callback):
        current_time = time()
        try:
            self.ctx = ctx
            self.logger = ctx.get_logger()
            self.logger.debug("Initializing AgentTaskSched...")
            self.config = ctx.get_config()
            self.datastore = datastore
            self.notify_callback = notify_callback
            self._scheduler_stop_event = threading.Event()

            # Configurable intervals (seconds)
            self.task_intervals = {
                "check_ports": float(self.config.get("agent_check_ports_interval", 60)),
                "send_stats": float(self.config.get("agent_send_stats_interval", 60)),
            }
            self.last_run_time = {
                "check_ports": current_time,
                "send_stats": current_time,
            }
            self.task_locks = {
                "check_ports": threading.Lock(),
                "send_stats": threading.Lock(),
            }
            self.thread = threading.Thread(target=self.run_task, daemon=True)
        except Exception as e:
            self.logger.error(f"Error initializing AgentTaskSched: {e}")
            raise
        finally:
            self.logger.info("Agent TaskSched initialized.")

    def start(self):
        if self.thread.is_alive():
            self.logger.warning("TaskSched thread already running.")
            return
        self.logger.debug("Starting TaskSched (agent)...")
        self._scheduler_stop_event.clear()
        self.thread.start()

    def run_task(self):
        self.logger.debug("TaskSched runner (agent)...")
        while not self._scheduler_stop_event.is_set():
            # Revisa si el agente ha solicitado parada
            if not self.ctx.get_var("agent_running"):
                self.logger.info("AgentTaskSched detected agent_running=False, stopping scheduler loop.")
                break
            current_time = time()
            try:
                self._run_task("check_ports", lambda: check_listen_ports(self.ctx, self.datastore, self.notify_callback), current_time)
                self._run_task("send_stats", lambda: send_stats(self.ctx, self.datastore, self.notify_callback), current_time)
                sleep(1)
            except Exception as e:
                self.logger.error(f"Error in TaskSched run: {e}")
                sleep(5)

    def _run_task(self, task_name, task_function, current_time):
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
            else:
                self.logger.info(f"TaskSched: {task_name} task locked..")

    def is_running(self):
        """Check if the scheduler thread is running."""
        return self.thread is not None and self.thread.is_alive()

    def stop(self):
        self._scheduler_stop_event.set()
        try:
            if self.thread.is_alive():
                self.thread.join(timeout=10)
                if self.thread.is_alive():
                    self.logger.warning("TaskSched thread did not stop after timeout.")
            self.logger.info("TaskSched stopped.")
        except Exception as e:
            self.logger.error(f"Error stopping TaskSched: {e}")

    def ensure_running(self):
        """Ensure the scheduler thread is running; restart if not."""
        if not self.thread.is_alive():
            self.logger.warning("TaskSched thread not running, restarting...")
            self._scheduler_stop_event.clear()
            # Prevent multiple threads if called in quick succession
            if not self.thread.is_alive():
                self.thread = threading.Thread(target=self.run_task, daemon=True)
                self.thread.start()
