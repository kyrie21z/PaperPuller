from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import AppConfig


def render_markdown(config: AppConfig, report_date: date, rows: list[dict]) -> str:
    high = [row for row in rows if row["score"] >= config.ranking.high_priority_threshold]
    possible = [
        row
        for row in rows
        if config.ranking.possible_threshold <= row["score"] < config.ranking.high_priority_threshold
    ]
    lines = [
        "# Daily arXiv Papers",
        "",
        f"Date: {report_date.isoformat()}",
        f"Model: `{config.llm.model}`",
        f"Categories: {', '.join(config.arxiv.categories)}",
        f"Included papers: {len(rows)}",
        "",
    ]
    lines.extend(_section("High Priority", high))
    lines.extend(_section("Possibly Relevant", possible))
    return "\n".join(lines).rstrip() + "\n"


def write_report(config: AppConfig, report_date: date, rows: list[dict]) -> Path:
    config.storage.report_dir.mkdir(parents=True, exist_ok=True)
    path = config.storage.report_dir / f"{report_date.isoformat()}.md"
    path.write_text(render_markdown(config, report_date, rows), encoding="utf-8")
    return path


def _section(title: str, rows: list[dict]) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(["No papers.", ""])
        return lines
    for index, row in enumerate(rows, start=1):
        authors = ", ".join(row["authors"][:6])
        if len(row["authors"]) > 6:
            authors += ", et al."
        lines.extend(
            [
                f"### {index}. {row['title']}",
                "",
                f"- Score: {row['score']:.1f}",
                f"- Tags: {', '.join(row['topic_tags'])}",
                f"- Authors: {authors}",
                f"- arXiv: [{row['arxiv_id']}]({row['abs_url']})",
                f"- PDF: [link]({row['pdf_url']})",
                f"- TL;DR: {row['tldr']}",
                f"- Reason: {row['reason']}",
                "",
            ]
        )
    return lines

