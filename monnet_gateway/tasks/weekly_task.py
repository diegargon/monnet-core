"""
Weekly task to perform periodic updates, such as updating host details.
"""

import ipaddress
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
            ip  = host.get("ip")
            if not hid:
                self.logger.error("Host ID and IP is missing. WeeklyTask cannot continue.")
                continue

            try:
                ipaddress.ip_address(ip)
            except ValueError:
                self.logger.error(f"Invalid IP address {ip} for host {hid}. Skipping...")
                continue

            # Check hostname missing/change
            hostname = get_hostname(ip)
            if hostname is not None and isinstance(hostname, str):
                db_hostname = host.get("hostname", None)
                if db_hostname is None and (db_hostname is None or db_hostname != hostname):
                    host["hostname"] = hostname
                    updated = True

            # Check MAC address missing/change
            mac = get_mac(ip)
            if mac is not None and isinstance(mac, str):
                db_mac = host.get("mac", None)
                if mac is not None and (db_mac is None or db_mac != mac):
                    host["mac"] = mac
                    updated = True

            # Update MAC vendor
            if mac is not None and isinstance(mac, str):
                # Asegurarse de que 'misc' sea un diccionario
                if not isinstance(host.get("misc"), dict):
                    host["misc"] = {}

                mac_vendor = get_org_from_mac(mac)
                if mac_vendor is not None and isinstance(mac_vendor, str):
                    db_mac_vendor = host["misc"].get("mac_vendor", None)
                    if mac_vendor is None and (db_mac_vendor is None or db_mac_vendor != mac_vendor):
                        host["misc"]["mac_vendor"] = mac_vendor
                        updated = True

            # Save updates to the database
            if updated:
                self.logger.debug(f"Updating host {host}")
                # Update the host in the database
                try:
                    self.host_service.update(hid, host)
                except Exception as e:
                    self.logger.error(f"Failed to update host {hid} in weekly tasks: {e}")
                    continue


        self.logger.info("WeeklyTask completed.")
