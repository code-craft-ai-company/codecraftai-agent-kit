"""
    Unit tests for resilience observability integration.

    Verifies that all resilience components log at the correct levels
    as specified by Requirements 26.1 through 26.8.
"""

import logging

from ccai.agentkit.circuitbreaker import CircuitBreaker
from ccai.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from ccai.agentkit.deadletterqueue import DeadLetterQueue
from ccai.agentkit.degradationlevel import DegradationLevel
from ccai.agentkit.degradationmanager import DegradationManager
from ccai.agentkit.degradationpolicy import DegradationPolicy
from ccai.agentkit.defaultvaluestrategy import DefaultValueStrategy
from ccai.agentkit.healthcheckregistry import HealthCheckRegistry
from ccai.agentkit.healthmonitor import HealthMonitor
from ccai.agentkit.healthstatus import HealthStatus
from ccai.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore
from ccai.agentkit.retryexecutor import RetryExecutor
from ccai.agentkit.retrypolicy import RetryPolicy
from ccai.agentkit.selfhealingpolicy import SelfHealingPolicy
from ccai.agentkit.selfhealingresult import SelfHealingResult
from ccai.testbase.mocking import Mock


class _LogCapture(logging.Handler):
    """
        Captures log records for assertion.
    """

    def __init__(self):
        super().__init__()
        self.records = []
        return

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        return


def _attach_handler() -> tuple:
    """
        Creates a _LogCapture handler and attaches it to the resilience logger.

        :returns: A tuple of (handler, logger).
    """
    handler = _LogCapture()
    logger = logging.getLogger("ccai.agentkit.resilience")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return handler, logger


def test_retry_executor_logs_at_info():
    """
        Verify RetryExecutor logs retry attempts at INFO level.
        Validates: Requirements 26.1, 26.2
    """
    handler, logger = _attach_handler()

    try:
        policy = RetryPolicy(max_retries=1, backoff_strategy="fixed",
                             base_delay=0.01, max_delay=0.1)
        executor = RetryExecutor(policy)
        executor.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))

        info_records = [r for r in handler.records if r.levelno == logging.INFO]
        assert len(info_records) > 0, "should have INFO log for retry attempt"

        log_message = info_records[0].getMessage()
        assert "1" in log_message, "log should contain attempt number"
    finally:
        logger.removeHandler(handler)
    return


def test_retry_executor_log_contains_delay_and_exception_type():
    """
        Verify RetryExecutor INFO log includes delay and exception type.
        Validates: Requirements 26.2
    """
    handler, logger = _attach_handler()

    try:
        policy = RetryPolicy(max_retries=2, backoff_strategy="fixed",
                             base_delay=0.01, max_delay=0.1,
                             retryable_exceptions=[ValueError])
        executor = RetryExecutor(policy)

        call_count = [0]

        def fail_then_succeed():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("transient")
            return "ok"

        executor.execute(fail_then_succeed)

        info_records = [r for r in handler.records if r.levelno == logging.INFO]
        assert len(info_records) == 1, "should have exactly 1 INFO log for 1 retry"

        log_message = info_records[0].getMessage()
        assert "ValueError" in log_message, "log should contain exception type"
    finally:
        logger.removeHandler(handler)
    return


def test_circuit_breaker_logs_at_warning():
    """
        Verify CircuitBreaker logs state transitions at WARNING level.
        Validates: Requirements 26.3
    """
    handler, logger = _attach_handler()

    try:
        config = CircuitBreakerConfiguration(
            failure_threshold=1, success_threshold=1,
            open_state_timeout=30.0, half_open_max_attempts=1
        )
        cb = CircuitBreaker("obs-test", config)

        try:
            cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        warning_records = [r for r in handler.records if r.levelno == logging.WARNING]
        assert len(warning_records) > 0, "should have WARNING log for state transition"

        log_message = warning_records[0].getMessage()
        assert "obs-test" in log_message, "log should contain circuit breaker name"
        assert "CLOSED" in log_message, "log should contain previous state"
        assert "OPEN" in log_message, "log should contain new state"
    finally:
        logger.removeHandler(handler)
    return


