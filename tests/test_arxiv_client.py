from paperpuller.arxiv_client import build_keyword_query


def test_build_keyword_query_quotes_phrases():
    query = build_keyword_query("scene text recognition", ["cs.CV", "cs.AI"])

    assert query == 'all:"scene text recognition" AND (cat:cs.CV OR cat:cs.AI)'
