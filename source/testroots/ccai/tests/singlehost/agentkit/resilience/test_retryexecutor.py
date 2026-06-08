"""
    Unit tests for the ccai.agentkit.retryexecutor module.

    Tests RetryExecutor success path, retryable failure path, non-retryable
    exception, exhausted retries, and logging.
"""

from ccai.agentkit.retryexecutor import RetryExecutor
from ccai.agentkit.retrypolicy import RetryPolicy


def test_retry_executor_success_no_retries():
    """
        Verify that RetryExecutor returns success when callable succeeds
        on the first attempt.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=1.0)
    executor = RetryExecutor(policy)

    result = executor.execute(lambda: "ok")

    assert result.success is True, "result should be successful"
    assert result.result == "ok", "result value should be 'ok'"
    assert len(result.attempts) == 0, "should have no retry attempts"
    return


def test_retry_executor_success_after_retries():
    """
        Verify that RetryExecutor retries and eventually succeeds.
    """
    call_count = [0]

    def flaky_op():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("transient failure")
        return "recovered"

    policy = RetryPolicy(max_retries=5, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=1.0,
                         retryable_exceptions=[ValueError])
    executor = RetryExecutor(policy)

    result = executor.execute(flaky_op)

    assert result.success is True, "result should be successful"
    assert result.result == "recovered", "result value should be 'recovered'"
    assert len(result.attempts) == 2, "should have 2 retry attempts"
    return


def test_retry_executor_non_retryable_exception():
    """
        Verify that non-retryable exceptions are raised immediately.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=1.0,
                         retryable_exceptions=[ValueError])
    executor = RetryExecutor(policy)

    caught = False
    try:
        executor.execute(lambda: (_ for _ in ()).throw(TypeError("not retryable")))
    except TypeError as exc:
        caught = True
        assert "not retryable" in str(exc), "should propagate original exception"

    assert caught is True, "non-retryable exception should be raised immediately"
    return


def test_retry_executor_exhausted_retries():
    """
        Verify that RetryExecutor returns failure when all retries are exhausted.
    """
    def always_fail():
        raise ValueError("persistent failure")

    policy = RetryPolicy(max_retries=2, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=1.0,
                         retryable_exceptions=[ValueError])
    executor = RetryExecutor(policy)

    result = executor.execute(always_fail)

    assert result.success is False, "result should be failure"
    assert result.exception is not None, "should have final exception"
    assert "persistent failure" in str(result.exception), "should contain error message"
    assert len(result.attempts) == 2, "should have 2 retry attempts"
    return


def test_retry_executor_retry_policy_property():
    """
        Verify that retry_policy property returns the configured policy.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="exponential",
                         base_delay=1.0, max_delay=30.0)
    executor = RetryExecutor(policy)

    assert executor.retry_policy is policy, "retry_policy should return the configured policy"
    return


def test_retry_executor_repr():
    """
        Verify that __repr__ includes class name and configuration.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                         base_delay=1.0, max_delay=10.0)
    executor = RetryExecutor(policy)
    repr_str = repr(executor)

    assert "RetryExecutor" in repr_str, "repr should contain class name"
    assert "3" in repr_str, "repr should contain max retries"
    assert "fixed" in repr_str, "repr should contain strategy"
    return


def test_retry_executor_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    policy = RetryPolicy(max_retries=5, backoff_strategy="exponential",
                         base_delay=2.0, max_delay=60.0)
    executor = RetryExecutor(policy)
    str_val = str(executor)

    assert "5" in str_val, "str should contain max retries"
    assert "exponential" in str_val, "str should contain strategy"
    return


def test_retry_executor_elapsed_time_tracked():
    """
        Verify that elapsed_time is tracked in the result.
    """
    policy = RetryPolicy(max_retries=1, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=1.0)
    executor = RetryExecutor(policy)

    result = executor.execute(lambda: 42)

    assert result.elapsed_time >= 0.0, "elapsed_time should be non-negative"
    return


def test_retry_executor_attempt_records_exception():
    """
        Verify that retry attempts record the exception that triggered them.
    """
    call_count = [0]

    def fail_then_succeed():
        call_count[0] += 1
        if call_count[0] == 1:
            raise ValueError("first failure")
        return "ok"

    policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=1.0,
                         retryable_exceptions=[ValueError])
    executor = RetryExecutor(policy)

    result = executor.execute(fail_then_succeed)

    assert result.success is True, "should succeed after retry"
    assert len(result.attempts) == 1, "should have 1 retry attempt"

    attempt = result.attempts[0]
    assert attempt.attempt_number == 1, "attempt number should be 1"
    assert isinstance(attempt.exception, ValueError), "exception should be ValueError"
    return
