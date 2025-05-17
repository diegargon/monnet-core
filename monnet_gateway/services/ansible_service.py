"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Service
@description: This module provides the main service layer for interacting with Ansible.

"""

# Standard
import os
import base64
import json
import subprocess
import re
from datetime import datetime

# Third-party
import yaml

# Local
from monnet_gateway.database.ansible_model import AnsibleModel
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.reports_model import ReportsModel
from monnet_gateway.mgateway_config import DEFAULT_ANSIBLE_GROUPS_FILE
from monnet_gateway.services.encrypt_service import EncryptService
from monnet_shared.app_context import AppContext

class AnsibleService:
    """Service layer for interacting with AnsibleModel."""

    def __init__(self, ctx: AppContext, ansible_model: AnsibleModel = None):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config.file_config)
        self.ansible_model = ansible_model or AnsibleModel(self.db)
        self.pb_metadata = None

    def _ensure_model(self):
        """Ensure the AnsibleModel """
        try:
            if not self.ansible_model.db.is_connected():
                self.logger.warning("AnsibleService Database connection lost. Attempting to reconnect.")
                self.db = DBManager(self.config)
                self.ansible_model = AnsibleModel(self.db)
        except Exception as e:
            self.logger.error(f"Error ensuring AnsibleModel: {e}")
            raise RuntimeError("Failed to reconnect AnsibleModel.")

    def fetch_active_tasks(self):
        """Fetch all active tasks."""
        self._ensure_model()
        return self.ansible_model.fetch_active_tasks()

    def delete_task(self, task_id: int):
        """Delete a task by its ID."""
        self._ensure_model()
        self.ansible_model.delete_task(task_id)

    def update_task_triggers(self, task_id: int, last_triggered: datetime, next_trigger: datetime = None):
        """Update task triggers."""
        self._ensure_model()
        self.ansible_model.update_task_triggers(task_id, last_triggered, next_trigger)

    def fetch_playbook_vars_by_hid(self, hid: int):
        """Fetch Ansible variables associated with a host (hid)."""
        self._ensure_model()
        vars = self.ansible_model.fetch_playbook_vars_by_hid(hid)
        for var in vars:
            if 'vkey' not in var or 'vvalue' not in var:
                self.logger.debug(f"Missing 'vkey' or 'vvalue' in variable for host {hid}. Skipping.")
                continue
            if var['vtype'] == 1 and var['vvalue'] not in (None, ''):
                try:
                    # Encrypyted variable saved as base64, decode before decrypting
                    ciphertext = base64.b64decode(var['vvalue'])
                    var['vvalue'] = EncryptService().decrypt(ciphertext)
                except (ValueError, TypeError) as e:
                    var['vvalue'] = None
                    self.logger.error(f"[Host {hid}] Error decrypting variable: {e}")
                except FileNotFoundError as e:
                    var['vvalue'] = None
                    self.logger.error(f"[Host {hid}] Key file not found for decryption: {e}")
                except Exception as e:
                    var['vvalue'] = None
                    self.logger.error(f"[Host {hid}] Unexpected error decrypting variable: {e}")
        return vars

    def fetch_ansible_hosts_groups(self):
        """Fetch Ansible hosts groups. NOT TESTED """
        host_file = DEFAULT_ANSIBLE_GROUPS_FILE
        if not host_file or not os.path.exists(host_file):
            self.logger.debug(f"Ansible hosts file not found: {host_file}")
            return []
        try:
            with open(host_file, 'r') as f:
                content = f.read()
            groups = self._parse_ansible_groups(content)
            return groups
        except Exception as e:
            self.logger.error(f"Error reading Ansible hosts file '{host_file}': {e}")
            return []

    def _parse_ansible_groups(self, content):
        """Parse Ansible groups from the content. NOT TESTED """
        try:
            parsed_data = yaml.safe_load(content)
            if isinstance(parsed_data, dict):
                # YAML format detected
                return self._parse_yaml_groups(parsed_data)
        except yaml.YAMLError as e:
            self.logger.info("Content is not in YAML format, attempting plain text parsing.")

        # Fallback to plain text parsing
        return self._parse_plain_text_groups(content)

    def _parse_yaml_groups(self, data):
        """Parse groups from YAML data. NOT TESTED"""
        groups = []
        for group, details in data.items():
            if isinstance(details, dict) and 'hosts' in details:
                groups.append({
                    'group': group,
                    'hosts': details['hosts']
                })
        return groups

    def _parse_plain_text_groups(self, content):
        """Parse groups from plain text content. NOT TESTED"""
        groups = []
        current_group = None
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                current_group = line[1:-1]
                groups.append({'group': current_group, 'hosts': []})
            elif current_group and line:
                groups[-1]['hosts'].append(line)
        return groups

    def run_ansible_playbook(self, playbook_id: str, extra_vars=None, ip=None, user=None, ansible_group=None):
        """
        Run Ansible Playbook
        """
        if not self.pb_metadata:
            self.extract_pb_metadata()

        playbook_metadata = next((pb for pb in self.pb_metadata if pb.get('id') == playbook_id), None)
        if not playbook_metadata:
            raise FileNotFoundError(f"Playbook with ID {playbook_id} not found in metadata.")

        playbook_path = None
        for directory in [
            os.path.join(self.ctx.workdir, '/var/lib/monnet/playbooks'),
            'monnet_gateway/playbooks'
        ]:
            potential_path = os.path.join(directory, playbook_metadata['_source_file'])
            if os.path.exists(potential_path):
                playbook_path = potential_path
                break

        if not playbook_path:
            raise FileNotFoundError(f"The playbook file for ID {playbook_id} could not be found in any directory.")

        command = ['ansible-playbook', playbook_path]
        try:
            extra_vars_str = json.dumps(extra_vars) if extra_vars else ""
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error converting extra_vars to JSON: {e}")
            raise ValueError(f"Error converting extra_vars to JSON: {e}")

        if extra_vars_str:
            command.extend(['--extra-vars', extra_vars_str])
        if ip:
            command.insert(1, '-i')
            command.insert(2, f"{ip},")
        if ansible_group:
            command.extend(['--limit', ansible_group])
        if user:
            command.extend(['-u', user])
        if extra_vars and 'ansible_port' in extra_vars:
            ansible_port = extra_vars['ansible_port']
            command.extend(['--ssh-common-args', f"-p {ansible_port}"])

        try:
            # Mask vars for logging
            if extra_vars:
                masked_extra_vars = {key: "****" for key in extra_vars.keys()}
                self.logger.info(f"Executing command: {' '.join(command)} with extra-vars: {json.dumps(masked_extra_vars)}")
            else:
                self.logger.info(f"Executing command: {' '.join(command)}")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stderr:
                raise Exception(f"Error executing playbook: {stderr.decode()}")
            return stdout.decode()
        except Exception as e:
            self.logger.error(f"Error executing playbook: {e}")
            raise Exception(f"Error executing playbook: {e}")

    def extract_pb_metadata(self):
        """
        Extract metadata from all YAML playbooks in the directories.
        """
        standard_playbooks_dir = os.path.join(self.ctx.workdir, 'monnet_gateway', 'playbooks')
        user_playbooks_dir = '/var/lib/monnet/playbooks'
        VALID_EXTENSIONS = ('.yml', '.yaml')
        REQUIRED_FIELDS = {'id', 'name'}
        METADATA_REGEX = r'#\s*@meta\s*(.+?)(?=\n---|\n\s*\n)'

        # Combine playbooks from both directories if they exist
        playbook_dirs = [d for d in [standard_playbooks_dir, user_playbooks_dir] if os.path.isdir(d)]
        if not playbook_dirs:
            self.logger.error("No playbooks directories found.")
            return []

        playbook_files = []
        for directory in playbook_dirs:
            playbook_files.extend([
                os.path.join(directory, f) for f in os.listdir(directory)
                if f.lower().endswith(VALID_EXTENSIONS) and os.path.isfile(os.path.join(directory, f))
            ])

        if not playbook_files:
            self.logger.warning("No valid YAML files found in the playbooks directories.")
            return []

        metadata_list = []
        for filepath in playbook_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not (metadata_block := re.search(METADATA_REGEX, content, re.DOTALL)):
                    self.logger.debug(f"No metadata found in {filepath}")
                    continue

                cleaned_lines = [
                    line.replace('#', '', 1).rstrip()
                    for line in metadata_block.group(1).split('\n')
                    if line.strip().startswith('#') and line.strip()
                ]
                metadata = yaml.safe_load('\n'.join(cleaned_lines))

                if not metadata or not REQUIRED_FIELDS.issubset(metadata):
                    self.logger.warning(f"Invalid metadata in {filepath}. Required fields: {REQUIRED_FIELDS}")
                    continue

                metadata['_source_file'] = os.path.basename(filepath)
                metadata_list.append(metadata)

            except yaml.YAMLError as e:
                self.logger.error(f"YAML syntax error in {filepath}: {str(e)}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error with {filepath}: {str(e)}")
                continue

        self.pb_metadata = metadata_list

        if not metadata_list:
            self.logger.warning("No metadata extracted from playbooks")

        return metadata_list

    def get_pb_metadata(self, pid: str):
        """
        Retrieve metadata for a specific playbook ID from the context.
        """
        if not self.pb_metadata:
            self.extract_pb_metadata()

        pb_metadata = self.pb_metadata
        if not pb_metadata:
            raise ValueError("No metadata found")

        for metadata in pb_metadata:
            if metadata.get('id') == pid:
                return metadata

        raise KeyError(f"Playbook ID {pid} not found")

    def get_all_pb_metadata(self):
        """
        Retrieve all playbook metadata from the context.
        """
        if not self.pb_metadata:
            self.extract_pb_metadata()

        pb_metadata = self.pb_metadata
        if not pb_metadata:
            raise ValueError("No metadata found")

        return pb_metadata

    def get_pb_meta_by_pid(self, pid: str):
        """
        Retrieve the playbook associated with a specific PID.
        """
        if not self.pb_metadata:
            self.extract_pb_metadata()

        if not self.pb_metadata:
            self.logger.error("No playbook metadata found")
            return None

        for metadata in self.pb_metadata:
            if metadata.get('id') == pid:
                #self.logger.debug(f"Playbook matched for PID {pid}: {metadata}")
                return metadata
        self.logger.error(f"Playbook ID {pid} not found in metadata")

    def save_report(self, report_data: dict):
        """
        Save a report using the ReportsModel.

        Args:
            report_data (dict): The report data to save.

        """
        self.logger.debug(f"Saving report")

        # TODO: meterlo en result no deberia ser necesario y complica el tema,
        # ansible-report lo necesita actualmente pero se deberia poder cambiar

        # Ensure the 'report' field is wrapped in a JSON-compatible "result" dictionary
        if "report" in report_data:
            if isinstance(report_data["report"], dict):
                # If it's already a dictionary, wrap it in "result" without serializing again
                report_data["report"] = {"result": report_data["report"]}
            elif isinstance(report_data["report"], str):
                try:
                    parsed_report = json.loads(report_data["report"])
                    report_data["report"] = {"result": parsed_report}
                except json.JSONDecodeError:
                    report_data["report"] = {"result": report_data["report"]}

        # Serialize the 'report' field to a JSON string
        try:
            report_data["report"] = json.dumps(report_data["report"])
        except (TypeError, ValueError) as e:
            self.logger.error(f"Failed to convert report data to JSON: {e}")
            return

        self._ensure_model()
        try:
            with self.db.transaction():
                reports_model = ReportsModel(self.db)
                reports_model.save_report(report_data)
                reports_model.commit()
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")

    def get_report_status(self, report: dict) -> int:
        """
        Extract the report status from the playbook result.
        Args:
            stats (dict): The stats dictionary from the playbook result.
        Returns:
            int: Status (0 for success, 1 for failure).
        """
        stats = report.get("stats", {})

        for host, host_stats in stats.items():
            if host_stats.get("failures", 0) > 0 or host_stats.get("unreachable", 0) > 0:
                return 1
        return 0

    def prepare_report(self, ctx: AppContext, data: dict, result: dict, rtype: int) -> dict:
        """
        Prepare a report for saving in the database.
        Args:
            ctx (AppContext): Application context.
            data (dict): Input data.
            result (dict): Result of the playbook execution.
            rtype (int): Report type.
        Returns:
            dict: Prepared report data.
        """
        self.logger.debug(f"Preparing report")
        if not isinstance(result, dict):
            self.logger.error("Prepare Report: Result is not a dictionary")
            return {}

        status = self.get_report_status(result)

        try:
            report_json = json.dumps(result)
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error converting report result to JSON: {e}")
            return {}

        if rtype == 1:  # Order Manual
            source_id = data.get("source_id")
        elif rtype == 2:  # Task
            source_id = data.get("id")
        else:
            self.logger.error(f"Invalid report type: {rtype}")
            return {}

        if not source_id:
            self.logger.error(f"Source ID is missing for report type {rtype}")
            return {}

        return {
            "host_id": data["hid"],
            "pid": data["pid"],
            "source_id": source_id,
            "rtype": rtype,
            "status": status,
            "report": report_json
        }

    def task_done(self, task_id: int):
        """
        Increment the 'done' field of a task by 1.
        Args:
            task_id (int): The ID of the task to update.
        """
        self._ensure_model()
        self.ansible_model.task_done(task_id)
