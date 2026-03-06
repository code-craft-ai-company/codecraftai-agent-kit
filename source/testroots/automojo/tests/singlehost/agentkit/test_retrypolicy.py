"""
    Unit tests for the automojo.agentkit.retrypolicy module.

    Tests RetryPolicy construction, backoff strategies, should_retry logic,
    serialization, and string representations.

    Feature: llm-integration, Task 13.4
    **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.11, 10.12, 10.13, 10.14, 19.15, 19.16**
"""

import json

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.retrypolicy import RetryPolicy


# ---------------------------------------------------------------------------
# Construction and properties
# ---------------------------------------------------------------------------


def test_construction_stores_all_fields():
    """
        RetryPolicy stores max_retries, backoff_strategy, base_delay,
        max_delay, and retryable_exceptions.

        **Validates: Requirements 10.1, 10.2**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=[ValueError, TypeError]
    )

    assert policy.max_retries == 3, (
        "max_retries should be 3, got: {}".format(policy.max_retries)
    )
    assert policy.backoff_strategy == "fixed", (
        "backoff_strategy should be 'fixed', got: {!r}".format(policy.backoff_strategy)
    )
    assert policy.base_delay == 1.0, (
        "base_delay should be 1.0, got: {}".format(policy.base_delay)
    )
    assert policy.max_delay == 10.0, (
        "max_delay should be 10.0, got: {}".format(policy.max_delay)
    )
    assert policy.retryable_exceptions == [ValueError, TypeError], (
        "retryable_exceptions should be [ValueError, TypeError], got: {!r}".format(
            policy.retryable_exceptions
        )
    )

    return


def test_construction_default_retryable_exceptions():
    """
        RetryPolicy defaults retryable_exceptions to an empty list when
        not provided.

        **Validates: Requirements 10.1**
    """
    policy = RetryPolicy(
        max_retries=2,
        backoff_strategy="exponential",
        base_delay=0.5,
        max_delay=30.0
    )

    assert policy.retryable_exceptions == [], (
        "Default retryable_exceptions should be [], got: {!r}".format(
            policy.retryable_exceptions
        )
    )

    return


def test_construction_invalid_strategy_raises_semantic_error():
    """
        RetryPolicy raises SemanticError for an invalid backoff_strategy.

        **Validates: Requirements 10.1**
    """
    raised = False
    try:
        RetryPolicy(
            max_retries=3,
            backoff_strategy="invalid_strategy",
            base_delay=1.0,
            max_delay=10.0
        )
    except SemanticError:
        raised = True

    assert raised is True, (
        "SemanticError should be raised for invalid backoff_strategy"
    )

    return


def test_retryable_exceptions_returns_copy():
    """
        The retryable_exceptions property returns a copy of the list.

        **Validates: Requirements 10.2**
    """
    original = [ValueError]
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=original
    )

    result = policy.retryable_exceptions
    result.append(TypeError)

    assert len(policy.retryable_exceptions) == 1, (
        "Modifying the returned list should not affect the policy"
    )

    return


# ---------------------------------------------------------------------------
# get_delay - fixed strategy
# ---------------------------------------------------------------------------


def test_get_delay_fixed_returns_base_delay():
    """
        Fixed strategy returns base_delay for all attempts.

        **Validates: Requirements 10.3, 10.4**
    """
    policy = RetryPolicy(
        max_retries=5,
        backoff_strategy="fixed",
        base_delay=2.0,
        max_delay=60.0
    )

    for attempt in range(5):
        delay = policy.get_delay(attempt)
        assert delay == 2.0, (
            "Fixed delay at attempt {} should be 2.0, got: {}".format(attempt, delay)
        )

    return


# ---------------------------------------------------------------------------
# get_delay - exponential strategy
# ---------------------------------------------------------------------------


def test_get_delay_exponential_attempt_zero():
    """
        Exponential strategy at attempt 0 returns base_delay * 2^0 = base_delay.

        **Validates: Requirements 10.3, 10.5**
    """
    policy = RetryPolicy(
        max_retries=5,
        backoff_strategy="exponential",
        base_delay=1.0,
        max_delay=60.0
    )

    delay = policy.get_delay(0)

    assert delay == 1.0, (
        "Exponential delay at attempt 0 should be 1.0, got: {}".format(delay)
    )

    return


def test_get_delay_exponential_attempt_one():
    """
        Exponential strategy at attempt 1 returns base_delay * 2^1.

        **Validates: Requirements 10.3, 10.5**
    """
    policy = RetryPolicy(
        max_retries=5,
        backoff_strategy="exponential",
        base_delay=1.0,
        max_delay=60.0
    )

    delay = policy.get_delay(1)

    assert delay == 2.0, (
        "Exponential delay at attempt 1 should be 2.0, got: {}".format(delay)
    )

    return


def test_get_delay_exponential_attempt_three():
    """
        Exponential strategy at attempt 3 returns base_delay * 2^3 = 8.0.

        **Validates: Requirements 10.3, 10.5**
    """
    policy = RetryPolicy(
        max_retries=5,
        backoff_strategy="exponential",
        base_delay=1.0,
        max_delay=60.0
    )

    delay = policy.get_delay(3)

    assert delay == 8.0, (
        "Exponential delay at attempt 3 should be 8.0, got: {}".format(delay)
    )

    return


def test_get_delay_exponential_capped_at_max_delay():
    """
        Exponential strategy caps the delay at max_delay.

        **Validates: Requirements 10.3, 10.5**
    """
    policy = RetryPolicy(
        max_retries=10,
        backoff_strategy="exponential",
        base_delay=1.0,
        max_delay=10.0
    )

    delay = policy.get_delay(5)
    expected = min(1.0 * (2 ** 5), 10.0)

    assert delay == expected, (
        "Exponential delay at attempt 5 should be capped at {}, got: {}".format(
            expected, delay
        )
    )

    return


# ---------------------------------------------------------------------------
# get_delay - exponential_with_jitter strategy
# ---------------------------------------------------------------------------


def test_get_delay_jitter_bounded_by_exponential_cap():
    """
        Exponential_with_jitter delay is between 0 and the capped
        exponential value.

        **Validates: Requirements 10.3, 10.6**
    """
    policy = RetryPolicy(
        max_retries=5,
        backoff_strategy="exponential_with_jitter",
        base_delay=1.0,
        max_delay=10.0
    )

    for attempt in range(5):
        capped = min(1.0 * (2 ** attempt), 10.0)
        delay = policy.get_delay(attempt)

        assert 0.0 <= delay <= capped, (
            "Jitter delay at attempt {} should be in [0, {}], got: {}".format(
                attempt, capped, delay
            )
        )

    return


# ---------------------------------------------------------------------------
# should_retry
# ---------------------------------------------------------------------------


def test_should_retry_within_max_retries_empty_exceptions():
    """
        should_retry returns True when attempt < max_retries and
        retryable_exceptions is empty (any exception retries).

        **Validates: Requirements 10.7**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0
    )

    result = policy.should_retry(ValueError("test"), 0)

    assert result is True, (
        "should_retry should return True for attempt 0 with max_retries=3"
    )

    return


