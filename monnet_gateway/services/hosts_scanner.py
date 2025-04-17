"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Hosts Scanner

"""
# Std
from time import sleep

# Local
from monnet_gateway.database.ports_model import PortsModel
from monnet_gateway.services.network_scanner import NetworkScanner

class HostsScanner:
    """
    HostScanner class to manage host scanning
    """

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.network_scanner = NetworkScanner(ctx)
        self.db = ctx.get_database()
        self.ports_model = PortsModel(self.db)

    def scan_hosts(self, all_hosts: dict):
        """
        Scan a list of hosts
        """
        self.logger.log("Scanning known hosts...", "info")

        if not all_hosts:
            self.logger.log("No hosts found to scan.", "notice")
            return []

        ip_status = []

        for host in all_hosts:
            ip = host['ip']
            check_method = host.get("check_method", 1)
            self.logger.debug(f"Scanning ip {ip}")
            if "misc" in host and isinstance(host["misc"], dict) and "timeout" in host["misc"]:
                try:
                    timeout = float(host["misc"]["timeout"])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid timeout value for host {host['ip']}, using default 0.3")
                    timeout = 0.3
            else:
                timeout = 0.3
            self.logger.log(f"Check method {check_method}")


            if check_method == 1:  # Ping
                scan_result = {"id": host["id"], "ip": ip, "online": 0, "check_method": check_method}
                ping_result = self.network_scanner.ping(ip, timeout)
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
                        "ip": ip,
                        "online": 0,
                        "check_method": check_method,
                        "port": pnumber,
                        "error": None
                    }

                    if protocol == 1:                   # TCP Port
                        port_result = self.network_scanner.check_tcp_port(ip, pnumber, timeout)
                    elif protocol == 2:                 # UDP Port
                        port_result = self.network_scanner.check_udp_port(ip, pnumber, timeout)
                    elif protocol == 3:                 # HTTPS
                        port_result = self.network_scanner.check_https(ip, pnumber, timeout, verify_ssl=True)
                    elif protocol == 4:                 # HTTPS Self-Signed
                        port_result = self.network_scanner.check_https(ip, pnumber, timeout, verify_ssl=False)
                    elif protocol == 5:                 # HTTP
                        port_result = self.network_scanner.check_http(ip, pnumber, timeout)
                    else:
                        self.logger.warning(f"Unknown protocol:port {protocol}:{pnumber} for host {ip}, skipping.")
                        continue
                    scan_result.update(port_result)
                    ip_status.append(scan_result)
                    sleep(0.1)
            else:
                self.logger.warning(f"Unknown check method for host {ip}, skipping.")
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
                    if new_host_status["online"] == 1:
                        host_status["online"] = 1
                        host_status["retries"] = new_host_status.get("retries", 0)
                        host_status["latency"] = new_host_status.get("latency")
                        break
                    host_status["retries"] = new_host_status.get("retries", 0)
                    sleep(0.2)
