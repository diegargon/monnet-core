"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Service
"""

from datetime import datetime
from monnet_gateway.database.ansible_model import AnsibleModel

class AnsibleService:
    """Service layer for interacting with AnsibleModel."""

    def __init__(self, ansible_model: AnsibleModel):
        self.ansible_model = ansible_model

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
        # TODO vtype password decrypt
        return self.ansible_model.fetch_ansible_vars_by_hid(hid)
