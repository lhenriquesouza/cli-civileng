"""Tests for config.py."""
import pytest
from cli_civileng.config import load_config


class TestLoadConfig:
    def test_loads_from_path(self, temp_config_file):
        config = load_config(temp_config_file)
        assert config["llm"]["provider"] == "deepseek"
        assert config["llm"]["api_key"] == "test-key-123"

    def test_raises_when_not_found(self, monkeypatch):
        """When no config exists, should raise FileNotFoundError."""
        # Patch DEFAULT_CONFIG_PATHS to non-existent paths
        from cli_civileng import config as config_mod
        monkeypatch.setattr(
            config_mod,
            "DEFAULT_CONFIG_PATHS",
            [config_mod.Path("/nonexistent/config.yaml")],
        )
        with pytest.raises(FileNotFoundError):
            load_config()
