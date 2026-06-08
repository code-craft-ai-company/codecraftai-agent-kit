"""
    Defines the HealthCheckRegistry for tracking HealthCheck instances.
"""

from typing import List
from typing import Optional

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.healthcheck import HealthCheck


class HealthCheckRegistry:
    """
        Registry tracking all HealthCheck instances for an Agent.
    """

    def __init__(self) -> None:
        self._health_checks = {}
        return

    def register(self, health_check: HealthCheck) -> None:
        name = health_check.name
        if name in self._health_checks:
            errmsg = "HealthCheck with name '{}' is already registered.".format(name)
            raise SemanticError(errmsg)
        self._health_checks[name] = health_check
        return

    def deregister(self, name: str) -> None:
        self._health_checks.pop(name, None)
        return

    def lookup(self, name: str) -> Optional[HealthCheck]:
        return self._health_checks.get(name)

    def list_all(self) -> List[HealthCheck]:
        return list(self._health_checks.values())

    @property
    def count(self) -> int:
        return len(self._health_checks)

    def has_health_check(self, name: str) -> bool:
        return name in self._health_checks

    def __repr__(self) -> str:
        return "HealthCheckRegistry(count={})".format(self.count)

    def __str__(self) -> str:
        names = list(self._health_checks.keys())
        return "HealthCheckRegistry: [{}]".format(", ".join(names))
