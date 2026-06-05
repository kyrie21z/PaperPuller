from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import date
import json

from .config import load_config
from .pipeline import regenerate_report, run_daily


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paperpuller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Fetch, evaluate, report, and optionally email papers.")
    run_parser.add_argument("--config", default="config/paperpuller.yaml")
    run_parser.add_argument("--no-email", action="store_true")
    run_parser.add_argument("--skip-llm", action="store_true", help="Fetch and report from existing evaluations only.")
    run_parser.add_argument("--max-candidates", type=int, help="Override the configured arXiv candidate cap.")
    run_parser.add_argument("--per-keyword-max-candidates", type=int, help="Override the configured arXiv keyword candidate cap.")
    run_parser.add_argument("--fetch-days", type=int, help="Override the configured arXiv fetch window.")
    run_parser.add_argument("--request-pause-seconds", type=float, help="Override the pause between arXiv requests.")
    run_parser.add_argument("--timeout-seconds", type=int, help="Override HTTP/API timeout seconds.")

    report_parser = subparsers.add_parser("report", help="Regenerate a Markdown report from SQLite.")
    report_parser.add_argument("--config", default="config/paperpuller.yaml")
    report_parser.add_argument("--date", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)

    if args.command == "run":
        if (
            args.max_candidates is not None
            or args.per_keyword_max_candidates is not None
            or args.fetch_days is not None
            or args.request_pause_seconds is not None
        ):
            config = replace(
                config,
                arxiv=replace(
                    config.arxiv,
                    max_candidates=args.max_candidates or config.arxiv.max_candidates,
                    per_keyword_max_candidates=(
                        args.per_keyword_max_candidates
                        or config.arxiv.per_keyword_max_candidates
                    ),
                    fetch_days=args.fetch_days or config.arxiv.fetch_days,
                    request_pause_seconds=(
                        args.request_pause_seconds
                        if args.request_pause_seconds is not None
                        else config.arxiv.request_pause_seconds
                    ),
                ),
            )
        if args.timeout_seconds is not None:
            config = replace(
                config,
                arxiv=replace(config.arxiv, timeout_seconds=args.timeout_seconds),
                llm=replace(config.llm, timeout_seconds=args.timeout_seconds),
            )
        result = run_daily(config, no_email=args.no_email, skip_llm=args.skip_llm)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "success" else 1

    if args.command == "report":
        report_path = regenerate_report(config, date.fromisoformat(args.date))
        print(report_path)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
