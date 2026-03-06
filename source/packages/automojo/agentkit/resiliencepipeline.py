"""
    Defines the ResiliencePipeline class that coordinates all resilience
    components for an Agent in the Error Handling & Resilience feature.
"""

import logging

from automojo.agentkit.circuitbreakerregistry import CircuitBreakerRegistry
from automojo.agentkit.deadletterqueue import DeadLetterQueue
from automojo.agentkit.degradationmanager import DegradationManager
from automojo.agentkit.healthcheckregistry import HealthCheckRegistry
from automojo.agentkit.healthmonitor import HealthMonitor
from automojo.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore
from automojo.agentkit.resilienceconfiguration import ResilienceConfiguration
from automojo.agentkit.resilienceerrors import CircuitBreakerOpenError
from automojo.agentkit.resilienceerrors import ResilienceError
from automojo.agentkit.retryexecutor import RetryExecutor


class ResiliencePipeline:
    """
        Coordinates the RetryExecutor, CircuitBreakerRegistry,
        DegradationManager, DeadLetterQueue, and HealthMonitor for an Agent.

        :param configuration: The ResilienceConfiguration.
        :param agent_identifier: The agent identifier string.
    """

    def __init__(self, configuration: ResilienceConfiguration,
                 agent_identifier: str) -> None:
        self._configuration = configuration
        self._agent_identifier = agent_identifier
        self._logger = logging.getLogger("automojo.agentkit.resilience")

        # Initialize RetryExecutor
        self._retry_executor = None
        if configuration.default_retry_policy is not None:
            self._retry_executor = RetryExecutor(configuration.default_retry_policy)

        # Initialize CircuitBreakerRegistry
        self._circuit_breaker_registry = None
        if configuration.circuit_breaker_enabled:
            self._circuit_breaker_registry = CircuitBreakerRegistry()

        # Initialize DegradationManager
        self._degradation_manager = None
        if configuration.degradation_enabled:
            self._degradation_manager = DegradationManager(agent_identifier)

        # Initialize DeadLetterQueue
        self._dead_letter_queue = None
        if configuration.dead_letter_enabled:
            store = InMemoryDeadLetterStore()
            self._dead_letter_queue = DeadLetterQueue(store)

        # Initialize HealthMonitor
        self._health_monitor = None
        if configuration.health_monitoring_enabled:
            registry = HealthCheckRegistry()
            self._health_monitor = HealthMonitor(
                registry, configuration.health_check_interval
            )

        return

    @property
    def configuration(self) -> ResilienceConfiguration:
        return self._configuration

    @property
    def retry_executor(self):
        return self._retry_executor

    @property
    def circuit_breaker_registry(self):
        return self._circuit_breaker_registry

    @property
    def degradation_manager(self):
        return self._degradation_manager

    @property
    def dead_letter_queue(self):
        return self._dead_letter_queue

    @property
    def health_monitor(self):
        return self._health_monitor

    def execute_with_resilience(self, callable_op, operation_name: str = None,
                                retry_policy=None,
                                circuit_breaker_name: str = None):
        """
            Executes the callable with retry logic and circuit breaker
            protection. On permanent failure, enqueues to dead letter queue
            and/or applies degradation strategy.

            :param callable_op: The callable to execute.
            :param operation_name: Optional name for the operation.
            :param retry_policy: Optional RetryPolicy override.
            :param circuit_breaker_name: Optional circuit breaker name.

            :returns: The operation result.
            :raises CircuitBreakerOpenError: If circuit breaker is OPEN.
            :raises ResilienceError: On resilience operation failure.
        """
        op_name = operation_name if operation_name is not None else "unknown"

        # Step 1: Check circuit breaker
        if circuit_breaker_name is not None and self._circuit_breaker_registry is not None:
            cb = self._circuit_breaker_registry.lookup(circuit_breaker_name)
            if cb is None:
                raise ResilienceError(
                    "Circuit breaker '{}' not found".format(circuit_breaker_name)
                )

            try:
                result = cb.execute(callable_op)
                return result
            except CircuitBreakerOpenError:
                # Try degradation fallback
                if self._degradation_manager is not None:
                    fallback = self._degradation_manager.report_failure(
                        circuit_breaker_name,
                        CircuitBreakerOpenError(circuit_breaker_name, circuit_breaker_name, 0.0)
                    )
                    if fallback is not None:
                        return fallback
                raise
            except Exception:
                raise

        # Step 2: Execute with retry
        if self._retry_executor is not None:
            policy = retry_policy if retry_policy is not None else self._configuration.default_retry_policy
            executor = RetryExecutor(policy) if retry_policy is not None else self._retry_executor
            retry_result = executor.execute(callable_op)

            if retry_result.is_success:
                return retry_result.result

            # All retries exhausted
            final_exception = retry_result.exception

            # Try degradation
            if self._degradation_manager is not None and operation_name is not None:
                fallback = self._degradation_manager.report_failure(
                    operation_name, final_exception
                )
                if fallback is not None:
                    return fallback

            # Enqueue to dead letter
            if self._dead_letter_queue is not None:
                self._dead_letter_queue.enqueue(
                    operation_type=op_name,
                    payload={},
                    exception_info=str(final_exception),
                    retry_attempts=len(retry_result.attempts),
                    source_component="ResiliencePipeline",
                    agent_identifier=self._agent_identifier
                )

            raise ResilienceError(
                "Operation '{}' failed after retries".format(op_name),
                cause=final_exception
            )

        # Step 3: No retry executor, just call directly
        try:
            result = callable_op()
            return result
        except Exception as exc:
            if self._dead_letter_queue is not None:
                self._dead_letter_queue.enqueue(
                    operation_type=op_name,
                    payload={},
                    exception_info=str(exc),
                    retry_attempts=0,
                    source_component="ResiliencePipeline",
                    agent_identifier=self._agent_identifier
                )
            raise

    def __repr__(self) -> str:
        return "ResiliencePipeline(agent={!r}, cb={}, deg={}, dl={}, hm={})".format(
            self._agent_identifier,
            self._circuit_breaker_registry is not None,
            self._degradation_manager is not None,
            self._dead_letter_queue is not None,
            self._health_monitor is not None
        )

    def __str__(self) -> str:
        return "ResiliencePipeline agent='{}', components: cb={}, degradation={}, dead_letter={}, health={}".format(
            self._agent_identifier,
            self._circuit_breaker_registry is not None,
            self._degradation_manager is not None,
            self._dead_letter_queue is not None,
            self._health_monitor is not None
        )
