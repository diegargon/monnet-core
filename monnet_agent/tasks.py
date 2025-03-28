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
import monnet_agent.agent_globals as agent_globals
from monnet_agent.datastore import Datastore

from shared.logger import log

def check_listen_ports(config: dict, datastore: Datastore, notify_callback, startup=None):
    """

        Send port changes. Startup force send update every agent start/restart

    """

    try:
        if 'check_ports' in agent_globals.timers:
            agent_globals.timers['check_ports'].cancel()

        current_listen_ports_info = info_linux.get_listen_ports_info()
        last_listen_ports_info = datastore.get_data("last_listen_ports_info")

        if ((current_listen_ports_info != last_listen_ports_info) or startup):
            datastore.update_data("last_listen_ports_info", current_listen_ports_info)
            notify_callback(config, "listen_ports_info", current_listen_ports_info)  # Notificar
        #else : #debug
        #    notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar
    except Exception as e:
        log(f"Error in check_listen_ports: {e}", "err")
    finally:
        agent_globals.timers['check_ports']  = threading.Timer(
            agent_globals.TIMER_STATS_INTERVAL,
            check_listen_ports,
            args=(config, datastore, notify_callback)
        )
        agent_globals.timers['check_ports'].start()


def send_stats(config, datastore, notify_callback):
    """
        Send stats every TIME_STATS_INTERVAL
    """
    try:
        if 'send_stats' in agent_globals.timers :
            agent_globals.timers['send_stats'].cancel()

        data = {}

        # Load
        last_avg_stats = datastore.get_data("last_load_avg")
        if last_avg_stats is not None and 'loadavg' in last_avg_stats:
            data['load_avg_stats'] = last_avg_stats['loadavg']

        # Io wait
        iowait_last_stats = datastore.get_data("iowait_last_stats")
        if not iowait_last_stats:
            iowait_last_stats = datastore.get_data("last_iowait")
        last_iowait = datastore.get_data("last_iowait")
        average_iowait =  (iowait_last_stats + last_iowait) / 2
        datastore.update_data("iowait_last_stats", last_iowait)
        data['iowait_stats'] = average_iowait

        # Memory
        last_memory_stats = datastore.get_data("last_memory_stats")
        if not last_memory_stats:
            last_memory_stats = datastore.get_data("last_memory_info")
        last_memory_info = datastore.get_data("last_memory_info")
        average_memory_percent = (
            last_memory_stats['meminfo']['percent'] +
            last_memory_info['meminfo']['percent']) / 2
        datastore.update_data("last_memory_stats", last_memory_stats)
        data['memory_stats'] = round(average_memory_percent)

        # Send
        notify_callback(config, 'send_stats', data)
    except Exception as e:
        log(f"Error in send_status: {e}", "err")
    finally:
        # Start again
        agent_globals.timers['send_stats']  = threading.Timer(
            agent_globals.TIMER_STATS_INTERVAL,
            send_stats,
            args=(config, datastore, notify_callback)
        )
        agent_globals.timers['send_stats'].start()
