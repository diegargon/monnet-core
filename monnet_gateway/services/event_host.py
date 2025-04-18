"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Event Log Service

"""

from constants.log_level import LogLevel
from constants.log_type import LogType
from monnet_gateway.database.event_host_model import EventHostModel
from shared.app_context import AppContext
from shared.clogger import Logger

class EventHostService:
    def __init__(self, ctx: AppContext):
        """
        Initialize EventLogService with a database manager and logger.

        Args:
            db_manager: Database manager instance.
            logger: Logger instance.
        """
        self.db = ctx.get_database()
        self.logger = ctx.get_logger()
        self.event_host_model = EventHostModel(self.db)

    def event(
        self,
        host_id: int,
        msg: str,
        log_type: int = 0,
        event_type: int = 0
    ) -> None:
        """
        Log a host event.

        Args:
            host_id (int): Host ID.
            msg (str): Log message.
            log_type (int): Log type. Defaults to 0.
            event_type (int): Event type. Defaults to 0.
        """
        max_db_msg = 254
        if len(msg) > max_db_msg:
            self.logger.warning(f"Log message too long (Host ID: {host_id})")
            msg_db = msg[:max_db_msg]
        else:
            msg_db = msg

        if  log_type == LogType.EVENT_WARN:
            log_level = LogLevel.WARNING
        elif log_type == LogType.EVENT_ALERT:
            log_level = LogLevel.ALERT
        else:
            log_level = LogLevel.NOTICE

        log_data = {
            "host_id": host_id,
            "level": log_level,
            "msg": msg_db,
            "log_type": log_type,
            "event_type": event_type
        }

        try:
            self.event_host_model.insert_event(log_data)
            self.event_host_model.commit()
        except Exception as e:
            self.logger.error(f"Failed to log event for Host ID {host_id}: {e}")
