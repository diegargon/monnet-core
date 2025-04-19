"""
Weekly task to perform periodic updates, such as updating host details.
"""

from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.networking.net_utils import get_hostname, get_mac, get_org_from_mac

class WeeklyTask:
    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.host_service = HostService(ctx)

    def run(self):
        self.logger.info("Starting WeeklyTask...")
        hosts = self.host_service.get_all()

        for host in hosts:
            updated = False

            # Update hostname if missing
            if not host.get("hostname"):
                hostname = get_hostname(host["ip"])
                if hostname:
                    host["hostname"] = hostname
                    updated = True

            # Update MAC if missing
            if "misc" in host and not host["misc"].get("mac"):
                mac = get_mac(host["ip"])
                if mac:
                    host["misc"]["mac"] = mac
                    updated = True

            # Update MAC vendor if missing
            if "misc" in host:
                mac = host["misc"].get("mac")
                if mac and not host["misc"].get("mac_vendor"):
                    mac_vendor = get_org_from_mac(mac)
                    if mac_vendor:
                        host["misc"]["mac_vendor"] = mac_vendor
                        updated = True

            # Save updates to the database
            if updated:
                self.host_service.update(host["id"], host)

        self.logger.info("WeeklyTask completed.")
