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
        if not hosts:
            self.logger.info("No hosts found.")
            return

        for host in hosts:
            updated = False
            hid = host.get("id")
            if not hid:
                self.logger.error("Host ID is missing.")
                continue
            # Update hostname if missing
            if not host.get("hostname") and host.get("ip") is not None:
                hostname = get_hostname(host.get("ip"))
                if hostname is not None and isinstance(hostname, str):
                    host["hostname"] = hostname
                    updated = True

            # Update MAC if missing
            if not host.get("mac") and host.get("ip") is not None:
                mac = get_mac(host["ip"])
                if mac is not None and isinstance(mac, str):
                    host["mac"] = mac
                    updated = True

            # Update MAC vendor if missing

            if mac is not None and isinstance(mac, str):
                mac = host.get("mac")
                # Asegurarse de que 'misc' sea un diccionario
                if not isinstance(host.get("misc"), dict):
                    host["misc"] = {}

                # Verificar si 'mac_vendor' está ausente
                if not host.get("misc", {}).get("mac_vendor"):
                    mac_vendor = get_org_from_mac(mac)
                    if mac_vendor is not None and isinstance(mac_vendor, str):
                        host["misc"]["mac_vendor"] = mac_vendor
                        updated = True

            # Save updates to the database
            if updated:
                #self.logger.info(f"Updating host {host}")
                # Update the host in the database
                self.host_service.update(hid, host)

        self.logger.info("WeeklyTask completed.")
