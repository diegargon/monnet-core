"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Scan known host CLI TEST

"""
# Std
from pathlib import Path
from pprint import pprint
import sys
from time import time

# Local
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.tests_cli.common_cli import init_context
from monnet_gateway.services.hosts_scanner import HostsScanner
from monnet_gateway.utils.myutils import pprint_table
from monnet_shared.time_utils import utc_date_now

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting discovery CLI", "info")
    config = ctx.get_config()
    retries = 3

    start_time = time()  # Start timing

    hosts_scanner = HostsScanner(ctx)
    hosts_service = HostService(ctx)
    all_hosts = hosts_service.get_all()

    if not all_hosts:
        sys.exit()

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

    hosts_online = []
    hosts_offline = []
    count_offline = 0

    for host_status in hosts_status:
        if host_status["online"] == 1:
            hosts_online.append(host_status)
        else:
            hosts_offline.append(host_status)
            count_offline += 1
    """
    if hosts_online:
        pprint_table(hosts_online)
    if hosts_offline:
        pprint_table(hosts_offline)
    """
    hosts_scanner.preup_hosts(hosts_status)

    try:
        config.update_db_key("cli_last_run", utc_date_now())
    except Exception as e:
        print(f"Error updating cli_last_run: {e}")

    end_time = time()
    total_host = len(hosts_status)
    print(f"Scanned: ", total_host, "Online: ", total_host - count_offline,  "Offline: ", count_offline)
    print(f"Total scan time: {round(end_time - start_time, 2)} seconds")
