"""CLI CivilEng — Config file loader."""
from pathlib import Path
import yaml

DEFAULT_CONFIG_PATHS = [
    Path("config.yaml"),
    Path.home() / ".cli-civileng" / "config.yaml",
]


def load_config(path: Path | None = None) -> dict:
    if path:
        return yaml.safe_load(path.read_text())
    for p in DEFAULT_CONFIG_PATHS:
        if p.exists():
            return yaml.safe_load(p.read_text())
    raise FileNotFoundError(
        "config.yaml not found. Copy config.yaml.example and fill in your API key."
    )
