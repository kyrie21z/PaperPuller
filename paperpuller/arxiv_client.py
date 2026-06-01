from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
import xml.etree.ElementTree as ET

import requests

from .models import Paper


ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def build_query(categories: list[str]) -> str:
    return " OR ".join(f"cat:{category}" for category in categories)


def build_keyword_query(keyword: str, categories: list[str]) -> str:
    term = keyword.strip()
    if not term:
        raise ValueError("keyword must not be empty")
    if " " in term:
        term = f'"{term}"'
    return f"all:{term} AND ({build_query(categories)})"


def fetch_recent_papers(
    categories: list[str],
    fetch_days: int,
    max_candidates: int,
    keyword_queries: list[str] | None = None,
    per_keyword_max_candidates: int = 50,
    request_pause_seconds: float = 3,
    timeout_seconds: int = 30,
    max_retries: int = 3,
) -> list[Paper]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=fetch_days)
    queries = [(build_query(categories), max_candidates)]
    for keyword in keyword_queries or []:
        queries.append((build_keyword_query(keyword, categories), per_keyword_max_candidates))

    papers_by_id: dict[str, Paper] = {}
    for index, (query, limit) in enumerate(queries):
        for paper in _fetch_query(query, limit, cutoff, timeout_seconds, max_retries):
            papers_by_id.setdefault(paper.arxiv_id, paper)
        if index < len(queries) - 1 and request_pause_seconds > 0:
            time.sleep(request_pause_seconds)

    return sorted(
        papers_by_id.values(),
        key=lambda paper: _parse_arxiv_time(paper.published_at),
        reverse=True,
    )


def _fetch_query(
    search_query: str,
    max_results: int,
    cutoff: datetime,
    timeout_seconds: int,
    max_retries: int,
) -> list[Paper]:
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    headers = {"User-Agent": "PaperPuller/0.1 (local research paper digest)"}
    response = None
    retryable_statuses = {429, 500, 502, 503, 504}
    attempts = max(max_retries, 6)
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout_seconds)
        except requests.RequestException:
            if attempt == attempts:
                raise
            time.sleep(_retry_delay(None, attempt))
            continue
        if response.status_code not in retryable_statuses:
            break
        if attempt < attempts:
            time.sleep(_retry_delay(response, attempt))
    assert response is not None
    response.raise_for_status()

    root = ET.fromstring(response.text)
    papers: list[Paper] = []
    seen: set[str] = set()

    for entry in root.findall(f"{ATOM}entry"):
        paper = _parse_entry(entry)
        if paper.arxiv_id in seen:
            continue
        seen.add(paper.arxiv_id)
        if _parse_arxiv_time(paper.published_at) >= cutoff:
            papers.append(paper)

    return papers


def _parse_entry(entry: ET.Element) -> Paper:
    entry_id = _text(entry, f"{ATOM}id")
    arxiv_id = entry_id.rstrip("/").split("/")[-1]
    title = " ".join(_text(entry, f"{ATOM}title").split())
    abstract = " ".join(_text(entry, f"{ATOM}summary").split())
    published_at = _text(entry, f"{ATOM}published")
    updated_at = _text(entry, f"{ATOM}updated")
    authors = [
        _text(author, f"{ATOM}name")
        for author in entry.findall(f"{ATOM}author")
        if _text(author, f"{ATOM}name")
    ]
    categories = [
        category.attrib.get("term", "")
        for category in entry.findall(f"{ATOM}category")
        if category.attrib.get("term")
    ]
    pdf_url = ""
    for link in entry.findall(f"{ATOM}link"):
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href", "")
            break
    if not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        categories=categories,
        published_at=published_at,
        updated_at=updated_at,
        abs_url=f"https://arxiv.org/abs/{arxiv_id}",
        pdf_url=pdf_url,
    )


def _text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text.strip() if child is not None and child.text else ""


def _retry_delay(response: requests.Response | None, attempt: int) -> int:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return min(int(retry_after), 300)
    return min(15 * (2 ** (attempt - 1)), 300)


def _parse_arxiv_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
