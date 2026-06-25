"""Shared fixtures for cli-civileng tests."""
import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_file():
    """Create a temporary config.yaml for testing."""
    config = {
        "llm": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "api_key": "test-key-123",
        }
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        json.dump(config, f)  # JSON is valid YAML
        temp_path = f.name
    yield Path(temp_path)
    Path(temp_path).unlink(missing_ok=True)
