from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import AppConfig


def render_markdown(config: AppConfig, report_date: date, rows: list[dict]) -> str:
    high = [r for r in rows if r["score"] >= config.ranking.high_priority_threshold]
    possible = [
        r
        for r in rows
        if config.ranking.possible_threshold <= r["score"] < config.ranking.high_priority_threshold
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
    if high:
        lines.append("## High Priority")
        lines.append("")
        lines.extend(_render_groups(high))
    if possible:
        lines.append("## Possibly Relevant")
        lines.append("")
        lines.extend(_render_groups(possible))
    return "\n".join(lines).rstrip() + "\n"


def write_report(config: AppConfig, report_date: date, rows: list[dict]) -> Path:
    config.storage.report_dir.mkdir(parents=True, exist_ok=True)
    path = config.storage.report_dir / f"{report_date.isoformat()}.md"
    path.write_text(render_markdown(config, report_date, rows), encoding="utf-8")
    return path


def _render_groups(rows: list[dict]) -> list[str]:
    """Group *rows* by their ``group`` field and render each group as a sub-section."""
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        g = row.get("group", "Other") or "Other"
        grouped.setdefault(g, []).append(row)

    # Sort groups alphabetically for stable output
    lines: list[str] = []
    for group_name in sorted(grouped):
        papers = grouped[group_name]
        lines.append(f"### {group_name}")
        lines.append("")
        lines.append(f"_{len(papers)} paper(s)_")
        lines.append("")
        for index, row in enumerate(papers, start=1):
            lines.extend(_paper_card(index, row))
    return lines


def _paper_card(index: int, row: dict) -> list[str]:
    authors = ", ".join(row["authors"][:6])
    if len(row["authors"]) > 6:
        authors += ", et al."
    lines = [
        f"#### {index}. {row['title']}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Score | {row['score']:.1f} |",
        f"| Tags | {', '.join(row['topic_tags'])} |",
        f"| Group | {row.get('group', 'Other') or 'Other'} |",
        f"| TL;DR | {row['tldr']} |",
        f"| Reason | {row['reason']} |",
        f"| Authors | {authors} |",
        f"| arXiv | [{row['arxiv_id']}]({row['abs_url']}) |",
        f"| PDF | [link]({row['pdf_url']}) |",
    ]
    extra = row.get("extra")
    if isinstance(extra, dict) and extra:
        for key, value in extra.items():
            display = _format_extra_value(value)
            lines.append(f"| {key} | {display} |")
    lines.append("")
    return lines


def _format_extra_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}: {v}" for k, v in value.items())
    return str(value)
