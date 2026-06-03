from paperpuller.llm import _parse_evaluation, _parse_str_list


def test_parse_evaluation_full_fields():
    data = {
        "score": 9,
        "topic_tags": ["OCR", "STR", "ViT"],
        "group": "Robust Recognition",
        "reason": "Directly relevant to the research area.",
        "tldr": "A method for robust STR with ViT encoder.",
        "extra": {
            "challenges": ["degradation", "occlusion", "mixed_script"],
            "pipeline_components": ["visual_encoder", "decoder"],
        },
    }
    evaluation = _parse_evaluation("2601.00099", "test-model", data)

    assert evaluation.score == 9.0
    assert evaluation.topic_tags == ["OCR", "STR", "ViT"]
    assert evaluation.group == "Robust Recognition"
    assert evaluation.reason == "Directly relevant to the research area."
    assert evaluation.tldr == "A method for robust STR with ViT encoder."
    assert evaluation.extra == {
        "challenges": ["degradation", "occlusion", "mixed_script"],
        "pipeline_components": ["visual_encoder", "decoder"],
    }


def test_parse_evaluation_minimal_fields():
    """LLM response without optional fields should get defaults."""
    data = {
        "score": 5,
        "topic_tags": ["Other"],
        "reason": "Not relevant.",
        "tldr": "A paper about robotics.",
    }
    evaluation = _parse_evaluation("2601.00100", "test-model", data)

    assert evaluation.score == 5.0
    assert evaluation.group == "Other"
    assert evaluation.extra == {}


def test_parse_evaluation_extra_is_string():
    """LLM returns a string for extra — should be ignored."""
    data = {
        "score": 6,
        "topic_tags": ["OCR"],
        "reason": "Test.",
        "tldr": "Test.",
        "extra": "not an object",
    }
    evaluation = _parse_evaluation("2601.00101", "test-model", data)
    assert evaluation.extra == {}


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
