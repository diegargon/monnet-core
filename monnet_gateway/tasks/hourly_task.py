"""
Hourly task to perform periodic updates, such as refreshing host statuses.
"""

from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.networking.gw_net_utils import is_local_ip

class HourlyTask:
    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.host_service = HostService(ctx)

    def run(self):
        self.logger.info("Starting HourlyTask...")
        hosts = self.host_service.get_all()
        if not hosts:
            self.logger.info("No hosts found.")
            return

        for host in hosts:
            updated = False
            hid = host.get("id")
            mac = host.get("mac")
            ip = host.get("ip")
            if not hid:
                self.logger.error("Host ID is missing. HourlyTask cannot continue.")
                continue

            # Si el campo mac está vacío o es None, poner mac_check a 1
            # Solo si la IP es local/privada
            if is_local_ip(ip):
                if not mac:
                    if host.get("mac_check") != 1:
                        host["mac_check"] = 1
                        updated = True

            if updated:
                self.logger.debug(f"Updating host {host}")
                try:
                    self.host_service.update(hid, host)
                except ValueError as e:
                    self.logger.error(f"Validation error updating host {hid}: {e}")
                except Exception as e:
                    self.logger.error(f"Failed to update host {hid} in hourly tasks: {e}")
                    continue

        self.logger.info("HourlyTask completed.")
