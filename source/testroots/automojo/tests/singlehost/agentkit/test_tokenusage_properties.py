"""
    Property-based tests for the automojo.agentkit.tokenusage module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 13: TokenUsage construction validates total equals sum
    - Property 14: TokenUsage addition produces correct sums

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.8**
"""

from automojo.testbase.properties import given, assume
from automojo.testbase.properties import strategies as st

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.tokenusage import TokenUsage


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_non_negative_int = st.integers(min_value=0, max_value=1_000_000)


# ---------------------------------------------------------------------------
# Property 13: TokenUsage construction validates total equals sum
# ---------------------------------------------------------------------------

@given(
    prompt_tokens=_non_negative_int,
    completion_tokens=_non_negative_int,
    constraints={"max_examples": 50},
)
def test_tokenusage_valid_construction_preserves_fields(
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

        For any two non-negative integers, constructing a TokenUsage
        with total_tokens equal to prompt_tokens + completion_tokens
        shall succeed and all properties shall return the provided values.
    """
    total_tokens = prompt_tokens + completion_tokens

    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    assert usage.prompt_tokens == prompt_tokens, (
        "prompt_tokens property should return {}, got {}".format(
            prompt_tokens, usage.prompt_tokens
        )
    )
    assert usage.completion_tokens == completion_tokens, (
        "completion_tokens property should return {}, got {}".format(
            completion_tokens, usage.completion_tokens
        )
    )
    assert usage.total_tokens == total_tokens, (
        "total_tokens property should return {}, got {}".format(
            total_tokens, usage.total_tokens
        )
    )

    return


@given(
    prompt_tokens=_non_negative_int,
    completion_tokens=_non_negative_int,
    total_tokens=_non_negative_int,
    constraints={"max_examples": 50},
)
def test_tokenusage_invalid_total_raises_semantic_error(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> None:
    """
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

        For any three non-negative integers where total_tokens does not
        equal prompt_tokens + completion_tokens, constructing a TokenUsage
        shall raise SemanticError.
    """
    expected_total = prompt_tokens + completion_tokens
    assume(total_tokens != expected_total)

    raised = False
    try:
        TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
    except SemanticError:
        raised = True

    assert raised is True, (
        "TokenUsage should raise SemanticError when total_tokens ({}) "
        "does not equal prompt_tokens ({}) + completion_tokens ({}) = {}".format(
            total_tokens, prompt_tokens, completion_tokens, expected_total
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 14: TokenUsage addition produces correct sums
# ---------------------------------------------------------------------------

@given(
    prompt_a=_non_negative_int,
    completion_a=_non_negative_int,
    prompt_b=_non_negative_int,
    completion_b=_non_negative_int,
    constraints={"max_examples": 50},
)
def test_tokenusage_addition_produces_correct_sums(
    prompt_a: int,
    completion_a: int,
    prompt_b: int,
    completion_b: int,
) -> None:
    """
        **Validates: Requirements 4.8**

        For any two valid TokenUsage instances, adding them with +
        shall produce a new TokenUsage whose prompt_tokens,
        completion_tokens, and total_tokens are the sums of the
        corresponding fields from the two operands.
    """
    usage_a = TokenUsage(
        prompt_tokens=prompt_a,
        completion_tokens=completion_a,
        total_tokens=prompt_a + completion_a,
    )
    usage_b = TokenUsage(
        prompt_tokens=prompt_b,
        completion_tokens=completion_b,
        total_tokens=prompt_b + completion_b,
    )

    result = usage_a + usage_b

    expected_prompt = prompt_a + prompt_b
    expected_completion = completion_a + completion_b
    expected_total = expected_prompt + expected_completion

    assert result.prompt_tokens == expected_prompt, (
        "prompt_tokens should be {}, got {}".format(
            expected_prompt, result.prompt_tokens
        )
    )
    assert result.completion_tokens == expected_completion, (
        "completion_tokens should be {}, got {}".format(
            expected_completion, result.completion_tokens
        )
    )
    assert result.total_tokens == expected_total, (
        "total_tokens should be {}, got {}".format(
            expected_total, result.total_tokens
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
