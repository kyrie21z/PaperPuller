from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published_at: str
    updated_at: str
    abs_url: str
    pdf_url: str


@dataclass(frozen=True)
class Evaluation:
    arxiv_id: str
    model: str
    score: float
    topic_tags: list[str]
    reason: str
    tldr: str

