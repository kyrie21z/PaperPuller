# PaperPuller Generalization Design

## Goal

Transform PaperPuller from an SLPR-specific arXiv paper monitoring tool into a general-purpose framework where any researcher can track papers in their own domain by providing their own `interest.md` configuration file.

## Design Philosophy

PaperPuller stays simple and domain-agnostic. All personalization (research interests, evaluation criteria, grouping logic, extra output fields) lives in `interest.md`. The user (or their AI assistant, e.g., ChatGPT) generates this file — PaperPuller just reads and executes.

---

## Changes Summary

| File | Change |
|---|---|
| `paperpuller/models.py` | Replace 5 SLPR fields with `group: str` + `extra: dict` |
| `paperpuller/llm.py` | Generic prompt template, parse `extra` + `group` |
| `paperpuller/tags.py` | Parse optional `## Local Keywords` section from `interest.md` |
| `paperpuller/database.py` | Add `group` + `extra_json` columns, migration to move old data |
| `paperpuller/report.py` | Group by `group` field, render `extra` as key-value rows |
| `paperpuller/config.py` | Remove SLPR defaults from `DEFAULT_KEYWORD_QUERIES` |
| `config/paperpuller.yaml` | Replace SLPR keywords with generic examples |
| `config/interest.md` → `config/interest.template.md` | Rename, serve as template for users |

---

## Detailed Design

### 1. `interest.md` Structure

The file serves as the single source of personalization. It has optional sections that PaperPuller parses:

```markdown
# Research Interest Profile

<free-form description of research area, problems, preferences>

## Evaluation Criteria

<what makes a paper high/low score — used directly in LLM prompt>

## Groups

- Group A: <description of papers that belong here>
- Group B: <description>
- ...

## Local Keywords (optional)

- TagName1: keyword1, keyword2, ...
- TagName2: keyword3, keyword4, ...

## Extra Fields (optional)

<description of additional JSON fields the LLM should return in the `extra` object>
```

### 2. LLM Prompt Template

Universal prompt that references `interest.md` content dynamically:

```
Interest profile:
{full text of interest.md}

Paper:
Title: {title}
Authors: {authors}
Categories: {categories}
Abstract: {abstract}
{Local keyword tags line, only if ## Local Keywords section exists}

Return strict JSON with exactly these keys:
- score: integer 1-10 (1=irrelevant, 10=must-read)
- topic_tags: array of short tags matching the interest profile's topics
- group: one group name from the interest profile's defined groups, or "Other"
- reason: one sentence explaining relevance (or lack thereof)
- tldr: 1-2 sentence summary of the paper's contribution
- extra: object containing any additional fields described in the interest profile, or empty object {}
```

### 3. Domain Models (`models.py`)

```python
@dataclass(frozen=True)
class Evaluation:
    arxiv_id: str
    model: str
    score: float
    topic_tags: list[str]
    reason: str
    tldr: str
    group: str = "Other"
    extra: dict = field(default_factory=dict)
```

Five SLPR-specific fields removed: `slpr_challenges`, `pipeline_components`, `integration_path`, `reproducibility`, `next_action`.

Replaced by:
- `group`: LLM-assigned category from the interest profile's Groups section
- `extra`: free-form JSON object for any domain-specific data

### 4. Database Schema (`database.py`)

New `evaluations` table:
```sql
CREATE TABLE IF NOT EXISTS evaluations (
    arxiv_id TEXT NOT NULL,
    model TEXT NOT NULL,
    score REAL NOT NULL,
    topic_tags_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    tldr TEXT NOT NULL,
    "group" TEXT NOT NULL DEFAULT 'Other',
    extra_json TEXT NOT NULL DEFAULT '{}',
    evaluated_at TEXT NOT NULL,
    PRIMARY KEY (arxiv_id, model),
    FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
);
```

**Migration** (runs on `Database.init()`):
1. Check if old SLPR columns exist (`slpr_challenges_json`, etc.)
2. If yes:
   - Read old data from all rows
   - Pack `slpr_challenges`, `pipeline_components`, `integration_path`, `reproducibility`, `next_action` into `extra_json`
   - Set `group` based on existing report track logic (first matching track label)
   - `ALTER TABLE ... DROP COLUMN` for each old column
3. If no: skip (new users)

### 5. Local Keywords (`tags.py`)

Parse `## Local Keywords` section from `interest.md` at startup:

```python
def parse_keywords(interest_text: str) -> dict[str, list[str]]:
    """Extract keyword groups from ## Local Keywords section."""
    # Returns {tag_name: [keywords]} or empty dict if section absent
```

Function `local_topic_tags(title, abstract, keywords)` returns matched tag names. If no keywords configured, returns empty list and the line is omitted from the LLM prompt.

### 6. Report (`report.py`)

- Title: `# Daily arXiv Papers — {first line of interest.md or "Research Digest"}`
- Papers grouped by the `group` field (LLM-assigned), then by score threshold (High Priority ≥ `high_priority_threshold`, Possibly Relevant ≥ `possible_threshold`)
- Each paper card renders:
  - Universal fields: Score, Tags, Group, TL;DR, Reason, Authors, arXiv link, PDF link
  - `extra` fields rendered as additional key-value rows in the table
- Track matcher functions removed — grouping is purely data-driven

### 7. Config (`config.py`)

`DEFAULT_KEYWORD_QUERIES` changed from SLPR-specific list to generic:
```python
DEFAULT_KEYWORD_QUERIES: list[str] = []
```

### 8. ChatGPT Prompt Template

A new file `config/CHATGPT_PROMPT.md` containing instructions users can send to any AI assistant with memory (ChatGPT, Claude, etc.) to generate their personalized `interest.md` and `paperpuller.yaml`:

```
I'm setting up PaperPuller (https://github.com/...), a tool that fetches
arXiv papers and uses an LLM to score them based on my research interests.
Please help me generate my personalized configuration files by asking me
questions about my research area, then producing:
1. config/interest.md — my research profile
2. Relevant sections of config/paperpuller.yaml — keywords, categories, thresholds

[Template of interest.md structure]
[Template of relevant YAML sections]
```

---

## Migration Path

1. Existing users: `Database.init()` auto-migrates old SLPR data into `extra_json` + `group` on next run
2. Existing `interest.md`: rename to `interest.template.md`, current users keep their file as-is (it still works — `## Local Keywords`, `## Groups`, `## Extra Fields` sections are optional)
3. Reports: old reports can still be regenerated — `extra_json` contains all old fields for backward-compatible rendering

---

## Out of Scope

- Web UI or dashboard
- Multi-user support
- Config validation UI
- Automatic `interest.md` generation (handled by user's external AI assistant)
