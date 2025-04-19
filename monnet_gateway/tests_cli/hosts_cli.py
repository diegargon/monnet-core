"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

# Std
from pathlib import Path
from pprint import pprint
import sys

from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.tests_cli.common_cli import init_context
from monnet_gateway.utils.myutils import pprint_table

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    print("Init monnet hosts test CLI")
    ctx = init_context("/opt/monnet-core")
    db = ctx.get_database()

    hosts = HostsModel(db)
    try:
        all_hosts = hosts.get_all()

        for host in all_hosts:
            if "misc" in host:
                del host["misc"]
            if "access_results" in host:
                del host["access_results"]
            del host["created"]
            if "fingerprint" in host:
                del host["fingerprint"]

        pprint_table(all_hosts)
    except RuntimeError as e:
        print(f"Database query error: {e}")
