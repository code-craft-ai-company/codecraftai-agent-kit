"""
    Property-based tests for the automojo.agentkit.retryexecutor module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 3: RetryExecutor success path
    - Property 4: RetryExecutor failure path with exhausted retries
    - Property 5: RetryExecutor non-retryable exception propagation

    **Validates: Requirements 1.4, 1.5, 1.6, 1.7**
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.retryexecutor import RetryExecutor
from automojo.agentkit.retrypolicy import RetryPolicy


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_backoff_strategy = st.sampled_from(["fixed", "exponential", "exponential_with_jitter"])

_max_retries = st.integers(min_value=0, max_value=10)

_base_delay = st.floats(min_value=0.001, max_value=1.0)

_max_delay = st.floats(min_value=1.0, max_value=60.0)

_return_value = st.one_of(
    st.integers(min_value=-10000, max_value=10000),
    st.text(min_size=0, max_size=100),
    st.floats(min_value=-1e6, max_value=1e6),
    st.booleans(),
    st.none(),
    st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10),
)


# ---------------------------------------------------------------------------
# Property 3: RetryExecutor success path
# ---------------------------------------------------------------------------

@given(
    max_retries=_max_retries,
    backoff=_backoff_strategy,
    base_delay=_base_delay,
    max_delay=_max_delay,
    return_value=_return_value,
    settings=settings(max_examples=50),
)
def test_retryexecutor_success_path(
    max_retries: int,
    backoff: str,
    base_delay: float,
    max_delay: float,
    return_value,
) -> None:
    """
        **Validates: Requirements 1.5**

        For all callables that return a value without raising an exception,
        the RetryExecutor execute method shall return a RetryResult with
        is_success == True, result equal to the callable's return value,
        and an empty attempts list.
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        backoff_strategy=backoff,
        base_delay=base_delay,
        max_delay=max_delay,
    )
    executor = RetryExecutor(policy)

    captured_value = return_value

    def successful_callable():
        return captured_value

    result = executor.execute(successful_callable)

    assert result.is_success is True, (
        "is_success should be True for a callable that succeeds, got {}".format(
            result.is_success
        )
    )

    assert result.result == captured_value or (result.result is captured_value), (
        "result value mismatch: expected {!r}, got {!r}".format(
            captured_value, result.result
        )
    )

    assert len(result.attempts) == 0, (
        "attempts list should be empty for immediate success, got {} attempts".format(
            len(result.attempts)
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 4: RetryExecutor failure path with exhausted retries
# ---------------------------------------------------------------------------

@given(
    max_retries=st.integers(min_value=1, max_value=5),
    backoff=_backoff_strategy,
    base_delay=st.floats(min_value=0.001, max_value=0.01),
    max_delay=st.floats(min_value=0.01, max_value=0.05),
    error_message=st.text(min_size=1, max_size=50),
    settings=settings(max_examples=50),
)
def test_retryexecutor_failure_path_exhausted_retries(
    max_retries: int,
    backoff: str,
    base_delay: float,
    max_delay: float,
    error_message: str,
) -> None:
    """
        **Validates: Requirements 1.6, 1.7**

        For all callables that always raise a retryable exception and for all
        RetryPolicy instances with max_retries >= 1, the RetryExecutor execute
        method shall return a RetryResult with is_success == False and
        len(attempts) == max_retries. Each RetryAttempt shall record the
        exception that triggered the retry.
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        backoff_strategy=backoff,
        base_delay=base_delay,
        max_delay=max_delay,
    )
    executor = RetryExecutor(policy)

    def always_failing_callable():
        raise RuntimeError(error_message)

    result = executor.execute(always_failing_callable)

    assert result.is_success is False, (
        "is_success should be False when all retries are exhausted, got {}".format(
            result.is_success
        )
    )

    assert len(result.attempts) == max_retries, (
        "attempts list length should equal max_retries ({}), got {}".format(
            max_retries, len(result.attempts)
        )
    )

    assert result.exception is not None, (
        "exception should not be None when retries are exhausted"
    )

    assert isinstance(result.exception, RuntimeError), (
        "exception should be a RuntimeError, got {}".format(
            type(result.exception).__name__
        )
    )

    for idx, attempt in enumerate(result.attempts):
        assert attempt.exception is not None, (
            "RetryAttempt {} should have a recorded exception".format(idx)
        )
        assert attempt.attempt_number == idx + 1, (
            "RetryAttempt {} should have attempt_number {}, got {}".format(
                idx, idx + 1, attempt.attempt_number
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 5: RetryExecutor non-retryable exception propagation
# ---------------------------------------------------------------------------

# A pool of exception types to choose from for retryable / non-retryable split.
_exception_types = [RuntimeError, ValueError, TypeError, KeyError, IOError, OSError]


@given(
    max_retries=st.integers(min_value=1, max_value=5),
    backoff=_backoff_strategy,
    base_delay=st.floats(min_value=0.001, max_value=0.01),
    max_delay=st.floats(min_value=0.01, max_value=0.05),
    error_message=st.text(min_size=1, max_size=50),
    retryable_index=st.integers(min_value=0, max_value=2),
    non_retryable_index=st.integers(min_value=3, max_value=5),
    settings=settings(max_examples=50),
)
def test_retryexecutor_non_retryable_exception_propagation(
    max_retries: int,
    backoff: str,
    base_delay: float,
    max_delay: float,
    error_message: str,
    retryable_index: int,
    non_retryable_index: int,
) -> None:
    """
        **Validates: Requirements 1.4**

        For all callables that raise a non-retryable exception (an exception
        whose type is not in the RetryPolicy retryable_exceptions list), the
        RetryExecutor execute method shall raise the same exception type
        immediately without creating any RetryAttempt objects.
    """
    retryable_type = _exception_types[retryable_index]
    non_retryable_type = _exception_types[non_retryable_index]

    policy = RetryPolicy(
        max_retries=max_retries,
        backoff_strategy=backoff,
        base_delay=base_delay,
        max_delay=max_delay,
        retryable_exceptions=[retryable_type],
    )
    executor = RetryExecutor(policy)

    def non_retryable_callable():
        raise non_retryable_type(error_message)

    caught_exception = None
    try:
        executor.execute(non_retryable_callable)
    except Exception as exc:
        caught_exception = exc

    assert caught_exception is not None, (
        "Expected a non-retryable exception to be raised, but no exception was raised"
    )

    assert isinstance(caught_exception, non_retryable_type), (
        "Expected exception type {}, got {}".format(
            non_retryable_type.__name__, type(caught_exception).__name__
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
