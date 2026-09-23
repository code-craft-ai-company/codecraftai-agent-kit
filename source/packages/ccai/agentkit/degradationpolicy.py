"""
    Defines the DegradationPolicy class for configuring degradation behavior
    per dependency in the Error Handling & Resilience feature.
"""

import json

from ccai.agentkit.degradationlevel import DegradationLevel
from ccai.agentkit.degradationstrategy import DegradationStrategy


class DegradationPolicy:
    """
        Immutable configuration object defining the degradation behavior
        for a specific dependency.

        :param dependency_name: The name of the dependency.
        :param strategy: The DegradationStrategy to apply.
        :param activation_level: The DegradationLevel at which the strategy activates.
        :param fallback_value: An optional fallback value.
    """

    def __init__(self, dependency_name: str, strategy: DegradationStrategy,
                 activation_level: DegradationLevel,
                 fallback_value=None) -> None:
        self._dependency_name = dependency_name
        self._strategy = strategy
        self._activation_level = activation_level
        self._fallback_value = fallback_value
        return

    @property
    def dependency_name(self) -> str:
        """
            The name of the dependency.

            :returns: The dependency name string.
        """
        return self._dependency_name

    @property
    def strategy(self) -> DegradationStrategy:
        """
            The DegradationStrategy to apply.

            :returns: The strategy instance.
        """
        return self._strategy

    @property
    def activation_level(self) -> DegradationLevel:
        """
            The DegradationLevel at which the strategy activates.

            :returns: The activation level.
        """
        return self._activation_level

    @property
    def fallback_value(self):
        """
            The optional fallback value.

            :returns: The fallback value or None.
        """
        return self._fallback_value

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the policy fields.

            :returns: A dictionary of policy fields.
        """
        result = {
            "dependency_name": self._dependency_name,
            "strategy_name": self._strategy.strategy_name,
            "activation_level": self._activation_level.value,
            "fallback_value": self._fallback_value
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the policy fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict, strategy: DegradationStrategy) -> "DegradationPolicy":
        """
            Constructs a DegradationPolicy from a dictionary.

            :param data: Dictionary containing policy fields.
            :param strategy: The DegradationStrategy instance to use.

            :returns: A DegradationPolicy instance.
        """
        policy = cls(
            dependency_name=data["dependency_name"],
            strategy=strategy,
            activation_level=DegradationLevel.from_string(data["activation_level"]),
            fallback_value=data.get("fallback_value")
        )
        return policy

    def __repr__(self) -> str:
        """
            Returns a detailed string representation.

            :returns: A repr string for debugging.
        """
        repr_str = "DegradationPolicy(dependency_name={!r}, strategy={!r}, level={})".format(
            self._dependency_name, self._strategy.strategy_name, self._activation_level.value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary.

            :returns: A human-readable string.
        """
        str_val = "DegradationPolicy dependency='{}', strategy='{}', activation_level={}".format(
            self._dependency_name, self._strategy.strategy_name, self._activation_level.value
        )
        return str_val
