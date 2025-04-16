"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

import sys

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway import mgateway_config
from shared.mconfig import load_config
from shared.app_context import AppContext

try:
    mgateway_config = load_config(mgateway_config.CONFIG_DB_PATH)
except RuntimeError as e:
    print(f"Error loading configuration: {e}")
    sys.exit(1)


ctx = AppContext("/opt/monnet-core")

db_manager = DBManager(mgateway_config)
ctx.set_database(db_manager)
hosts_model = HostsModel(db_manager)
host_service = HostService(ctx, hosts_model)

host_data = {
    "last_seen": "2025-04-15 12:00:00",
    "online": 0,
    "misc": {
        "latency": 0.777,
    },
}

try:
    host_service.update(199, host_data)

except ValueError as e:
    print(f"Error al actualizar el host: {e}")
