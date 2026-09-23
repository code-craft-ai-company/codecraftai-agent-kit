"""
    Defines the MetricMeasurement class representing an immutable
    single metric data point.

    MetricMeasurement objects contain a metric name, a float value,
    a timestamp, and a labels dictionary of string key-value pairs.
    The timestamp defaults to the current UTC time when not explicitly
    provided. All fields are exposed as read-only properties to
    preserve immutability after construction.
"""

import json

from datetime import datetime


class MetricMeasurement:
    """
        An immutable object representing a single metric data point.

        Contains the metric name, the value as a float, a timestamp,
        and a labels dictionary of string key-value pairs. The timestamp
        defaults to the current UTC time when not explicitly provided.

        :param metric_name: The name of the metric being measured.
        :param value: The metric value as a float.
        :param timestamp: Optional timestamp for the measurement.
            Defaults to the current UTC time if not provided.
        :param labels: Optional dictionary of string key-value labels
            for dimensional context.
    """

    def __init__(self, metric_name: str, value: float,
                 timestamp: datetime = None, labels: dict = None) -> None:

        self._metric_name = metric_name
        self._value = value

        if timestamp is not None:
            self._timestamp = timestamp
        else:
            self._timestamp = datetime.utcnow()

        if labels is not None:
            self._labels = dict(labels)
        else:
            self._labels = {}

        return

    @property
    def metric_name(self) -> str:
        """
            The name of the metric being measured.

            :returns: The metric name string.
        """
        return self._metric_name

    @property
    def value(self) -> float:
        """
            The metric value as a float.

            :returns: The metric value.
        """
        return self._value

    @property
    def timestamp(self) -> datetime:
        """
            The timestamp when this measurement was recorded.

            :returns: The datetime timestamp.
        """
        return self._timestamp

    @property
    def labels(self) -> dict:
        """
            A copy of the labels dictionary of string key-value pairs.
            Returns a copy to preserve immutability.

            :returns: A dictionary copy of the labels.
        """
        result = dict(self._labels)
        return result

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the measurement fields.

            The timestamp is serialized as an ISO format string for
            consistent representation.

            :returns: A dictionary containing all measurement fields.
        """
        result = {
            "metric_name": self._metric_name,
            "value": self._value,
            "timestamp": self._timestamp.isoformat(),
            "labels": dict(self._labels)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the measurement fields.

            :returns: A JSON string containing all measurement fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "MetricMeasurement":
        """
            Constructs a MetricMeasurement from a dictionary.

            The timestamp field is expected to be an ISO format string
            and is parsed back into a datetime object.

            :param data: A dictionary containing measurement fields.

            :returns: A MetricMeasurement instance reconstructed from
                the dictionary.
        """
        metric_name = data["metric_name"]
        value = data["value"]
        timestamp = datetime.fromisoformat(data["timestamp"])
        labels = data.get("labels", None)

        measurement = cls(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp,
            labels=labels
        )
        return measurement

    @classmethod
    def from_json(cls, json_str: str) -> "MetricMeasurement":
        """
            Deserializes a JSON string into a MetricMeasurement instance.

            :param json_str: A JSON string containing measurement fields.

            :returns: A MetricMeasurement instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        measurement = cls.from_dict(data)
        return measurement

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            metric name, and value.

            :returns: A repr string for debugging.
        """
        repr_str = "MetricMeasurement(metric_name={!r}, value={!r})".format(
            self._metric_name, self._value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the metric name,
            value, and labels.

            :returns: A human-readable string.
        """
        str_val = "MetricMeasurement: metric_name={}, value={}, labels={}".format(
            self._metric_name, self._value, self._labels
        )
        return str_val
