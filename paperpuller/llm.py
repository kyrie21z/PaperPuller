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

Return JSON with exactly these keys:
- score: number from 1 to 10
- topic_tags: array of short tags chosen from OCR, STR, ViT, MAE, Augmentation, Other
- reason: one sentence explaining why this paper is or is not worth reading
- tldr: concise summary in 1-2 sentences
""".strip()


def _parse_evaluation(arxiv_id: str, model: str, data: dict) -> Evaluation:
    score = float(data.get("score", 0))
    score = max(0.0, min(10.0, score))
    topic_tags = data.get("topic_tags", ["Other"])
    if not isinstance(topic_tags, list):
        topic_tags = ["Other"]
    return Evaluation(
        arxiv_id=arxiv_id,
        model=model,
        score=score,
        topic_tags=[str(tag) for tag in topic_tags] or ["Other"],
        reason=str(data.get("reason", "")).strip(),
        tldr=str(data.get("tldr", "")).strip(),
    )

