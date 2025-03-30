"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

Tasks
    check_listen_ports
    send_stats

"""

# Standard
import threading

# Local
import info_linux
import monnet_agent.agent_config as agent_config
from monnet_agent.datastore import Datastore
from shared.app_context import AppContext

def check_listen_ports(ctx: AppContext, datastore: Datastore, notify_callback, startup=None):
    """
        Send port changes. Startup force send update every agent start/restart
    """
    logger = ctx.get_logger()
    logger.debug("Checking listen ports triggered")
    try:
        if 'check_ports' in agent_config.timers:
            agent_config.timers['check_ports'].cancel()

        current_listen_ports_info = info_linux.get_listen_ports_info()
        last_listen_ports_info = datastore.get_data("last_listen_ports_info")

        # Calculate differences
        added_ports = set(current_listen_ports_info) - set(last_listen_ports_info or [])
        removed_ports = set(last_listen_ports_info or []) - set(current_listen_ports_info)
        port_differences = {
            "added": list(added_ports),
            "removed": list(removed_ports)
        }

        # Trigger notification if there are differences
        if (added_ports or removed_ports or startup):
            logger.debug(f"Port differences: {port_differences} Statup {startup}")
            datastore.update_data("last_listen_ports_info", current_listen_ports_info)
            notify_callback(ctx, "listen_ports_info", current_listen_ports_info)  # Pass ctx to callback
        #else : #debug
        #    notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar
    except Exception as e:
        logger.error(f"Error in check_listen_ports: {e}")  # Log error instead of raising
    finally:
        agent_config.timers['check_ports'] = threading.Timer(
            agent_config.TIMER_STATS_INTERVAL,
            check_listen_ports,
            args=(ctx, datastore, notify_callback)
        )
        agent_config.timers['check_ports'].start()


def send_stats(ctx: AppContext, datastore, notify_callback):
    """
        Send stats every TIME_STATS_INTERVAL
    """
    logger = ctx.get_logger()
    logger.debug("Sending stats triggered")

    try:
        if 'send_stats' in agent_config.timers:
            agent_config.timers['send_stats'].cancel()

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
    finally:
        # Start again
        agent_config.timers['send_stats'] = threading.Timer(
            agent_config.TIMER_STATS_INTERVAL,
            send_stats,
            args=(ctx, datastore, notify_callback)  # Ensure ctx is passed here
        )
        agent_config.timers['send_stats'].start()
