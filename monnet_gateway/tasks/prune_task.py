"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Prune Task

"""

from monnet_gateway.database.dbmanager import DBManager
from shared.app_context import AppContext

class PruneTask:
    """Class to perform periodic cleanup tasks."""
    def __init__(self, ctx: AppContext):
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config)

    def run(self):
        """Executes the cleanup task."""
        self.logger.info("Running PruneTask...")
        try:
            self.clear_stats()
            self.clear_system_logs()
            self.clear_hosts_logs()
            self.clear_reports()
            self.db.commit()
            self.db.close()
        except Exception as e:
            self.logger.error(f"Error during PruneTask: {e}")

    def clear_stats(self):
        """Cleans up old statistics."""
        interval = self.config.get("clear_stats_intvl", 30)  # Default to 30 days
        query = "DELETE FROM stats WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear stats, affected rows: {affected}")

    def clear_system_logs(self):
        """Cleans up old system logs."""
        interval = self.config.get("clear_logs_intvl", 30)  # Default to 30 days
        query = "DELETE FROM system_logs WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear system logs, affected rows: {affected}")

    def clear_hosts_logs(self):
        """Cleans up old host logs."""
        interval = self.config.get("clear_logs_intvl", 30)  # Default to 30 days
        query = "DELETE FROM hosts_logs WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear host logs, affected rows: {affected}")

    def clear_reports(self):
        """Cleans up old reports."""
        interval = self.config.get("clear_reports_intvl", 30)  # Default to 30 days
        query = "DELETE FROM reports WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear reports, affected rows: {affected}")
