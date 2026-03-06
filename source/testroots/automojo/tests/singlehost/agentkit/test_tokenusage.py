"""
    Unit tests for the automojo.agentkit.tokenusage module.

    Tests TokenUsage construction, validation, properties, arithmetic,
    equality, and string representations.

    Feature: llm-integration, Task 1.5
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 19.9, 19.10**
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.tokenusage import TokenUsage


# ---------------------------------------------------------------------------
# Construction and validation
# ---------------------------------------------------------------------------


def test_token_usage_valid_construction():
    """
        TokenUsage accepts valid token counts where total equals the sum.

        **Validates: Requirements 4.1, 4.3**
    """
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    assert usage.prompt_tokens == 10, (
        "prompt_tokens mismatch: {}".format(usage.prompt_tokens)
    )
    assert usage.completion_tokens == 20, (
        "completion_tokens mismatch: {}".format(usage.completion_tokens)
    )
    assert usage.total_tokens == 30, (
        "total_tokens mismatch: {}".format(usage.total_tokens)
    )

    return


def test_token_usage_zero_values():
    """
        TokenUsage accepts all-zero token counts.

        **Validates: Requirements 4.1, 4.3**
    """
    usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    assert usage.prompt_tokens == 0, "prompt_tokens should be 0"
    assert usage.completion_tokens == 0, "completion_tokens should be 0"
    assert usage.total_tokens == 0, "total_tokens should be 0"

    return


def test_token_usage_invalid_total_raises_semantic_error():
    """
        TokenUsage raises SemanticError when total does not equal the sum.

        **Validates: Requirements 4.4**
    """
    caught = False

    try:
        TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=99)
    except SemanticError:
        caught = True

    assert caught is True, (
        "TokenUsage should raise SemanticError for mismatched total"
    )

    return


# ---------------------------------------------------------------------------
# Read-only properties
# ---------------------------------------------------------------------------


def test_token_usage_properties_are_read_only():
    """
        TokenUsage properties return the correct values.

        **Validates: Requirements 4.2**
    """
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)

    assert usage.prompt_tokens == 100, "prompt_tokens property mismatch"
    assert usage.completion_tokens == 50, "completion_tokens property mismatch"
    assert usage.total_tokens == 150, "total_tokens property mismatch"

    return


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------


def test_token_usage_as_dict():
    """
        TokenUsage as_dict returns a dictionary with all token counts.

        **Validates: Requirements 4.5**
    """
    usage = TokenUsage(prompt_tokens=5, completion_tokens=15, total_tokens=20)
    result = usage.as_dict()

    assert result["prompt_tokens"] == 5, "as_dict prompt_tokens mismatch"
    assert result["completion_tokens"] == 15, "as_dict completion_tokens mismatch"
    assert result["total_tokens"] == 20, "as_dict total_tokens mismatch"

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__
# ---------------------------------------------------------------------------


def test_token_usage_repr():
    """
        TokenUsage __repr__ includes class name and all token counts.

        **Validates: Requirements 4.6, 19.9**
    """
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    repr_str = repr(usage)

    assert "TokenUsage" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "10" in repr_str, (
        "repr should contain prompt tokens, got: {!r}".format(repr_str)
    )
    assert "20" in repr_str, (
        "repr should contain completion tokens, got: {!r}".format(repr_str)
    )
    assert "30" in repr_str, (
        "repr should contain total tokens, got: {!r}".format(repr_str)
    )

    return


def test_token_usage_str():
    """
        TokenUsage __str__ returns a human-readable summary.

        **Validates: Requirements 4.7, 19.10**
    """
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    str_val = str(usage)

    assert "10" in str_val, "str should contain prompt tokens"
    assert "20" in str_val, "str should contain completion tokens"
    assert "30" in str_val, "str should contain total tokens"

    return


# ---------------------------------------------------------------------------
# __add__
# ---------------------------------------------------------------------------


def test_token_usage_add():
    """
        TokenUsage __add__ returns a new TokenUsage with summed counts.

        **Validates: Requirements 4.8**
    """
    a = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    b = TokenUsage(prompt_tokens=5, completion_tokens=15, total_tokens=20)

    result = a + b

    assert result.prompt_tokens == 15, (
        "Added prompt_tokens mismatch: {}".format(result.prompt_tokens)
    )
    assert result.completion_tokens == 35, (
        "Added completion_tokens mismatch: {}".format(result.completion_tokens)
    )
    assert result.total_tokens == 50, (
        "Added total_tokens mismatch: {}".format(result.total_tokens)
    )

    return


def test_token_usage_add_with_zero():
    """
        TokenUsage __add__ with a zero-valued operand returns equivalent counts.

        **Validates: Requirements 4.8**
    """
    a = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    zero = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    result = a + zero

    assert result == a, "Adding zero TokenUsage should produce an equal result"

    return


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_token_usage_eq_same_values():
    """
        TokenUsage __eq__ returns True for equal token counts.

        **Validates: Requirements 4.1**
    """
    a = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    b = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    assert a == b, "TokenUsage with same values should be equal"

    return


def test_token_usage_eq_different_values():
    """
        TokenUsage __eq__ returns False for different token counts.

        **Validates: Requirements 4.1**
    """
    a = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    b = TokenUsage(prompt_tokens=5, completion_tokens=25, total_tokens=30)

    assert (a == b) is False, "TokenUsage with different values should not be equal"

    return


def test_token_usage_eq_non_token_usage():
    """
        TokenUsage __eq__ returns False when compared to a non-TokenUsage object.

        **Validates: Requirements 4.1**
    """
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    assert (usage == "not a token usage") is False, (
        "TokenUsage should not be equal to a string"
    )

    return

