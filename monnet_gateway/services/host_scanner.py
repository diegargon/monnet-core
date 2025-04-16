"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

from pprint import pprint
from time import sleep
from monnet_gateway.services.network_scanner import NetworkScanner


class HostScanner:
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
            ping_result = self.network_scanner.ping(ip, timeout)
            ping_result["id"] = host["id"]
            ping_result["used_timeout"] = timeout
            if "retries" in host:
                ping_result["retries"] = host["retries"] + 1
            else:
                ping_result["retries"] = 0

            ip_status.append(ping_result)
            sleep(0.1)

        return ip_status
