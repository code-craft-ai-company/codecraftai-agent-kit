"""
    Defines the DegradationManager class for monitoring dependency availability
    and applying degradation policies in the Error Handling & Resilience feature.
"""

import logging

from typing import Callable
from typing import Optional

from ccai.agentkit.degradationchangeevent import DegradationChangeEvent
from ccai.agentkit.degradationlevel import DegradationLevel
from ccai.agentkit.degradationpolicy import DegradationPolicy


class DegradationManager:
    """
        Monitors dependency availability and applies DegradationPolicy rules
        to maintain agent operation when dependencies fail.

        :param agent_identifier: The identifier of the owning agent.
    """

    def __init__(self, agent_identifier: str) -> None:
        self._agent_identifier = agent_identifier
        self._policies = {}
        self._dependency_levels = {}
        self._listeners = []
        self._logger = logging.getLogger("ccai.agentkit.resilience")
        return

    @property
    def agent_identifier(self) -> str:
        return self._agent_identifier

    @property
    def overall_level(self) -> DegradationLevel:
        """
            The overall degradation level, computed as the maximum across
            all dependencies.

            :returns: The overall DegradationLevel.
        """
        if len(self._dependency_levels) == 0:
            return DegradationLevel.NORMAL

        level_order = {
            DegradationLevel.NORMAL: 0,
            DegradationLevel.DEGRADED: 1,
            DegradationLevel.CRITICAL: 2
        }
        max_level = DegradationLevel.NORMAL
        max_order = 0

        for level in self._dependency_levels.values():
            order = level_order.get(level, 0)
            if order > max_order:
                max_order = order
                max_level = level

        return max_level

    def register_policy(self, policy: DegradationPolicy) -> None:
        """
            Registers a degradation policy for a dependency.

            :param policy: The DegradationPolicy to register.
        """
        self._policies[policy.dependency_name] = policy
        if policy.dependency_name not in self._dependency_levels:
            self._dependency_levels[policy.dependency_name] = DegradationLevel.NORMAL
        return

    def deregister_policy(self, dependency_name: str) -> None:
        """
            Removes a degradation policy for a dependency.

            :param dependency_name: The dependency name.
        """
        self._policies.pop(dependency_name, None)
        self._dependency_levels.pop(dependency_name, None)
        return

    def report_failure(self, dependency_name: str, exception: Exception) -> None:
        """
            Reports a failure for a dependency, potentially changing its
            degradation level.

            :param dependency_name: The dependency that failed.
            :param exception: The exception that occurred.
        """
        previous_level = self._dependency_levels.get(dependency_name, DegradationLevel.NORMAL)

        if previous_level == DegradationLevel.NORMAL:
            new_level = DegradationLevel.DEGRADED
        elif previous_level == DegradationLevel.DEGRADED:
            new_level = DegradationLevel.CRITICAL
        else:
            new_level = DegradationLevel.CRITICAL

        if new_level != previous_level:
            self._dependency_levels[dependency_name] = new_level
            reason = "Failure reported: {}".format(str(exception))

            event = DegradationChangeEvent(
                dependency_name=dependency_name,
                previous_level=previous_level,
                new_level=new_level,
                reason=reason
            )

            self._logger.warning(
                "Degradation level changed for '%s': %s -> %s (%s)",
                dependency_name, previous_level.value, new_level.value, reason
            )

            self._notify_listeners(event)
        return

    def report_recovery(self, dependency_name: str) -> None:
        """
            Reports recovery for a dependency, returning it to NORMAL level.

            :param dependency_name: The dependency that recovered.
        """
        previous_level = self._dependency_levels.get(dependency_name, DegradationLevel.NORMAL)

        if previous_level != DegradationLevel.NORMAL:
            self._dependency_levels[dependency_name] = DegradationLevel.NORMAL
            reason = "Dependency recovered"

            event = DegradationChangeEvent(
                dependency_name=dependency_name,
                previous_level=previous_level,
                new_level=DegradationLevel.NORMAL,
                reason=reason
            )

            self._logger.warning(
                "Degradation level changed for '%s': %s -> %s (%s)",
                dependency_name, previous_level.value, DegradationLevel.NORMAL.value, reason
            )

            self._notify_listeners(event)
        return

    def add_listener(self, listener: Callable) -> None:
        """
            Registers a DegradationChangeListener.

            :param listener: A callable accepting a DegradationChangeEvent.
        """
        self._listeners.append(listener)
        return

    def remove_listener(self, listener: Callable) -> None:
        """
            Removes a DegradationChangeListener.

            :param listener: The listener to remove.
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
        return

    def get_dependency_level(self, dependency_name: str) -> DegradationLevel:
        """
            Returns the current degradation level for a dependency.

            :param dependency_name: The dependency name.

            :returns: The current DegradationLevel.
        """
        return self._dependency_levels.get(dependency_name, DegradationLevel.NORMAL)

    def get_policy(self, dependency_name: str) -> Optional[DegradationPolicy]:
        """
            Returns the policy for a dependency.

            :param dependency_name: The dependency name.

            :returns: The DegradationPolicy or None.
        """
        return self._policies.get(dependency_name)

    def _notify_listeners(self, event: DegradationChangeEvent) -> None:
        """
            Notifies all registered listeners of a degradation change.
            Catches and logs listener exceptions.

            :param event: The DegradationChangeEvent.
        """
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as exc:
                self._logger.warning(
                    "DegradationChangeListener raised exception: %s", str(exc)
                )
        return

    def __repr__(self) -> str:
        repr_str = "DegradationManager(agent={!r}, overall_level={})".format(
            self._agent_identifier, self.overall_level.value
        )
        return repr_str

    def __str__(self) -> str:
        str_val = "DegradationManager agent='{}', overall_level={}, policies={}".format(
            self._agent_identifier, self.overall_level.value, len(self._policies)
        )
        return str_val
