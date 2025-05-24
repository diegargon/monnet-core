"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Config file
"""

GW_VERSION = "0.15"
GW_VERSION_MINOR = 46
GW_F_VERSION =  str(GW_VERSION) + "." + str(GW_VERSION_MINOR)

HOST = 'localhost'
PORT = 65432
PORT_TEST = 65433
GW_CONFIG_PATH = "/etc/monnet/mgateway-config"
CONFIG_DB_PATH = "/etc/monnet/config-db.json"

ALLOWED_MODULES = ["ansible",]

DEFAULT_ANSIBLE_GROUPS_FILE = "/etc/ansible/hosts"
