"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

import sys

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway import mgateway_config
from shared.clogger import Logger
from shared.app_context import AppContext
from monnet_gateway.services.config import Config

def init_context(base_dir):
    """
    Initialize the application context and database connection.
    """
    # Initialize application context
    ctx = AppContext(base_dir)
    clogger = Logger()
    ctx.set_logger(clogger)

    # Initialize Config and load configurations
    try:
        config = Config(ctx, mgateway_config.CONFIG_DB_PATH)
        config.load_db_config()
        ctx.set_config(config)
    except (RuntimeError, ValueError) as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    return ctx
