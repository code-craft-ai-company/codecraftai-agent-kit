"""
    Unit tests for the ccai.agentkit.llmerrors module.

    Tests LLMRequestError and LLMResponseParsingError field storage,
    property access, inheritance, and __repr__ output.

    Feature: llm-integration, Task 1.5
    **Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5**
"""

from ccai.agentkit.errors import AgentKitError
from ccai.agentkit.llmerrors import LLMRequestError
from ccai.agentkit.llmerrors import LLMResponseParsingError


# ---------------------------------------------------------------------------
# LLMRequestError tests
# ---------------------------------------------------------------------------


def test_llm_request_error_inherits_from_agentkit_error():
    """
        LLMRequestError inherits from AgentKitError.

        **Validates: Requirements 15.1**
    """
    err = LLMRequestError(
        provider_name="openai",
        model_name="gpt-4",
        category="server_error"
    )

    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, (
        "LLMRequestError should inherit from AgentKitError"
    )

    return


def test_llm_request_error_fields():
    """
        LLMRequestError stores and exposes provider_name, model_name,
        category, and cause through read-only properties.

        **Validates: Requirements 15.2**
    """
    cause = RuntimeError("connection reset")
    err = LLMRequestError(
        provider_name="anthropic",
        model_name="claude-3",
        category="connection",
        cause=cause
    )

    assert err.provider_name == "anthropic", (
        "provider_name mismatch: {!r}".format(err.provider_name)
    )
    assert err.model_name == "claude-3", (
        "model_name mismatch: {!r}".format(err.model_name)
    )
    assert err.category == "connection", (
        "category mismatch: {!r}".format(err.category)
    )
    assert err.cause is cause, (
        "cause should be the same exception instance"
    )

    return


def test_llm_request_error_cause_none_by_default():
    """
        LLMRequestError cause is None when not provided.

        **Validates: Requirements 15.2**
    """
    err = LLMRequestError(
        provider_name="openai",
        model_name="gpt-4",
        category="rate_limit"
    )

    assert err.cause is None, (
        "cause should be None when not provided"
    )

    return


def test_llm_request_error_invalid_category_raises_value_error():
    """
        LLMRequestError raises ValueError for an invalid category.

        **Validates: Requirements 15.2**
    """
    caught = False

    try:
        LLMRequestError(
            provider_name="openai",
            model_name="gpt-4",
            category="not_a_real_category"
        )
    except ValueError:
        caught = True

    assert caught is True, (
        "LLMRequestError should raise ValueError for invalid category"
    )

    return


def test_llm_request_error_all_valid_categories():
    """
        LLMRequestError accepts all valid categories without error.

        **Validates: Requirements 15.2**
    """
    valid_categories = [
        "rate_limit", "authentication", "server_error",
        "timeout", "connection", "invalid_request"
    ]

    for category in valid_categories:
        err = LLMRequestError(
            provider_name="test_provider",
            model_name="test_model",
            category=category
        )
        assert err.category == category, (
            "Category {!r} should be accepted".format(category)
        )

    return


def test_llm_request_error_repr():
    """
        LLMRequestError __repr__ includes class name, provider, model,
        and category.

        **Validates: Requirements 15.5**
    """
    err = LLMRequestError(
        provider_name="openai",
        model_name="gpt-4",
        category="timeout"
    )

    repr_str = repr(err)

    assert "LLMRequestError" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "openai" in repr_str, (
        "repr should contain provider name, got: {!r}".format(repr_str)
    )
    assert "gpt-4" in repr_str, (
        "repr should contain model name, got: {!r}".format(repr_str)
    )
    assert "timeout" in repr_str, (
        "repr should contain category, got: {!r}".format(repr_str)
    )

    return


def test_llm_request_error_message_contains_provider_and_model():
    """
        LLMRequestError message string includes provider name and model name.

        **Validates: Requirements 15.1, 15.5**
    """
    err = LLMRequestError(
        provider_name="bedrock",
        model_name="titan",
        category="authentication"
    )

    error_message = str(err)

    assert "bedrock" in error_message, (
        "Error message should contain provider name, got: {!r}".format(error_message)
    )
    assert "titan" in error_message, (
        "Error message should contain model name, got: {!r}".format(error_message)
    )

    return