def test_degradation_manager_logs_at_warning():
    """
        Verify DegradationManager logs level changes at WARNING level.
        Validates: Requirements 26.4
    """
    handler, logger = _attach_handler()

    try:
        manager = DegradationManager("agent-obs")
        strategy = DefaultValueStrategy(default_value="fallback")
        policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
        manager.register_policy(policy)
        manager.report_failure("db", RuntimeError("down"))

        warning_records = [r for r in handler.records if r.levelno == logging.WARNING]
        assert len(warning_records) > 0, "should have WARNING log for degradation change"

        log_message = warning_records[0].getMessage()
        assert "db" in log_message, "log should contain dependency name"
        assert "NORMAL" in log_message, "log should contain previous level"
        assert "DEGRADED" in log_message, "log should contain new level"
    finally:
        logger.removeHandler(handler)
    return


def test_dead_letter_queue_logs_at_warning():
    """
        Verify DeadLetterQueue logs enqueue at WARNING level.
        Validates: Requirements 26.5
    """
    handler, logger = _attach_handler()

    try:
        store = InMemoryDeadLetterStore()
        dlq = DeadLetterQueue(store)
        dlq.enqueue("send_message", {"data": "test"}, "ConnectionError",
                     3, "transport", "agent-01")

        warning_records = [r for r in handler.records if r.levelno == logging.WARNING]
        assert len(warning_records) > 0, "should have WARNING log for enqueue"

        log_message = warning_records[0].getMessage()
        assert "send_message" in log_message, "log should contain operation type"
        assert "transport" in log_message, "log should contain source component"
    finally:
        logger.removeHandler(handler)
    return


def test_health_monitor_logs_healthy_at_debug():
    """
        Verify HealthMonitor logs healthy checks at DEBUG level.
        Validates: Requirements 26.6
    """
    handler, logger = _attach_handler()

    try:
        mock_check = Mock()
        mock_check.configure(recursive=True)
        ctx = mock_check.mock_context()
        ctx.set_attribute("name", "test-check")
        ctx.set_attribute("check_interval", 30.0)
        status = HealthStatus("test-check", "healthy")
        ctx.mock_method("check", return_value=status)

        registry = HealthCheckRegistry()
        registry.register(mock_check)
        monitor = HealthMonitor(registry)
        monitor.check_now()

        debug_records = [r for r in handler.records if r.levelno == logging.DEBUG]
        assert len(debug_records) > 0, "should have DEBUG log for healthy check"

        log_message = debug_records[0].getMessage()
        assert "test-check" in log_message, "log should contain check name"
    finally:
        logger.removeHandler(handler)
    return


def test_health_monitor_logs_unhealthy_at_warning():
    """
        Verify HealthMonitor logs unhealthy checks at WARNING level.
        Validates: Requirements 26.6
    """
    handler, logger = _attach_handler()

    try:
        mock_check = Mock()
        mock_check.configure(recursive=True)
        ctx = mock_check.mock_context()
        ctx.set_attribute("name", "bad-check")
        ctx.set_attribute("check_interval", 30.0)
        status = HealthStatus("bad-check", "unhealthy", detail="down")
        ctx.mock_method("check", return_value=status)

        registry = HealthCheckRegistry()
        registry.register(mock_check)
        monitor = HealthMonitor(registry)
        monitor.check_now()

        warning_records = [r for r in handler.records if r.levelno == logging.WARNING]
        assert len(warning_records) > 0, "should have WARNING log for unhealthy check"

        log_message = warning_records[0].getMessage()
        assert "bad-check" in log_message, "log should contain check name"
        assert "down" in log_message, "log should contain detail message"
    finally:
        logger.removeHandler(handler)
    return


