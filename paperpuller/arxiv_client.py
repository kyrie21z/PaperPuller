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


def fetch_recent_papers(
    categories: list[str],
    fetch_days: int,
    max_candidates: int,
    timeout_seconds: int = 30,
    max_retries: int = 3,
) -> list[Paper]:
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": build_query(categories),
        "start": 0,
        "max_results": max_candidates,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    headers = {"User-Agent": "PaperPuller/0.1 (local research paper digest)"}
    response = None
    for attempt in range(1, max_retries + 1):
        response = requests.get(url, params=params, headers=headers, timeout=timeout_seconds)
        if response.status_code not in {429, 500, 502, 503, 504}:
            break
        if attempt < max_retries:
            time.sleep(3 * attempt)
    assert response is not None
    response.raise_for_status()

    cutoff = datetime.now(timezone.utc) - timedelta(days=fetch_days)
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


def _parse_arxiv_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
