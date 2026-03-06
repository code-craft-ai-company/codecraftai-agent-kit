"""
    Defines the ConfigurationLayer class representing an immutable layer
    in the configuration hierarchy of the automojo-agent-kit framework.

    A ConfigurationLayer contains a layer name, priority, source, and
    configuration dictionary. Layers are merged in ascending priority
    order by the ConfigurationManager, with higher-priority layers
    overriding lower-priority values.
"""

import json

from automojo.agentkit.configurationlayersource import ConfigurationLayerSource


class ConfigurationLayer:
    """
        Immutable object representing a single layer in the configuration hierarchy.

        Contains a layer name, priority, source, and configuration dictionary.
        Layers are merged in ascending priority order by the ConfigurationManager.

        :param name: The name identifying this configuration layer.
        :param priority: The priority integer for merge ordering.
        :param source: The ConfigurationLayerSource indicating the origin of this layer.
        :param configuration: The configuration dictionary for this layer.
    """

    def __init__(self, name: str, priority: int, source: ConfigurationLayerSource,
                 configuration: dict) -> None:
        self._name = name
        self._priority = priority
        self._source = source

        if configuration is not None:
            self._configuration = dict(configuration)
        else:
            self._configuration = {}

        return

    @property
    def name(self) -> str:
        """
            The name identifying this configuration layer.

            :returns: The layer name string.
        """
        return self._name

    @property
    def priority(self) -> int:
        """
            The priority integer for merge ordering.

            :returns: The priority value.
        """
        return self._priority

    @property
    def source(self) -> ConfigurationLayerSource:
        """
            The ConfigurationLayerSource indicating the origin of this layer.

            :returns: The ConfigurationLayerSource value.
        """
        return self._source

    @property
    def configuration(self) -> dict:
        """
            A defensive copy of the configuration dictionary for this layer.

            :returns: A dictionary copy of the configuration.
        """
        return dict(self._configuration)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the layer fields
            including the configuration dictionary.

            :returns: A dictionary with name, priority, source, and configuration.
        """
        result = {
            "name": self._name,
            "priority": self._priority,
            "source": self._source.value,
            "configuration": dict(self._configuration)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the layer fields.

            :returns: A JSON string containing name, priority, source, and configuration.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "ConfigurationLayer":
        """
            Constructs a ConfigurationLayer from a dictionary.

            :param data: A dictionary containing name, priority, source, and configuration.

            :returns: A ConfigurationLayer instance reconstructed from the dictionary.
        """
        name = data["name"]
        priority = data["priority"]
        source = ConfigurationLayerSource.from_string(data["source"])
        configuration = data.get("configuration", {})

        layer = cls(
            name=name,
            priority=priority,
            source=source,
            configuration=configuration
        )
        return layer

    @classmethod
    def from_json(cls, json_str: str) -> "ConfigurationLayer":
        """
            Deserializes a JSON string into a ConfigurationLayer instance.

            :param json_str: A JSON string containing layer fields.

            :returns: A ConfigurationLayer instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        layer = cls.from_dict(data)
        return layer

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            layer name, priority, and source.

            :returns: A repr string for debugging.
        """
        repr_str = "ConfigurationLayer(name={!r}, priority={}, source={!r})".format(
            self._name, self._priority, self._source
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the layer name,
            priority, and source.

            :returns: A human-readable string.
        """
        str_val = "ConfigurationLayer '{}' (priority={}, source={})".format(
            self._name, self._priority, self._source
        )
        return str_val
