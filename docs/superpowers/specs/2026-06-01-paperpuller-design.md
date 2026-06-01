# PaperPuller Design

Date: 2026-06-01

## Goal

PaperPuller will run daily and collect recent arXiv papers related to OCR, scene text recognition, vision transformers, masked autoencoders, and data augmentation. It will rank papers by relevance using an OpenAI-compatible API, store structured history in SQLite, generate Markdown daily reports, and optionally send the report by email.

The project will be based on `JoeLeelyf/customize-arxiv-daily` instead of a full rewrite. The upstream project will be cloned into `vendor/customize-arxiv-daily`, and PaperPuller will add a local adaptation layer around it.

## Scope

In scope:

- Use `customize-arxiv-daily` as the implementation base.
- Pull broad recent paper candidates from arXiv.
- Score and summarize candidates with an OpenAI-compatible API.
- Store paper metadata, scores, tags, summaries, and email state in SQLite.
- Generate `reports/YYYY-MM-DD.md`.
- Keep email delivery available through SMTP.
- Support local Windows scheduling first.
- Keep GitHub Actions support available as a later deployment path.

Out of scope for the first implementation:

- Building a web UI.
- Downloading and storing PDFs.
- Full-text paper parsing.
- Zotero integration.
- Multi-user accounts or hosted service behavior.

## Chosen Approach

Use approach 1: directly adapt `customize-arxiv-daily` while preserving its core flow.

This gives a faster working baseline than a rewrite because the upstream project already handles arXiv retrieval, custom interest descriptions, LLM-based recommendation, local Markdown saving, and email delivery. PaperPuller will add persistence, repeatable configuration, scheduling scripts, and report conventions needed for long-term local use.

## Repository Layout

Expected structure:

```text
PaperPuller/
  config/
    interest.md
    paperpuller.yaml
  data/
    papers.sqlite3
  docs/
    superpowers/
      specs/
        2026-06-01-paperpuller-design.md
  reports/
    YYYY-MM-DD.md
  scripts/
    run_daily.ps1
  vendor/
    customize-arxiv-daily/
  .github/
    workflows/
      daily.yml
```

The `vendor/customize-arxiv-daily` directory will hold the cloned upstream project. PaperPuller-specific files live outside `vendor` so upstream code and local adaptation remain clearly separated.

## Data Flow

1. The daily command reads `config/paperpuller.yaml` and `config/interest.md`.
2. It pulls recent arXiv papers from configured categories using broad recall.
3. It normalizes arXiv metadata into a local paper record.
4. SQLite deduplicates papers by arXiv ID and records first-seen and last-seen timestamps.
5. New or unscored papers are sent to the OpenAI-compatible API for relevance scoring, topic tagging, a short reason, and a TL;DR.
6. The database stores score, tags, reason, TL;DR, and processing status.
7. A Markdown report is generated under `reports/`.
8. If email is enabled, the same ranked result set is sent by SMTP.
9. If email fails after report generation, the failure is logged without duplicating paper records.

## Configuration

Configuration will be centralized in `config/paperpuller.yaml`. Secrets will be read from environment variables and will not be committed.

Default configuration:

- arXiv categories: `cs.CV`, `cs.AI`, `cs.LG`
- fetch window: last 2 days
- candidate cap: 100 papers per run
- display threshold: score >= 7
- interest file: `config/interest.md`
- SQLite path: `data/papers.sqlite3`
- report directory: `reports/`
- email enabled: configurable

LLM settings:

- `base_url`
- `model`
- `api_key_env`
- `temperature`
- request timeout and retry limits

Email settings:

- `enabled`
- SMTP server and port
- sender and receiver
- sender password environment variable
- subject template

## Interest Profile

`config/interest.md` will describe wanted and unwanted papers in natural language.

Wanted topics:

- OCR and document understanding.
- Scene text recognition.
- Vision transformers and transformer-based visual recognition.
- Masked autoencoders and self-supervised visual pretraining.
- Data augmentation, synthetic data, and robustness for visual recognition.

Unwanted topics can be added to reduce noise, for example robotics-only papers, general LLM papers with no visual recognition contribution, or pure medical imaging papers if they are not useful.

