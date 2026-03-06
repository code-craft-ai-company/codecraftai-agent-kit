"""
    Defines the MetricsRegistry class that tracks all MetricDefinition
    instances available to an Agent.

    The registry provides registration, deregistration, lookup by name,
    enumeration, and count of registered metric definitions. Duplicate
    name registration raises SemanticError.
"""

from typing import Optional

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.metricdefinition import MetricDefinition


class MetricsRegistry:
    """
        A registry that tracks all MetricDefinition instances available
        to an Agent, providing lookup by name and enumeration.

        Metric definitions are stored in a dictionary keyed by metric
        name. Attempting to register a definition with a name that
        already exists raises a SemanticError.
    """

    def __init__(self) -> None:

        self._definitions = {}

        return

    @property
    def count(self) -> int:
        """
            The count of currently registered metric definitions.

            :returns: The number of registered metrics as an integer.
        """
        return len(self._definitions)

    def register(self, definition: MetricDefinition) -> None:
        """
            Registers a MetricDefinition instance using the metric name
            as the registration key.

            :param definition: The MetricDefinition instance to register.

            :raises SemanticError: If a MetricDefinition with the same
                name is already registered.
        """
        name = definition.name

        if name in self._definitions:
            raise SemanticError(
                "Duplicate metric name: {!r} is already registered".format(name)
            )

        self._definitions[name] = definition

        return

    def deregister(self, name: str) -> None:
        """
            Removes a MetricDefinition from the registry by name.

            If the name is not found, the method silently returns
            without raising an error.

            :param name: The metric name string to deregister.
        """
        self._definitions.pop(name, None)

        return

    def lookup(self, name: str) -> Optional[MetricDefinition]:
        """
            Looks up a registered MetricDefinition by name.

            :param name: The metric name string to look up.

            :returns: The MetricDefinition instance if found, or None
                when the name is not registered.
        """
        result = self._definitions.get(name, None)
        return result

    def has_metric(self, name: str) -> bool:
        """
            Checks whether a MetricDefinition with the given name is
            registered.

            :param name: The metric name string to check.

            :returns: True if the metric is registered, False otherwise.
        """
        result = name in self._definitions
        return result

    def list_all(self) -> list:
        """
            Returns a list of all registered MetricDefinition instances.

            :returns: A list of MetricDefinition objects.
        """
        result = list(self._definitions.values())
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of registered metrics.

            :returns: A repr string for debugging.
        """
        repr_str = "MetricsRegistry(count={})".format(len(self._definitions))
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered
            metric names and types.

            :returns: A human-readable string.
        """
        entries = []
        for name, defn in self._definitions.items():
            entries.append("{}({})".format(name, defn.metric_type.value))

        str_val = "MetricsRegistry: metrics=[{}]".format(", ".join(entries))
        return str_val
