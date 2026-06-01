# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

PaperPuller pulls recent arXiv papers for computer vision subfields (OCR, STR, ViT, MAE, data augmentation), scores them with an OpenAI-compatible LLM, persists results to SQLite, and produces a daily Markdown report. It optionally emails the report via SMTP.

The project depends on (but does not modify) the upstream `JoeLeelyf/customize-arxiv-daily` repo vendored at `vendor/customize-arxiv-daily`. All real logic lives under `paperpuller/`.

## Commands

```bash
# Install (editable, with test deps)
pip install -e .[dev]

# Run tests
python -m pytest -q

# Dry-run: fetch 1 candidate, no email, real LLM
python -m paperpuller run --config config/paperpuller.yaml --no-email --max-candidates 1 --fetch-days 30

# Skip LLM entirely, just test fetch + SQLite + report
python -m paperpuller run --config config/paperpuller.yaml --no-email --skip-llm --max-candidates 5 --fetch-days 30

# Full production run
python -m paperpuller run --config config/paperpuller.yaml

# Regenerate a past day's Markdown report from SQLite
python -m paperpuller report --config config/paperpuller.yaml --date 2026-06-01
```

The CLI entry point is `paperpuller.cli:main`, also wired as the `paperpuller` console script in `pyproject.toml`.

On Linux, use `python3` if `python` is not available.

Scheduled execution:
- Windows: `scripts/run_daily.ps1` (Task Scheduler)
- Linux: `scripts/run_daily.sh` (cron or systemd timer)

## Architecture

### Pipeline (the main loop)

`paperpuller.pipeline.run_daily()` orchestrates the end-to-end flow:

1. **Fetch** — `arxiv_client.fetch_recent_papers()` queries the arXiv API. It first fetches by category (`build_query`), then issues one API call per keyword (`build_keyword_query`). Results are deduplicated by `arxiv_id` and filtered by `published_at` cutoff. Retries with exponential backoff on 429/5xx.
2. **Store** — `Database.upsert_papers()` inserts new papers and refreshes metadata for existing ones (upsert on `arxiv_id`).
3. **Evaluate** — `LlmEvaluator.evaluate()` sends each unevaluated paper to the configured LLM with the `config/interest.md` profile as the system prompt. The LLM returns JSON with `score`, `topic_tags`, `reason`, `tldr`. Results are saved to the `evaluations` table keyed on `(arxiv_id, model)`.
4. **Report** — `Database.report_rows()` joins papers to evaluations above the `possible_threshold`. `report.write_report()` renders them as Markdown with High Priority / Possibly Relevant sections.
5. **Email** — If enabled and not skipped, `emailer.send_email()` delivers an HTML rendering via SMTP.

### Module responsibilities

| Module | Role |
|---|---|
| `config.py` | YAML loading into frozen `AppConfig` dataclass tree. Relative paths (e.g. `data/papers.sqlite3`) are resolved against the config file's parent directory. |
| `models.py` | Immutable `Paper` and `Evaluation` dataclasses — the two core domain types. |
| `arxiv_client.py` | Raw arXiv API integration (Atom XML parsing, retry logic, keyword & category query builders). |
| `database.py` | SQLite wrapper with `SCHEMA` (tables: `papers`, `evaluations`, `runs`, `email_deliveries`). List columns are JSON-encoded. `upsert_papers` returns a dedup count. |
| `llm.py` | OpenAI-compatible client. Requires `PAPERPULLER_API_KEY` env var. Uses `response_format={"type": "json_object"}`. Clamps scores to [0,10]. |
| `tags.py` | Pure local keyword matching against title+abstract — used inside the LLM prompt to prime the model. Not used for filtering. |
| `report.py` | Markdown rendering. Groups papers by `high_priority_threshold` / `possible_threshold`. |
| `emailer.py` | SMTP delivery with HTML rendering. Port 465 → SSL, otherwise STARTTLS. Strips spaces from Gmail app passwords. |
| `pipeline.py` | Top-level orchestration: wires fetch → store → evaluate → report → email, records a run in the `runs` table. |
| `cli.py` | argparse CLI with `run` and `report` subcommands. CLI flags override frozen config by creating new dataclass instances via `dataclasses.replace`. |

### Config patterns

- `config/paperpuller.yaml` contains all runtime settings. Secrets are **never** in this file — only environment variable names (e.g. `api_key_env: PAPERPULLER_API_KEY`).
- Config is loaded as a frozen dataclass tree. CLI overrides use `dataclasses.replace()` to create modified copies.
- `config/interest.md` is read at runtime and passed directly as part of the LLM prompt.

### Database conventions

- `authors`, `categories`, `topic_tags` are stored as JSON text columns (suffixed `_json`).
- `first_seen_at` / `last_seen_at` track when a paper first appeared and was last refreshed.
- `runs` table records each invocation with counts and status, for observability.
- Evaluations are keyed by `(arxiv_id, model)` — same paper can have evaluations from different models.

## Key design decisions

- **All domain types are frozen dataclasses** — they're never mutated after construction. CLI overrides create new instances.
- **The upstream vendor directory is read-only** — PaperPuller wraps the concept (arXiv fetching + LLM scoring) into its own pipeline but does not import from `vendor/`.
- **LLM evaluation is idempotent** — `save_evaluation` uses `ON CONFLICT ... DO UPDATE`, so re-running with the same model overwrites previous scores.
- **The LLM prompt includes local keyword tags** (`tags.py`) to help the model, but the pipeline itself filters only on the model's numeric score.
