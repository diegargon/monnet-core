"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Runner Task
@description: This module is responsible for executing Ansible tasks based on the configuration stored in the database.

"""

"""
TODO: Manage run ansible playbook exceptions
"""
# Std
from datetime import datetime, timedelta
import json
import socket
from ipaddress import ip_address, ip_network

# Third-party
from croniter import croniter

# Local
from monnet_shared.event_type import EventType
from monnet_shared.log_type import LogType
from monnet_shared.app_context import AppContext
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
        self.db = DBManager(self.config.file_config)
        self.ansible_model = AnsibleModel(self.db)
        self.ansible_service = AnsibleService(ctx, self.ansible_model)
        self.host_service = HostService(ctx)

    def _ensure_db_connection(self):
        """Ensure the database connection is active and reconnect if necessary."""
        try:
            if not self.db.is_connected():
                self.db.close()
                self.db = DBManager(self.config.file_config)
                self.ansible_model = AnsibleModel(self.db)
                self.ansible_service = AnsibleService(self.ctx, self.ansible_model)
                self.logger.warning("AnsibleTask: Database connection lost. Reconnect success.")
        except Exception as e:
            self.logger.error(f"AnsibleTask: Failed to ensure database connection: {e}")
            raise

    def run(self):
        try:
            self.logger.debug("Execution ansible task...")
            self._ensure_db_connection()
            tasks = self.ansible_service.fetch_active_tasks()
            self.logger.debug(f"Number of tasks {len(tasks)}")
            now = datetime.now()

            for task in tasks:
                self._ensure_db_connection()
                trigger_type = task.get("trigger_type")
                if trigger_type in [2, 3, 6]:
                    self.logger.debug(f"Ignoring task {task['task_name']} with trigger_type={trigger_type}")
                    continue

                if trigger_type == 1 and task.get("done") > 0:
                    self.logger.debug(f"Task {task['task_name']} with trigger_type=1 is already done. Skipping.")
                    continue

                next_trigger = task.get("next_trigger")
                last_triggered = task.get("last_triggered")
                hid = task.get("hid")
                pid = task.get("pid")
                if not pid:
                    self.logger.warning(f"PID not found for task {task['task_name']}. Skipping task.")
                    continue
                # Fetch the playbook associated with the task
                self.logger.debug(f"Fetching playbook for task {task['task_name']} with pid={pid}")
                playbook = self.ansible_service.get_pb_meta_by_pid(pid)
                if not playbook:
                    self.logger.warning(f"Playbook {playbook} not found for task {task['task_name']}. Skipping task.")
                    continue

                # Fetch the IP of the host associated with the hid
                host = self.host_service.get_by_id(hid)
                if not host or "ip" not in host or not host["ip"]:
                    self.logger.warning(f"Host with hid={hid} not found or missing IP. Skipping task {task['task_name']}.")
                    continue

                try:
                    host_ip = ip_address(host["ip"])
                except ValueError:
                    self.logger.error(f'Invalid IP address for task task {task["task_name"]}. Skipping.')
                    continue
                # Initialize extra_vars
                extra_vars = {}

                # Check if the playbook metadata contains the tag 'agent-config'
                tags = playbook.get("tags", [])
                if "agent-config" in tags:
                    agent_config = self._build_agent_config(host)
                    if not agent_config:
                        self.logger.error(f"Failed to build agent config for task {task['task_name']}. Skipping.")
                        continue
                    try:
                        extra_vars["agent_config"] = json.dumps(agent_config)
                    except (TypeError, ValueError) as e:
                        self.logger.error(f"Failed to serialize agent_config to JSON for task {task['task_name']}: {e}")
                        continue

                # Fetch Ansible variables associated with the hid
                playbook_vars = self.ansible_service.fetch_playbook_vars_by_hid(hid)
                extra_vars.update({var["vkey"]: var["vvalue"] for var in playbook_vars})
                self.logger.debug(f"Extra vars for task {task['task_name']}: {extra_vars}")

                # Fetch ansible user. Precedence: ansible_var, otherwise config default or "ansible"
                ansible_user = extra_vars.get("ansible_user") or self.config.get("ansible_user", "ansible")

                # TODO: set ansible_group
                ansible_group = None

                # 1 Uniq task: run and delete
                # 2 Manual: Ignore, triggered by user
                # 3 Event Response: Ignore, triggered by event
                # 4 Cron: run if cron time is reached
                # 5 Interval: run if interval time is reached
                # 6 Task Chain: Ignore, triggered by another task
                if trigger_type == 1:
                    self.ansible_service.task_done(task["id"])
                    self.logger.info(f"Running Uniq task: {task['task_name']} {task['pid']}")
                    result = self.ansible_service.run_ansible_playbook(
                        pid, extra_vars, ip=host_ip, user=ansible_user, ansible_group=ansible_group
                    )

                    if not self._handle_task_result(hid, task, result):
                        continue

                elif trigger_type == 4:
                    crontime = task.get("crontime")
                    last_triggered = task.get("last_triggered")
                    created = task.get("created")
                    if crontime and croniter.is_valid(crontime):
                        # TODO manage croniter exceptions
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
                            self.ansible_service.task_done(task["id"])
                            result = self.ansible_service.run_ansible_playbook(
                                pid, extra_vars, ip=host_ip, user=ansible_user, ansible_group=ansible_group
                            )

                            if not self._handle_task_result(hid, task, result):
                                continue

                            self.ansible_service.update_task_triggers(
                                task["id"], last_triggered=now
                            )
                            self.logger.debug(
                                f"Updated task {task['id']} with last_triggered={now} "
                                f"and next_trigger={next_cron_time}"
                            )

                elif trigger_type == 5 and (not next_trigger or not last_triggered or now >= next_trigger):
                    if task.get('task_interval', None) is None:
                        self.logger.warning(f"Missing interval from the interval task {task['task_name']}")
                        continue
                    try:
                        interval_seconds = self._parse_interval(task["task_interval"])
                    except ValueError as e:
                        continue

                    self.logger.info(f"Running interval task: {task['task_name']} at interval of {task['task_interval']}")

                    self.ansible_service.task_done(task["id"])
                    result = self.ansible_service.run_ansible_playbook(
                        pid, extra_vars, ip=host_ip, user=ansible_user, ansible_group=ansible_group
                    )

                    if not self._handle_task_result(hid, task, result):
                        continue

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
        finally:
            # Testing with and without close_connection
            # self.close_connection()
            pass

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
            self.logger.error(f"Invalid interval format: {interval}. Defaulting to 5 minutes.")

        return 300

    def _build_agent_config(self, host):
        """
        Build the agent configuration based on the host and system settings.

        Args:
            host (dict): The host metadata.

        Returns:
            dict: The agent configuration.
        """
        token = host.get("token")
        if not token:
            self.logger.error(f"Host {host.get('id')} is missing a token. Cannot build agent config.")
            return None

        # Obtener la IP del host
        host_ip = host.get("ip")
        if not host_ip:
            self.logger.error(f"Host {host.get('id')} is missing an IP address. Cannot build agent config.")
            return None

        # Determinar si la IP es externa
        try:
            ip = ip_address(host_ip)
            is_external = not any(
                ip in ip_network(net) for net in ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"]
            )
        except ValueError:
            self.logger.error(f"Invalid IP address {host_ip} for host {host.get('id')}. Cannot build agent config.")
            return None
        except Exception as e:
            self.logger.error(f"Error determining IP address type for host {host.get('id')}: {e}")
            return None

        server_host = None

        # If host is external, use the external host config
        if is_external:
            server_host = self.config.get("agent_external_host", None)

        # If host is internal, use the internal host config
        if not server_host:
            server_host = self.config.get("agent_internal_host", None)

        # if everything fails, use the default server host
        if not server_host:
            server_host = socket.getfqdn()
            if not server_host:
                self.logger.error(f"Unable to resolve server host for config the agent")
                return None

        return {
            "id": host.get("id"),
            "token": token,
            "agent_log_level": self.config.get("agent_log_level", "INFO"),
            "default_interval": self.config.get("agent_default_interval", 60),
            "ignore_cert": self.config.get("agent_allow_selfcerts", 0),
            "server_host": server_host,
            "mem_alert_threshold": self.config.get("default_mem_alert_threshold", 90),
            "mem_warn_threshold": self.config.get("default_mem_warn_threshold", 80),
            "disks_alert_threshold": self.config.get("default_disks_alert_threshold", 90),
            "disks_warn_threshold": self.config.get("default_disks_warn_threshold", 80),
            "server_endpoint": self.config.get("server_endpoint", "/feedme.php"),
        }

    def _report_event(self, host_id: int, task: dict, result: dict):
        """
        Report task status event
        status 0 = success
        status 1 = failure

        Args:
            host_id (int): The ID of the host.
            task (dict): The task.
            result (dict): The result of the Ansible playbook execution.
        """

        if not result or not isinstance(result, dict):
            self.logger.error(f"Report Event: Invalid result for task {task.get('id')}: {result}")
            return

        status = self.ansible_service.get_report_status(result)

        if status == 1:
            log_type = LogType.EVENT_WARN
            event_type = EventType.TASK_FAILURE
            message = "failure"
        else:
            log_type = LogType.EVENT
            event_type = EventType.TASK_SUCCESS
            message = "success"

        self.host_service.create_event(
            host_id=host_id,
            message=f"Task {task['task_name']} status: {message}",
            log_type=log_type,
            event_type=event_type
        )

    def _handle_task_result(self, hid, task, result):
        """
        Handle the result of an Ansible playbook execution.

        Args:
            hid (int): Host ID.
            task (dict): Task metadata.
            result (str): Result of the playbook execution in JSON format.

        Returns:
            bool: True if the result was handled successfully, False otherwise.
        """
        if not result or not isinstance(result, str):
            self.logger.error(f"Invalid result for task {task['task_name']}: {result}")
            return False

        try:
            result_dict = json.loads(result)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON result for task {task['task_name']}: {e}")
            return False

        # Report event
        self._report_event(hid, task, result_dict)

        try:
            report_data = self.ansible_service.prepare_report(
                self.ctx, task, result_dict, rtype=2
            )
        except TypeError as e:
            self.logger.error(f"Type error while preparing report for task {task['task_name']}: {e}")
            return False
        except ValueError as e:
            self.logger.error(f"Value error while preparing report for task {task['task_name']}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while preparing report for task {task['task_name']}: {e}")
            return False

        self.ansible_service.save_report(report_data)
        return True

    def close_connection(self):
        """Closes the database connection."""
        try:
            if self.db:
                self.db.close()
                self.logger.debug("AnsibleTask: Database connection closed.")
        except Exception as e:
            self.logger.error(f"AnsibleTask: Failed to close database connection: {e}")