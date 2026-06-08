"""
    Unit tests for the ccai.agentkit.llmresponse module.

    Tests LLMResponse construction, read-only properties, serialization,
    string representations, and equality.

    Feature: llm-integration, Task 4.4
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 17.5, 17.6, 17.11, 19.7, 19.8**
"""

import json

from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.llmresponse import LLMResponse
from ccai.agentkit.tokenusage import TokenUsage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(provider_name="openai", model_name="gpt-4",
                   prompt_tokens=10, completion_tokens=20,
                   duration=1.5, role="assistant",
                   content="Hello!", metadata=None):
    """
        Creates an LLMResponse with sensible defaults for testing.
    """
    message = LLMMessage(role=role, content=content, metadata=metadata)
    token_usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )
    rtnval = LLMResponse(
        message=message,
        token_usage=token_usage,
        provider_name=provider_name,
        model_name=model_name,
        duration=duration
    )
    return rtnval


# ---------------------------------------------------------------------------
# Construction and read-only properties
# ---------------------------------------------------------------------------


def test_llm_response_valid_construction():
    """
        LLMResponse stores all fields correctly.

        **Validates: Requirements 3.1, 3.2**
    """
    resp = _make_response()

    assert resp.provider_name == "openai", (
        "provider_name mismatch: {!r}".format(resp.provider_name)
    )
    assert resp.model_name == "gpt-4", (
        "model_name mismatch: {!r}".format(resp.model_name)
    )
    assert resp.message.role == "assistant", (
        "message role mismatch: {!r}".format(resp.message.role)
    )
    assert resp.message.content == "Hello!", (
        "message content mismatch: {!r}".format(resp.message.content)
    )
    assert resp.token_usage.prompt_tokens == 10, (
        "prompt_tokens mismatch: {}".format(resp.token_usage.prompt_tokens)
    )
    assert resp.token_usage.completion_tokens == 20, (
        "completion_tokens mismatch: {}".format(resp.token_usage.completion_tokens)
    )
    assert resp.token_usage.total_tokens == 30, (
        "total_tokens mismatch: {}".format(resp.token_usage.total_tokens)
    )
    assert abs(resp.duration - 1.5) < 1e-9, (
        "duration mismatch: {}".format(resp.duration)
    )

    return


def test_llm_response_with_metadata():
    """
        LLMResponse preserves message metadata.

        **Validates: Requirements 3.1, 3.2**
    """
    metadata = {"tool_calls": [{"name": "search", "args": {"q": "test"}}]}
    resp = _make_response(metadata=metadata)

    assert resp.message.metadata == metadata, (
        "message metadata mismatch: {!r}".format(resp.message.metadata)
    )

    return


def test_llm_response_zero_duration():
    """
        LLMResponse accepts a zero duration.

        **Validates: Requirements 3.1**
    """
    resp = _make_response(duration=0.0)

    assert abs(resp.duration - 0.0) < 1e-9, (
        "duration should be 0.0, got: {}".format(resp.duration)
    )

    return


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------


def test_llm_response_as_dict():
    """
        LLMResponse as_dict returns a dictionary with all response fields.

        **Validates: Requirements 3.3**
    """
    resp = _make_response()
    result = resp.as_dict()

    assert result["provider_name"] == "openai", (
        "as_dict provider_name mismatch"
    )
    assert result["model_name"] == "gpt-4", (
        "as_dict model_name mismatch"
    )
    assert result["message"]["role"] == "assistant", (
        "as_dict message role mismatch"
    )
    assert result["message"]["content"] == "Hello!", (
        "as_dict message content mismatch"
    )
    assert result["token_usage"]["prompt_tokens"] == 10, (
        "as_dict prompt_tokens mismatch"
    )
    assert result["token_usage"]["completion_tokens"] == 20, (
        "as_dict completion_tokens mismatch"
    )
    assert result["token_usage"]["total_tokens"] == 30, (
        "as_dict total_tokens mismatch"
    )
    assert abs(result["duration"] - 1.5) < 1e-9, (
        "as_dict duration mismatch"
    )

    return


# ---------------------------------------------------------------------------
# to_json and from_json
# ---------------------------------------------------------------------------


def test_llm_response_to_json():
    """
        LLMResponse to_json returns a valid JSON string.

        **Validates: Requirements 3.4, 17.5**
    """
    resp = _make_response()
    json_str = resp.to_json()

    data = json.loads(json_str)

    assert data["provider_name"] == "openai", (
        "to_json provider_name mismatch"
    )
    assert data["model_name"] == "gpt-4", (
        "to_json model_name mismatch"
    )

    return


def test_llm_response_from_json():
    """
        LLMResponse from_json reconstructs an equivalent instance.

        **Validates: Requirements 3.5, 17.6**
    """
    original = _make_response()
    json_str = original.to_json()
    restored = LLMResponse.from_json(json_str)

    assert restored.provider_name == original.provider_name, (
        "from_json provider_name mismatch"
    )
    assert restored.model_name == original.model_name, (
        "from_json model_name mismatch"
    )
    assert restored.message == original.message, (
        "from_json message mismatch"
    )
    assert restored.token_usage == original.token_usage, (
        "from_json token_usage mismatch"
    )
    assert abs(restored.duration - original.duration) < 1e-9, (
        "from_json duration mismatch"
    )

    return


def test_llm_response_json_round_trip():
    """
        LLMResponse to_json followed by from_json produces an equal object.

        **Validates: Requirements 3.6, 17.11**
    """
    original = _make_response(
        provider_name="anthropic", model_name="claude-3",
        prompt_tokens=100, completion_tokens=200,
        duration=2.345, content="Round trip test"
    )
    restored = LLMResponse.from_json(original.to_json())

    assert original == restored, (
        "JSON round-trip should produce an equal LLMResponse"
    )

    return


