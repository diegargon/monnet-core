"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

from pprint import pprint
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
        Scan a host
        """
        self.logger.log("Scanning known hosts...", "info")

        if not all_hosts:
            self.logger.log("No hosts found to scan.", "info")
            return []

        ip_status = []

        for host in all_hosts:
            ip = host['ip']
            ping_result = self.network_scanner.ping(ip, timeout=0.3)
            ping_result["id"] = host["id"]
            ip_status.append(ping_result)

        return ip_status
