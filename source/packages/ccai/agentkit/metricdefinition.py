"""
    Defines the MetricDefinition class representing an immutable
    description of a metric with a name, description, unit, and type.

    MetricDefinition objects are registered in a MetricsRegistry and
    used by the MetricsCollector to validate metric operations. All
    fields are exposed as read-only properties to preserve immutability
    after construction.
"""

import json

from ccai.agentkit.metrictype import MetricType


class MetricDefinition:
    """
        An immutable object describing a metric with a name, description,
        unit, and type.

        :param name: The metric name string.
        :param description: A human-readable description of the metric.
        :param unit: The unit of measurement string (e.g. "seconds",
            "count", "tokens").
        :param metric_type: The MetricType enum value classifying this
            metric.
    """

    def __init__(self, name: str, description: str, unit: str,
                 metric_type: MetricType) -> None:

        self._name = name
        self._description = description
        self._unit = unit
        self._metric_type = metric_type

        return

    @property
    def name(self) -> str:
        """
            The metric name string.

            :returns: The metric name.
        """
        return self._name

    @property
    def description(self) -> str:
        """
            A human-readable description of the metric.

            :returns: The description string.
        """
        return self._description

    @property
    def unit(self) -> str:
        """
            The unit of measurement string.

            :returns: The unit string.
        """
        return self._unit

    @property
    def metric_type(self) -> MetricType:
        """
            The MetricType enum value classifying this metric.

            :returns: The MetricType value.
        """
        return self._metric_type

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the definition fields.

            The metric_type is serialized as its string value for
            consistent representation.

            :returns: A dictionary containing all definition fields.
        """
        result = {
            "name": self._name,
            "description": self._description,
            "unit": self._unit,
            "metric_type": self._metric_type.value
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the definition fields.

            :returns: A JSON string containing all definition fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "MetricDefinition":
        """
            Constructs a MetricDefinition from a dictionary.

            The metric_type field is expected to be a string value
            and is converted to a MetricType enum member.

            :param data: A dictionary containing definition fields.

            :returns: A MetricDefinition instance reconstructed from
                the dictionary.
        """
        name = data["name"]
        description = data["description"]
        unit = data["unit"]
        metric_type = MetricType.from_string(data["metric_type"])

        definition = cls(
            name=name,
            description=description,
            unit=unit,
            metric_type=metric_type
        )
        return definition

    @classmethod
    def from_json(cls, json_str: str) -> "MetricDefinition":
        """
            Deserializes a JSON string into a MetricDefinition instance.

            :param json_str: A JSON string containing definition fields.

            :returns: A MetricDefinition instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        definition = cls.from_dict(data)
        return definition

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            metric name, and metric type.

            :returns: A repr string for debugging.
        """
        repr_str = "MetricDefinition(name={!r}, metric_type={!r})".format(
            self._name, self._metric_type.value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the metric name,
            type, and unit.

            :returns: A human-readable string.
        """
        str_val = "MetricDefinition: name={}, type={}, unit={}".format(
            self._name, self._metric_type.value, self._unit
        )
        return str_val
