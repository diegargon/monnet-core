"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""
# Local
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.services.hosts_service import HostService
from monnet_gateway.tests_cli.common_cli import init_context


print("Init monnet hosts test CLI")
ctx = init_context("/opt/monnet-core")
db = DBManager(ctx.get_config())

host_service = HostService(ctx)

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
