"""
    Defines the ResetCircuitBreakerAction for resetting a CircuitBreaker
    to the CLOSED state.
"""

from automojo.agentkit.circuitbreaker import CircuitBreaker
from automojo.agentkit.healthstatus import HealthStatus
from automojo.agentkit.selfhealingaction import SelfHealingAction
from automojo.agentkit.selfhealingresult import SelfHealingResult


class ResetCircuitBreakerAction(SelfHealingAction):
    """
        Resets a CircuitBreaker to the CLOSED state.

        :param circuit_breaker: The CircuitBreaker instance to reset.
    """

    def __init__(self, circuit_breaker: CircuitBreaker) -> None:
        super().__init__(action_name="reset_circuit_breaker")
        self._circuit_breaker = circuit_breaker
        return

    def heal(self, check_name: str, status: HealthStatus) -> SelfHealingResult:
        """
            Resets the circuit breaker to CLOSED.

            :param check_name: Name of the health check that triggered healing.
            :param status: The HealthStatus that triggered the action.

            :returns: A SelfHealingResult indicating success or failure.
        """
        try:
            self._circuit_breaker.reset()
            result = SelfHealingResult(
                check_name=check_name,
                action_name=self._action_name,
                success=True
            )
            return result
        except Exception as exc:
            result = SelfHealingResult(
                check_name=check_name,
                action_name=self._action_name,
                success=False,
                error_message=str(exc)
            )
            return result
