"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet

"""

# Std
from pathlib import Path
from pprint import pprint
import sys

from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.utils.myutils import pprint_table

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway import config
from shared.mconfig import load_config, validate_db_config
from shared.app_context import AppContext


if __name__ == "__main__":
    print("Init monnet linux agent")
    # Cargar la configuracion desde el archivo
    try:
        config = load_config(config.CONFIG_DB_PATH)
        validate_db_config(config)
    except (RuntimeError, ValueError) as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    ctx = AppContext("/opt/monnet-core")

    # Iniciar la conexión solo una vez y almacenarla en el contexto
    try:
        db = DBManager(config)
    except RuntimeError as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

    if not db:
        print("Database connection is not available")
        exit(1)

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


