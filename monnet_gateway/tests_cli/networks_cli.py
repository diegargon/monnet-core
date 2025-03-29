"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

# Std
from pathlib import Path
import sys

from monnet_gateway.utils.myutils import pprint_table
from monnet_gateway.tests_cli.common_cli import init_context, init_database, initialize_context, initialize_database

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.database.networks_model import NetworksModel

if __name__ == "__main__":
    print("Loading Configuration")
    ctx = init_context("/opt/monnet-core")
    db = ctx.get_database()

    networks = NetworksModel(db)
    try:
        all_networks = networks.get_all()

        pprint_table(all_networks)
    except RuntimeError as e:
        print(f"Database query error: {e}")
