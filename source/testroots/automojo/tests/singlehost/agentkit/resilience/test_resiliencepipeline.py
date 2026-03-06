"""
    Unit tests for ResiliencePipeline.
"""

from automojo.agentkit.circuitbreaker import CircuitBreaker
from automojo.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from automojo.agentkit.resilienceconfiguration import ResilienceConfiguration
from automojo.agentkit.resilienceerrors import CircuitBreakerOpenError
from automojo.agentkit.resilienceerrors import ResilienceError
from automojo.agentkit.resiliencepipeline import ResiliencePipeline
from automojo.agentkit.retrypolicy import RetryPolicy


def test_pipeline_initializes_all_components():
    """
        Verify pipeline initializes all components when all flags are True.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=0.1)
    config = ResilienceConfiguration(default_retry_policy=policy)
    pipeline = ResiliencePipeline(config, "agent-1")

    assert pipeline.retry_executor is not None, "retry_executor should be initialized"
    assert pipeline.circuit_breaker_registry is not None, "cb_registry should be initialized"
    assert pipeline.degradation_manager is not None, "degradation_manager should be initialized"
    assert pipeline.dead_letter_queue is not None, "dead_letter_queue should be initialized"
    assert pipeline.health_monitor is not None, "health_monitor should be initialized"
    return


def test_pipeline_disabled_components():
    """
        Verify pipeline skips components when flags are False.
    """
    config = ResilienceConfiguration(
        circuit_breaker_enabled=False,
        degradation_enabled=False,
        dead_letter_enabled=False,
        health_monitoring_enabled=False,
        self_healing_enabled=False
    )
    pipeline = ResiliencePipeline(config, "agent-1")

    assert pipeline.retry_executor is None, "retry_executor should be None"
    assert pipeline.circuit_breaker_registry is None, "cb_registry should be None"
    assert pipeline.degradation_manager is None, "degradation_manager should be None"
    assert pipeline.dead_letter_queue is None, "dead_letter_queue should be None"
    assert pipeline.health_monitor is None, "health_monitor should be None"
    return


def test_pipeline_execute_success_with_retry():
    """
        Verify execute_with_resilience returns result on success.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=0.1)
    config = ResilienceConfiguration(default_retry_policy=policy)
    pipeline = ResiliencePipeline(config, "agent-1")

    result = pipeline.execute_with_resilience(lambda: 42, operation_name="test-op")

    assert result == 42, "should return callable result"
    return


def test_pipeline_execute_success_no_retry():
    """
        Verify execute_with_resilience works without retry executor.
    """
    config = ResilienceConfiguration()
    pipeline = ResiliencePipeline(config, "agent-1")

    result = pipeline.execute_with_resilience(lambda: "hello")

    assert result == "hello", "should return callable result"
    return


def test_pipeline_execute_failure_raises_resilience_error():
    """
        Verify execute_with_resilience raises ResilienceError after retries exhausted.
    """
    policy = RetryPolicy(max_retries=1, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=0.1)
    config = ResilienceConfiguration(default_retry_policy=policy)
    pipeline = ResiliencePipeline(config, "agent-1")

    raised = False
    try:
        pipeline.execute_with_resilience(
            lambda: (_ for _ in ()).throw(ValueError("fail")),
            operation_name="test-op"
        )
    except ResilienceError:
        raised = True

    assert raised is True, "should raise ResilienceError after retries exhausted"
    return


def test_pipeline_execute_failure_enqueues_dead_letter():
    """
        Verify failed operations are enqueued to dead letter queue.
    """
    policy = RetryPolicy(max_retries=1, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=0.1)
    config = ResilienceConfiguration(default_retry_policy=policy)
    pipeline = ResiliencePipeline(config, "agent-1")

    try:
        pipeline.execute_with_resilience(
            lambda: (_ for _ in ()).throw(ValueError("fail")),
            operation_name="test-op"
        )
    except ResilienceError:
        pass

    assert pipeline.dead_letter_queue.entry_count == 1, "should have 1 dead letter entry"
    return


def test_pipeline_circuit_breaker_open_raises():
    """
        Verify CircuitBreakerOpenError is raised when CB is OPEN.
    """
    policy = RetryPolicy(max_retries=1, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=0.1)
    config = ResilienceConfiguration(default_retry_policy=policy)
    pipeline = ResiliencePipeline(config, "agent-1")

    cb_config = CircuitBreakerConfiguration(
        failure_threshold=1, success_threshold=1,
        open_state_timeout=60.0, half_open_max_attempts=1
    )
    cb = CircuitBreaker("test-service", cb_config)
    pipeline.circuit_breaker_registry.register(cb)

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    raised = False
    try:
        pipeline.execute_with_resilience(
            lambda: "ok",
            circuit_breaker_name="test-service"
        )
    except CircuitBreakerOpenError:
        raised = True

    assert raised is True, "should raise CircuitBreakerOpenError"
    return


def test_pipeline_nonexistent_circuit_breaker_raises():
    """
        Verify ResilienceError for non-existent circuit breaker name.
    """
    config = ResilienceConfiguration()
    pipeline = ResiliencePipeline(config, "agent-1")

    raised = False
    try:
        pipeline.execute_with_resilience(
            lambda: "ok",
            circuit_breaker_name="nonexistent"
        )
    except ResilienceError:
        raised = True

    assert raised is True, "should raise ResilienceError for unknown CB"
    return


def test_pipeline_circuit_breaker_success():
    """
        Verify successful execution through circuit breaker.
    """
    config = ResilienceConfiguration()
    pipeline = ResiliencePipeline(config, "agent-1")

    cb_config = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=2,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    cb = CircuitBreaker("test-service", cb_config)
    pipeline.circuit_breaker_registry.register(cb)

    result = pipeline.execute_with_resilience(
        lambda: "success",
        circuit_breaker_name="test-service"
    )

    assert result == "success", "should return callable result through CB"
    return


def test_pipeline_repr():
    """
        Verify __repr__ contains key fields.
    """
    config = ResilienceConfiguration()
    pipeline = ResiliencePipeline(config, "agent-1")
    repr_str = repr(pipeline)

    assert "ResiliencePipeline" in repr_str, "repr should contain class name"
    assert "agent-1" in repr_str, "repr should contain agent_identifier"
    return


def test_pipeline_str():
    """
        Verify __str__ contains key fields.
    """
    config = ResilienceConfiguration()
    pipeline = ResiliencePipeline(config, "agent-1")
    str_val = str(pipeline)

    assert "ResiliencePipeline" in str_val, "str should contain class name"
    assert "agent-1" in str_val, "str should contain agent_identifier"
    return
