"""
    Defines the CircuitBreakerHealthCheck for checking CircuitBreaker state.
"""

from ccai.agentkit.circuitbreakerstate import CircuitBreakerState
from ccai.agentkit.healthcheck import HealthCheck
from ccai.agentkit.healthstatus import HealthStatus


class CircuitBreakerHealthCheck(HealthCheck):
    """
        Checks CircuitBreaker state. Returns "degraded" when OPEN,
        "healthy" when CLOSED.

        :param name: The health check name.
        :param circuit_breaker: The CircuitBreaker instance to check.
        :param check_interval: The interval between checks in seconds.
    """

    def __init__(self, name: str, circuit_breaker, check_interval: float = 30.0) -> None:
        super().__init__(name, check_interval)
        self._circuit_breaker = circuit_breaker
        return

    def check(self) -> HealthStatus:
        state = self._circuit_breaker.state
        if state == CircuitBreakerState.OPEN:
            return HealthStatus(self._name, "degraded", detail="circuit breaker is OPEN")
        elif state == CircuitBreakerState.HALF_OPEN:
            return HealthStatus(self._name, "degraded", detail="circuit breaker is HALF_OPEN")
        else:
            return HealthStatus(self._name, "healthy")
