"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Unified Config
"""

# Std
import json

# Local
from monnet_shared.app_context import AppContext
from monnet_shared.file_config import FileConfig
from monnet_gateway.database.dbmanager import DBManager

class DBConfig(FileConfig):
    """
    Configuration class for file-based and database-based configuration.
    """
    def __init__(self, ctx: AppContext, config_file_path: str):
        super().__init__(ctx, config_file_path)
        self.db_config = {}
        self.logger.debug("Database configuration enabled. Loading from database...")
        self._validate_db_config(self.file_config)
        self.load_db_config()

    def get(self, key: str, default=None):
        """
        Retrieve a configuration value by key, preferring database config.
        """
        return self.db_config.get(key, self.file_config.get(key, default))

    def update_db_key(self, key: str, value, create_key: bool = False):
        """
        Update a key-value pair in the database-based configuration.
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

    def _validate_db_config(self, config: dict):
        """
        Validate the database configuration.
        """
        required_keys = ["host", "port", "database", "user", "password", "python_driver"]
        missing_keys = [key for key in required_keys if not config.get(key)]
        if missing_keys:
            raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")

    def load_db_config(self):
        """
        Load additional configuration from the database.
        """
        self.logger.debug("Loading additional configuration from database...")
        db = DBManager(self.file_config)
        try:
            query = "SELECT `ckey`, `cvalue`, `ctype`  FROM config WHERE uid = 0"
            results = db.fetchall(query)
            db.close()
            for row in results:
                value_raw = row.get("cvalue")
                key = row.get("ckey")
                ctype = row.get("ctype")

                if value_raw is None or value_raw.strip() == "":
                    continue
                try:
                    value = json.loads(value_raw)
                    if value in (None, "", {}, []):
                        continue
                    if ctype in (1, 2): # Integer
                       value = int(value)
                    if ctype == 3: # Float
                       value = float(value)
                    self.db_config[row["ckey"]] = value
                except json.JSONDecodeError:
                    self.db_config[row["ckey"]] = row["cvalue"]
            self.logger.info("Database configuration loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load configuration from database: {e}")

    def reload(self):
        """
        Reload the configuration from the file and database.
        """
        self.logger.debug("Triggered reload configuration...")
        try:
            if not self.config_file_path:
                raise ValueError("File path for configuration is not set.")
            self.load_file_config()
            self.load_db_config()
            self.logger.info("Configuration reloaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            raise RuntimeError(f"Error reloading configuration: {e}")
