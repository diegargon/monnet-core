"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet

"""

from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway import config
from shared.logger import log
from shared.mconfig import load_config, validate_db_config
from shared.app_context import AppContext


if __name__ == "__main__":
    log("Init monnet linux agent", "info")
    # Cargar la configuracion desde el archivo
    config = load_config(config.CONFIG_DB_PATH)
    if not config:
        log("Cant load config. Finishing", "err")
        exit(1)
    try:
        validate_db_config(config)
    except ValueError as e:
        log(str(e), "err")
        exit(1)

    ctx = AppContext("/opt/monnet-core")

    # Iniciar la conexión solo una vez y almacenarla en el contexto
    try:
        db_instance = DBManager(config)
        ctx.set_database(db_instance)
    except RuntimeError as e:
        print(f"Database connection error: {e}")

    # Example obtain and use instance
    db_instance = ctx.get_database()

    if db_instance:
        try:
            users = db_instance.fetchall("SELECT * FROM users")
            print(users)
        except RuntimeError as e:
            print(f"Database query error: {e}")
    else:
        print("Database connection is not available")
