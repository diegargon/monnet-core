"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Model

"""

from datetime import datetime
from monnet_gateway.database.dbmanager import DBManager

class AnsibleModel:
    """Encapsulates queries related to Ansible tasks."""

    def __init__(self, db: DBManager):
        self.db = db

    def fetch_active_tasks(self):
        """Fetches all active tasks (disable = 0)."""
        return self.db.fetchall("SELECT * FROM tasks WHERE disable = 0")

    def delete_task(self, task_id: int):
        """Deletes a task by its ID."""
        with self.db.transaction():
            self.db.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

    def update_task_triggers(self, task_id: int, last_triggered: datetime, next_trigger: datetime = None):
        """Updates the triggers of a task."""
        data = {"last_triggered": last_triggered.strftime("%Y-%m-%d %H:%M:%S")}
        if next_trigger:
            data["next_trigger"] = next_trigger.strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction():
            self.db.update("tasks", data=data, where={"id": task_id})

    def fetch_ansible_vars_by_hid(self, hid: int):
        """Fetches Ansible variables associated with a host (hid)."""
        query = "SELECT vtype, vkey, vvalue FROM ansible_vars WHERE hid = %s"
        return self.db.fetchall(query, (hid,))

