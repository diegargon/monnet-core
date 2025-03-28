"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent


"""

import json
import time
from typing import Optional, Dict, Any

# Local
from shared.app_context import AppContext
from shared.logger import log

class Datastore:
    """
    Keep data and Save/Load from disk in json format
    Attributes:
         :param filename: File to save/load data.
    """
    def __init__(self, ctx: AppContext, filename: str = "/tmp/datastore.json"):
        """
        Initialization
            :param filename: File to save/load data.
        """
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.save_interval = 10 * 60
        self.last_save = time.time()
        self.filename = filename
        self.data: Dict[str, Optional[Dict[str, Any]]] = {
            "last_load_avg": None,
            "last_memory_info": None,
            "last_disk_info": None,
            "last_ports_info": None,
            "iowait_last_stats": None,
            "last_iowait": 0,
            "last_memory_stats": None,
        }
        self.load_data()

    def update_data(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Updates the specified data set.
        If the key does not exist, it is automatically added to allow future expansion.

        Args
            key (str):
            data (dict):
        """
        if key not in self.data:
            self.logger.log(f"New data set added: {key}")
        self.data[key] = data

        if time.time() - self.last_save >= self.save_interval:
            return self.save_data()
        return True

    def get_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the data set associated with the given key.

        Args:
            key (str):
        Returns:
            dict: Optional
        """
        return self.data.get(key)

    def list_keys(self) -> list:
        """
        Returns a list of all registered keys.
        """
        return list(self.data.keys())

    def save_data(self)-> bool:
        """
        Saves the current data to a JSON file.
        """
        try:
            with open(self.filename,
                      "w", encoding='utf-8') as file:
                json.dump(self.data, file, indent=4)
            self.last_save = time.time()
            self.logger.log(f"Data saved successfully to {self.filename}")
            return True
        except Exception as e:
            self.logger.log(f"Error saving data to {self.filename}: {e}")
            return False

    def load_data(self)-> bool:
        """
        Loads data from a JSON file.
        """
        try:
            with open(self.filename, "r", encoding='utf-8') as file:
                self.data = json.load(file)
            self.logger.log(f"Data loaded successfully from {self.filename}")
            return True
        except FileNotFoundError:
            self.logger.log("No existing data file found. Starting fresh.")
            return False
        except Exception as e:
            self.logger.log(f"Error loading data from {self.filename}: {e}")
            return False
