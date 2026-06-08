"""
    Defines the CachedResultStrategy for returning cached successful results
    when a dependency is unavailable.
"""

from typing import Optional

from ccai.agentkit.degradationstrategy import DegradationStrategy


class CachedResultStrategy(DegradationStrategy):
    """
        Returns the most recently cached successful result for the dependency
        when the dependency is unavailable.
    """

    def __init__(self) -> None:
        super().__init__("cached_result")
        self._cache = {}
        return

    def cache_result(self, dependency_name: str, result) -> None:
        """
            Caches a successful result for a dependency.

            :param dependency_name: The dependency name.
            :param result: The result to cache.
        """
        self._cache[dependency_name] = result
        return

    def degrade(self, dependency_name: str, exception: Exception,
                context: Optional[dict] = None):
        """
            Returns the most recently cached result for the dependency.

            :param dependency_name: Name of the unavailable dependency.
            :param exception: The exception that triggered degradation.
            :param context: Optional context dictionary.

            :returns: The cached result or None if no cache exists.
        """
        return self._cache.get(dependency_name)
