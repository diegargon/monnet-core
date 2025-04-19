"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - DB Config

"""

import json  # Import JSON module for parsing
from shared.app_context import AppContext


class Config:
    """
    Configuration class for the Monnet Gateway database.
    """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.db = ctx.get_database()
        self.config = {}

    def load_db_config(self):
        """
        Load configuration from database.
        """
        self.logger.debug("Loading database configuration...")
        try:
            query = "SELECT `ckey`, `cvalue` FROM config WHERE uid = 0"
            results = self.db.fetchall(query)

            # Parse cvalue as JSON and store in a dictionary
            self.config = {}
            for row in results:
                try:
                    self.config[row['ckey']] = json.loads(row['cvalue'])
                except json.JSONDecodeError:
                    self.config[row['ckey']] = row['cvalue']  # Fallback to raw value if not JSON
            self.logger.info("Configuration loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = {}

    def get(self, key: str, default=None):
        """
        Retrieve a configuration value by key.

        :param key: The configuration key to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The configuration value or the default value.
        """
        return self.config.get(key, default)