## Filtering and Ranking

The arXiv retrieval stage will use broad recall rather than narrow keyword-only search. The local pipeline will then enrich and rank papers.

Ranking stages:

1. Lightweight local keyword tagging for OCR, STR, ViT, MAE, augmentation, synthetic data, and related terms.
2. LLM scoring using title, abstract, arXiv categories, and local keyword hits.
3. Final sorting by score, then publish date.

The LLM response should produce:

- `score`: integer from 1 to 10
- `topic_tags`: list such as OCR, STR, ViT, MAE, Augmentation, Other
- `reason`: one-sentence recommendation reason
- `tldr`: concise summary

Reports will group papers into:

- High priority
- Possibly relevant
- Low relevance, hidden or summarized depending on configuration

## SQLite Storage

SQLite will be the durable source of truth for deduplication and history.

Minimum tables:

- `papers`: arXiv ID, title, authors, abstract, categories, published date, updated date, PDF URL, abs URL, first seen date, last seen date.
- `evaluations`: paper ID, model, score, topic tags, reason, TL;DR, evaluated at.
- `runs`: run ID, start time, end time, status, counts, error summary.
- `email_deliveries`: report date, sent at, status, recipient, error message.

The first implementation can keep the schema compact, but it must support rerunning a day without duplicating papers.

## Reports

Markdown reports will be written as `reports/YYYY-MM-DD.md`.

Each report should include:

- Run date and configuration summary.
- Counts for fetched, new, evaluated, included, and emailed papers.
- High-priority papers sorted by score.
- Possibly relevant papers sorted by score.
- For each paper: title, authors, arXiv link, PDF link, score, tags, TL;DR, and reason.

Reports should be deterministic for the same database state and configuration.

## Email Behavior

Email remains available and optional.

Rules:

- `email.enabled` controls delivery.
- Email should include high-priority and possibly relevant papers only.
- Markdown and SQLite generation must not depend on successful email delivery.
- If SMTP fails, the run records the failure and exits with a status that makes the failure visible.
- The database tracks whether a report was sent so a later retry can avoid duplicate delivery when configured to do so.

## Deployment

Primary deployment is local Windows scheduling.

Manual run:

```powershell
python -m paperpuller run --config config/paperpuller.yaml
```

Run without email:

```powershell
python -m paperpuller run --no-email
```

Regenerate a report:

```powershell
python -m paperpuller report --date YYYY-MM-DD
```

Windows scheduled task:

```powershell
scripts/run_daily.ps1
```

GitHub Actions will be kept as a future deployment path. It will use repository secrets for API and SMTP credentials and commit generated reports when enabled.

## Error Handling

Expected failure modes:

- arXiv request failure.
- LLM API timeout or invalid response.
- SQLite write failure.
- Markdown generation failure.
- SMTP failure.

Handling rules:

- Failures are recorded in the run log and `runs` table.
- arXiv and LLM calls should have bounded retries.
- A failed LLM evaluation should not corrupt paper metadata.
- A failed email send should not remove or rewrite the generated report.
- Reruns should reuse existing paper metadata and only fill missing evaluation or delivery state.

## Testing

Unit tests:

- Configuration parsing.
- arXiv metadata normalization.
- SQLite insert and deduplication.
- LLM response parsing and validation.
- Markdown report rendering.

Integration tests:

- Run the full pipeline with mock arXiv records and mocked LLM responses.
- Verify that rerunning the same input does not duplicate papers.
- Verify that email failure does not prevent report creation.

Manual smoke tests:

- Real arXiv fetch with a small candidate cap, such as 5 papers.
- LLM evaluation with a low candidate cap.
- Report generation with email disabled.
- Optional SMTP test after credentials are configured.

## Open Decisions

These decisions can be made during implementation without changing the architecture:

- Exact OpenAI-compatible provider and model name.
- Exact score thresholds for high-priority and possibly relevant sections.
- Whether low-relevance papers are hidden completely or rendered in a collapsed report section.
- Whether GitHub Actions is enabled in the first implementation or only scaffolded.

