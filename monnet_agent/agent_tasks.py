"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Tasks Implementation
"""

import info_linux
from monnet_agent.datastore import Datastore
from monnet_shared.app_context import AppContext

def check_listen_ports(ctx: AppContext, datastore: Datastore, notify_callback, startup=None):
    """
        Send port changes. Startup force send update every agent start/restart
    """
    logger = ctx.get_logger()
    logger.debug("Checking listen ports triggered")
    try:
        # Get current and last port data
        current_data = info_linux.get_listen_ports_info()
        last_data = datastore.get_data("last_listen_ports_info") or {}

        # Debug: Log raw data before comparison
        logger.debug(f"Current data: {current_data}")
        logger.debug(f"Last data: {last_data}")


        # Normalize data structure
        current_ports = current_data.get('listen_ports_info', [])
        last_ports = last_data.get('listen_ports_info', [])

        # Create comparable items using key fields
        def get_port_key(port_info):
            """Create a unique key for each port"""
            return (
                port_info.get('interface'),
                port_info.get('port'),
                port_info.get('protocol'),
                port_info.get('ip_version')
            )

        # Build mappings for comparison
        current_map = {get_port_key(p): p for p in current_ports}
        last_map = {get_port_key(p): p for p in last_ports}

        # Find differences
        added_ports = [current_map[key] for key in current_map.keys() - last_map.keys()]
        removed_ports = [last_map[key] for key in last_map.keys() - current_map.keys()]
        modified_ports = [
            current_map[key]
            for key in current_map.keys() & last_map.keys()
            if current_map[key] != last_map[key]
        ]

        # Debug logging
        logger.debug(f"Added ports details: {added_ports}")
        logger.debug(f"Removed ports details: {removed_ports}")
        logger.debug(f"Modified ports details: {modified_ports}")

        # Trigger notification if there are differences
        if added_ports or removed_ports or modified_ports or startup:
            logger.info("Port changes detected, updating storage and notifying")
            datastore.update_data("last_listen_ports_info", current_data)
            notify_callback(ctx, "listen_ports_info", current_data)
    except KeyError as e:
        logger.error(f"Missing expected port field: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in port check: {e}", exc_info=True)

def send_stats(ctx: AppContext, datastore, notify_callback):
    """
        Send stats every TIME_STATS_INTERVAL
    """
    logger = ctx.get_logger()
    logger.debug("Sending stats triggered")

    try:
        data = {}

        # Load
        last_avg_stats = datastore.get_data("last_load_avg")
        if last_avg_stats and 'loadavg' in last_avg_stats:
            data['load_avg_stats'] = last_avg_stats['loadavg']

        # Io wait
        iowait_last_stats = datastore.get_data("iowait_last_stats")
        if not iowait_last_stats:
            iowait_last_stats = datastore.get_data("last_iowait")
        last_iowait = datastore.get_data("last_iowait")

        if iowait_last_stats is not None and last_iowait is not None:
            average_iowait = (iowait_last_stats + last_iowait) / 2
            datastore.update_data("iowait_last_stats", last_iowait)
            data['iowait_stats'] = average_iowait
        else:
            logger.warning("Missing iowait stats data for calculation")

        # Memory
        last_memory_stats = datastore.get_data("last_memory_stats")
        if not last_memory_stats:
            last_memory_stats = datastore.get_data("last_memory_info")
        last_memory_info = datastore.get_data("last_memory_info")

        if (
            last_memory_stats and last_memory_info and
            last_memory_stats.get('meminfo', {}).get('percent') is not None and
            last_memory_info.get('meminfo', {}).get('percent') is not None
        ):
            average_memory_percent = (
                last_memory_stats['meminfo']['percent'] +
                last_memory_info['meminfo']['percent']
            ) / 2
            datastore.update_data("last_memory_stats", last_memory_stats)
            data['memory_stats'] = round(average_memory_percent)
        else:
            logger.warning("Missing memory stats data for calculation")

        # Send
        notify_callback(ctx, 'send_stats', data)
    except Exception as e:
        logger.error(f"Error in send_stats: {e}")  # Log error instead of raising

def hourly_task(ctx: AppContext, datastore, notify_callback):
    """
    Tarea programada para ejecutarse cada hora.
    """
    logger = ctx.get_logger()
    logger.debug("hourly_task triggered")
    try:
        import info_linux
        data = {}
        try:
            uptime = info_linux.get_uptime()
            if uptime is not None:
                data['uptime'] = uptime
        except Exception as e:
            logger.warning(f"Could not get uptime: {e}")

        if data:
            notify_callback(ctx, "scheduler_update", data)
            logger.debug("hourly_task: scheduler_update sent")

    except Exception as e:
        logger.error(f"Error in hourly_task: {e}")

def daily_task(ctx: AppContext, datastore, notify_callback):
    """
    Tarea programada para ejecutarse diariamente.
    """
    pass
