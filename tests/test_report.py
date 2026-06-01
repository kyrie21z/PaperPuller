from datetime import date
from pathlib import Path

from paperpuller.config import load_config
from paperpuller.report import render_markdown


def test_render_markdown_groups_papers():
    config = load_config(Path("config/paperpuller.yaml"))
    rows = [
        {
            "title": "OCR Paper",
            "score": 8.0,
            "topic_tags": ["OCR"],
            "authors": ["A. Author"],
            "arxiv_id": "2601.00003",
            "abs_url": "https://arxiv.org/abs/2601.00003",
            "pdf_url": "https://arxiv.org/pdf/2601.00003",
            "tldr": "Summary.",
            "reason": "Reason.",
        }
    ]

    markdown = render_markdown(config, date(2026, 6, 1), rows)

    assert "## High Priority" in markdown
    assert "OCR Paper" in markdown
    assert "Score: 8.0" in markdown

