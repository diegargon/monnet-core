"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Model
@description: This module encapsulates the database model for Ansible tasks.

"""

from datetime import datetime
from monnet_gateway.database.dbmanager import DBManager

class AnsibleModel:
    """
    Encapsulates queries related to Ansible tasks.

    The `ansible_vars` table structure:
    - `id` (Primary, int, AUTO_INCREMENT): Unique identifier for each variable.
    - `hid` (Index, int): Host ID associated with the variable.
    - `vtype` (tinyint): Type of the variable (1 for encrypted values, 2 for strings).
    - `vkey` (Index, varchar(255)): Key or name of the variable.
    - `vvalue` (varchar(700)): Value of the variable.

    The `tasks` table structure:
    - `id` (Primary, int, AUTO_INCREMENT): Unique identifier for each task.
    - `task_name` (varchar(255)): Name of the task.
    - `task_interval` (varchar(255)): Interval for the task execution.
    - `trigger_type` (tinyint): Type of trigger (1 for cron, 2 for interval, etc.).
    - `disable` (tinyint): Indicates if the task is disabled (0 for active, 1 for inactive).
    - `last_triggered` (datetime): Timestamp of the last execution.
    - `next_trigger` (datetime): Timestamp of the next scheduled
    - `done` int (task done for uniq task)
    """

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

    def fetch_playbook_vars_by_hid(self, hid: int):
        """
        Fetches Ansible variables associated with a host (hid).

        Args:
            hid (int): The host ID for which to fetch Ansible variables.

        Returns:
            list: A list of tuples containing `vtype`, `vkey`, and `vvalue` for the specified host.
        """
        query = "SELECT vtype, vkey, vvalue FROM ansible_vars WHERE hid = %s"
        return self.db.fetchall(query, (hid,))

    def is_connected(self):
        """
        Check if the database connection is active.
        Returns:
            bool: True if the connection is active, False otherwise.
        """
        return self.db.is_connected()

    def task_done(self, task_id: int):
        """
        Increments the 'done' field of a task by 1.

        Args:
            task_id (int): The ID of the task to update.
        """
        query = "UPDATE tasks SET done = done + 1 WHERE id = %s"
        with self.db.transaction():
            self.db.execute(query, (task_id,))

