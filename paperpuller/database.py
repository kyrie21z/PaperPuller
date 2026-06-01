from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from typing import Iterator

from .models import Evaluation, Paper


SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    arxiv_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    abstract TEXT NOT NULL,
    categories_json TEXT NOT NULL,
    published_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    abs_url TEXT NOT NULL,
    pdf_url TEXT NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
    arxiv_id TEXT NOT NULL,
    model TEXT NOT NULL,
    score REAL NOT NULL,
    topic_tags_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    tldr TEXT NOT NULL,
    evaluated_at TEXT NOT NULL,
    PRIMARY KEY (arxiv_id, model),
    FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    new_count INTEGER NOT NULL DEFAULT 0,
    evaluated_count INTEGER NOT NULL DEFAULT 0,
    included_count INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS email_deliveries (
    report_date TEXT PRIMARY KEY,
    sent_at TEXT,
    status TEXT NOT NULL,
    recipient TEXT NOT NULL,
    error_message TEXT NOT NULL DEFAULT ''
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def init(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def start_run(self) -> int:
        now = _now()
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO runs (started_at, status) VALUES (?, ?)",
                (now, "running"),
            )
            return int(cursor.lastrowid)

    def finish_run(
        self,
        run_id: int,
        status: str,
        fetched_count: int,
        new_count: int,
        evaluated_count: int,
        included_count: int,
        error_summary: str = "",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET ended_at = ?, status = ?, fetched_count = ?, new_count = ?,
                    evaluated_count = ?, included_count = ?, error_summary = ?
                WHERE id = ?
                """,
                (
                    _now(),
                    status,
                    fetched_count,
                    new_count,
                    evaluated_count,
                    included_count,
                    error_summary,
                    run_id,
                ),
            )

    def upsert_papers(self, papers: list[Paper]) -> int:
        now = _now()
        new_count = 0
        with self.connect() as connection:
            for paper in papers:
                exists = connection.execute(
                    "SELECT 1 FROM papers WHERE arxiv_id = ?",
                    (paper.arxiv_id,),
                ).fetchone()
                if exists is None:
                    new_count += 1
                connection.execute(
                    """
                    INSERT INTO papers (
                        arxiv_id, title, authors_json, abstract, categories_json,
                        published_at, updated_at, abs_url, pdf_url, first_seen_at, last_seen_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(arxiv_id) DO UPDATE SET
                        title = excluded.title,
                        authors_json = excluded.authors_json,
                        abstract = excluded.abstract,
                        categories_json = excluded.categories_json,
                        updated_at = excluded.updated_at,
                        abs_url = excluded.abs_url,
                        pdf_url = excluded.pdf_url,
                        last_seen_at = excluded.last_seen_at
                    """,
                    (
                        paper.arxiv_id,
                        paper.title,
                        json.dumps(paper.authors, ensure_ascii=False),
                        paper.abstract,
                        json.dumps(paper.categories, ensure_ascii=False),
                        paper.published_at,
                        paper.updated_at,
                        paper.abs_url,
                        paper.pdf_url,
                        now,
                        now,
                    ),
                )
        return new_count

    def unevaluated_papers(self, model: str) -> list[Paper]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT p.*
                FROM papers p
                LEFT JOIN evaluations e ON e.arxiv_id = p.arxiv_id AND e.model = ?
                WHERE e.arxiv_id IS NULL
                ORDER BY p.published_at DESC
                """,
                (model,),
            ).fetchall()
        return [_row_to_paper(row) for row in rows]

    def save_evaluation(self, evaluation: Evaluation) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO evaluations (
                    arxiv_id, model, score, topic_tags_json, reason, tldr, evaluated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(arxiv_id, model) DO UPDATE SET
                    score = excluded.score,
                    topic_tags_json = excluded.topic_tags_json,
                    reason = excluded.reason,
                    tldr = excluded.tldr,
                    evaluated_at = excluded.evaluated_at
                """,
                (
                    evaluation.arxiv_id,
                    evaluation.model,
                    evaluation.score,
                    json.dumps(evaluation.topic_tags, ensure_ascii=False),
                    evaluation.reason,
                    evaluation.tldr,
                    _now(),
                ),
            )

    def report_rows(
        self,
        model: str,
        min_score: float,
        limit: int,
        report_date: str | None = None,
    ) -> list[dict]:
        date_clause = ""
        params: list[object] = [model, min_score]
        if report_date is not None:
            date_clause = "AND substr(p.first_seen_at, 1, 10) = ?"
            params.append(report_date)
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT p.*, e.model, e.score, e.topic_tags_json, e.reason, e.tldr, e.evaluated_at
                FROM papers p
                JOIN evaluations e ON e.arxiv_id = p.arxiv_id
                WHERE e.model = ? AND e.score >= ?
                {date_clause}
                ORDER BY e.score DESC, p.published_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_row_to_report(row) for row in rows]

    def mark_email(self, report_date: str, status: str, recipient: str, error: str = "") -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO email_deliveries (report_date, sent_at, status, recipient, error_message)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(report_date) DO UPDATE SET
                    sent_at = excluded.sent_at,
                    status = excluded.status,
                    recipient = excluded.recipient,
                    error_message = excluded.error_message
                """,
                (report_date, _now() if status == "sent" else None, status, recipient, error),
            )


def _row_to_paper(row: sqlite3.Row) -> Paper:
    return Paper(
        arxiv_id=row["arxiv_id"],
        title=row["title"],
        authors=json.loads(row["authors_json"]),
        abstract=row["abstract"],
        categories=json.loads(row["categories_json"]),
        published_at=row["published_at"],
        updated_at=row["updated_at"],
        abs_url=row["abs_url"],
        pdf_url=row["pdf_url"],
    )


def _row_to_report(row: sqlite3.Row) -> dict:
    return {
        "arxiv_id": row["arxiv_id"],
        "title": row["title"],
        "authors": json.loads(row["authors_json"]),
        "abstract": row["abstract"],
        "categories": json.loads(row["categories_json"]),
        "published_at": row["published_at"],
        "updated_at": row["updated_at"],
        "abs_url": row["abs_url"],
        "pdf_url": row["pdf_url"],
        "model": row["model"],
        "score": row["score"],
        "topic_tags": json.loads(row["topic_tags_json"]),
        "reason": row["reason"],
        "tldr": row["tldr"],
        "evaluated_at": row["evaluated_at"],
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
