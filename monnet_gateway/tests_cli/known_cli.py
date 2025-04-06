"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""
# Std
from pathlib import Path
import sys
from time import sleep
from time import time  # Add this import for timing

# Local

from monnet_gateway.tests_cli.common_cli import init_context
from monnet_gateway.services.host_scanner import HostScanner


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting discovery CLI", "info")

    start_time = time()  # Start timing

    host_scanner = HostScanner(ctx)

    hosts_status = host_scanner.scanKnown()

    count_offline = 0
    for host_stat in hosts_status:
        if host_stat['online'] == 0:
            count_offline += 1
        print(host_stat)

    end_time = time()
    print(f"Scanned: ", len(hosts_status), "Offline: ", count_offline)
    print(f"Total scan time: {round(end_time - start_time, 2)} seconds")
