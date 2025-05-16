"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

import sys

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway import mgateway_config
from monnet_shared.clogger import Logger
from monnet_shared.app_context import AppContext
from monnet_shared.config import Config

def init_context(base_dir):
    """
    Initialize the application context
    """
    # Initialize application context
    ctx = AppContext(base_dir)
    clogger = Logger()
    ctx.set_logger(clogger)

    # Initialize Config and load configurations
    try:
        config = Config(ctx, mgateway_config.CONFIG_DB_PATH)
        ctx.set_config(config)
    except (RuntimeError, ValueError) as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    return ctx
