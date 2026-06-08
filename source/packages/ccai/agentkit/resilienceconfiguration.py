"""
    Defines the ResilienceConfiguration class for declarative resilience
    settings in the Error Handling & Resilience feature.
"""

import json

import yaml

from ccai.agentkit.errors import ConfigurationError
from ccai.agentkit.retrypolicy import RetryPolicy


class ResilienceConfiguration:
    """
        Configuration object defining the resilience settings for an Agent.
        Supports loading from dictionaries, JSON, and YAML.

        :param default_retry_policy: Optional default RetryPolicy.
        :param circuit_breaker_enabled: Whether circuit breakers are enabled.
        :param degradation_enabled: Whether degradation is enabled.
        :param dead_letter_enabled: Whether dead letter queue is enabled.
        :param health_monitoring_enabled: Whether health monitoring is enabled.
        :param health_check_interval: Interval between health checks in seconds.
        :param self_healing_enabled: Whether self-healing is enabled.
    """

    def __init__(self, default_retry_policy=None,
                 circuit_breaker_enabled: bool = True,
                 degradation_enabled: bool = True,
                 dead_letter_enabled: bool = True,
                 health_monitoring_enabled: bool = True,
                 health_check_interval: float = 30.0,
                 self_healing_enabled: bool = True) -> None:
        self._default_retry_policy = default_retry_policy
        self._circuit_breaker_enabled = circuit_breaker_enabled
        self._degradation_enabled = degradation_enabled
        self._dead_letter_enabled = dead_letter_enabled
        self._health_monitoring_enabled = health_monitoring_enabled
        self._health_check_interval = health_check_interval
        self._self_healing_enabled = self_healing_enabled
        return

    @property
    def default_retry_policy(self):
        return self._default_retry_policy

    @property
    def circuit_breaker_enabled(self) -> bool:
        return self._circuit_breaker_enabled

    @property
    def degradation_enabled(self) -> bool:
        return self._degradation_enabled

    @property
    def dead_letter_enabled(self) -> bool:
        return self._dead_letter_enabled

    @property
    def health_monitoring_enabled(self) -> bool:
        return self._health_monitoring_enabled

    @property
    def health_check_interval(self) -> float:
        return self._health_check_interval

    @property
    def self_healing_enabled(self) -> bool:
        return self._self_healing_enabled

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration.

            :returns: A dictionary of configuration fields.
        """
        result = {
            "default_retry_policy": self._default_retry_policy.as_dict() if self._default_retry_policy is not None else None,
            "circuit_breaker_enabled": self._circuit_breaker_enabled,
            "degradation_enabled": self._degradation_enabled,
            "dead_letter_enabled": self._dead_letter_enabled,
            "health_monitoring_enabled": self._health_monitoring_enabled,
            "health_check_interval": self._health_check_interval,
            "self_healing_enabled": self._self_healing_enabled
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the configuration.

            :returns: A JSON string.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    def to_yaml(self) -> str:
        """
            Returns a YAML string representation of the configuration.

            :returns: A YAML string.
        """
        data = self.as_dict()
        yaml_str = yaml.dump(data, default_flow_style=False)
        return yaml_str

    @classmethod
    def from_dict(cls, data: dict) -> "ResilienceConfiguration":
        """
            Constructs a ResilienceConfiguration from a dictionary.

            :param data: Dictionary containing configuration fields.

            :returns: A ResilienceConfiguration instance.
            :raises ConfigurationError: If required fields are missing.
        """
        retry_policy = None
        retry_data = data.get("default_retry_policy")
        if retry_data is not None:
            try:
                retry_policy = RetryPolicy.from_dict(retry_data)
            except Exception as exc:
                raise ConfigurationError(
                    "Invalid default_retry_policy: {}".format(str(exc))
                )

        config = cls(
            default_retry_policy=retry_policy,
            circuit_breaker_enabled=data.get("circuit_breaker_enabled", True),
            degradation_enabled=data.get("degradation_enabled", True),
            dead_letter_enabled=data.get("dead_letter_enabled", True),
            health_monitoring_enabled=data.get("health_monitoring_enabled", True),
            health_check_interval=data.get("health_check_interval", 30.0),
            self_healing_enabled=data.get("self_healing_enabled", True)
        )
        return config

    @classmethod
    def from_json(cls, json_str: str) -> "ResilienceConfiguration":
        """
            Deserializes a JSON string into a ResilienceConfiguration.

            :param json_str: JSON string to deserialize.

            :returns: A ResilienceConfiguration instance.
            :raises ConfigurationError: If JSON is invalid.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ConfigurationError("Invalid JSON: {}".format(str(exc)))

        config = cls.from_dict(data)
        return config

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ResilienceConfiguration":
        """
            Deserializes a YAML string into a ResilienceConfiguration.

            :param yaml_str: YAML string to deserialize.

            :returns: A ResilienceConfiguration instance.
            :raises ConfigurationError: If YAML is invalid.
        """
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as exc:
            raise ConfigurationError("Invalid YAML: {}".format(str(exc)))

        if not isinstance(data, dict):
            raise ConfigurationError("YAML content must be a mapping")

        config = cls.from_dict(data)
        return config

    def __repr__(self) -> str:
        return "ResilienceConfiguration(cb={}, deg={}, dl={}, hm={}, sh={})".format(
            self._circuit_breaker_enabled, self._degradation_enabled,
            self._dead_letter_enabled, self._health_monitoring_enabled,
            self._self_healing_enabled
        )

    def __str__(self) -> str:
        return "ResilienceConfiguration cb={}, degradation={}, dead_letter={}, health={}, self_healing={}, interval={}s".format(
            self._circuit_breaker_enabled, self._degradation_enabled,
            self._dead_letter_enabled, self._health_monitoring_enabled,
            self._self_healing_enabled, self._health_check_interval
        )
