# PaperPuller

PaperPuller pulls recent arXiv papers, ranks them against an OCR/STR/ViT/MAE/data-augmentation interest profile with an OpenAI-compatible API, stores history in SQLite, writes Markdown reports, and can send the report by SMTP email.

The upstream reference project is cloned locally under `vendor/customize-arxiv-daily`. PaperPuller keeps its own wrapper and persistence layer outside `vendor`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

Set API credentials:

```powershell
$env:PAPERPULLER_API_KEY = "..."
```

Optional SMTP credentials:

```powershell
$env:PAPERPULLER_SMTP_PASSWORD = "..."
```

Edit `config/paperpuller.yaml` for model, API base URL, email settings, and thresholds.

## Run

```powershell
python -m paperpuller run --config config/paperpuller.yaml --no-email
```

Small smoke test without LLM or email:

```powershell
python -m paperpuller run --config config/paperpuller.yaml --no-email --skip-llm --max-candidates 5
```

Regenerate a report from the database:

```powershell
python -m paperpuller report --date 2026-06-01
```

Windows scheduled runs use:

```powershell
scripts/run_daily.ps1
```

## Vendor Bootstrap

If `vendor/customize-arxiv-daily` is missing, clone it with:

```powershell
git clone https://github.com/JoeLeelyf/customize-arxiv-daily.git vendor/customize-arxiv-daily
```
