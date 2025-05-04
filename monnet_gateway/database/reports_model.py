"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Reports Model
@description: This module is responsible for managing the reports in the database.

"""

from monnet_gateway.database.dbmanager import DBManager

class ReportsModel:
    def __init__(self, db: DBManager):
        self.db = db

    def save_report(self, report_data: dict):
        """
        Save a report into the reports table.

        Args:
            report_data (dict): The report data to save.
        """
        query = """
            INSERT INTO reports (host_id, pid, pb_id, source_id, rtype, report)
            VALUES (%(host_id)s, %(pid)s, %(pb_id)s, %(source_id)s, %(rtype)s, %(report)s)
        """
        self.db.execute(query, report_data)

    def commit(self):
        """
        Commit the current transaction.
        """
        self.db.commit()
    def rollback(self):
        """
        Rollback the current transaction.
        """
        self.db.rollback()
