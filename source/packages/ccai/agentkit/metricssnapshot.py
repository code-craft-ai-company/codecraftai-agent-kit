"""
    Defines the MetricsSnapshot class representing an immutable
    point-in-time snapshot of all metric values.

    MetricsSnapshot objects contain a snapshot timestamp and a
    dictionary of metric names to their current aggregated values
    and labels. All fields are exposed as read-only properties to
    preserve immutability after construction.
"""

import json

from datetime import datetime
from typing import Optional


class MetricsSnapshot:
    """
        An immutable object representing a point-in-time snapshot of
        all metric values.

        Contains a snapshot timestamp and a dictionary of metric names
        to their current aggregated values and labels.

        :param timestamp: The timestamp when the snapshot was taken.
        :param metrics: A dictionary mapping metric names to their
            current values and labels.
    """

    def __init__(self, timestamp: datetime, metrics: dict) -> None:

        self._timestamp = timestamp
        self._metrics = dict(metrics)

        return

    @property
    def timestamp(self) -> datetime:
        """
            The timestamp when the snapshot was taken.

            :returns: The datetime timestamp.
        """
        return self._timestamp

    @property
    def metrics(self) -> dict:
        """
            A copy of the metrics dictionary mapping metric names to
            their current values and labels. Returns a copy to preserve
            immutability.

            :returns: A dictionary copy of the metrics data.
        """
        result = dict(self._metrics)
        return result

    def get_metric(self, name: str) -> Optional[dict]:
        """
            Returns the current value and labels for the specified metric
            name, or None when the metric has no recorded values.

            :param name: The metric name to look up.

            :returns: A dictionary containing the metric value and labels,
                or None if the metric is not found.
        """
        result = self._metrics.get(name, None)
        return result

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the snapshot fields.

            The timestamp is serialized as an ISO format string for
            consistent representation.

            :returns: A dictionary containing all snapshot fields.
        """
        result = {
            "timestamp": self._timestamp.isoformat(),
            "metrics": dict(self._metrics)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the snapshot fields.

            :returns: A JSON string containing all snapshot fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "MetricsSnapshot":
        """
            Constructs a MetricsSnapshot from a dictionary.

            The timestamp field is expected to be an ISO format string
            and is parsed back into a datetime object.

            :param data: A dictionary containing snapshot fields.

            :returns: A MetricsSnapshot instance reconstructed from
                the dictionary.
        """
        timestamp = datetime.fromisoformat(data["timestamp"])
        metrics = data.get("metrics", {})

        snapshot = cls(
            timestamp=timestamp,
            metrics=metrics
        )
        return snapshot

    @classmethod
    def from_json(cls, json_str: str) -> "MetricsSnapshot":
        """
            Deserializes a JSON string into a MetricsSnapshot instance.

            :param json_str: A JSON string containing snapshot fields.

            :returns: A MetricsSnapshot instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        snapshot = cls.from_dict(data)
        return snapshot

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            snapshot timestamp, and the count of metrics.

            :returns: A repr string for debugging.
        """
        repr_str = "MetricsSnapshot(timestamp={!r}, metric_count={})".format(
            self._timestamp.isoformat(), len(self._metrics)
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the snapshot
            timestamp and the list of metric names.

            :returns: A human-readable string.
        """
        metric_names = list(self._metrics.keys())
        str_val = "MetricsSnapshot: timestamp={}, metrics={}".format(
            self._timestamp.isoformat(), metric_names
        )
        return str_val
