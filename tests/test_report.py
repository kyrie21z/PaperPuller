from datetime import date
from pathlib import Path

from paperpuller.config import load_config
from paperpuller.report import render_markdown


def test_render_markdown_groups_papers_with_new_fields():
    config = load_config(Path("config/paperpuller.yaml"))
    rows = [
        {
            "title": "Must Read Paper",
            "score": 8.0,
            "topic_tags": ["OCR", "SLPR"],
            "authors": ["A. Author"],
            "arxiv_id": "2601.00003",
            "abs_url": "https://arxiv.org/abs/2601.00003",
            "pdf_url": "https://arxiv.org/pdf/2601.00003",
            "tldr": "Summary.",
            "reason": "Directly relevant.",
            "slpr_challenges": ["degradation", "occlusion"],
            "pipeline_components": ["visual_encoder"],
            "integration_path": "finetune",
            "reproducibility": "high",
            "next_action": "read",
        },
        {
            "title": "Related Work Paper",
            "score": 5.0,
            "topic_tags": ["ViT"],
            "authors": ["B. Author"],
            "arxiv_id": "2601.00004",
            "abs_url": "https://arxiv.org/abs/2601.00004",
            "pdf_url": "https://arxiv.org/pdf/2601.00004",
            "tldr": "Interesting but not core.",
            "reason": "Tangentially relevant.",
            "slpr_challenges": [],
            "pipeline_components": ["analysis_only"],
            "integration_path": "related_work",
            "reproducibility": "medium",
            "next_action": "skim",
        },
    ]

    markdown = render_markdown(config, date(2026, 6, 1), rows)

    assert "## Must Read" in markdown
    assert "Must Read Paper" in markdown
    assert "Score | 8.0" in markdown
    assert "SLPR Challenges | degradation, occlusion" in markdown
    assert "Next Action | read" in markdown
    assert "## Related Work / Others" in markdown
    assert "Related Work Paper" in markdown


def test_render_markdown_handles_old_data_missing_new_fields():
    """Old evaluations without the new columns should render safely."""
    config = load_config(Path("config/paperpuller.yaml"))
    rows = [
        {
            "title": "Legacy Paper",
            "score": 7.5,
            "topic_tags": ["OCR"],
            "authors": ["C. Author"],
            "arxiv_id": "2601.00005",
            "abs_url": "https://arxiv.org/abs/2601.00005",
            "pdf_url": "https://arxiv.org/pdf/2601.00005",
            "tldr": "Summary.",
            "reason": "Relevant.",
            # No new fields at all
        }
    ]

    markdown = render_markdown(config, date(2026, 6, 1), rows)

    assert "Legacy Paper" in markdown
    assert "Score | 7.5" in markdown
    # Old data: next_action defaults to "skim", so falls into Related Work
    assert "Related Work" in markdown
    # Should display fallback values, not crash
    assert "—" in markdown or "unknown" in markdown or "skim" in markdown
