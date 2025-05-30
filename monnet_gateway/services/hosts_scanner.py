"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Hosts Scanner

"""
# Std
from datetime import datetime, timezone
from time import sleep
from collections import defaultdict

# Local
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.stats_model import StatsModel
from monnet_gateway.services.network_scanner import NetworkScanner
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.services.ports_service import PortsService
from monnet_gateway.networking.net_utils import get_mac

class HostsScanner:
    """
    HostScanner class to manage host scanning
    """

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.network_scanner = NetworkScanner(ctx)
        self.db = DBManager(ctx.get_config().file_config)
        self.ports_service = PortsService(ctx)
        self.hosts_service = HostService(ctx)
        self.stats_model = StatsModel(self.db)

    def scan_hosts(self, all_hosts: dict):
        """
        Scan a list of hosts.
        """

        if not all_hosts:
            self.logger.notice("No hosts found to scan.")
            return []
        if not isinstance(all_hosts, list):
            self.logger.warning("Invalid list of known hosts.")
            return []

        ip_status = []

        now_utc = datetime.now(timezone.utc)
        f_now_utc = now_utc.strftime('%Y-%m-%d %H:%M:%S')

        for host in all_hosts:
            if not host:
                continue

            id = host.get("id")
            if not id or not isinstance(id, int):
                self.logger.warning(f"Scan host wrong ID.")
                continue

            ip_or_host = host.get("ip")
            if not ip_or_host:
                self.logger.warning(f"Host id {id} has no IP or domain address.")
                continue

            check_method = host.get("check_method", 1)
            #self.logger.debug(f"Scanning ip {ip_or_host}")
            if "misc" in host and isinstance(host["misc"], dict) and "timeout" in host["misc"]:
                try:
                    timeout = float(host.get("misc").get("timeout"))
                except (ValueError, TypeError):
                    self.logger.notice(f"Invalid timeout value for host {ip_or_host}, using default 0.3")
                    timeout = 0.3
            else:
                timeout = 0.3

            if  "disable_ping" in host and host["disable_ping"] == 1 and check_method == 1:
                continue

            # If host agent is installed and host its online skip ping TODO: Review this we need latency
            if host.get("online") == 1 and host.get("misc", {}).get("agent_installed") == 1:
                continue

            #self.logger.debug(f"Check method {check_method}")

            if check_method == 1:  # Ping
                scan_result = {
                    "id": host["id"],
                    "ip": host["ip"],
                    "host": ip_or_host,
                    "online": 0,
                    "prev_online": host.get("online", 0),
                    "check_method": check_method,
                    "last_check": f_now_utc
                }
                if "hostname" in host:
                    scan_result["hostname"] = host["hostname"]

                ping_result = self.network_scanner.ping(ip_or_host, timeout)
                scan_result.update(ping_result)

                if "retries" in host:
                    scan_result["retries"] = host["retries"] + 1
                else:
                    scan_result["retries"] = 0

                ip_status.append(scan_result)

            elif check_method == 2:  # Ports
                id = host.get("id")

                if not id or not isinstance(id, int):
                    self.logger.warning(f"Scan host (ports) wrong ID.")
                    continue

                host_ports = self.ports_service.get_host_ports(id, scan_type=1)

                for host_port in host_ports:
                    protocol = host_port.get("protocol")
                    pnumber = host_port.get("pnumber")
                    scan_result = {
                        "id": id,
                        "ip": host["ip"],
                        "port_id": host_port.get("id"),
                        "online": 0,
                        "prev_online": host.get("online", 0),
                        "check_method": check_method,
                        "port": pnumber,
                        "last_check": f_now_utc,
                        "error": None
                    }

                    #self.logger.debug(f"Protocol {protocol}")
                    # For http/s check using hostname
                    if "hostname" in host and host["hostname"] and protocol > 3:
                        ip_or_host = scan_result["host"] = host.get("hostname")
                    else:
                        ip_or_host = scan_result["host"] = host.get("ip")

                    if not ip_or_host:
                        self.logger.warning(f"Host id {id} has no IP or Domain address.")
                        continue

                    if protocol == 1:                   # TCP Port
                        port_result = self.network_scanner.check_tcp_port(ip_or_host, pnumber, timeout)
                    elif protocol == 2:                 # UDP Port
                        port_result = self.network_scanner.check_udp_port(ip_or_host, pnumber, timeout)
                    elif protocol == 3:                 # HTTPS
                        port_result = self.network_scanner.check_https(ip_or_host, pnumber, timeout, verify_ssl=True)
                    elif protocol == 4:                 # HTTPS Self-Signed
                        port_result = self.network_scanner.check_https(ip_or_host, pnumber, timeout, verify_ssl=False)
                    elif protocol == 5:                 # HTTP
                        port_result = self.network_scanner.check_http(ip_or_host, pnumber, timeout)
                    else:
                        self.logger.warning(f"Unknown protocol:port {protocol}:{pnumber} for host {ip_or_host}, skipping.")
                        continue
                    scan_result.update(port_result)

                    if "retries" in host:
                        scan_result["retries"] = host.get("retries") + 1
                    else:
                        scan_result["retries"] = 0

                    ip_status.append(scan_result)
                    sleep(0.1)
            else:
                self.logger.warning(f"Unknown check method for host {host}, skipping.")
                continue

            sleep(0.1)

        return ip_status

    def retry_scan(self, hosts_status: list[dict], retries: int) -> None:
        for host_status in hosts_status:
            if "change" in host_status and host_status.get("change") == 1:
                for attempt in range(1, retries + 1):
                    host_status_retry_result = self.scan_hosts([host_status])
                    if not host_status_retry_result:
                        continue
                    # Get first element since return a list
                    new_host_status = host_status_retry_result[0]
                    host_status["retries"] = new_host_status.get("retries", 1)
                    if new_host_status["online"] == 1:
                        host_status["online"] = 1
                        host_status["latency"] = new_host_status.get("latency")
                        break
                    sleep(0.2)

    def pre_update_hosts(self, hosts_status: list[dict]):
        """
        Prepare data to update the status of hosts and ports.
        """
        host_updates = defaultdict(lambda: {"online": 0, "misc": {"latency": 0}})
        port_updates = []
        stats_updates = {}

        now_utc = datetime.now(timezone.utc)
        f_now_utc = now_utc.strftime('%Y-%m-%d %H:%M:%S')

        for host_status in hosts_status:
            host_id = host_status.get("id")
            if not host_id or not isinstance(host_id, int):
                self.logger.warning(f"Host status wrong ID.")
                continue

            # Makes sure host_status have misc dict
            if not "misc" in host_status:
                host_status["misc"] = {}

            if "port" in host_status:
                port_online = host_status.get("online", 0)
                port_latency = host_status.get("latency")
                if port_online == 1:
                    host_updates[host_id]["online"] = 1
                    current_latency = host_updates[host_id].get("misc", {}).get("latency")
                    if port_latency is not None and (current_latency is None or port_latency < current_latency):
                        host_updates[host_id]["latency"] = port_latency

                port_updates.append({
                    "id": host_status.get("port_id"),
                    "online": port_online,
                    "latency": port_latency,
                    "last_check": host_status.get("last_check")
                })
            else:
                host_updates[host_id]["online"] = host_status.get("online", 0)


            host_updates[host_id]["misc"]["latency"] = host_status.get("latency")
            host_updates[host_id]["last_check"] = host_status.get("last_check")

            # Si pasa de offline a online, intenta obtener la MAC siempre, y solo actualiza si es diferente
            if host_updates[host_id]["online"] == 1:
                prev_online = host_status.get("prev_online", None)
                if prev_online == 0 or prev_online is None:
                    ip = host_status.get("ip")
                    mac_actual = host_status.get("mac")
                    if ip:
                        mac_result = get_mac(ip)
                        if mac_result and isinstance(mac_result, str):
                            if mac_result != mac_actual:
                                host_updates[host_id]["mac"] = mac_result
                        else:
                            host_updates[host_id]["mac_check"] = 1  # Marcar para chequeo posterior
                host_updates[host_id]["last_seen"] = f_now_utc

            # Stats update
            stats_updates[host_id] = {
                "type": 1,
                "host_id": host_id,
                "value": host_status.get("latency"),
                "date": host_status.get("last_check")
            }


        for host_id, set_host in host_updates.items():
            self.hosts_service.update(host_id, set_host)

        if port_updates:
            self.ports_service.update_ports(port_updates)

        if stats_updates:
            # self.logger.debug(f"stats_updates: {stats_updates}");
            # Convert stats_updates to a list of dictionaries
            stats_data = list(stats_updates.values())
            self.stats_model.update_stats_bulk(stats_data)
