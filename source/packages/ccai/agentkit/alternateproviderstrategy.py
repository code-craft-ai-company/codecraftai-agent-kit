"""
    Defines the AlternateProviderStrategy for routing operations to an
    alternative provider when the primary dependency is unavailable.
"""

from typing import Callable
from typing import Optional

from ccai.agentkit.degradationstrategy import DegradationStrategy


class AlternateProviderStrategy(DegradationStrategy):
    """
        Routes the operation to an alternative provider or backend when
        the primary dependency is unavailable.

        :param alternate_callable: The callable to invoke as the alternate provider.
    """

    def __init__(self, alternate_callable: Callable) -> None:
        super().__init__("alternate_provider")
        self._alternate_callable = alternate_callable
        return

    def degrade(self, dependency_name: str, exception: Exception,
                context: Optional[dict] = None):
        """
            Invokes the alternate callable.

            :param dependency_name: Name of the unavailable dependency.
            :param exception: The exception that triggered degradation.
            :param context: Optional context dictionary.

            :returns: The result from the alternate callable.
        """
        return self._alternate_callable()
