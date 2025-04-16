"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""
# Std
from pathlib import Path
from pprint import pprint
import sys
from time import sleep
from time import time  # Add this import for timing

# Local
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.tests_cli.common_cli import init_context
from monnet_gateway.services.host_scanner import HostScanner
from monnet_gateway.utils.myutils import pprint_table

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting discovery CLI", "info")
    retries = 4

    start_time = time()  # Start timing

    host_scanner = HostScanner(ctx)
    hosts_model = HostsModel(ctx.get_database())
    hosts_service = HostService(ctx, hosts_model)
    all_hosts = hosts_service.get_all()

    hosts_status = host_scanner.scan_hosts(all_hosts)

    count_offline = 0
    for host_stat in hosts_status:
        if host_stat['online'] == 0:
            count_offline += 1

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


    for host_status in hosts_status:
        if "change" in host_status and host_status["change"] == 1:
            for attempt in range(1, retries + 1):
                # Get first element since return a list
                new_host_status = host_scanner.scan_hosts([host_status])[0]
                if new_host_status["online"] == 1:
                    host_status["online"] = 1
                    host_status["retries"] = new_host_status["retries"]
                    host_status["latency"] = new_host_status["latency"]
                    break
                host_status["retries"] = new_host_status["retries"]
                sleep(0.5)

    hosts_online = []
    hosts_offline = []

    for host_status in hosts_status:
        if host_status["online"] == 1:
            hosts_online.append(host_status)
        else:
            hosts_offline.append(host_status)

    pprint_table(hosts_online)
    pprint_table(hosts_offline)

    end_time = time()
    total_host = len(hosts_status)
    print(f"Scanned: ", total_host, "Online: ", total_host - count_offline,  "Offline: ", count_offline)
    print(f"Total scan time: {round(end_time - start_time, 2)} seconds")
