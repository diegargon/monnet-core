"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

import sys

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway import mgateway_config
from shared.mconfig import load_config, validate_db_config
from shared.app_context import AppContext

def init_context(base_dir):
    """
    Initialize the application context and database connection.
    """
    try:
        # Load configuration
        config_data = load_config(mgateway_config.CONFIG_DB_PATH)
        validate_db_config(config_data)
    except (RuntimeError, ValueError) as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize application context
    ctx = AppContext(base_dir)

    # Initialize database connection
    try:
        db = DBManager(config_data)
        ctx.set_database(db)
    except RuntimeError as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

    return ctx
