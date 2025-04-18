"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Hosts Scanner

"""
# Std
from datetime import datetime, timezone
from pprint import pprint
from time import sleep
from collections import defaultdict

# Local
from monnet_gateway.database.ports_model import PortsModel
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.services.network_scanner import NetworkScanner
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.utils.myutils import pprint_table

class HostsScanner:
    """
    HostScanner class to manage host scanning
    """

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.network_scanner = NetworkScanner(ctx)
        self.db = ctx.get_database()
        hosts_model = HostsModel(self.db)
        self.ports_model = PortsModel(self.db)
        self.hosts_service = HostService(ctx, hosts_model)

    def scan_hosts(self, all_hosts: dict):
        """
        Scan a list of hosts
        """
        self.logger.log("Scanning known hosts...", "info")

        if not all_hosts:
            self.logger.log("No hosts found to scan.", "notice")
            return []

        ip_status = []

        now_utc = datetime.now(timezone.utc)
        f_now_utc = now_utc.strftime('%Y-%m-%d %H:%M:%S')

        for host in all_hosts:
            ip_or_host = host['ip']
            check_method = host.get("check_method", 1)
            self.logger.debug(f"Scanning ip {ip_or_host}")
            if "misc" in host and isinstance(host["misc"], dict) and "timeout" in host["misc"]:
                try:
                    timeout = float(host["misc"]["timeout"])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid timeout value for host {ip_or_host}, using default 0.3")
                    timeout = 0.3
            else:
                timeout = 0.3

            if  "disable_ping" in host and host["disable_ping"] == 1 and check_method == 1:
                continue

            # If host agent is installed and host its online skip ping
            if host["online"] == 1 and "agent_installed" in host and host["agent_installed"]:
                continue

            self.logger.debug(f"Check method {check_method}")

            if check_method == 1:  # Ping
                scan_result = {
                    "id": host["id"],
                    "ip": host["ip"],
                    "host": ip_or_host,
                    "online": 0,
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
                host_ports = self.ports_model.get_by_hid(host["id"], scan_type=1)

                for host_port in host_ports:
                    protocol = host_port.get("protocol")
                    pnumber = host_port.get("pnumber")
                    scan_result = {
                        "id": host["id"],
                        "ip": host["ip"],
                        "port_id": host_port["id"],
                        "online": 0,
                        "check_method": check_method,
                        "port": pnumber,
                        "last_check": f_now_utc,
                        "error": None
                    }

                    self.logger.debug(f"Protocol {protocol}")
                    # For http/s check using hostname
                    if "hostname" in host and host["hostname"] and protocol > 3:
                        ip_or_host = scan_result["host"] = host["hostname"]
                    else:
                        ip_or_host = scan_result["host"] = host["ip"]

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
                        scan_result["retries"] = host["retries"] + 1
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
            if "change" in host_status and host_status["change"] == 1:
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

    def update_hosts(self, hosts_status: list[dict]):
        """
        Prepara los datos para actualizar el estado de los hosts y puertos.
        """
        host_updates = defaultdict(lambda: {"online": 0, "misc": {"latency": 0}})
        port_updates = []

        for host_status in hosts_status:
            host_id = host_status["id"]

            if "port" in host_status:
                port_online = host_status.get("online", 0)
                port_latency = host_status.get("latency")

                if port_online == 1:
                    host_updates[host_id]["online"] = 1
                    current_latency = host_updates[host_id]["misc"]["latency"]
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
        # Actualizar la base de datos

        for host_id, set_host in host_updates.items():
            print(f"ID: {host_id}")
            pprint(set_host)
            self.hosts_service.update(host_id, set_host)

        if port_updates:
            pprint(port_updates)
            self.ports_model.update_ports(port_updates)
