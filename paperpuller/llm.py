from __future__ import annotations

import json
import os
import time

from openai import OpenAI

from .config import AppConfig
from .models import Evaluation, Paper
from .tags import local_topic_tags


class LlmEvaluator:
    def __init__(self, config: AppConfig, interest: str):
        api_key = os.environ.get(config.llm.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {config.llm.api_key_env}")
        self.config = config
        self.interest = interest
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.llm.base_url,
            timeout=config.llm.timeout_seconds,
            max_retries=0,
        )

    def evaluate(self, paper: Paper) -> Evaluation:
        prompt = self._build_prompt(paper)
        last_error: Exception | None = None
        for attempt in range(1, self.config.llm.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.llm.model,
                    temperature=self.config.llm.temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You rank arXiv papers for a research reading workflow. Return strict JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                content = response.choices[0].message.content or "{}"
                data = json.loads(content)
                return _parse_evaluation(paper.arxiv_id, self.config.llm.model, data)
            except Exception as error:
                last_error = error
                if attempt < self.config.llm.max_retries:
                    time.sleep(attempt)
        raise RuntimeError(f"LLM evaluation failed for {paper.arxiv_id}: {last_error}")

    def _build_prompt(self, paper: Paper) -> str:
        local_tags = ", ".join(local_topic_tags(paper.title, paper.abstract))
        return f"""
Interest profile:
{self.interest}

Paper:
Title: {paper.title}
Authors: {", ".join(paper.authors)}
Categories: {", ".join(paper.categories)}
Local keyword tags: {local_tags}
Abstract: {paper.abstract}

Return strict JSON with exactly these keys:
- score: integer 1-10 (1=irrelevant, 10=must-read for my SLPR research)
- topic_tags: array of short tags, choose from: OCR, STR, SLPR, ViT, MAE, Augmentation, Restoration, Semantic, Decoder, Reranking, ErrorCorrection, Benchmark, Analysis, Other
- slpr_challenges: array of zero or more from ["degradation", "occlusion", "complex_layout", "multi_line", "vertical_text", "long_sequence", "mixed_script", "similar_character_confusion", "domain_shift", "other"]
- pipeline_components: array of zero or more from ["visual_encoder", "mae_pretraining", "semantic_enhancement", "decoder", "data_augmentation", "restoration", "domain_adaptation", "reranking", "error_correction", "benchmark_or_dataset", "analysis_only", "other"]
- integration_path: one of "pretrain", "finetune", "data", "decoder", "postprocess", "evaluation", "related_work", "ignore"
- reproducibility: one of "high", "medium", "low", "unknown"
- next_action: one of "read", "skim", "reproduce", "related_work", "ignore"
- reason: one sentence explaining relevance (or lack thereof) to my SLPR research
- tldr: 1-2 sentence summary of the paper's contribution
""".strip()


def _parse_evaluation(arxiv_id: str, model: str, data: dict) -> Evaluation:
    score = float(data.get("score", 0))
    score = max(0.0, min(10.0, score))
    topic_tags = _parse_str_list(data.get("topic_tags"), fallback=["Other"])
    slpr_challenges = _parse_str_list(data.get("slpr_challenges"))
    pipeline_components = _parse_str_list(data.get("pipeline_components"))
    integration_path = str(data.get("integration_path", "")).strip()
    reproducibility = str(data.get("reproducibility", "unknown")).strip()
    next_action = str(data.get("next_action", "skim")).strip()
    return Evaluation(
        arxiv_id=arxiv_id,
        model=model,
        score=score,
        topic_tags=topic_tags,
        reason=str(data.get("reason", "")).strip(),
        tldr=str(data.get("tldr", "")).strip(),
        slpr_challenges=slpr_challenges,
        pipeline_components=pipeline_components,
        integration_path=integration_path or "",
        reproducibility=reproducibility or "unknown",
        next_action=next_action or "skim",
    )


def _parse_str_list(value: object, fallback: list[str] | None = None) -> list[str]:
    if fallback is None:
        fallback = []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
        return parts if parts else fallback
    return fallback

