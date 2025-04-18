"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Event Log Service

"""

from monnet_gateway.database.event_host_model import EventHostModel
from shared.clogger import Logger

class EventHostService:
    def __init__(self, db_manager, logger: Logger):
        """
        Initialize EventLogService with a database manager and logger.

        Args:
            db_manager: Database manager instance.
            logger: Logger instance.
        """
        self.event_host_model = EventHostModel(db_manager)
        self.logger = logger

    def event_host(
        self,
        log_level: int,
        host_id: int,
        msg: str,
        log_type: int = 0,
        event_type: int = 0
    ) -> None:
        """
        Log a host event.

        Args:
            log_level (int): Log level.
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

        log_data = {
            "host_id": host_id,
            "level": log_level,
            "msg": msg_db,
            "log_type": log_type,
            "event_type": event_type
        }
        self.event_host_model.insert_event(log_data)
