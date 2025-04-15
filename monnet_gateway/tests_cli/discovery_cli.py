"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

# Std
import ipaddress
from pathlib import Path
from pprint import pprint
import sys
from time import sleep
from time import time

# Local
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.networking.net_utils import get_mac, get_org_from_mac, get_hostname
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.services.network_scanner import NetworkScanner
from monnet_gateway.tests_cli.common_cli import init_context
from shared.time_utils import utc_date_now
from shared.clogger import Logger
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.database.networks_model import NetworksModel

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting discovery CLI", "info")

    start_time = time()  # Start timing

    networks_model = NetworksModel(ctx.get_database())
    network_scanner = NetworkScanner(ctx)
    host_model = HostsModel(ctx.get_database())
    host_service = HostService(ctx, host_model)

    logger = Logger()

    networks = networks_model.get_all()

    ip_list = network_scanner.get_discovery_ips(networks_model, host_model)
    #ip_list = [
    #    "192.168.1.1",
    #    "192.168.2.126",
    #    "192.168.2.200",
    #]
#    ping_status = network_scanner.ping('192.168.2.126')
#    print(ping_status)

    discovery_host = []

    for ip in ip_list:
        # print(f"Scanning {ip}...")
        ping_status = network_scanner.ping(ip, 0.3)

        if (ping_status['online'] == 1):
            if 'latency' in ping_status:
                ping_status['latency'] = round(ping_status['latency'], 3)

            ping_status['last_seen'] = utc_date_now()
            mac_result = get_mac(ping_status["ip"])
            host_data = {
                "ip": ping_status["ip"],
                "last_seen": ping_status["last_seen"],
                "online": 1,
                "network": 1, # default
                "warn": 1, # New host discovery
                "misc": {
                    "latency": ping_status["latency"],
                },
            }
            if mac_result is not None:
                host_data["mac"] = mac_result
                organization = get_org_from_mac(mac_result)
                if organization:
                    host_data["misc"]["mac_vendor"] = organization

            host_ip = ipaddress.IPv4Address(ping_status["ip"])
            for network in networks:
                network_cidr = ipaddress.IPv4Network(network["network"], strict=False)
                if host_ip in network_cidr:
                    logger.debug(f"Ip discovery {host_ip} added to network {network['network']}")
                    host_data["network"] = network["id"]
                    break

            if host_data["network"] == 1:
                logger.warning(f"Ip discovery {host_ip} not match any network, added to default")
            hostname = get_hostname(str(host_ip))
            if hostname:
                host_data["hostname"] = hostname
            discovery_host.append(host_data)
        sleep(0.1)

    print(f"Scanned: ", len(ip_list))
    print(f"Discovery hosts: ",  len(discovery_host) )
    pprint(discovery_host)
    end_time = time()
    print(f"Total scan time: {round(end_time - start_time, 2)} seconds")
