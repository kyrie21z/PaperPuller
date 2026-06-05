from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_KEYWORD_QUERIES: list[str] = []


@dataclass(frozen=True)
class ArxivConfig:
    categories: list[str]
    fetch_days: int
    max_candidates: int
    keyword_queries: list[str]
    per_keyword_max_candidates: int
    request_pause_seconds: float
    max_retries: int
    timeout_seconds: int


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    model: str
    api_key_env: str
    temperature: float
    timeout_seconds: int
    max_retries: int


@dataclass(frozen=True)
class RankingConfig:
    high_priority_threshold: float
    possible_threshold: float
    max_report_papers: int


@dataclass(frozen=True)
class StorageConfig:
    sqlite_path: Path
    report_dir: Path


@dataclass(frozen=True)
class EmailConfig:
    enabled: bool
    smtp_server: str
    smtp_port: int
    sender: str
    receiver: str
    password_env: str
    subject: str


@dataclass(frozen=True)
class AppConfig:
    root: Path
    interest_file: Path
    arxiv: ArxivConfig
    llm: LlmConfig
    ranking: RankingConfig
    storage: StorageConfig
    email: EmailConfig


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).resolve()
    root = config_path.parent.parent
    with config_path.open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}

    arxiv = raw.get("arxiv", {})
    llm = raw.get("llm", {})
    ranking = raw.get("ranking", {})
    storage = raw.get("storage", {})
    email = raw.get("email", {})

    return AppConfig(
        root=root,
        interest_file=_resolve(root, raw.get("interest_file", "config/interest.md")),
        arxiv=ArxivConfig(
            categories=list(arxiv.get("categories", ["cs.CV"])),
            fetch_days=int(arxiv.get("fetch_days", 2)),
            max_candidates=int(arxiv.get("max_candidates", 100)),
            keyword_queries=list(arxiv.get("keyword_queries") or DEFAULT_KEYWORD_QUERIES),
            per_keyword_max_candidates=int(arxiv.get("per_keyword_max_candidates", 50)),
            request_pause_seconds=float(arxiv.get("request_pause_seconds", 3)),
            max_retries=int(arxiv.get("max_retries", 6)),
            timeout_seconds=int(arxiv.get("timeout_seconds", 30)),
        ),
        llm=LlmConfig(
            base_url=str(llm.get("base_url", "https://api.openai.com/v1")),
            model=str(llm.get("model", "gpt-4o-mini")),
            api_key_env=str(llm.get("api_key_env", "PAPERPULLER_API_KEY")),
            temperature=float(llm.get("temperature", 0.1)),
            timeout_seconds=int(llm.get("timeout_seconds", 60)),
            max_retries=int(llm.get("max_retries", 3)),
        ),
        ranking=RankingConfig(
            high_priority_threshold=float(ranking.get("high_priority_threshold", 7)),
            possible_threshold=float(ranking.get("possible_threshold", 5)),
            max_report_papers=int(ranking.get("max_report_papers", 50)),
        ),
        storage=StorageConfig(
            sqlite_path=_resolve(root, storage.get("sqlite_path", "data/papers.sqlite3")),
            report_dir=_resolve(root, storage.get("report_dir", "reports")),
        ),
        email=EmailConfig(
            enabled=bool(email.get("enabled", False)),
            smtp_server=str(email.get("smtp_server", "")),
            smtp_port=int(email.get("smtp_port", 587)),
            sender=str(email.get("sender", "")),
            receiver=str(email.get("receiver", "")),
            password_env=str(email.get("password_env", "PAPERPULLER_SMTP_PASSWORD")),
            subject=str(email.get("subject", "Daily arXiv")),
        ),
    )
