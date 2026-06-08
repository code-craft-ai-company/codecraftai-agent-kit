"""
    Defines the DegradationStrategy abstract base class for graceful
    degradation when a dependency is unavailable.
"""

import abc

from typing import Optional


class DegradationStrategy(abc.ABC):
    """
        Abstract base class representing a strategy for graceful degradation
        when a dependency is unavailable. Concrete implementations define
        fallback behavior.

        :param strategy_name: The name of the strategy.
    """

    def __init__(self, strategy_name: str) -> None:
        self._strategy_name = strategy_name
        return

    @property
    def strategy_name(self) -> str:
        """
            The name of the strategy.

            :returns: The strategy name string.
        """
        return self._strategy_name

    @abc.abstractmethod
    def degrade(self, dependency_name: str, exception: Exception,
                context: Optional[dict] = None):
        """
            Applies the degradation strategy and returns a fallback result.

            :param dependency_name: Name of the unavailable dependency.
            :param exception: The exception that triggered degradation.
            :param context: Optional context dictionary.

            :returns: A fallback result value.
        """
        ...

    def __repr__(self) -> str:
        """
            Returns a detailed string representation.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(strategy_name={!r})".format(
            self.__class__.__name__, self._strategy_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary.

            :returns: A human-readable string.
        """
        str_val = "{} strategy_name='{}'".format(
            self.__class__.__name__, self._strategy_name
        )
        return str_val
