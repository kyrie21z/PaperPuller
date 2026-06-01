from __future__ import annotations

from datetime import date

from .arxiv_client import fetch_recent_papers
from .config import AppConfig
from .database import Database
from .emailer import send_email
from .llm import LlmEvaluator
from .report import write_report


def run_daily(config: AppConfig, no_email: bool = False, skip_llm: bool = False) -> dict:
    db = Database(config.storage.sqlite_path)
    db.init()
    run_id = db.start_run()
    errors: list[str] = []
    evaluated_count = 0
    included_count = 0
    today = date.today()
    try:
        papers = fetch_recent_papers(
            config.arxiv.categories,
            config.arxiv.fetch_days,
            config.arxiv.max_candidates,
            timeout_seconds=config.llm.timeout_seconds,
            max_retries=config.llm.max_retries,
        )
        new_count = db.upsert_papers(papers)

        if not skip_llm:
            interest = config.interest_file.read_text(encoding="utf-8")
            evaluator = LlmEvaluator(config, interest)
            for paper in db.unevaluated_papers(config.llm.model):
                evaluation = evaluator.evaluate(paper)
                db.save_evaluation(evaluation)
                evaluated_count += 1

        rows = db.report_rows(
            config.llm.model,
            config.ranking.possible_threshold,
            config.ranking.max_report_papers,
            report_date=today.isoformat(),
        )
        included_count = len(rows)
        report_path = write_report(config, today, rows)

        email_status = "disabled"
        if config.email.enabled and not no_email:
            try:
                send_email(config, today, rows)
                db.mark_email(today.isoformat(), "sent", config.email.receiver)
                email_status = "sent"
            except Exception as error:
                db.mark_email(today.isoformat(), "failed", config.email.receiver, str(error))
                errors.append(f"email: {error}")
                email_status = "failed"

        status = "failed" if errors else "success"
        db.finish_run(
            run_id,
            status,
            fetched_count=len(papers),
            new_count=new_count,
            evaluated_count=evaluated_count,
            included_count=included_count,
            error_summary="; ".join(errors),
        )
        return {
            "status": status,
            "report_path": str(report_path),
            "fetched_count": len(papers),
            "new_count": new_count,
            "evaluated_count": evaluated_count,
            "included_count": included_count,
            "email_status": email_status,
        }
    except Exception as error:
        db.finish_run(
            run_id,
            "failed",
            fetched_count=0,
            new_count=0,
            evaluated_count=evaluated_count,
            included_count=included_count,
            error_summary=str(error),
        )
        raise


def regenerate_report(config: AppConfig, report_date: date) -> str:
    db = Database(config.storage.sqlite_path)
    db.init()
    rows = db.report_rows(
        config.llm.model,
        config.ranking.possible_threshold,
        config.ranking.max_report_papers,
        report_date=report_date.isoformat(),
    )
    return str(write_report(config, report_date, rows))
