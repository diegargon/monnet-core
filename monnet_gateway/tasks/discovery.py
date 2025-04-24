"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

import ipaddress
from time import sleep, time
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.database.networks_model import NetworksModel
from monnet_gateway.networking.net_utils import get_hostname, get_mac, get_org_from_mac
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.services.network_scanner import NetworkScanner
from shared.app_context import AppContext
from shared.time_utils import utc_date_now

class DiscoveryHostsTask:
    """ Descubrimiento de hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()

    def run(self):
        db = DBManager(self.ctx.get_config())
        start_time = time()

        networks_model = NetworksModel(db)
        network_scanner = NetworkScanner(self.ctx)
        hosts_model = HostsModel(db)
        host_service = HostService(self.ctx)
        networks = networks_model.get_all()

        ip_list = network_scanner.get_discovery_ips(networks_model, hosts_model)

        discovery_host = []

        for ip in ip_list:

            if ip is None:
                self.logger.warning(f"IP not found in discovery")
                continue
            ping_status = network_scanner.ping(ip, 0.3)

            if (ping_status and ping_status.get("online") == 1):
                if 'latency' in ping_status:
                    ping_status['latency'] = round(ping_status.get("latency"), 3)

                ping_status['last_seen'] = utc_date_now()

                mac_result = get_mac(ip)
                host_data = {
                    "ip": ip,
                    "last_seen": ping_status.get("last_seen"),
                    "online": 1,
                    "network": 1,   # default
                    "warn": 1,      # New host discovery
                    "misc": {
                        "latency": ping_status.get("latency"),
                    },
                }
                # Set default as name for network default 1
                network_name = 'default'

                if mac_result and isinstance(mac_result, str):
                    host_data["mac"] = mac_result
                    organization = get_org_from_mac(mac_result)
                    if organization:
                        if "misc" not in host_data:
                            host_data["misc"] = {}
                        host_data["misc"]["mac_vendor"] = organization
                try:
                    host_ip = ipaddress.IPv4Address(ip)
                except ipaddress.AddressValueError:
                    self.logger.warning(f"Invalid IP address: {ip}")
                    continue

                for network in networks:
                    network_cidr = network.get("network", None)
                    if network_cidr is None:
                        self.logger.warning(f"Network CIDR not found for network: {network.get('name')}")
                        continue

                    try:
                        network_cidr = ipaddress.IPv4Network(network.get("network"), strict=False)
                    except ipaddress.AddressValueError:
                        self.logger.warning(f"Invalid CIDR notation: {network_cidr}")
                        continue

                    if host_ip in network_cidr:
                        network_name = network.get("name")
                        host_data["network"] = network.get("id")
                        break

                hostname = get_hostname(str(host_ip))
                if hostname:
                    host_data["hostname"] = hostname
                discovery_host.append(host_data)
                sleep(0.1)

        try:
            host_service.add_hosts(discovery_host)
        except ValueError as e:
            self.logger.error(f"Error inserting discovery hosts: {e}")

        try:
            self.config.update_db_key("discovery_last_run", utc_date_now())
        except KeyError as e:
            self.logger.error(f"KeyError updating discovery_last_run: {e}")
        except AttributeError as e:
            self.logger.error(f"AttributeError updating discovery_last_run: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating discovery_last_run: {e}")

        self.logger.debug(f"Scanned:  {len(ip_list)}")
        self.logger.debug(f"Discovery hosts: {len(discovery_host)}")
        end_time = time()
        self.logger.debug(f"Total scan time {round(end_time - start_time, 2)} seconds")

