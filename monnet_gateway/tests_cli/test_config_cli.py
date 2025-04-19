"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Test DB Config
"""

from monnet_gateway.services.config import Config
from monnet_gateway.tests_cli.common_cli import init_context


ctx = init_context("/opt/monnet-core")
ctx.get_logger().log("Starting test_config CLI", "info")


config = Config(ctx)
config.load_db_config()


for key in config.config.keys():
    value = config.get(key)
    print(f"{key}: {value}")

