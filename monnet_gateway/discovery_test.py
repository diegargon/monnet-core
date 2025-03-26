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

    try:
        with DBManager(config) as db:
            # Fetch all users
            users = db.fetchall("SELECT * FROM users")
            print(users)

            # Insert a new user within a transaction
            #with db.transaction():
            #    rows_affected = db.execute("INSERT INTO users (username, password) VALUES (%s, %s)", ("John Doe", "test"))
            #    print(f"Rows inserted: {rows_affected}")
    except RuntimeError as e:
        print(e)