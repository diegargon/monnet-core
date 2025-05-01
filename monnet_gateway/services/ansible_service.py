"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Service
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
from monnet_gateway.mgateway_config import DEFAULT_ANSIBLE_GROUPS_FILE
from monnet_gateway.services.encrypt_service import EncryptService
from shared.app_context import AppContext

class AnsibleService:
    """Service layer for interacting with AnsibleModel."""

    def __init__(self, ctx: AppContext, ansible_model: AnsibleModel = None):
        self.ansible_model = ansible_model
        self.logger = ctx.get_logger()
        self.ctx = ctx

    def _ensure_model(self):
        """Ensure the AnsibleModel is initialized."""
        if not self.ansible_model:
            self.logger.debug("Initializing AnsibleModel lazily.")
            self.ansible_model = AnsibleModel(self.ctx)

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

    def fetch_ansible_vars_by_hid(self, hid: int):
        """Fetch Ansible variables associated with a host (hid)."""
        self._ensure_model()
        vars = self.ansible_model.fetch_ansible_vars_by_hid(hid)
        for var in vars:
            if var['vtype'] == 1 and var['vvalue'] not in (None, ''):
                try:
                    # Decodificar el valor Base64 a bytes
                    ciphertext = base64.b64decode(var['vvalue'])
                    # Intentar descifrar el valor
                    var['vvalue'] = EncryptService().decrypt(ciphertext)
                except (ValueError, TypeError) as e:
                    var['vvalue'] = None
                    self.logger.error(f"Error decrypting variable for host {hid}: {e}")
                except FileNotFoundError as e:
                    var['vvalue'] = None
                    self.logger.error(f"Key file not found for decryption on host {hid}: {e}")
                except Exception as e:
                    var['vvalue'] = None
                    self.logger.error(f"Unexpected error decrypting variable for host {hid}: {e}")

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
            self.logger.error(f"Error reading Ansible hosts file: {e}")
            return []

    def _parse_ansible_groups(self, content):
        """Parse Ansible groups from the content. NOT TESTED """
        try:
            # Attempt to parse as YAML
            parsed_data = yaml.safe_load(content)
            if isinstance(parsed_data, dict):
                # YAML format detected
                return self._parse_yaml_groups(parsed_data)
        except yaml.YAMLError:
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

    def run_ansible_playbook(self, playbook: str, extra_vars=None, ip=None, user=None, ansible_group=None):
        """
        Run Ansible Playbook
        """
        workdir = self.ctx.workdir
        extra_vars_str = json.dumps(extra_vars) if extra_vars else ""
        playbook_directory = os.path.join(workdir, 'monnet_gateway/playbooks')
        playbook_path = os.path.join(playbook_directory, playbook)

        command = ['ansible-playbook', playbook_path]
        if extra_vars_str:
            command.extend(['--extra-vars', extra_vars_str])
        if ip:
            command.insert(1, '-i')
            command.insert(2, f"{ip},")
        if ansible_group:
            command.extend(['--limit', ansible_group])
        if user:
            command.extend(['-u', user])

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stderr:
                raise Exception(f"Error executing playbook: {stderr.decode()}")
            return stdout.decode()
        except Exception as e:
            raise Exception(f"Error executing playbook: {e}")

    def extract_pb_metadata(self):
        """
        Extract metadata from all YAML playbooks in the directory.
        """
        PLAYBOOKS_DIR = os.path.join(self.ctx.workdir, 'monnet_gateway', 'playbooks')
        VALID_EXTENSIONS = ('.yml', '.yaml')
        REQUIRED_FIELDS = {'id', 'name'}
        METADATA_REGEX = r'#\s*@meta\s*(.+?)(?=\n---|\n\s*\n)'

        if not os.path.isdir(PLAYBOOKS_DIR):
            self.logger.error(f"Playbooks directory not found: {PLAYBOOKS_DIR}")
            raise FileNotFoundError(f"Playbooks directory not found: {PLAYBOOKS_DIR}")

        playbook_files = [
            f for f in os.listdir(PLAYBOOKS_DIR)
            if f.lower().endswith(VALID_EXTENSIONS)
            and os.path.isfile(os.path.join(PLAYBOOKS_DIR, f))
        ]

        if not playbook_files:
            self.logger.warning(f"No valid YAML files found in {PLAYBOOKS_DIR}")
            raise FileNotFoundError(f"No valid YAML files found in {PLAYBOOKS_DIR}")

        metadata_list = []
        for filename in playbook_files:
            filepath = os.path.join(PLAYBOOKS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not (metadata_block := re.search(METADATA_REGEX, content, re.DOTALL)):
                    self.logger.debug(f"No metadata found in {filename}")
                    continue

                cleaned_lines = [
                    line.replace('#', '', 1).rstrip()
                    for line in metadata_block.group(1).split('\n')
                    if line.strip().startswith('#') and line.strip()
                ]
                metadata = yaml.safe_load('\n'.join(cleaned_lines))

                if not metadata or not REQUIRED_FIELDS.issubset(metadata):
                    self.logger.warning(f"Invalid metadata in {filename}. Required fields: {REQUIRED_FIELDS}")
                    raise ValueError(f"Invalid metadata in {filename}. Required fields: {REQUIRED_FIELDS}")

                metadata['_source_file'] = filename
                metadata_list.append(metadata)

            except yaml.YAMLError as e:
                self.logger.error(f"YAML syntax error in {filename}: {str(e)}")
                raise ValueError(f"YAML syntax error in {filename}: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error with {filename}: {str(e)}")
                raise RuntimeError(f"Unexpected error with {filename}: {str(e)}")

        self.ctx.set_pb_metadata(metadata_list)

        if not metadata_list:
            self.logger.error("No metadata extracted from playbooks")
            raise ValueError("No metadata extracted from playbooks")

        return metadata_list

    def get_pb_metadata(self, pb_id: str):
        """
        Retrieve metadata for a specific playbook ID from the context.
        """
        if not self.ctx.has_pb_metadata():
            self.extract_pb_metadata()

        pb_metadata = self.ctx.get_pb_metadata()
        if not pb_metadata:
            raise ValueError("No metadata found")

        for metadata in pb_metadata:
            if metadata.get('id') == pb_id:
                return metadata

        raise KeyError(f"Playbook ID {pb_id} not found")
