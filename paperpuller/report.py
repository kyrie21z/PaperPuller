from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import AppConfig

# (label, matcher) — first match wins.
TRACKS: list[tuple[str, object]] = []


def _register(label: str):
    def deco(fn):
        TRACKS.append((label, fn))
        return fn
    return deco


@_register("Must Read")
def _must_read(row: dict, cfg: AppConfig) -> bool:
    return (
        row["score"] >= cfg.ranking.high_priority_threshold
        and row.get("next_action", "") in ("read", "reproduce")
    )


@_register("Robust Recognition / Degradation")
def _robust(row: dict, _cfg: AppConfig) -> bool:
    challenges: list[str] = row.get("slpr_challenges", []) or []
    components: list[str] = row.get("pipeline_components", []) or []
    robust_ch = {"degradation", "occlusion", "domain_shift"}
    robust_cp = {"restoration", "domain_adaptation"}
    return bool(set(challenges) & robust_ch or set(components) & robust_cp)


@_register("Complex Layout / Structured Recognition")
def _layout(row: dict, _cfg: AppConfig) -> bool:
    challenges: list[str] = row.get("slpr_challenges", []) or []
    layout_ch = {"complex_layout", "multi_line", "vertical_text", "long_sequence", "mixed_script"}
    return bool(set(challenges) & layout_ch)


@_register("Visual Encoder / MAE Pretraining")
def _encoder(row: dict, _cfg: AppConfig) -> bool:
    components: list[str] = row.get("pipeline_components", []) or []
    return bool(set(components) & {"visual_encoder", "mae_pretraining"})


@_register("Semantic Enhancement / Decoder")
def _semantic(row: dict, _cfg: AppConfig) -> bool:
    components: list[str] = row.get("pipeline_components", []) or []
    return bool(set(components) & {"semantic_enhancement", "decoder"})


@_register("Data / Augmentation / Restoration")
def _data(row: dict, _cfg: AppConfig) -> bool:
    components: list[str] = row.get("pipeline_components", []) or []
    return bool(set(components) & {"data_augmentation", "restoration", "domain_adaptation", "benchmark_or_dataset"})


@_register("Reranking / Error Correction / Calibration")
def _rerank(row: dict, _cfg: AppConfig) -> bool:
    components: list[str] = row.get("pipeline_components", []) or []
    challenges: list[str] = row.get("slpr_challenges", []) or []
    return bool(set(components) & {"reranking", "error_correction"} or "similar_character_confusion" in challenges)


@_register("Related Work / Others")
def _others(_row: dict, _cfg: AppConfig) -> bool:
    return True


def _classify(rows: list[dict], config: AppConfig) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {label: [] for label, _ in TRACKS}
    assigned: set[int] = set()
    for idx, row in enumerate(rows):
        for label, matcher in TRACKS:
            if matcher(row, config):
                groups[label].append(row)
                assigned.add(idx)
                break
    groups = {label: papers for label, papers in groups.items() if papers}
    return groups


def render_markdown(config: AppConfig, report_date: date, rows: list[dict]) -> str:
    groups = _classify(rows, config)
    lines = [
        "# Daily arXiv Papers — SLPR Research Digest",
        "",
        f"Date: {report_date.isoformat()}",
        f"Model: `{config.llm.model}`",
        f"Categories: {', '.join(config.arxiv.categories)}",
        f"Included papers: {len(rows)}",
        "",
    ]
    for label, _ in TRACKS:
        papers = groups.get(label, [])
        if papers:
            lines.extend(_section(label, papers))
    return "\n".join(lines).rstrip() + "\n"


def write_report(config: AppConfig, report_date: date, rows: list[dict]) -> Path:
    config.storage.report_dir.mkdir(parents=True, exist_ok=True)
    path = config.storage.report_dir / f"{report_date.isoformat()}.md"
    path.write_text(render_markdown(config, report_date, rows), encoding="utf-8")
    return path


def _section(title: str, rows: list[dict]) -> list[str]:
    lines = [f"## {title}", f"", f"_{len(rows)} paper(s)_", ""]
    for index, row in enumerate(rows, start=1):
        authors = ", ".join(row["authors"][:6])
        if len(row["authors"]) > 6:
            authors += ", et al."
        slpr_ch = ", ".join(row.get("slpr_challenges", []) or []) or "—"
        pipeline_cp = ", ".join(row.get("pipeline_components", []) or []) or "—"
        integration = row.get("integration_path", "") or "unknown"
        reproducibility = row.get("reproducibility", "unknown") or "unknown"
        next_action = row.get("next_action", "skim") or "skim"
        lines.extend(
            [
                f"### {index}. {row['title']}",
                "",
                f"| Field | Value |",
                f"|---|---|",
                f"| Score | {row['score']:.1f} |",
                f"| Tags | {', '.join(row['topic_tags'])} |",
                f"| SLPR Challenges | {slpr_ch} |",
                f"| Pipeline Components | {pipeline_cp} |",
                f"| Integration Path | {integration} |",
                f"| Reproducibility | {reproducibility} |",
                f"| Next Action | {next_action} |",
                f"| Authors | {authors} |",
                f"| arXiv | [{row['arxiv_id']}]({row['abs_url']}) |",
                f"| PDF | [link]({row['pdf_url']}) |",
                f"| TL;DR | {row['tldr']} |",
                f"| Reason | {row['reason']} |",
                "",
            ]
        )
    return lines
