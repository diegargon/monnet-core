"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Check Known Hosts

"""

from time import time
from monnet_gateway.services.hosts_scanner import HostsScanner
from monnet_gateway.services.hosts_service import HostService
from monnet_shared.app_context import AppContext
from monnet_shared.time_utils import utc_date_now

class HostsCheckerTask:
    """ Verify known hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()

    def run(self):
        self.logger.debug("Running known host checker...")
        retries = 3
        start_time = time()

        hosts_scanner = HostsScanner(self.ctx)
        hosts_service = HostService(self.ctx)
        all_hosts = hosts_service.get_all()

        if not all_hosts:
            self.logger.warning("No hosts to check.")
            return

        if not isinstance(all_hosts, list):
            self.logger.warning("Invalid list of known hosts.")
            return

        self.logger.debug("Scanning known hosts...")
        hosts_status = hosts_scanner.scan_hosts(all_hosts)

        # Mark host that become off for retry
        for previous_host in all_hosts:
            for current_host in hosts_status:
                if (
                    previous_host["ip"] == current_host["ip"]
                    and previous_host["online"] == 1
                    and current_host["online"] == 0
                ):
                    current_host["change"] = 1
                    current_host["retries"] = 0

        hosts_scanner.retry_scan(hosts_status, retries)

        count_offline = 0
        for host_status in hosts_status:
            if "online" not in host_status:
                self.logger.warning(f"Host status missing 'online' key: {host_status}")
                continue
            if not host_status["online"]:
                count_offline += 1

        hosts_scanner.preup_hosts(hosts_status)

        try:
            self.config.update_db_key("cli_last_run", utc_date_now())
        except KeyError as e:
            self.logger.error(f"KeyError updating cli_last_run: {e}")
        except AttributeError as e:
            self.logger.error(f"AttributeError updating cli_last_run: {e}")
        except Exception as e:
            self.logger.error(f"Error updating cli_last_run: {e}")

        end_time = time()
        total_host = len(hosts_status)
        self.logger.debug(f"Scanned: {total_host} Online: {total_host - count_offline} Offline: {count_offline}")
        self.logger.debug(f"Total scan time: {round(end_time - start_time, 2)} seconds")
