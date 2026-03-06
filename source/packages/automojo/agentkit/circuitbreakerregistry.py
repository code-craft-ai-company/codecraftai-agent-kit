"""
    Defines the CircuitBreakerRegistry class for tracking all CircuitBreaker
    instances for an Agent in the Error Handling & Resilience feature.
"""

from typing import List
from typing import Optional

from automojo.agentkit.circuitbreaker import CircuitBreaker
from automojo.agentkit.errors import SemanticError


class CircuitBreakerRegistry:
    """
        Registry tracking all CircuitBreaker instances for an Agent.
        Provides lookup by name and enumeration.
    """

    def __init__(self) -> None:
        self._circuit_breakers = {}
        return

    def register(self, circuit_breaker: CircuitBreaker) -> None:
        """
            Registers a CircuitBreaker using its name as the key.

            :param circuit_breaker: The CircuitBreaker to register.

            :raises SemanticError: If a circuit breaker with the same name exists.
        """
        name = circuit_breaker.name

        if name in self._circuit_breakers:
            errmsg = "CircuitBreaker with name '{}' is already registered.".format(name)
            raise SemanticError(errmsg)

        self._circuit_breakers[name] = circuit_breaker
        return

    def deregister(self, name: str) -> None:
        """
            Removes a CircuitBreaker by name.

            :param name: The name of the circuit breaker to remove.
        """
        self._circuit_breakers.pop(name, None)
        return

    def lookup(self, name: str) -> Optional[CircuitBreaker]:
        """
            Looks up a registered CircuitBreaker by name.

            :param name: The name to look up.

            :returns: The CircuitBreaker instance or None.
        """
        return self._circuit_breakers.get(name)

    def list_all(self) -> List[CircuitBreaker]:
        """
            Returns all registered CircuitBreaker instances.

            :returns: A list of CircuitBreaker instances.
        """
        return list(self._circuit_breakers.values())

    @property
    def count(self) -> int:
        """
            The count of currently registered circuit breakers.

            :returns: The count as an integer.
        """
        return len(self._circuit_breakers)

    def has_circuit_breaker(self, name: str) -> bool:
        """
            Checks whether a CircuitBreaker with the given name is registered.

            :param name: The name to check.

            :returns: True if registered, False otherwise.
        """
        return name in self._circuit_breakers

    def reset_all(self) -> None:
        """
            Calls the reset method on all registered CircuitBreaker instances.
        """
        for cb in self._circuit_breakers.values():
            cb.reset()
        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name
            and count of registered circuit breakers.

            :returns: A repr string for debugging.
        """
        repr_str = "CircuitBreakerRegistry(count={})".format(self.count)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered circuit
            breaker names and their current states.

            :returns: A human-readable string.
        """
        entries = []
        for name, cb in self._circuit_breakers.items():
            entries.append("{}={}".format(name, cb.state.value))

        str_val = "CircuitBreakerRegistry: [{}]".format(", ".join(entries))
        return str_val
