"""
    Defines the SelfHealingAction abstract base class for automated
    recovery actions triggered by unhealthy health checks.
"""

import abc

from automojo.agentkit.healthstatus import HealthStatus


class SelfHealingAction(abc.ABC):
    """
        Abstract base class representing an automated recovery action
        triggered when a HealthCheck reports an unhealthy status.

        :param action_name: The name of the healing action.
    """

    def __init__(self, action_name: str) -> None:
        self._action_name = action_name
        return

    @property
    def action_name(self) -> str:
        return self._action_name

    @abc.abstractmethod
    def heal(self, check_name: str, status: HealthStatus):
        """
            Executes the healing action.

            :param check_name: Name of the health check that triggered healing.
            :param status: The HealthStatus that triggered the action.

            :returns: A SelfHealingResult.
        """
        ...

    def __repr__(self) -> str:
        return "{}(action_name={!r})".format(self.__class__.__name__, self._action_name)

    def __str__(self) -> str:
        return "{} action_name='{}'".format(self.__class__.__name__, self._action_name)
