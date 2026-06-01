from pathlib import Path

from paperpuller.config import load_config


def test_load_config_resolves_paths():
    config = load_config(Path("config/paperpuller.yaml"))

    assert config.arxiv.categories == ["cs.CV", "cs.AI", "cs.LG"]
    assert "scene text recognition" in config.arxiv.keyword_queries
    assert config.arxiv.per_keyword_max_candidates == 50
    assert config.storage.sqlite_path.is_absolute()
    assert config.interest_file.name == "interest.md"
