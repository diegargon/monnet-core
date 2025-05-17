"""
Monnet Gateway - Test DB Config
"""

from monnet_gateway.mgateway_config import CONFIG_DB_PATH
from monnet_shared.config import DBConfig
from monnet_gateway.tests_cli.common_cli import init_context

ctx = init_context("/opt/monnet-core")
ctx.get_logger().log("Starting test_config CLI", "info")

# Initialize Config
if ctx.has_config():
    config = ctx.get_config()
else:
    config = DBConfig(ctx, CONFIG_DB_PATH)

# Print all file-based configuration values
ctx.get_logger().log("Loaded file-based configuration values:", "info")
for key, value in config.file_config.items():
    print(f"File Config - {key}: {value}")

# Print all database-based configuration values
ctx.get_logger().log("Loaded database-based configuration values:", "info")
for key, value in config.db_config.items():
    print(f"DB Config - {key}: {value}")

print("**** TESTING CONFIGURATION KEYS ****")
# Test updating a file-based configuration key
try:
    config.update_file_key("test_file_key", "test_file_value", create_key=True)
    print(f"Updated file-based config: test_file_key = {config.get('test_file_key')}")
except Exception as e:
    print(f"Failed to update file-based config: {e}")


# Test updating a database-based configuration key
try:
    config.update_db_key("test_db_key", "test_db_value", create_key=True)
    print(f"Updated database config: test_db_key = {config.get('test_db_key')}")
except Exception as e:
    print(f"Failed to update database config: {e}")

# DO NOT TEST THIS - Need ctype check for update a nested key
# Test updating a database-based configuration key with a nested structure
#try:
#    config.update_db_key("test_db_key", {"nested": "value"})
#    print(f"Updated database config: test_db_key = {config.get('test_db_key')}")
#except Exception as e:
#    print(f"Failed to update database config: {e}")

