from paperpuller.database import Database
from paperpuller.models import Evaluation, Paper


def test_database_deduplicates_papers(tmp_path):
    db = Database(tmp_path / "papers.sqlite3")
    db.init()
    paper = Paper(
        arxiv_id="2601.00001",
        title="A Test Paper",
        authors=["A. Author"],
        abstract="About OCR and scene text recognition.",
        categories=["cs.CV"],
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        abs_url="https://arxiv.org/abs/2601.00001",
        pdf_url="https://arxiv.org/pdf/2601.00001",
    )

    assert db.upsert_papers([paper]) == 1
    assert db.upsert_papers([paper]) == 0


def test_database_report_rows(tmp_path):
    db = Database(tmp_path / "papers.sqlite3")
    db.init()
    paper = Paper(
        arxiv_id="2601.00002",
        title="A ViT Paper",
        authors=["B. Author"],
        abstract="About vision transformers.",
        categories=["cs.CV"],
        published_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        abs_url="https://arxiv.org/abs/2601.00002",
        pdf_url="https://arxiv.org/pdf/2601.00002",
    )
    db.upsert_papers([paper])
    db.save_evaluation(
        Evaluation(
            arxiv_id=paper.arxiv_id,
            model="test-model",
            score=8,
            topic_tags=["ViT"],
            reason="Relevant to vision transformers.",
            tldr="A concise summary.",
        )
    )

    rows = db.report_rows("test-model", 5, 10)
    assert len(rows) == 1
    assert rows[0]["topic_tags"] == ["ViT"]