def test_should_retry_at_boundary_returns_false():
    """
        should_retry returns False when attempt == max_retries.

        **Validates: Requirements 10.7**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0
    )

    result = policy.should_retry(ValueError("test"), 3)

    assert result is False, (
        "should_retry should return False when attempt == max_retries"
    )

    return


def test_should_retry_beyond_max_retries_returns_false():
    """
        should_retry returns False when attempt > max_retries.

        **Validates: Requirements 10.7**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0
    )

    result = policy.should_retry(ValueError("test"), 5)

    assert result is False, (
        "should_retry should return False when attempt > max_retries"
    )

    return


def test_should_retry_matching_exception_type():
    """
        should_retry returns True when the exception matches a retryable type.

        **Validates: Requirements 10.7**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=[ValueError, TimeoutError]
    )

    result = policy.should_retry(ValueError("test"), 0)

    assert result is True, (
        "should_retry should return True for matching exception type"
    )

    return


def test_should_retry_non_matching_exception_type():
    """
        should_retry returns False when the exception does not match
        any retryable type.

        **Validates: Requirements 10.7**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=[ValueError, TimeoutError]
    )

    result = policy.should_retry(TypeError("test"), 0)

    assert result is False, (
        "should_retry should return False for non-matching exception type"
    )

    return


# ---------------------------------------------------------------------------
# Serialization: as_dict, to_json, from_dict
# ---------------------------------------------------------------------------


