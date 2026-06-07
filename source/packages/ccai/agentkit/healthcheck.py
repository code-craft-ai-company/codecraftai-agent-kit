"""
    Defines the HealthCheck abstract base class for health checks.
"""

import abc

from ccai.agentkit.healthstatus import HealthStatus


class HealthCheck(abc.ABC):
    """
        Abstract base class representing a health check for a specific
        agent component or external dependency.

        :param name: The name of the health check.
        :param check_interval: The interval between checks in seconds.
    """

    def __init__(self, name: str, check_interval: float = 30.0) -> None:
        self._name = name
        self._check_interval = check_interval
        return

    @property
    def name(self) -> str:
        return self._name

    @property
    def check_interval(self) -> float:
        return self._check_interval

    @abc.abstractmethod
    def check(self) -> HealthStatus:
        ...

    def __repr__(self) -> str:
        return "{}(name={!r})".format(self.__class__.__name__, self._name)

    def __str__(self) -> str:
        return "{} name='{}', interval={}s".format(
            self.__class__.__name__, self._name, self._check_interval
        )
