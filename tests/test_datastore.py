import pytest
import json
import time
from pathlib import Path

class TestDatastoreInitialization:
    def test_default_keys(self, datastore):
        assert "last_load_avg" in datastore.data
        assert datastore.data["last_iowait"] == 0

    def test_load_nonexistent_file(self, datastore, mock_logger):
        mock_logger.assert_called_with("No existing data file found. Starting fresh.")

class TestDatastoreCRUD:
    def test_update_existing_key(self, datastore):
        datastore.update_data("last_load_avg", {"1m": 0.75})
        assert datastore.data["last_load_avg"]["1m"] == 0.75

    def test_update_new_key(self, datastore, mock_logger):
        datastore.update_data("new_metric", {"value": 100})
        mock_logger.assert_called_with("New data set added: new_metric")
        assert "new_metric" in datastore.data

class TestDatastorePersistence:
    def test_auto_save(self, datastore, temp_json_file, mock_logger):
        datastore.save_interval = 0.1  # Forzamos guardado rápido
        datastore.update_data("test", {"value": 1})
        time.sleep(0.2)
        mock_logger.assert_called_with(f"Data saved successfully to {temp_json_file}")

    def test_file_integrity(self, datastore, temp_json_file, sample_data):
        datastore.data = sample_data
        datastore.save_data()
        with open(temp_json_file, "r") as f:
            assert json.load(f) == sample_data