def test_llm_request_error_message_contains_cause_when_provided():
    """
        LLMRequestError message includes cause text when a cause is provided.

        **Validates: Requirements 15.2**
    """
    cause = TimeoutError("request timed out after 30s")
    err = LLMRequestError(
        provider_name="openai",
        model_name="gpt-4",
        category="timeout",
        cause=cause
    )

    error_message = str(err)

    assert "request timed out after 30s" in error_message, (
        "Error message should contain cause text, got: {!r}".format(error_message)
    )

    return


def test_llm_request_error_catchable_as_agentkit_error():
    """
        LLMRequestError can be caught as AgentKitError.

        **Validates: Requirements 15.1**
    """
    caught = False

    try:
        raise LLMRequestError(
            provider_name="openai",
            model_name="gpt-4",
            category="server_error"
        )
    except AgentKitError:
        caught = True

    assert caught is True, (
        "LLMRequestError should be catchable as AgentKitError"
    )

    return


# ---------------------------------------------------------------------------
# LLMResponseParsingError tests
# ---------------------------------------------------------------------------


def test_llm_response_parsing_error_inherits_from_agentkit_error():
    """
        LLMResponseParsingError inherits from AgentKitError.

        **Validates: Requirements 15.3**
    """
    err = LLMResponseParsingError(
        parser_name="JsonOutputParser",
        raw_text="not json",
        message="Invalid JSON"
    )

    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, (
        "LLMResponseParsingError should inherit from AgentKitError"
    )

    return


def test_llm_response_parsing_error_fields():
    """
        LLMResponseParsingError stores and exposes parser_name, raw_text,
        and error_message through read-only properties.

        **Validates: Requirements 15.4**
    """
    err = LLMResponseParsingError(
        parser_name="RegexOutputParser",
        raw_text="some raw output text",
        message="Pattern did not match"
    )

    assert err.parser_name == "RegexOutputParser", (
        "parser_name mismatch: {!r}".format(err.parser_name)
    )
    assert err.raw_text == "some raw output text", (
        "raw_text mismatch: {!r}".format(err.raw_text)
    )
    assert err.error_message == "Pattern did not match", (
        "error_message mismatch: {!r}".format(err.error_message)
    )

    return


def test_llm_response_parsing_error_repr():
    """
        LLMResponseParsingError __repr__ includes class name, parser name,
        and error message.

        **Validates: Requirements 15.5**
    """
    err = LLMResponseParsingError(
        parser_name="JsonOutputParser",
        raw_text="bad data",
        message="Expecting value"
    )

    repr_str = repr(err)

    assert "LLMResponseParsingError" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "JsonOutputParser" in repr_str, (
        "repr should contain parser name, got: {!r}".format(repr_str)
    )
    assert "Expecting value" in repr_str, (
        "repr should contain error message, got: {!r}".format(repr_str)
    )

    return


def test_llm_response_parsing_error_message_truncates_raw_text():
    """
        LLMResponseParsingError message includes a truncated preview
        of the raw text (first 200 chars).

        **Validates: Requirements 15.4**
    """
    long_text = "x" * 500
    err = LLMResponseParsingError(
        parser_name="JsonOutputParser",
        raw_text=long_text,
        message="Invalid JSON"
    )

    error_message = str(err)

    # The raw text preview should be truncated to 200 chars
    full_raw_in_message = ("x" * 500) in error_message
    assert full_raw_in_message is False, (
        "Error message should not contain the full 500-char raw text"
    )

    return


def test_llm_response_parsing_error_catchable_as_agentkit_error():
    """
        LLMResponseParsingError can be caught as AgentKitError.

        **Validates: Requirements 15.3**
    """
    caught = False

    try:
        raise LLMResponseParsingError(
            parser_name="JsonOutputParser",
            raw_text="bad",
            message="parse failed"
        )
    except AgentKitError:
        caught = True

    assert caught is True, (
        "LLMResponseParsingError should be catchable as AgentKitError"
    )

    return

