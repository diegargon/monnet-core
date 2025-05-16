"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Just initial Near do nothing test
"""

import pytest
import json
from unittest.mock import MagicMock
from pathlib import Path

@pytest.fixture
def mock_logger():
    """Mock reusable para el logger"""
    return MagicMock()

@pytest.fixture
def temp_json_file(tmp_path):
    """Crea un archivo JSON temporal reusable"""
    file_path = tmp_path / "test_datastore.json"
    return str(file_path)

@pytest.fixture
def sample_data():
    """Datos de ejemplo para pruebas de persistencia"""
    return {
        "last_load_avg": {"1m": 0.5},
        "last_memory_info": {"total": 1024}
    }

@pytest.fixture
def datastore(temp_json_file, mock_logger):
    """Instancia limpia de Datastore con mock logger"""
    from monnet_agent.datastore import Datastore
    from monnet_shared.app_context import AppContext

    mock_ctx = MagicMock()
    mock_ctx.get_logger.return_value = mock_logger

    ds = Datastore(ctx=mock_ctx, filename=temp_json_file)
    ds.log = mock_logger  # Inyección de dependencia
    return ds
