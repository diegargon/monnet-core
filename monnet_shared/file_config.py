"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Shared: File Config
"""
import os
import json
from monnet_shared.log_level import LogLevel

class FileConfig:
    """
    Configuration class for file-based configuration (standalone, no DB).
    """
    def __init__(self, ctx, config_file_path: str):
        self.ctx = ctx
        self.logger = ctx.get_logger() if ctx else None
        self.file_config = {}
        self.config_file_path = config_file_path

        if self.logger:
            self.logger.debug(f"Loading configuration from file: {config_file_path}")
        self.load_file_config()
        if self.ctx:
            self.ctx.set_config(self)

    def get(self, key: str, default=None):
        return self.file_config.get(key, default)

    def set(self, key: str, value):
        """
        Set a configuration value in memory (does not persist to file).
        """
        self.file_config[key] = value

    def update_file_key(self, key: str, value, create_key: bool = False):
        if key not in self.file_config and not create_key:
            raise KeyError(f"Key '{key}' does not exist in the file-based configuration.")
        if "_config_path" not in self.file_config:
            raise ValueError("Configuration dictionary is missing '_config_path' key.")
        if not os.path.isfile(self.config_file_path) or not os.access(self.config_file_path, os.W_OK):
            raise ValueError(f"Config file does not exist or is not writable: {self.config_file_path}")
        self.file_config[key] = value
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as file:
                json.dump(self.file_config, file, indent=4)
        except Exception as e:
            raise RuntimeError(f"Error saving configuration: {e}")

    def load_file_config(self):
        if not os.path.isfile(self.config_file_path) or not os.access(self.config_file_path, os.R_OK):
            raise ValueError(f"File path does not exist or is not readable: {self.config_file_path}")
        try:
            with open(self.config_file_path, "r", encoding="utf-8") as file:
                file_config = json.load(file)
                self.file_config.update(file_config)
                self.file_config["_config_path"] = self.config_file_path
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration file: {e}")

    def reload(self):
        if self.logger:
            self.logger.debug("Triggered reload configuration...")
        try:
            if not self.config_file_path:
                raise ValueError("File path for configuration is not set.")
            self.load_file_config()
            if self.logger:
                self.logger.info("Configuration reloaded successfully.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to reload configuration: {e}")
            raise RuntimeError(f"Error reloading configuration: {e}")

    def validate_agent_config(self):
        required_keys = [
            "token",
            "id",
            "default_interval",
            "ignore_cert",
            "server_host",
            "server_endpoint"
        ]
        missing_keys = [key for key in required_keys if not self.file_config.get(key)]
        if missing_keys:
            self.logger.error(f"Missing required keys in configuration: {', '.join(missing_keys)}")
            raise ValueError(f"Missing or invalid values for keys: {', '.join(missing_keys)}")
        agent_log_level = self.get("agent_log_level", "INFO")
        if agent_log_level.upper() not in LogLevel.__dict__:
            self.file_config["agent_log_level"] = "INFO"
        else:
            self.file_config["agent_log_level"] = agent_log_level
        return True
