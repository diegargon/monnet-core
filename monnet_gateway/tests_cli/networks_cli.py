"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet

"""

# Std
from pathlib import Path
import sys

from monnet_gateway.utils.myutils import pprint_table

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.database.networks_model import NetworksModel
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway import config
from shared.mconfig import load_config, validate_db_config
from shared.app_context import AppContext


if __name__ == "__main__":
    print("Loading Configuration")
    # Cargar la configuracion desde el archivo
    config = load_config(config.CONFIG_DB_PATH)
    if not config:
        print("Cant load config. Finishing")
        sys.exit(1)
    try:
        validate_db_config(config)
    except ValueError as e:
        print(str(e))
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

    networks = NetworksModel(db)
    try:
        all_networks = networks.get_all()

        pprint_table(all_networks)
    except RuntimeError as e:
        print(f"Database query error: {e}")


