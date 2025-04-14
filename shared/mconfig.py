"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Shared: Config
"""
import os
import json

def load_config(file_path: str) -> dict:
    """Load JSON config"""

    if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
        raise ValueError("File path not exist or not readable")

    try:
        with open(file_path, "r", encoding='utf-8') as file:
            config = json.load(file)
            config['_config_path'] = file_path
            return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except TypeError as e:
        raise ValueError(f"Invalid type in JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error loading configuration: {e}")

def update_config(config: dict):
    """
    Saves the entire configu to the file specified in `_config_path`.

    Args:
        config (dict): The loaded configuration dictionary containing `_config_path`.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    try:
        if '_config_path' not in config:
            raise ValueError("Configuration dictionary missing '_config_path' key.")

        if not os.path.isfile(config["_config_path"]) or not os.access([config['_config_path']], os.W_OK):
            raise ValueError("Config path not exist or not writable")

        # Save the entire config back to the file
        try:
            with open(config['_config_path'], 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=4)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid type in JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Error saving configuration: {e}")

        return True
    except Exception as e:
        raise RuntimeError(f"Error saving configuration: {e}")

def update_config_key(config: dict, key: str, value):
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

        if not os.path.isfile(config["_config_path"]) or not os.access([config['_config_path']], os.W_OK):
            raise ValueError("Config path not exist or not writable")
        # Update or add the key-value pair
        config[key] = value

        # Save the updated config back to the file
        with open(config['_config_path'], 'w', encoding='utf-8') as file:
            json.dump(config, file, indent=4)

        return True
    except Exception as e:
        raise RuntimeError(f"Error updating configuration: {e}")

def validate_agent_config(config: dict):
    """
    Basic validation: exist and are not empty.

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

    return True
