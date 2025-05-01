"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Service
"""

import base64
from datetime import datetime
from monnet_gateway.database.ansible_model import AnsibleModel
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