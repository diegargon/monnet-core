"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.services.network_scanner import NetworkScanner


class HostScanner:
    """
    HostScanner class to manage host scanning
    """

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        db = ctx.get_database()
        self.hosts_model = HostsModel(db)
        self.network_scanner = NetworkScanner(ctx)

    def scanKnown(self):
        """
        Scan a host
        """
        self.logger.log("Scanning known hosts...", "info")
        all_hosts = self.hosts_model.get_all_enabled()
        if not all_hosts:
            self.logger.log("No hosts found to scan.", "info")
            return

        ip_status = []

        for host in all_hosts:
            ip = host['ip']
            ping_result = self.network_scanner.ping(ip, timeout={'sec': 1, 'usec': 200000})
            ip_status.append(ping_result)

        return ip_status