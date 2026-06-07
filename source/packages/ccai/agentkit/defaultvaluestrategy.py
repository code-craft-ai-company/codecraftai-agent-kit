"""
    Defines the DefaultValueStrategy for returning a configured default value
    when a dependency is unavailable.
"""

from typing import Optional

from ccai.agentkit.degradationstrategy import DegradationStrategy


class DefaultValueStrategy(DegradationStrategy):
    """
        Returns a configured default value when the dependency is unavailable.

        :param default_value: The default value to return.
    """

    def __init__(self, default_value) -> None:
        super().__init__("default_value")
        self._default_value = default_value
        return

    @property
    def default_value(self):
        """
            The configured default value.

            :returns: The default value.
        """
        return self._default_value

    def degrade(self, dependency_name: str, exception: Exception,
                context: Optional[dict] = None):
        """
            Returns the configured default value.

            :param dependency_name: Name of the unavailable dependency.
            :param exception: The exception that triggered degradation.
            :param context: Optional context dictionary.

            :returns: The configured default value.
        """
        return self._default_value
