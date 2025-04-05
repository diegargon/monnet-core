"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

# Std
from pathlib import Path
import sys
from time import sleep

# Local
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.services.network_scanner import NetworkScanner
from monnet_gateway.utils.myutils import pprint_table
from monnet_gateway.tests_cli.common_cli import init_context
from shared.time_utils import utc_date_now

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.database.networks_model import NetworksModel

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting discovery CLI", "info")

    networks_model = NetworksModel(ctx.get_database())
    network_scanner = NetworkScanner(ctx, networks_model)
    host_model = HostsModel(ctx.get_database())

    ip_list = network_scanner.get_discovery_ips(host_model)

#    ping_status = network_scanner.ping('192.168.2.126')
#    print(ping_status)

    for ip in ip_list:
        # print(f"Scanning {ip}...")
        ping_status = network_scanner.ping(ip)

        if (ping_status['online'] == 1):
            if 'latency' in ping_status:
                ping_status['latency'] = round(ping_status['latency'], 3)
            ping_status['last_seen'] = utc_date_now()
            print(ip, ping_status)

    print(f"Scanned: ", len(ip_list))
