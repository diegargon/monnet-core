"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

# Std
import ipaddress
from pathlib import Path
from pprint import pprint
import sys
from time import time

# Local

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.database.networks_model import NetworksModel
from monnet_gateway.networking.gw_net_utils import get_mac, get_org_from_mac, get_hostname
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.services.network_scanner import NetworkScanner
from monnet_gateway.tests_cli.common_cli import init_context
from monnet_shared.time_utils import utc_date_now
from monnet_shared.clogger import Logger

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting discovery CLI", "info")
    config = ctx.get_config()
    db = DBManager(ctx.get_config())
    start_time = time()  # Start timing

    networks_model = NetworksModel(db)
    network_scanner = NetworkScanner(ctx)
    hosts_model = HostsModel(db)
    host_service = HostService(ctx)
    logger = Logger()

    networks = networks_model.get_all()

    # Real Discovery Test
    ip_list = network_scanner.get_discovery_ips(networks_model, hosts_model)

    # Fake IP List Discover Test
    #ip_list = [
    #    "192.168.1.1",
    #]

    discovery_host = []

    for ip in ip_list:
        # print(f"Scanning {ip}...")
        if ip is None:
            logger.warning(f"IP not found in discovery")
            continue
        ping_status = network_scanner.ping(ip, 0.3)

        if (ping_status.get("online") == 1):
            if 'latency' in ping_status:
                ping_status['latency'] = round(ping_status.get("latency"), 3)

            ping_status['last_check'] = utc_date_now()

            mac_result = get_mac(ip)
            host_data = {
                "ip": ip,
                "last_check": ping_status.get("last_check"),
                "online": 1,
                "network": 1, # default
                "warn": 1, # New host discovery
                "misc": {
                    "latency": ping_status.get("latency"),
                },
            }
            # Set default as name for network default 1
            network_name = 'default'

            if mac_result is not None:
                host_data["mac"] = mac_result
                organization = get_org_from_mac(mac_result)
                if organization:
                    if "misc" not in host_data:
                        host_data["misc"] = {}
                    host_data["misc"]["mac_vendor"] = organization
            try:
                host_ip = ipaddress.IPv4Address(ip)
            except ipaddress.AddressValueError:
                logger.warning(f"Invalid IP address: {ip}")
                continue

            for network in networks:
                try:
                    network_cidr = ipaddress.IPv4Network(network.get("network"), strict=False)
                except ipaddress.AddressValueError:
                    logger.warning(f"Invalid CIDR notation: {network.get('network')}")
                    continue
                if host_ip in network_cidr:
                    network_name = network.get("name")
                    host_data["network"] = network.get("id")
                    break

            hostname = get_hostname(str(host_ip))
            if hostname:
                host_data["hostname"] = hostname
            discovery_host.append(host_data)

    try:
        insert_ids = host_service.add_hosts(discovery_host)
    except ValueError as e:
        print(f"Error inserting discovery hosts: {e}")

    try:
        config.update_db_key("discovery_last_run", utc_date_now())
    except Exception as e:
        print(f"Error updating discovery_last_run: {e}")

    print(f"Scanned: ", len(ip_list))
    print(f"Discovery hosts: ",  len(discovery_host) )
    pprint(discovery_host)
    end_time = time()
    print(f"Total scan time: {round(end_time - start_time, 2)} seconds")
