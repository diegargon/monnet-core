"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Prune Task

"""

from monnet_gateway.database.dbmanager import DBManager
from shared.app_context import AppContext
from monnet_gateway.services.hosts_service import HostService

class PruneTask:
    """Class to perform periodic cleanup tasks."""
    def __init__(self, ctx: AppContext):
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = None
        self.host_service = HostService(ctx)

    def run(self):
        """Executes the cleanup task."""
        self.logger.info("Running PruneTask...")
        try:
            if not self.db or self.db is not isinstance(self.db, DBManager):
                self.db = DBManager(self.config)
            with self.db.transaction():
                self.clear_stats()
                self.clear_system_logs()
                self.clear_hosts_logs()
                self.clear_reports()
                self.clear_not_seen_hosts()
        except Exception as e:
            self.logger.error(f"Error during PruneTask: {e}")
        finally:
            self.db.close()
    def clear_stats(self):
        """Cleans up old statistics."""
        interval = self.config.get("clear_stats_intvl", 30)  # Default to 30 days
        if (interval <= 0):
            return
        query = "DELETE FROM stats WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear stats, affected rows: {affected}")

    def clear_system_logs(self):
        """Cleans up old system logs."""
        interval = self.config.get("clear_logs_intvl", 30)  # Default to 30 days
        if (interval <= 0):
            return
        query = "DELETE FROM system_logs WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear system logs, affected rows: {affected}")

    def clear_hosts_logs(self):
        """Cleans up old host logs."""
        interval = self.config.get("clear_logs_intvl", 30)  # Default to 30 days
        if (interval <= 0):
            return
        query = "DELETE FROM hosts_logs WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear host logs, affected rows: {affected}")

    def clear_reports(self):
        """Cleans up old reports."""
        interval = self.config.get("clear_reports_intvl", 30)  # Default to 30 days
        if (interval <= 0):
            return
        query = "DELETE FROM reports WHERE date < DATE_SUB(CURDATE(), INTERVAL %s DAY)"
        affected = self.db.execute(query, (interval,))
        self.logger.info(f"Clear reports, affected rows: {affected}")

    #def clear_not_seen_hosts(self):
    #    """Cleans up hosts not seen for a specified number of days."""
    #    days = self.config.get("clear_not_seen_hosts_intvl", 30)  # Default to 30 days
    #    if days <= 0:
    #        return
    #    affected = self.host_service.clear_not_seen_hosts(days)
    #    self.logger.info(f"Cleared {affected} hosts not seen for more than {days} days.")
