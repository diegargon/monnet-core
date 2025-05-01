"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Service
"""

# Standard
import os
import base64
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

    def __init__(self, ctx: AppContext, ansible_model: AnsibleModel):
        self.ansible_model = ansible_model
        self.logger = ctx.get_logger()

    def fetch_active_tasks(self):
        """Fetch all active tasks."""
        return self.ansible_model.fetch_active_tasks()

    def delete_task(self, task_id: int):
        """Delete a task by its ID."""
        self.ansible_model.delete_task(task_id)

    def update_task_triggers(self, task_id: int, last_triggered: datetime, next_trigger: datetime = None):
        """Update task triggers."""
        self.ansible_model.update_task_triggers(task_id, last_triggered, next_trigger)

    def fetch_ansible_vars_by_hid(self, hid: int):
        """Fetch Ansible variables associated with a host (hid)."""
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
