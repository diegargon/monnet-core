"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent
"""

import json
# Local
from shared.logger import log

def load_config(file_path):
    """Load JSON config"""
    try:
        with open(file_path, "r", encoding='utf-8') as file:
            config = json.load(file)
            config['_config_path'] = file_path
            return config
    except Exception as e:
        log(f"Error loading configuration: {e}", "err")
        return None

def update_config(config: dict, key: str, value):
    """
    Updates or adds a key-value pair in the given configuration dictionary and saves it to the file.

    Args:
        config (dict): The loaded configuration dictionary containing `_config_path`.
        key (str): The key to add or update.
        value (Any): The value to set for the key.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    try:
        if '_config_path' not in config:
            raise ValueError("Configuration dictionary missing '_config_path' key.")

        # Update or add the key-value pair
        config[key] = value

        # Save the updated config back to the file
        with open(config['_config_path'], 'w', encoding='utf-8') as file:
            json.dump(config, file, indent=4)

        return True
    except Exception as e:
        print(f"Error updating configuration: {e}")
        return False

def validate_agent_config(config: dict):
    """
    Basic validation: exist  and are not empty.

    :param config: dict containing configuration values.
    :return: True or Raises ValueError if validation fails.
    """

    required_keys = [
        "token",
        "id",
        "default_interval",
        "ignore_cert",
        "server_host",
        "server_endpoint"
    ]

    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")
    log("Configuration is valid", "debug")

    return True

def validate_db_config(config: dict):
    """
    Basic validation: exist and are not empty.

    :param config: dict containing database configuration values.
    :return: True or Raises ValueError if validation fails.
    """

    required_keys = ["host", "port", "database", "user", "password", "python_driver"]

    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")

    log("Database configuration is valid", "debug")
    return True
