"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

# Std

from datetime import datetime, timedelta

# Third-party
from croniter import croniter

# Local
from shared.app_context import AppContext
from monnet_gateway.handlers.handler_ansible import run_ansible_playbook
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.ansible_model import AnsibleModel
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.services.ansible_service import AnsibleService

class AnsibleTask:
    """Ejecuta tareas Ansible según la configuración en la base de datos."""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config)
        self.ansible_model = AnsibleModel(self.db)
        self.ansible_service = AnsibleService(ctx, self.ansible_model)
        self.host_service = HostService(ctx)

    def run(self):
        self.logger.debug("Execution ansible task...")
        tasks = self.ansible_service.fetch_active_tasks()
        now = datetime.now()

        for task in tasks:
            trigger_type = task.get("trigger_type")
            if trigger_type in [2, 3, 6]:
                self.logger.debug(f"Ignoring task {task['task_name']} with trigger_type={trigger_type}")
                continue

            # Obtain task parameters
            task_interval = task.get("task_interval") or "1m"
            interval_seconds = self._parse_interval(task_interval)
            next_trigger = task.get("next_trigger")
            last_triggered = task.get("last_triggered")
            hid = task.get("hid")
            playbook = task.get("playbook")
            if not playbook:
                self.logger.warning(f"Playbook not found for task {task['task_name']}. Skipping task.")
                continue

            # Fetch Ansible variables associated with the hid
            ansible_vars = self.ansible_service.fetch_ansible_vars_by_hid(hid)
            extra_vars = {var["vkey"]: var["vvalue"] for var in ansible_vars}
            self.logger.debug(f"Extra vars for task {task['task_name']}: {extra_vars}")

            # Fetch the IP of the host associated with the hid
            host = self.host_service.get_by_id(hid)
            if not host or "ip" not in host:
                self.logger.warning(f"Host with hid={hid} not found or missing IP. Skipping task {task['task_name']}.")
                continue
            host_ip = host["ip"]

            # Fetch ansible user. Precedence: ansible_var, otherwise config default or "ansible"
            if "ansible_user" in extra_vars and not None:
                ansible_user = extra_vars.get("ansible_user")
            else:
                ansible_user = self.config.get("ansible_user", "ansible")

            # TODO: set ansible_group
            ansible_group = None

            # 1 Uniq task: run and delete
            # 2 Manual: Ignore, triggered by user
            # 3 Event Response: Ignore, triggered by event
            # 4 Cron: run if cron time is reached
            # 5 Interval: run if interval time is reached
            # 6 Task Chain: Ignore, triggered by another task
            if trigger_type == 1:
                self.logger.info(f"Running task: {task['task_name']}")
                # run_ansible_playbook(self.ctx, playbook, extra_vars, ip=host_ip, user=ansible_user, ansible_group=ansible_group)

                self.ansible_service.delete_task(task["id"])
                self.logger.debug(f"Deleted task {task['id']} with trigger_type=1")

            elif trigger_type == 4:
                crontime = task.get("crontime")
                last_triggered = task.get("last_triggered")
                created = task.get("created")
                if crontime and croniter.is_valid(crontime):
                    cron = croniter(crontime, now)
                    next_cron_time = cron.get_next(datetime)
                    last_cron_time = cron.get_prev(datetime)
                    # Run the task if:
                    # 1 Normal: if now is equal or greater than next_cron_time
                    # 2 Last triggered is less than last_cron_time (Missing Task Run)
                    # 3 Never triggered and the last cron (never none) is greater than created time
                    if (
                        now >= next_cron_time or
                        (last_triggered is not None and last_triggered < last_cron_time) or
                        (last_triggered is None and now >= last_cron_time and last_cron_time > created)
                    ):
                        self.logger.info(
                            f"Running task: {task['task_name']} at crontime={crontime}"
                        )
                        # run_ansible_playbook(
                        #     self.ctx, playbook, extra_vars, ip=host_ip, user=ansible_user,
                        #     ansible_group=ansible_group
                        # )

                        self.ansible_service.update_task_triggers(
                            task["id"], last_triggered=now
                        )
                        self.logger.debug(
                            f"Updated task {task['id']} with last_triggered={now} "
                            f"and next_trigger={next_cron_time}"
                        )

            elif trigger_type == 5 and (not next_trigger or not last_triggered or now >= next_trigger):
                self.logger.info(f"Running task: {task['task_name']}")
                # run_ansible_playbook(
                #     self.ctx, playbook, extra_vars, ip=host_ip, user=ansible_user,
                #     ansible_group=ansible_group
                # )

                # Calculate new triggers
                new_last_triggered = now
                new_next_trigger = now + timedelta(seconds=interval_seconds)
                self.ansible_service.update_task_triggers(
                    task["id"], last_triggered=new_last_triggered, next_trigger=new_next_trigger
                )
                self.logger.debug(
                    f"Updated task {task['id']} with last_triggered={new_last_triggered} "
                    f"and next_trigger={new_next_trigger}"
                )

    def _parse_interval(self, interval: str) -> int:
        """
        Parse task_interval string into seconds.
        Supported formats: Xm (minutes), Xh (hours), Xd (days), Xmo (months), and Xy (years).
        Defaults to 1 minute if invalid.
        """
        try:
            if interval.endswith("m"):
                return int(interval[:-1]) * 60
            elif interval.endswith("h"):
                return int(interval[:-1]) * 3600
            elif interval.endswith("d"):
                return int(interval[:-1]) * 86400
            elif interval.endswith("mo"):
                return int(interval[:-2]) * 2592000
            elif interval.endswith("y"):
                return int(interval[:-1]) * 31536000
        except ValueError:
            pass
        return 60
