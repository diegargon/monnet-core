"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

from shared.app_context import AppContext
from monnet_gateway.handlers.handler_ansible import run_ansible_playbook
from monnet_gateway.database.dbmanager import DBManager  # Import DBManager
from datetime import datetime, timedelta
from croniter import croniter

class AnsibleTask:
    """Ejecuta tareas Ansible según la configuración en la base de datos."""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.db = DBManager(ctx.get_config())

    def run(self):
        self.logger.debug("Execution ansible task...")
        tasks = self.db.fetchall("SELECT * FROM tasks WHERE disable = 0")
        now = datetime.now()

        for task in tasks:
            trigger_type = task.get("trigger_type")
            if trigger_type in [2, 3, 6]:
                self.logger.debug(f"Ignoring task {task['task_name']} with trigger_type={trigger_type}")
                continue

            task_interval = task.get("task_interval") or "1m"
            interval_seconds = self._parse_interval(task_interval)
            next_trigger = task.get("next_trigger")
            last_triggered = task.get("last_triggered")

            if trigger_type == 1:
                self.logger.info(f"Running task: {task['task_name']}")
                #run_ansible_playbook(task)

                with self.db.transaction():
                    # Delete task after execution
                    self.db.execute("DELETE FROM tasks WHERE id = %s", (task["id"],))
                    self.logger.debug(f"Deleted task {task['id']} with trigger_type=1")

            elif trigger_type == 4:
                crontime = task.get("crontime")
                last_triggered = task.get("last_triggered")
                if crontime and croniter.is_valid(crontime):
                    cron = croniter(crontime, now)
                    next_cron_time = cron.get_next(datetime)
                    last_cron_time = cron.get_prev(datetime)
                    if now >= next_cron_time or (last_triggered is not None and last_triggered < last_cron_time):
                        self.logger.info(f"Running task: {task['task_name']} at crontime={crontime}")
                        #run_ansible_playbook(task)

                        with self.db.transaction():
                            self.db.update(
                                "tasks",
                                data={
                                    "last_triggered": now.strftime("%Y-%m-%d %H:%M:%S"),
                                },
                                where={"id": task["id"]},
                            )
                            self.logger.debug(
                                f"Updated task {task['id']} with last_triggered={now}"
                            )

                    else:
                        self.logger.debug(
                            f"Task {task['task_name']} with trigger_type=4 will run at {next_cron_time}"
                        )

            elif trigger_type == 5 and (not next_trigger or not last_triggered or now >= next_trigger):
                self.logger.info(f"Running task: {task['task_name']}")
                #run_ansible_playbook(task)

                # Calculate new triggers
                new_last_triggered = now
                new_next_trigger = now + timedelta(seconds=interval_seconds)

                with self.db.transaction():
                    # Update triggers for tasks with trigger_type 5
                    self.db.update(
                        "tasks",
                        data={
                            "last_triggered": new_last_triggered.strftime("%Y-%m-%d %H:%M:%S"),
                            "next_trigger": new_next_trigger.strftime("%Y-%m-%d %H:%M:%S"),
                        },
                        where={"id": task["id"]},
                    )
                    self.logger.debug(
                        f"Updated task {task['id']} with last_triggered={new_last_triggered} "
                        f"and next_trigger={new_next_trigger}"
                    )

    def _parse_interval(self, interval: str) -> int:
        """
        Parse task_interval string into seconds.
        Supported formats: Xm (minutes), Xh (hours), Xd (days).
        Defaults to 1 minute if invalid.
        """
        try:
            if interval.endswith("m"):
                return int(interval[:-1]) * 60
            elif interval.endswith("h"):
                return int(interval[:-1]) * 3600
            elif interval.endswith("d"):
                return int(interval[:-1]) * 86400
        except ValueError:
            pass
        return 60  # Default to 1 minute
