"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

"""

import time
from typing import List, Dict, Any
# Local
import monnet_agent.agent_config as agent_config
from monnet_shared.app_context import AppContext
from monnet_shared.log_level import LogLevel
from monnet_shared.event_type import EventType

class EventProcessor:
    """
        Event Processor. Process and track the events to avoid spamming
    """
    def __init__(self, ctx: AppContext):
        """
        Initializes the event processor.
        """
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()

        # Dict  processed events with time stamp
        self.processed_events: Dict[str, float] = {}

        # Used to track the start time of events, to avoid alert if the event
        # is still active after the THRESHOLD_DURATION
        self.event_start_times: Dict[str, float] = {}
        self.event_expiration = agent_config.EVENT_EXPIRATION
        self.threshold_duration = agent_config.THRESHOLD_DURATION

    def process_changes(self, datastore) -> List[Dict[str, Any]]:
        """
        Processes changes in the datastore.
        Returns a list of events that have not been sent recently or have expired.
        """
        events = []
        current_time = time.time()
        config = self.config

        # Thresholds
        disks_alert_threshold = config.get("disks_alert_threshold", agent_config.DFLT_ALERT_THRESHOLD)
        disks_warn_threshold = config.get("disks_warn_threshold", agent_config.DFLT_WARN_THRESHOLD)
        mem_alert_threshold = config.get("mem_alert_threshold", agent_config.DFLT_ALERT_THRESHOLD)
        mem_warn_threshold = config.get("mem_warn_threshold", agent_config.DFLT_WARN_THRESHOLD)

        # Event > Iowait threshold
        iowait = datastore.get_data("last_iowait")
        if iowait is not None and iowait > agent_config.DFLT_WARN_THRESHOLD:
            event_id = "high_io_delay"
            if event_id not in self.event_start_times:
                self.event_start_times[event_id] = current_time
            elif current_time - self.event_start_times[event_id] >= self.threshold_duration:
                if iowait > agent_config.DFLT_ALERT_THRESHOLD:
                    log_level = LogLevel.ALERT
                else:
                    log_level = LogLevel.WARNING
                event_type = EventType.HIGH_IOWAIT

                if self._should_send_event(event_id, current_time):
                    events.append({
                        "name": "high_iowait",
                        "data": {
                            "iowait": iowait,
                            "event_value": iowait,
                            "log_level": log_level,
                            "event_type": event_type
                        }
                    })
                    self._mark_event(event_id, current_time)
        else:
            # If the iowait is below the threshold, remove the event start time
            self.event_start_times.pop("high_io_delay", None)

        # Event: > Load avg threshold
        load_avg = datastore.get_data("last_load_avg")
        # logpo("Load avg", load_avg, "debug")
        if load_avg and "loadavg" in load_avg:
            loadavg_data = load_avg["loadavg"]
            if (
                loadavg_data.get("usage") is not None
                and loadavg_data.get("usage") > agent_config.DFLT_WARN_THRESHOLD
            ):
                event_id = "high_cpu_usage"
                if event_id not in self.event_start_times:
                    self.event_start_times[event_id] = current_time
                elif current_time - self.event_start_times[event_id] >= self.threshold_duration:
                    if loadavg_data.get("usage") > agent_config.DFLT_ALERT_THRESHOLD:
                        log_level = LogLevel.ALERT
                    else:
                        log_level = LogLevel.WARNING
                    event_type = EventType.HIGH_CPU_USAGE

                    if self._should_send_event(event_id, current_time):
                        events.append({
                            "name": "high_cpu_usage",
                            "data": {
                                "cpu_usage": loadavg_data["usage"],
                                "event_value": loadavg_data.get("usage"),
                                "log_level": log_level,
                                "event_type": event_type
                            }
                        })
                        self._mark_event(event_id, current_time)
            else:
                # If the CPU usage is below the threshold, remove the event start time
                self.event_start_times.pop("high_cpu_usage", None)

        # Event: > Memory threshold
        memory_info = datastore.get_data("last_memory_info")
        # logpo("Memory info", memory_info, "debug")
        if memory_info and "meminfo" in memory_info:
            meminfo_data = memory_info["meminfo"]
            if meminfo_data["percent"] > mem_warn_threshold:
                event_id = "high_memory_usage"
                if event_id not in self.event_start_times:
                    self.event_start_times[event_id] = current_time
                elif current_time - self.event_start_times[event_id] >= self.threshold_duration:
                    if meminfo_data["percent"] > mem_alert_threshold:
                        log_level = LogLevel.ALERT
                    else:
                        log_level = LogLevel.WARNING
                    event_type = EventType.HIGH_MEMORY_USAGE

                    if self._should_send_event(event_id, current_time):
                        events.append({
                            "name": "high_memory_usage",
                            "data": {
                                "memory_usage": meminfo_data,
                                "event_value": meminfo_data["percent"],
                                "log_level": log_level,
                                "event_type": event_type
                            }
                        })
                        self._mark_event(event_id, current_time)
            else:
                # If the memory usage is below the threshold, remove the event start time
                self.event_start_times.pop("high_memory_usage", None)

        # Event: Disk threshold
        disk_info = datastore.get_data("last_disk_info")
        if isinstance(disk_info, dict) and "disksinfo" in disk_info:
            for stats in disk_info["disksinfo"]:
                if isinstance(stats, dict):
                    if stats.get("percent") and stats["percent"] > disks_warn_threshold:
                        event_id = f"high_disk_usage_{stats.get('device', 'unknown')}"
                        if event_id not in self.event_start_times:
                            self.event_start_times[event_id] = current_time
                        elif current_time - self.event_start_times[event_id] >= self.threshold_duration:
                            if stats["percent"] > disks_alert_threshold:
                                log_level = LogLevel.ALERT
                            else:
                                log_level = LogLevel.WARNING

                            event_type = EventType.HIGH_DISK_USAGE

                            if self._should_send_event(event_id, current_time):
                                events.append({
                                    "name": "high_disk_usage",
                                    "data": {
                                        "disks_stats": stats,
                                        "event_value": stats["percent"],
                                        "log_level": log_level,
                                        "event_type": event_type
                                    }
                                })
                                self._mark_event(event_id, current_time)
                    else:
                        # If the disk usage is below the threshold, remove the event start time
                        self.event_start_times.pop(f"high_disk_usage_{stats.get('device', 'unknown')}", None)
        else:
            self.logger.error(f"Unexpected structure in disk info: {type(disk_info)} -> {disk_info}")
        # Cleanup processed_events
        self._cleanup_events(current_time)

        return events

    def _should_send_event(self, event_id: str, current_time: float) -> bool:
        """
        Verify if we should send the event (time mark)
        """
        last_time = self.processed_events.get(event_id)
        return last_time is None or (current_time - last_time > self.event_expiration)

    def _mark_event(self, event_id: str, current_time: float):
        """
        Mark event, update time
        """
        self.processed_events[event_id] = current_time

    def _cleanup_events(self, current_time: float):
        """
        Clean old events
        """
        self.processed_events = {
            event_id: timestamp
            for event_id, timestamp in self.processed_events.items()
            if current_time - timestamp <= self.event_expiration * 2
        }
