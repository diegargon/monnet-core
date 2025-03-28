"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Just initial Near do nothing test
"""

import pytest
import json
import time
from pathlib import Path

class TestDatastoreInitialization:
    def test_logger_from_context(self, datastore, mock_logger):
        assert datastore.logger is mock_logger
        assert datastore.ctx.get_logger() is mock_logger
    def test_default_keys(self, datastore):
        assert "last_load_avg" in datastore.data
        assert datastore.data["last_iowait"] == 0

class TestDatastoreCRUD:
    def test_update_existing_key(self, datastore):
        assert datastore.update_data("last_load_avg", {"1m": 0.75}) is True
        assert datastore.data["last_load_avg"]["1m"] == 0.75

    def test_update_new_key(self, datastore, mock_logger):
        assert datastore.logger is mock_logger
        assert datastore.update_data("new_metric", {"value": 100}) is True
#   Fix before logger to class
#        mock_logger.info.assert_called_with("New data set added: new_metric")
#        assert "new_metric" in datastore.data

class TestDatastorePersistence:
    def test_auto_save(self, datastore, temp_json_file, mock_logger):
        datastore.save_interval = 0.10  # Forzamos guardado rápido
        datastore.last_save = time.time() - 0.11 # Caducamos
        assert datastore.update_data("test", {"value": 1}) is True
        time.sleep(0.20)  # Esperar a que se guarde
        with open(temp_json_file, "r", encoding="utf-8") as f:
            assert "test" in json.load(f)

    def test_file_integrity(self, datastore, temp_json_file, sample_data):
        datastore.data = sample_data
        datastore.save_data()
        with open(temp_json_file, "r", encoding='utf-8') as f:
            assert json.load(f) == sample_data