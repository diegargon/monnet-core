"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent
"""

# Standard
import threading

# Local
from monnet_agent import agent_globals
import info_linux
from monnet_agent.datastore import Datastore

#from shared.log_linux import log, logpo


def check_listen_ports(datastore: Datastore, notify_callback, startup=None):
    """

        Send port changes. Startup force send update every agent start/restart

    """
    if 'check_ports' in agent_globals.timers:
        agent_globals.timers['check_ports'].cancel()

    current_listen_ports_info = info_linux.get_listen_ports_info()
    last_listen_ports_info = datastore.get_data("last_listen_ports_info")

    if ((current_listen_ports_info != last_listen_ports_info) or startup):
        datastore.update_data("last_listen_ports_info", current_listen_ports_info)
        notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar
    #else : #debug
    #    notify_callback("listen_ports_info", current_listen_ports_info)  # Notificar

    agent_globals.timers['check_ports']  = threading.Timer(
        agent_globals.TIMER_STATS_INTERVAL,
        check_listen_ports,
        args=(datastore, notify_callback)
    )
    agent_globals.timers['check_ports'].start()


def send_stats(datastore, notify_callback):
    """
        Send stats every TIME_STATS_INTERVAL
    """
    if 'send_stats' in agent_globals.timers :
        agent_globals.timers['send_stats'].cancel()

    data = {}

    # Load
    last_avg_stats = datastore.get_data("last_load_avg")
    if last_avg_stats is not None :
        data['load_avg_stats'] = last_avg_stats['loadavg']

    # Io wait
    iowait_last_stats = datastore.get_data("iowait_last_stats")
    if not iowait_last_stats:
        iowait_last_stats = datastore.get_data("last_iowait")
    last_iowait = datastore.get_data("last_iowait")
    average_iowait =  (iowait_last_stats + last_iowait) / 2
    datastore.update_data("iowait_last_stats", last_iowait)
    data['iowait_stats'] = average_iowait

    # Send
    notify_callback('send_stats', data)

    # Start again
    agent_globals.timers['send_stats']  = threading.Timer(
        agent_globals.TIMER_STATS_INTERVAL,
        send_stats,
        args=(datastore, notify_callback)
    )
    agent_globals.timers['send_stats'].start()
