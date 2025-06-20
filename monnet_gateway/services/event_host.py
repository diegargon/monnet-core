"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Event Log Service

"""
from datetime import datetime
from monnet_shared.log_level import LogLevel
from monnet_shared.log_type import LogType
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.event_host_model import EventHostModel
from monnet_shared.app_context import AppContext

class EventHostService:
    def __init__(self, ctx: AppContext):
        """
        Initialize EventLogService with a database manager and logger.

        Args:
            db_manager: Database manager instance.
            logger: Logger instance.
        """
        self.ctx = ctx
        self.db = DBManager(ctx.get_config().file_config)
        self.logger = ctx.get_logger()
        self.event_host_model = EventHostModel(self.db)
        self.hostService = None

    def _ensure_connection(self):
        if not self.db.is_connected():
            self.logger.warning("EventHostService: DB connection lost. Reconnecting...")
            self.db.close()
            self.db = DBManager(self.ctx.get_config().file_config)
            self.event_host_model = EventHostModel(self.db)

    def event(
        self,
        host_id: int,
        msg: str,
        log_type: int = 0,
        event_type: int = 0,
        reference: str = None
    ) -> None:
        """
        Log a host event.

        Args:
            host_id (int): Host ID.
            msg (str): Log message.
            log_type (int): Log type. Defaults to 0.
            event_type (int): Event type. Defaults to 0.
            reference (str): Optional reference for the event.
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

        utc_now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        log_data = {
            "host_id": host_id,
            "level": log_level,
            "msg": msg_db,
            "log_type": log_type,
            "event_type": event_type,
            "date": utc_now,
            "reference": reference if reference else None
        }

        self._ensure_connection()
        try:
            self.event_host_model.insert_event(log_data)
            self.event_host_model.commit()
        except Exception as e:
            self.logger.error(f"Failed to log event for Host ID {host_id}: {e}")
