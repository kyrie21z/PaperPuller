from datetime import date
from pathlib import Path

from paperpuller.config import load_config
from paperpuller.report import render_markdown


def test_render_markdown_groups_by_group_field():
    config = load_config(Path("config/paperpuller.yaml"))
    rows = [
        {
            "title": "High Priority Paper",
            "score": 8.5,
            "topic_tags": ["OCR", "STR"],
            "group": "Robust Recognition",
            "authors": ["A. Author"],
            "arxiv_id": "2601.00003",
            "abs_url": "https://arxiv.org/abs/2601.00003",
            "pdf_url": "https://arxiv.org/pdf/2601.00003",
            "tldr": "Summary.",
            "reason": "Directly relevant.",
            "extra": {
                "challenges": ["degradation", "occlusion"],
                "pipeline_components": ["visual_encoder"],
            },
        },
        {
            "title": "Related Work Paper",
            "score": 5.0,
            "topic_tags": ["ViT"],
            "group": "Related Work",
            "authors": ["B. Author"],
            "arxiv_id": "2601.00004",
            "abs_url": "https://arxiv.org/abs/2601.00004",
            "pdf_url": "https://arxiv.org/pdf/2601.00004",
            "tldr": "Interesting but not core.",
            "reason": "Tangentially relevant.",
            "extra": {},
        },
    ]

    markdown = render_markdown(config, date(2026, 6, 1), rows)

    assert "## High Priority" in markdown
    assert "### Robust Recognition" in markdown
    assert "High Priority Paper" in markdown
    assert "Score | 8.5" in markdown
    assert "Group | Robust Recognition" in markdown
    assert "## Possibly Relevant" in markdown
    assert "### Related Work" in markdown
    assert "Related Work Paper" in markdown


def test_render_markdown_defaults_group_to_other():
    config = load_config(Path("config/paperpuller.yaml"))
    rows = [
        {
            "title": "No Group Paper",
            "score": 7.5,
            "topic_tags": ["OCR"],
            "group": "",
            "authors": ["C. Author"],
            "arxiv_id": "2601.00005",
            "abs_url": "https://arxiv.org/abs/2601.00005",
            "pdf_url": "https://arxiv.org/pdf/2601.00005",
            "tldr": "Summary.",
            "reason": "Relevant.",
            "extra": {},
        }
    ]

    markdown = render_markdown(config, date(2026, 6, 1), rows)

    assert "No Group Paper" in markdown
    assert "Score | 7.5" in markdown
    assert "### Other" in markdown


def test_render_markdown_renders_extra_fields():
    config = load_config(Path("config/paperpuller.yaml"))
    rows = [
        {
            "title": "Extra Paper",
            "score": 9.0,
            "topic_tags": ["MAE"],
            "group": "Visual Encoder",
            "authors": ["D. Author"],
            "arxiv_id": "2601.00006",
            "abs_url": "https://arxiv.org/abs/2601.00006",
            "pdf_url": "https://arxiv.org/pdf/2601.00006",
            "tldr": "Summary.",
            "reason": "Important.",
            "extra": {
                "reproducibility": "high",
                "next_action": "read",
            },
        }
    ]

    markdown = render_markdown(config, date(2026, 6, 1), rows)

    assert "| reproducibility | high |" in markdown
    assert "| next_action | read |" in markdown
