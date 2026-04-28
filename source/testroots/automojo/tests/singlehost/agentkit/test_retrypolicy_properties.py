"""
    Property-based tests for the automojo.agentkit.retrypolicy and
    automojo.agentkit.fallbackchain modules.

    Uses the automojo.testbase.properties engine to verify:
    - Property 6: RetryPolicy serialization round-trip
    - Property 29: RetryPolicy fixed delay returns base_delay
    - Property 30: RetryPolicy exponential delay is bounded
    - Property 31: RetryPolicy exponential_with_jitter delay is bounded
    - Property 32: RetryPolicy should_retry respects max_retries and exception types
    - Property 33: FallbackChain next_provider returns correct sequence

    **Validates: Requirements 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10,
                 10.11, 10.12, 10.13, 10.14**
"""

import json

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.retrypolicy import RetryPolicy
from automojo.agentkit.fallbackchain import FallbackChain


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_positive_int = st.integers(min_value=0, max_value=50)

_positive_float = st.floats(
    min_value=0.01,
    max_value=100.0,
)

_backoff_strategy = st.sampled_from(["fixed", "exponential", "exponential_with_jitter"])

_attempt_number = st.integers(min_value=0, max_value=20)

_provider_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=10,
)

_model_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=10,
)


@composite
def _retry_policy(draw, strategy=None):
    """
        Draws a valid RetryPolicy instance.
    """
    max_retries = draw(_positive_int)
    backoff = strategy if strategy is not None else draw(_backoff_strategy)
    base_delay = draw(_positive_float)
    max_delay_raw = draw(_positive_float)
    max_delay = max(base_delay, max_delay_raw)

    policy = RetryPolicy(
        max_retries=max_retries,
        backoff_strategy=backoff,
        base_delay=base_delay,
        max_delay=max_delay,
    )

    return policy


@composite
def _provider_pair(draw):
    """
        Draws a (provider_name, model_name) tuple.
    """
    pname = draw(_provider_name)
    mname = draw(_model_name)
    return (pname, mname)


@composite
def _unique_provider_pair_list(draw):
    """
        Draws a list of unique (provider_name, model_name) tuples.
    """
    raw_pairs = draw(st.lists(_provider_pair(), min_size=1, max_size=10))

    seen = set()
    unique_pairs = []
    for pair in raw_pairs:
        if pair not in seen:
            seen.add(pair)
            unique_pairs.append(pair)

    if len(unique_pairs) == 0:
        unique_pairs.append(draw(_provider_pair()))

    return unique_pairs


# ---------------------------------------------------------------------------
# Property 6: RetryPolicy serialization round-trip
# ---------------------------------------------------------------------------

