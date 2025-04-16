"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Config file
"""

VERSION = "0.6"
MINOR_VERSION = 3
HOST = 'localhost'
PORT = 65432
PORT_TEST = 65433
CONFIG_MGATEWAY_PATH = "/etc/monnet/mgateway-config"
CONFIG_DB_PATH = "/etc/monnet/config-db.json"

TASK_INTERVAL = 10  # Seconds
ALLOWED_MODULES = ["ansible",]