def test_llm_response_json_round_trip_with_metadata():
    """
        LLMResponse JSON round-trip preserves message metadata.

        **Validates: Requirements 3.6, 17.11**
    """
    metadata = {"finish_reason": "stop", "index": 0}
    original = _make_response(metadata=metadata)
    restored = LLMResponse.from_json(original.to_json())

    assert original == restored, (
        "JSON round-trip with metadata should produce an equal LLMResponse"
    )

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__
# ---------------------------------------------------------------------------


def test_llm_response_repr_contains_class_name_and_fields():
    """
        LLMResponse __repr__ includes the class name, provider name,
        model name, and total token count.

        **Validates: Requirements 3.7, 19.7**
    """
    resp = _make_response()
    repr_str = repr(resp)

    assert "LLMResponse" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "openai" in repr_str, (
        "repr should contain provider_name, got: {!r}".format(repr_str)
    )
    assert "gpt-4" in repr_str, (
        "repr should contain model_name, got: {!r}".format(repr_str)
    )
    assert "30" in repr_str, (
        "repr should contain total token count, got: {!r}".format(repr_str)
    )

    return


def test_llm_response_str_contains_summary():
    """
        LLMResponse __str__ returns a human-readable summary with provider,
        model, token usage, and duration.

        **Validates: Requirements 3.8, 19.8**
    """
    resp = _make_response(duration=2.5)
    str_val = str(resp)

    assert "openai" in str_val, (
        "str should contain provider_name, got: {!r}".format(str_val)
    )
    assert "gpt-4" in str_val, (
        "str should contain model_name, got: {!r}".format(str_val)
    )
    assert "2.50" in str_val, (
        "str should contain formatted duration, got: {!r}".format(str_val)
    )

    return


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_llm_response_eq_same_values():
    """
        LLMResponse __eq__ returns True for responses with identical fields.

        **Validates: Requirements 3.1**
    """
    a = _make_response()
    b = _make_response()

    assert a == b, "LLMResponse with same values should be equal"

    return


def test_llm_response_eq_different_provider():
    """
        LLMResponse __eq__ returns False when provider names differ.

        **Validates: Requirements 3.1**
    """
    a = _make_response(provider_name="openai")
    b = _make_response(provider_name="anthropic")

    assert (a == b) is False, (
        "LLMResponse with different provider_name should not be equal"
    )

    return


def test_llm_response_eq_different_model():
    """
        LLMResponse __eq__ returns False when model names differ.

        **Validates: Requirements 3.1**
    """
    a = _make_response(model_name="gpt-4")
    b = _make_response(model_name="gpt-3.5")

    assert (a == b) is False, (
        "LLMResponse with different model_name should not be equal"
    )

    return


def test_llm_response_eq_different_message():
    """
        LLMResponse __eq__ returns False when messages differ.

        **Validates: Requirements 3.1**
    """
    a = _make_response(content="Hello!")
    b = _make_response(content="Goodbye!")

    assert (a == b) is False, (
        "LLMResponse with different message content should not be equal"
    )

    return


def test_llm_response_eq_different_token_usage():
    """
        LLMResponse __eq__ returns False when token usage differs.

        **Validates: Requirements 3.1**
    """
    a = _make_response(prompt_tokens=10, completion_tokens=20)
    b = _make_response(prompt_tokens=50, completion_tokens=60)

    assert (a == b) is False, (
        "LLMResponse with different token_usage should not be equal"
    )

    return


def test_llm_response_eq_different_duration():
    """
        LLMResponse __eq__ returns False when durations differ.

        **Validates: Requirements 3.1**
    """
    a = _make_response(duration=1.0)
    b = _make_response(duration=5.0)

    assert (a == b) is False, (
        "LLMResponse with different duration should not be equal"
    )

    return


def test_llm_response_eq_non_llm_response():
    """
        LLMResponse __eq__ returns False when compared to a non-LLMResponse.

        **Validates: Requirements 3.1**
    """
    resp = _make_response()

    assert (resp == "not a response") is False, (
        "LLMResponse should not be equal to a string"
    )

    return


# ---------------------------------------------------------------------------
# Serialization edge cases
# ---------------------------------------------------------------------------


def test_llm_response_empty_content_serialization():
    """
        LLMResponse with empty message content serializes and deserializes.

        **Validates: Requirements 3.3, 3.4, 3.5, 3.6**
    """
    original = _make_response(content="")
    restored = LLMResponse.from_json(original.to_json())

    assert original == restored, (
        "Empty content LLMResponse should round-trip correctly"
    )

    return


def test_llm_response_large_token_counts_serialization():
    """
        LLMResponse with large token counts serializes and deserializes.

        **Validates: Requirements 3.3, 3.4, 3.5, 3.6**
    """
    original = _make_response(
        prompt_tokens=1000000, completion_tokens=2000000
    )
    restored = LLMResponse.from_json(original.to_json())

    assert original == restored, (
        "Large token count LLMResponse should round-trip correctly"
    )

    return


def test_llm_response_special_characters_in_content():
    """
        LLMResponse with special characters in content serializes correctly.

        **Validates: Requirements 3.4, 3.5, 3.6**
    """
    content = 'Line1\nLine2\t"quoted"\u00e9'
    original = _make_response(content=content)
    restored = LLMResponse.from_json(original.to_json())

    assert original == restored, (
        "Special character content should round-trip correctly"
    )

    return