@given(policy=_retry_policy(), constraints={"max_examples": 50})
def test_retrypolicy_serialization_round_trip(policy: RetryPolicy) -> None:
    """
        **Validates: Requirements 10.11, 10.12, 10.13, 10.14**

        For any valid RetryPolicy instance, calling to_json() and then
        from_dict() on the parsed JSON shall produce a RetryPolicy with
        equivalent max_retries, backoff_strategy, base_delay, and max_delay
        values.
    """
    json_str = policy.to_json()
    data = json.loads(json_str)
    restored = RetryPolicy.from_dict(data)

    assert restored.max_retries == policy.max_retries, (
        "max_retries should be {}, got {}".format(
            policy.max_retries, restored.max_retries
        )
    )
    assert restored.backoff_strategy == policy.backoff_strategy, (
        "backoff_strategy should be {!r}, got {!r}".format(
            policy.backoff_strategy, restored.backoff_strategy
        )
    )
    assert abs(restored.base_delay - policy.base_delay) < 1e-9, (
        "base_delay should be ~{}, got {}".format(
            policy.base_delay, restored.base_delay
        )
    )
    assert abs(restored.max_delay - policy.max_delay) < 1e-9, (
        "max_delay should be ~{}, got {}".format(
            policy.max_delay, restored.max_delay
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 29: RetryPolicy fixed delay returns base_delay
# ---------------------------------------------------------------------------

@given(policy=_retry_policy(strategy="fixed"), attempt=_attempt_number, constraints={"max_examples": 50})
def test_retrypolicy_fixed_delay_returns_base_delay(
    policy: RetryPolicy, attempt: int
) -> None:
    """
        **Validates: Requirements 10.3, 10.4**

        For any RetryPolicy with "fixed" backoff strategy and any attempt
        number, get_delay(attempt) shall return the base_delay.
    """
    delay = policy.get_delay(attempt)

    assert abs(delay - policy.base_delay) < 1e-9, (
        "fixed delay should be {}, got {}".format(policy.base_delay, delay)
    )

    return


# ---------------------------------------------------------------------------
# Property 30: RetryPolicy exponential delay is bounded
# ---------------------------------------------------------------------------

@given(policy=_retry_policy(strategy="exponential"), attempt=_attempt_number, constraints={"max_examples": 50})
def test_retrypolicy_exponential_delay_is_bounded(
    policy: RetryPolicy, attempt: int
) -> None:
    """
        **Validates: Requirements 10.3, 10.5**

        For any RetryPolicy with "exponential" backoff strategy, base_delay,
        max_delay, and any attempt number, get_delay(attempt) shall return
        min(base_delay * 2^attempt, max_delay).
    """
    delay = policy.get_delay(attempt)
    expected = min(policy.base_delay * (2 ** attempt), policy.max_delay)

    assert abs(delay - expected) < 1e-9, (
        "exponential delay should be {}, got {}".format(expected, delay)
    )

    return


# ---------------------------------------------------------------------------
# Property 31: RetryPolicy exponential_with_jitter delay is bounded
# ---------------------------------------------------------------------------

@given(policy=_retry_policy(strategy="exponential_with_jitter"), attempt=_attempt_number, constraints={"max_examples": 50})
def test_retrypolicy_exponential_with_jitter_delay_is_bounded(
    policy: RetryPolicy, attempt: int
) -> None:
    """
        **Validates: Requirements 10.3, 10.6**

        For any RetryPolicy with "exponential_with_jitter" backoff strategy
        and any attempt number, get_delay(attempt) shall return a value
        between 0 and min(base_delay * 2^attempt, max_delay) inclusive.
    """
    delay = policy.get_delay(attempt)
    upper_bound = min(policy.base_delay * (2 ** attempt), policy.max_delay)

    assert delay >= 0.0, (
        "jitter delay should be >= 0, got {}".format(delay)
    )
    assert delay <= upper_bound + 1e-9, (
        "jitter delay should be <= {}, got {}".format(upper_bound, delay)
    )

    return


# ---------------------------------------------------------------------------
# Property 32: RetryPolicy should_retry respects max_retries and exception types
# ---------------------------------------------------------------------------

@given(max_retries=st.integers(min_value=1, max_value=20),
       attempt_within=st.integers(min_value=0, max_value=19),
       constraints={"max_examples": 50})
def test_retrypolicy_should_retry_respects_max_retries_and_exception_types(
    max_retries: int, attempt_within: int
) -> None:
    """
        **Validates: Requirements 10.7**

        For any RetryPolicy with max_retries M and a list of retryable
        exception types:
        (a) should_retry returns False when attempt >= M,
        (b) when attempt < M and exception is a retryable type, returns True,
        (c) when attempt < M and exception is not a retryable type, returns False.
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=[ValueError, TypeError],
    )

    # (a) attempt >= max_retries should return False
    beyond_attempt = max_retries
    result_beyond = policy.should_retry(ValueError("test"), beyond_attempt)
    assert result_beyond is False, (
        "should_retry should be False when attempt ({}) >= max_retries ({}), got {}".format(
            beyond_attempt, max_retries, result_beyond
        )
    )

    # (b) attempt < max_retries with matching exception type should return True
    attempt = attempt_within % max_retries
    result_matching = policy.should_retry(ValueError("test"), attempt)
    assert result_matching is True, (
        "should_retry should be True for retryable exception at attempt {}, got {}".format(
            attempt, result_matching
        )
    )

    # (c) attempt < max_retries with non-matching exception type should return False
    result_non_matching = policy.should_retry(RuntimeError("test"), attempt)
    assert result_non_matching is False, (
        "should_retry should be False for non-retryable exception at attempt {}, got {}".format(
            attempt, result_non_matching
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 33: FallbackChain next_provider returns correct sequence
# ---------------------------------------------------------------------------

@given(providers=_unique_provider_pair_list(), constraints={"max_examples": 50})
def test_fallbackchain_next_provider_returns_correct_sequence(
    providers: list,
) -> None:
    """
        **Validates: Requirements 10.8, 10.9, 10.10**

        For any FallbackChain with N provider pairs, calling
        next_provider(current) with the i-th provider shall return the
        (i+1)-th provider, and calling with the last provider shall
        return None.
    """
    chain = FallbackChain(providers)

    for i in range(len(providers)):
        current_name, current_model = providers[i]
        result = chain.next_provider(current_name, current_model)

        if i < len(providers) - 1:
            expected = providers[i + 1]
            assert result == expected, (
                "next_provider at index {} should be {}, got {}".format(
                    i, expected, result
                )
            )
        else:
            assert result is None, (
                "next_provider at last index should be None, got {}".format(result)
            )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
