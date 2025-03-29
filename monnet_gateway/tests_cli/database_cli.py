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
from shared.mconfig import load_config, validate_db_config
from shared.app_context import AppContext


if __name__ == "__main__":
    print("Loading Configuration")
    try:
        # Cargar la configuracion desde el archivo
        config = load_config(config.CONFIG_DB_PATH)
    except RuntimeError as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    if not config:
        print("Cant load config. Finishing")
        sys.exit(1)

    try:
        validate_db_config(config)
    except ValueError as e:
        print(f"Configuration validation error: {e}")
        sys.exit(1)

    ctx = AppContext("/opt/monnet-core")

    # Iniciar la conexión solo una vez y almacenarla en el contexto
    try:
        db = DBManager(config)
        ctx.set_database(db)
    except RuntimeError as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

    # Example obtain and use instance
    db = ctx.get_database()

    if db:
        try:
            users = db.fetchall("SELECT * FROM users")
            print(users)
        except RuntimeError as e:
            print(f"Database query error: {e}")
    else:
        print("Database connection is not available")


