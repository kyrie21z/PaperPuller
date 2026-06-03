from __future__ import annotations

import re


def parse_keywords(interest_text: str) -> dict[str, list[str]]:
    """Extract keyword groups from an optional ``## Local Keywords`` section.

    Expected format::

        ## Local Keywords
        - TagName: keyword1, keyword2, ...
        - AnotherTag: keyword3, ...

    Returns ``{tag_name: [keywords]}`` or an empty dict when the section is
    absent or contains no entries.
    """
    section = _extract_section(interest_text, "Local Keywords")
    if not section:
        return {}

    keywords: dict[str, list[str]] = {}
    for line in section.splitlines():
        match = re.match(r"^\s*-\s*(.+?)\s*:\s*(.+)", line)
        if not match:
            continue
        tag = match.group(1).strip()
        raw = match.group(2).strip()
        terms = [t.strip().lower() for t in raw.split(",") if t.strip()]
        if tag and terms:
            keywords[tag] = terms
    return keywords


def local_topic_tags(
    title: str,
    abstract: str,
    keywords: dict[str, list[str]] | None = None,
) -> list[str]:
    """Return tag names whose keywords appear in *title* or *abstract*.

    When *keywords* is empty or ``None``, returns an empty list.
    """
    if not keywords:
        return []

    haystack = f"{title}\n{abstract}".lower()
    tags = [
        tag
        for tag, terms in keywords.items()
        if any(term in haystack for term in terms)
    ]
    return tags


def _extract_section(text: str, heading: str) -> str | None:
    """Return the content under a markdown heading like ``## {heading}``.

    Stops at the next heading of equal or higher level (``##`` or ``#``).
    Returns ``None`` when the heading is not found.
    """
    pattern = rf"^##\s+{re.escape(heading)}\s*$(.+?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()
