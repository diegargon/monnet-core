"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Unified Config
"""

# Std
import os
import json

# Local
from shared.app_context import AppContext
from monnet_gateway.database.dbmanager import DBManager
class Config:
    """
    Configuration class for the Monnet Gateway.
    Combines file-based and database-based configurations.
    """
    def __init__(self, ctx: AppContext, file_path: str):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.file_config = {}
        self.db_config = {}

        # Load file-based configuration
        self.logger.debug(f"Loading configuration from file: {file_path}")
        self._load_file_config(file_path)

        self._load_db_config()
        self.ctx.set_config(self)

    def get(self, key: str, default=None):
        """
        Retrieve a configuration value by key.

        :param key: The configuration key to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The configuration value or the default value.
        """
        # Check database config first, then file config
        return self.db_config.get(key, self.file_config.get(key, default))

    def update_file_key(self, key: str, value, create_key: bool = False):
        """
        Update a key-value pair in the file-based configuration and save it to the file.

        :param key: The key to update.
        :param value: The value to set for the key.
        :param create_key: Whether to create the key if it does not exist. Default is False.
        """
        if key not in self.file_config and not create_key:
            raise KeyError(f"Key '{key}' does not exist in the file-based configuration.")

        if "_config_path" not in self.file_config:
            raise ValueError("Configuration dictionary is missing '_config_path' key.")

        file_path = self.file_config["_config_path"]
        if not os.path.isfile(file_path) or not os.access(file_path, os.W_OK):
            raise ValueError(f"Config file does not exist or is not writable: {file_path}")

        self.file_config[key] = value

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(self.file_config, file, indent=4)
        except Exception as e:
            raise RuntimeError(f"Error saving configuration: {e}")

    def update_db_key(self, key: str, value, create_key: bool = False):
        """
        Update a key-value pair in the database-based configuration.

        :param key: The key to update.
        :param value: The value to set for the key.
        :param create_key: Whether to create the key if it does not exist. Default is False.
        """
        db = DBManager(self.file_config)

        try:
            query_check = "SELECT COUNT(*) as count FROM config WHERE ckey = %s"
            result = db.fetchone(query_check, (key,))
            exists = result and result["count"] > 0

            if not exists and not create_key:
                raise KeyError(f"Key '{key}' does not exist in the database-based configuration.")

            if exists:
                query_update = "UPDATE config SET cvalue = %s WHERE ckey = %s"
                db.execute(query_update, (json.dumps(value), key))
            else:
                query_insert = "INSERT INTO config (ckey, cvalue) VALUES (%s, %s)"
                db.execute(query_insert, (key, json.dumps(value)))

            db.commit()

            self.db_config[key] = value
            self.logger.info(f"Configuration key '{key}' updated successfully in the database.")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to update configuration key '{key}' in the database: {e}")
            raise RuntimeError(f"Error updating database configuration: {e}")
        finally:
            db.close()

    def _load_file_config(self, file_path: str):
        """
        Load configuration from a JSON file.

        :param file_path: Path to the configuration file.
        """
        if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
            raise ValueError(f"File path does not exist or is not readable: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_config = json.load(file)
                self._validate_db_config(file_config)
                self.file_config.update(file_config)
                self.file_config["_config_path"] = file_path
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration file: {e}")

    def _validate_db_config(self, config: dict):
        """
        Validate the database configuration.

        :param config: Configuration dictionary.
        """
        required_keys = ["host", "port", "database", "user", "password", "python_driver"]
        missing_keys = [key for key in required_keys if not config.get(key)]
        if missing_keys:
            raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")

    def _load_db_config(self):
        """
        Load additional configuration from the database.
        """
        self.logger.debug("Loading additional configuration from database...")
        db = DBManager(self.file_config)
        try:
            query = "SELECT `ckey`, `cvalue` FROM config WHERE uid = 0"
            results = db.fetchall(query)
            db.close()
            for row in results:
                value_raw = row.get("cvalue")
                key = row.get("ckey")

                if value_raw is None or value_raw.strip() == "":
                    continue
                try:
                    value = json.loads(value_raw)
                    if value in (None, "", {}, []):
                        continue
                    self.db_config[row["ckey"]] = value
                except json.JSONDecodeError:
                    self.db_config[row["ckey"]] = row["cvalue"]
            self.logger.info("Database configuration loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load configuration from database: {e}")
