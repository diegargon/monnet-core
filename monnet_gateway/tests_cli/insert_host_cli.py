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
    # Cargar la configuracion desde el archivo
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
    "ip": "192.168.100.100",
    "last_seen": "2025-04-15 12:00:00",
    "online": 1,
    "network": 1,
    "warn": 1,
    "misc": {
        "latency": 0.777,
        "mac_vendor": "test vendor",
    },
}

try:
    host_id = host_service.add_host(host_data)
    print(f"Host insertado con ID: {host_id}")
except ValueError as e:
    print(f"Error al agregar el host: {e}")