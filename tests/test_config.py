from pathlib import Path

from paperpuller.config import load_config


def test_load_config_resolves_paths():
    config = load_config(Path("config/paperpuller.yaml"))

    assert config.arxiv.categories == ["cs.CV", "cs.AI", "cs.LG"]
    assert config.storage.sqlite_path.is_absolute()
    assert config.interest_file.name == "interest.md"

