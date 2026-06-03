from __future__ import annotations

import sys
import time
from datetime import date

from .arxiv_client import fetch_recent_papers
from .config import AppConfig
from .database import Database
from .emailer import send_email
from .llm import LlmEvaluator
from .report import write_report


def _info(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def run_daily(config: AppConfig, no_email: bool = False, skip_llm: bool = False) -> dict:
    db = Database(config.storage.sqlite_path)
    db.init()
    run_id = db.start_run()
    errors: list[str] = []
    evaluated_count = 0
    included_count = 0
    today = date.today()
    started_at = time.monotonic()
    _info(
        f"[PaperPuller] 开始: 分类 {', '.join(config.arxiv.categories)}"
        f" | 模型 {config.llm.model}"
        f" | 回溯 {config.arxiv.fetch_days} 天"
    )
    try:
        papers = fetch_recent_papers(
            config.arxiv.categories,
            config.arxiv.fetch_days,
            keyword_queries=config.arxiv.keyword_queries,
            per_keyword_max_candidates=config.arxiv.per_keyword_max_candidates,
            request_pause_seconds=config.arxiv.request_pause_seconds,
            timeout_seconds=config.llm.timeout_seconds,
            max_retries=config.llm.max_retries,
        )
        new_count = db.upsert_papers(papers)
        _info(f"[Fetch] 共获取 {len(papers)} 篇，其中 {new_count} 篇为新论文")

        if not skip_llm:
            interest = config.interest_file.read_text(encoding="utf-8")
            evaluator = LlmEvaluator(config, interest)
            candidates = db.unevaluated_papers(config.llm.model)
            total = len(candidates)
            _info(f"[Eval] {total} 篇待评估")
            bar_width = 20
            for idx, paper in enumerate(candidates, start=1):
                evaluation = evaluator.evaluate(paper)
                db.save_evaluation(evaluation)
                evaluated_count += 1
                tags = ", ".join(evaluation.topic_tags)
                filled = int(idx / total * bar_width) if total else bar_width
                bar = "█" * filled + "░" * (bar_width - filled)
                msg = (
                    f"[Eval] [{bar}] {idx}/{total}"
                    f"  score={evaluation.score:.1f}  {paper.arxiv_id}  tags=[{tags}]"
                )
                print(f"\r{msg}\033[K", file=sys.stderr, end="", flush=True)
            print("", file=sys.stderr, flush=True)  # final newline
        else:
            _info("[Eval] 已跳过 (--skip-llm)")

        rows = db.report_rows(
            config.llm.model,
            config.ranking.possible_threshold,
            config.ranking.max_report_papers,
            report_date=today.isoformat(),
        )
        included_count = len(rows)
        report_path = write_report(config, today, rows)
        _info(f"[Report] {report_path} (含 {included_count} 篇)")

        email_status = "disabled"
        if config.email.enabled and not no_email:
            try:
                send_email(config, today, rows)
                db.mark_email(today.isoformat(), "sent", config.email.receiver)
                email_status = "sent"
                _info(f"[Email] 发送成功 → {config.email.receiver}")
            except Exception as error:
                db.mark_email(today.isoformat(), "failed", config.email.receiver, str(error))
                errors.append(f"email: {error}")
                email_status = "failed"
                _info(f"[Email] 发送失败: {error}")

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
        elapsed = time.monotonic() - started_at
        _info(
            f"[PaperPuller] 完成, 耗时 {elapsed:.1f}s"
            f" | 获取{len(papers)} 新增{new_count} 评估{evaluated_count} 纳入{included_count}"
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
