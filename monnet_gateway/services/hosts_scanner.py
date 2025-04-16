"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Hosts Scanner

"""

from time import sleep
from monnet_gateway.services.network_scanner import NetworkScanner


class HostsScanner:
    """
    HostScanner class to manage host scanning
    """

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.network_scanner = NetworkScanner(ctx)

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
            self.logger.debug(f"Scanning ip {ip}")
            if "misc" in host and isinstance(host["misc"], dict) and "timeout" in host["misc"]:
                try:
                    timeout = float(host["misc"]["timeout"])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid timeout value for host {host['ip']}, using default 0.3")
                    timeout = 0.3
            else:
                timeout = 0.3
            scan_result = self.network_scanner.ping(ip, timeout)
            scan_result["check_method"] = host.get("check_method", 1)
            scan_result["id"] = host["id"]
            scan_result["used_timeout"] = timeout
            if "retries" in host:
                scan_result["retries"] = host["retries"] + 1
            else:
                scan_result["retries"] = 0

            ip_status.append(scan_result)
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