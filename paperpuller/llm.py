from __future__ import annotations

import json
import os
import time

from openai import OpenAI

from .config import AppConfig
from .models import Evaluation, Paper
from .tags import local_topic_tags


class LlmEvaluator:
    def __init__(
        self,
        config: AppConfig,
        interest: str,
        keywords: dict[str, list[str]] | None = None,
    ):
        api_key = os.environ.get(config.llm.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {config.llm.api_key_env}")
        self.config = config
        self.interest = interest
        self.keywords = keywords or {}
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
        parts = [
            "Interest profile:",
            self.interest,
            "",
            "Paper:",
            f"Title: {paper.title}",
            f"Authors: {', '.join(paper.authors)}",
            f"Categories: {', '.join(paper.categories)}",
        ]
        if self.keywords:
            matched = local_topic_tags(paper.title, paper.abstract, self.keywords)
            if matched:
                parts.append(f"Local keyword tags: {', '.join(matched)}")
        parts.append(f"Abstract: {paper.abstract}")
        parts.append(
            "Return strict JSON with exactly these keys:\n"
            "- score: integer 1-10 (1=irrelevant, 10=must-read)\n"
            "- topic_tags: array of short tags matching the interest profile's topics\n"
            "- group: one group name from the interest profile's defined groups, or \"Other\"\n"
            "- reason: one sentence explaining relevance (or lack thereof)\n"
            "- tldr: 1-2 sentence summary of the paper's contribution\n"
            "- extra: object containing any additional fields described in the interest profile, or empty object {}"
        )
        return "\n".join(parts)


def _parse_evaluation(arxiv_id: str, model: str, data: dict) -> Evaluation:
    score = float(data.get("score", 0))
    score = max(0.0, min(10.0, score))
    topic_tags = _parse_str_list(data.get("topic_tags"), fallback=["Other"])
    group = str(data.get("group", "")).strip() or "Other"
    extra = data.get("extra")
    if not isinstance(extra, dict):
        extra = {}
    return Evaluation(
        arxiv_id=arxiv_id,
        model=model,
        score=score,
        topic_tags=topic_tags,
        reason=str(data.get("reason", "")).strip(),
        tldr=str(data.get("tldr", "")).strip(),
        group=group,
        extra=extra,
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