def test_as_dict_contains_all_fields():
    """
        as_dict returns a dictionary with max_retries, backoff_strategy,
        base_delay, and max_delay.

        **Validates: Requirements 10.11**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="exponential",
        base_delay=1.5,
        max_delay=30.0
    )

    result = policy.as_dict()

    assert result["max_retries"] == 3, (
        "as_dict max_retries should be 3, got: {}".format(result["max_retries"])
    )
    assert result["backoff_strategy"] == "exponential", (
        "as_dict backoff_strategy should be 'exponential', got: {!r}".format(
            result["backoff_strategy"]
        )
    )
    assert result["base_delay"] == 1.5, (
        "as_dict base_delay should be 1.5, got: {}".format(result["base_delay"])
    )
    assert result["max_delay"] == 30.0, (
        "as_dict max_delay should be 30.0, got: {}".format(result["max_delay"])
    )

    return


def test_to_json_produces_valid_json():
    """
        to_json returns a valid JSON string that can be parsed.

        **Validates: Requirements 10.12**
    """
    policy = RetryPolicy(
        max_retries=2,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=5.0
    )

    json_str = policy.to_json()
    parsed = json.loads(json_str)

    assert parsed["max_retries"] == 2, (
        "Parsed JSON max_retries should be 2, got: {}".format(parsed["max_retries"])
    )
    assert parsed["backoff_strategy"] == "fixed", (
        "Parsed JSON backoff_strategy should be 'fixed', got: {!r}".format(
            parsed["backoff_strategy"]
        )
    )

    return


def test_from_dict_restores_policy():
    """
        from_dict constructs a RetryPolicy with equivalent fields.

        **Validates: Requirements 10.13**
    """
    data = {
        "max_retries": 4,
        "backoff_strategy": "exponential_with_jitter",
        "base_delay": 0.5,
        "max_delay": 20.0
    }

    policy = RetryPolicy.from_dict(data)

    assert policy.max_retries == 4, (
        "from_dict max_retries should be 4, got: {}".format(policy.max_retries)
    )
    assert policy.backoff_strategy == "exponential_with_jitter", (
        "from_dict backoff_strategy should be 'exponential_with_jitter', got: {!r}".format(
            policy.backoff_strategy
        )
    )
    assert policy.base_delay == 0.5, (
        "from_dict base_delay should be 0.5, got: {}".format(policy.base_delay)
    )
    assert policy.max_delay == 20.0, (
        "from_dict max_delay should be 20.0, got: {}".format(policy.max_delay)
    )

    return


def test_from_dict_does_not_restore_retryable_exceptions():
    """
        from_dict does NOT restore retryable_exceptions since they are
        not serialized.

        **Validates: Requirements 10.13, 10.14**
    """
    policy_original = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=[ValueError]
    )

    data = policy_original.as_dict()
    restored = RetryPolicy.from_dict(data)

    assert restored.retryable_exceptions == [], (
        "from_dict should not restore retryable_exceptions, got: {!r}".format(
            restored.retryable_exceptions
        )
    )

    return


def test_serialization_round_trip():
    """
        to_json followed by json.loads and from_dict produces a policy
        with equivalent fields.

        **Validates: Requirements 10.11, 10.12, 10.13, 10.14**
    """
    original = RetryPolicy(
        max_retries=5,
        backoff_strategy="exponential",
        base_delay=2.0,
        max_delay=60.0
    )

    json_str = original.to_json()
    data = json.loads(json_str)
    restored = RetryPolicy.from_dict(data)

    assert restored.max_retries == original.max_retries, (
        "Round-trip max_retries mismatch"
    )
    assert restored.backoff_strategy == original.backoff_strategy, (
        "Round-trip backoff_strategy mismatch"
    )
    assert restored.base_delay == original.base_delay, (
        "Round-trip base_delay mismatch"
    )
    assert restored.max_delay == original.max_delay, (
        "Round-trip max_delay mismatch"
    )

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__
# ---------------------------------------------------------------------------


def test_repr_contains_class_name_and_fields():
    """
        __repr__ includes the class name, max_retries, and strategy.

        **Validates: Requirements 19.15**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="exponential",
        base_delay=1.0,
        max_delay=10.0
    )

    result = repr(policy)

    assert "RetryPolicy" in result, (
        "__repr__ should contain 'RetryPolicy', got: {!r}".format(result)
    )
    assert "3" in result, (
        "__repr__ should contain max_retries value '3', got: {!r}".format(result)
    )
    assert "exponential" in result, (
        "__repr__ should contain strategy 'exponential', got: {!r}".format(result)
    )

    return


def test_str_contains_full_config_summary():
    """
        __str__ returns a human-readable summary with all config fields.

        **Validates: Requirements 19.16**
    """
    policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=1.5,
        max_delay=30.0
    )

    result = str(policy)

    assert "RetryPolicy" in result, (
        "__str__ should contain 'RetryPolicy', got: {!r}".format(result)
    )
    assert "3" in result, (
        "__str__ should contain max_retries '3', got: {!r}".format(result)
    )
    assert "fixed" in result, (
        "__str__ should contain strategy 'fixed', got: {!r}".format(result)
    )
    assert "1.5" in result, (
        "__str__ should contain base_delay '1.5', got: {!r}".format(result)
    )
    assert "30.0" in result, (
        "__str__ should contain max_delay '30.0', got: {!r}".format(result)
    )

    return
