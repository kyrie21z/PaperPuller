from paperpuller.llm import _parse_evaluation, _parse_str_list


def test_parse_evaluation_full_fields():
    data = {
        "score": 9,
        "topic_tags": ["OCR", "SLPR", "ViT"],
        "slpr_challenges": ["degradation", "occlusion", "mixed_script"],
        "pipeline_components": ["visual_encoder", "decoder"],
        "integration_path": "finetune",
        "reproducibility": "high",
        "next_action": "read",
        "reason": "Directly relevant to SLPR.",
        "tldr": "A method for robust STR with ViT encoder.",
    }
    evaluation = _parse_evaluation("2601.00099", "test-model", data)

    assert evaluation.score == 9.0
    assert evaluation.topic_tags == ["OCR", "SLPR", "ViT"]
    assert evaluation.slpr_challenges == ["degradation", "occlusion", "mixed_script"]
    assert evaluation.pipeline_components == ["visual_encoder", "decoder"]
    assert evaluation.integration_path == "finetune"
    assert evaluation.reproducibility == "high"
    assert evaluation.next_action == "read"
    assert evaluation.reason == "Directly relevant to SLPR."
    assert evaluation.tldr == "A method for robust STR with ViT encoder."


def test_parse_evaluation_missing_all_new_fields():
    """Old-style LLM response without any new fields should get defaults."""
    data = {
        "score": 5,
        "topic_tags": ["Other"],
        "reason": "Not relevant.",
        "tldr": "A paper about robotics.",
    }
    evaluation = _parse_evaluation("2601.00100", "test-model", data)

    assert evaluation.score == 5.0
    assert evaluation.slpr_challenges == []
    assert evaluation.pipeline_components == []
    assert evaluation.integration_path == ""
    assert evaluation.reproducibility == "unknown"
    assert evaluation.next_action == "skim"


def test_parse_evaluation_score_clamped():
    data = {
        "score": 15,
        "topic_tags": ["OCR"],
        "reason": "Test.",
        "tldr": "Test.",
    }
    evaluation = _parse_evaluation("2601.00101", "test-model", data)
    assert evaluation.score == 10.0

    data["score"] = -3
    evaluation = _parse_evaluation("2601.00102", "test-model", data)
    assert evaluation.score == 0.0


def test_parse_evaluation_topic_tags_always_list():
    data = {
        "score": 7,
        "topic_tags": "OCR, STR",
        "reason": "Test.",
        "tldr": "Test.",
    }
    evaluation = _parse_evaluation("2601.00103", "test-model", data)
    assert evaluation.topic_tags == ["OCR", "STR"]


def test_parse_evaluation_nil_topic_tags_fallback():
    data = {
        "score": 6,
        "topic_tags": None,
        "reason": "Test.",
        "tldr": "Test.",
    }
    evaluation = _parse_evaluation("2601.00104", "test-model", data)
    assert evaluation.topic_tags == ["Other"]


class TestParseStrList:
    def test_list(self):
        assert _parse_str_list(["a", "b"]) == ["a", "b"]

    def test_comma_string(self):
        assert _parse_str_list("a, b, c") == ["a", "b", "c"]

    def test_none(self):
        assert _parse_str_list(None) == []

    def test_empty_list(self):
        assert _parse_str_list([]) == []

    def test_fallback(self):
        assert _parse_str_list(None, fallback=["default"]) == ["default"]