def test_health_monitor_logs_degraded_at_warning():
    """
        Verify HealthMonitor logs degraded checks at WARNING level.
        Validates: Requirements 26.6
    """
    handler, logger = _attach_handler()

    try:
        mock_check = Mock()
        mock_check.configure(recursive=True)
        ctx = mock_check.mock_context()
        ctx.set_attribute("name", "slow-check")
        ctx.set_attribute("check_interval", 30.0)
        status = HealthStatus("slow-check", "degraded", detail="high latency")
        ctx.mock_method("check", return_value=status)

        registry = HealthCheckRegistry()
        registry.register(mock_check)
        monitor = HealthMonitor(registry)
        monitor.check_now()

        warning_records = [r for r in handler.records if r.levelno == logging.WARNING]
        assert len(warning_records) > 0, "should have WARNING log for degraded check"

        log_message = warning_records[0].getMessage()
        assert "slow-check" in log_message, "log should contain check name"
    finally:
        logger.removeHandler(handler)
    return


def test_health_monitor_logs_self_healing_at_info():
    """
        Verify HealthMonitor logs self-healing execution at INFO level.
        Validates: Requirements 26.7
    """
    handler, logger = _attach_handler()

    try:
        mock_check = Mock()
        mock_check.configure(recursive=True)
        ctx = mock_check.mock_context()
        ctx.set_attribute("name", "transport-check")
        ctx.set_attribute("check_interval", 30.0)
        status = HealthStatus("transport-check", "unhealthy", detail="disconnected")
        ctx.mock_method("check", return_value=status)

        mock_action = Mock()
        mock_action.configure(recursive=True)
        action_ctx = mock_action.mock_context()
        action_ctx.set_attribute("action_name", "reconnect")

        def heal_fn(check_name: str, health_status: HealthStatus) -> SelfHealingResult:
            return SelfHealingResult(
                check_name=check_name,
                action_name="reconnect",
                success=True
            )

        action_ctx.mock_method("heal", side_effect=heal_fn)

        policy = SelfHealingPolicy("transport-check", mock_action,
                                   max_attempts=3, cooldown_interval=60.0)

        registry = HealthCheckRegistry()
        registry.register(mock_check)
        monitor = HealthMonitor(registry)
        monitor.register_healing_policy(policy)
        monitor.check_now()

        info_records = [r for r in handler.records if r.levelno == logging.INFO]
        assert len(info_records) > 0, "should have INFO log for self-healing action"

        log_message = info_records[0].getMessage()
        assert "transport-check" in log_message, "log should contain health check name"
        assert "reconnect" in log_message, "log should contain action name"
    finally:
        logger.removeHandler(handler)
    return


def test_health_monitor_logs_healing_exception_at_warning():
    """
        Verify HealthMonitor logs self-healing exceptions at WARNING level.
        Validates: Requirements 26.7
    """
    handler, logger = _attach_handler()

    try:
        mock_check = Mock()
        mock_check.configure(recursive=True)
        ctx = mock_check.mock_context()
        ctx.set_attribute("name", "cache-check")
        ctx.set_attribute("check_interval", 30.0)
        status = HealthStatus("cache-check", "unhealthy", detail="corrupted")
        ctx.mock_method("check", return_value=status)

        mock_action = Mock()
        mock_action.configure(recursive=True)
        action_ctx = mock_action.mock_context()
        action_ctx.set_attribute("action_name", "clear_cache")

        def raise_heal(check_name: str, health_status: HealthStatus) -> None:
            raise RuntimeError("heal failed")

        action_ctx.mock_method("heal", side_effect=raise_heal)

        policy = SelfHealingPolicy("cache-check", mock_action,
                                   max_attempts=3, cooldown_interval=60.0)

        registry = HealthCheckRegistry()
        registry.register(mock_check)
        monitor = HealthMonitor(registry)
        monitor.register_healing_policy(policy)
        monitor.check_now()

        warning_records = [r for r in handler.records if r.levelno == logging.WARNING]
        healing_warnings = [r for r in warning_records
                           if "clear_cache" in r.getMessage() or "heal" in r.getMessage().lower()]
        assert len(healing_warnings) > 0, "should have WARNING log for healing exception"
    finally:
        logger.removeHandler(handler)
    return
