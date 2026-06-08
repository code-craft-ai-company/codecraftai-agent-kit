"""
    Defines the MetricsCollector class that records MetricMeasurement
    objects for defined metrics.

    The MetricsCollector validates metric names against a MetricsRegistry,
    enforces metric type constraints, accumulates counter, gauge, and
    histogram values, delivers measurements to registered exporters,
    and provides snapshot and reset capabilities.
"""

from datetime import datetime
from typing import Optional

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.metricmeasurement import MetricMeasurement
from ccai.agentkit.metricsregistry import MetricsRegistry
from ccai.agentkit.metricssnapshot import MetricsSnapshot
from ccai.agentkit.metrictype import MetricType


class MetricsCollector:
    """
        A component that records MetricMeasurement objects for defined
        metrics.

        The collector validates each recording operation against the
        MetricsRegistry to ensure the metric exists and the operation
        matches the metric type. Counter values are accumulated, gauge
        values are set, and histogram values are appended to a list.

        :param registry: The MetricsRegistry instance used for
            validating metric names and types.
    """

    def __init__(self, registry: MetricsRegistry) -> None:

        self._registry = registry
        self._counter_values = {}
        self._gauge_values = {}
        self._histogram_values = {}
        self._exporters = []

        return

    def _validate_metric(self, metric_name: str, expected_type: MetricType) -> None:
        """
            Validates that the metric name is registered and matches
            the expected MetricType.

            :param metric_name: The metric name string to validate.
            :param expected_type: The expected MetricType enum value.

            :raises SemanticError: If the metric is not registered or
                the type does not match.
        """
        definition = self._registry.lookup(metric_name)

        if definition is None:
            raise SemanticError(
                "Metric {!r} is not registered in the MetricsRegistry".format(
                    metric_name
                )
            )

        if definition.metric_type != expected_type:
            raise SemanticError(
                "Metric {!r} has type {}, expected {}".format(
                    metric_name,
                    definition.metric_type.value,
                    expected_type.value
                )
            )

        return

    def _deliver_to_exporters(self, measurement: MetricMeasurement) -> None:
        """
            Delivers a MetricMeasurement to all registered exporters.

            :param measurement: The MetricMeasurement to deliver.
        """
        for exporter in self._exporters:
            exporter.export([measurement])

        return

    def increment_counter(self, metric_name: str, value: float = 1.0,
                          labels: dict = None) -> None:
        """
            Records a counter increment for the specified metric.

            Validates that the metric is registered and has type COUNTER.
            Adds the value to the accumulated counter total and delivers
            a MetricMeasurement to all registered exporters.

            :param metric_name: The name of the counter metric.
            :param value: The increment value as a float, defaulting to 1.0.
            :param labels: Optional dictionary of string key-value labels.

            :raises SemanticError: If the metric is not registered or
                is not a COUNTER type.
        """
        self._validate_metric(metric_name, MetricType.COUNTER)

        if metric_name not in self._counter_values:
            self._counter_values[metric_name] = 0.0

        self._counter_values[metric_name] += value

        measurement = MetricMeasurement(
            metric_name=metric_name,
            value=value,
            labels=labels
        )
        self._deliver_to_exporters(measurement)

        return

    def set_gauge(self, metric_name: str, value: float,
                  labels: dict = None) -> None:
        """
            Records a gauge value for the specified metric.

            Validates that the metric is registered and has type GAUGE.
            Sets the gauge value and delivers a MetricMeasurement to
            all registered exporters.

            :param metric_name: The name of the gauge metric.
            :param value: The gauge value as a float.
            :param labels: Optional dictionary of string key-value labels.

            :raises SemanticError: If the metric is not registered or
                is not a GAUGE type.
        """
        self._validate_metric(metric_name, MetricType.GAUGE)

        self._gauge_values[metric_name] = value

        measurement = MetricMeasurement(
            metric_name=metric_name,
            value=value,
            labels=labels
        )
        self._deliver_to_exporters(measurement)

        return

    def record_histogram(self, metric_name: str, value: float,
                         labels: dict = None) -> None:
        """
            Records a histogram observation for the specified metric.

            Validates that the metric is registered and has type HISTOGRAM.
            Appends the value to the histogram observations list and
            delivers a MetricMeasurement to all registered exporters.

            :param metric_name: The name of the histogram metric.
            :param value: The observation value as a float.
            :param labels: Optional dictionary of string key-value labels.

            :raises SemanticError: If the metric is not registered or
                is not a HISTOGRAM type.
        """
        self._validate_metric(metric_name, MetricType.HISTOGRAM)

        if metric_name not in self._histogram_values:
            self._histogram_values[metric_name] = []

        self._histogram_values[metric_name].append(value)

        measurement = MetricMeasurement(
            metric_name=metric_name,
            value=value,
            labels=labels
        )
        self._deliver_to_exporters(measurement)

        return

    def snapshot(self) -> MetricsSnapshot:
        """
            Returns a MetricsSnapshot containing the current values
            of all recorded metrics.

            Counter metrics are represented by their accumulated total.
            Gauge metrics are represented by their current value.
            Histogram metrics are represented by their list of observations.

            :returns: A MetricsSnapshot instance with current metric values.
        """
        metrics = {}

        for name, value in self._counter_values.items():
            metrics[name] = {"value": value, "type": "COUNTER"}

        for name, value in self._gauge_values.items():
            metrics[name] = {"value": value, "type": "GAUGE"}

        for name, values in self._histogram_values.items():
            metrics[name] = {"values": list(values), "type": "HISTOGRAM"}

        snapshot = MetricsSnapshot(
            timestamp=datetime.utcnow(),
            metrics=metrics
        )
        return snapshot

    def reset(self) -> None:
        """
            Clears all accumulated metric values.

            Resets counter, gauge, and histogram value dictionaries
            to empty.
        """
        self._counter_values = {}
        self._gauge_values = {}
        self._histogram_values = {}

        return

    def register_exporter(self, exporter) -> None:
        """
            Registers a MetricsExporter instance to receive metric
            measurements.

            :param exporter: The MetricsExporter instance to register.
        """
        self._exporters.append(exporter)

        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of registered metrics.

            :returns: A repr string for debugging.
        """
        repr_str = "MetricsCollector(registry_count={})".format(
            self._registry.count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count of
            registered metrics and the count of recorded measurements.

            :returns: A human-readable string.
        """
        total_measurements = (
            len(self._counter_values) +
            len(self._gauge_values) +
            len(self._histogram_values)
        )
        str_val = (
            "MetricsCollector: registry_count={}, recorded_metrics={}"
        ).format(self._registry.count, total_measurements)
        return str_val
