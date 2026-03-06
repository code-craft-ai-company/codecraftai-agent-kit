"""
    Unit tests for the automojo.agentkit.metricscollector module.

    Tests the MetricsCollector class covering increment_counter,
    set_gauge, record_histogram, type mismatch errors, unregistered
    name errors, snapshot, reset, exporter delivery, and string
    representations.

    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8,
                  13.9, 13.10, 13.11, 13.12, 13.13
"""

from automojo.agentkit.metricscollector import MetricsCollector
from automojo.agentkit.metricsregistry import MetricsRegistry
from automojo.agentkit.metricdefinition import MetricDefinition
from automojo.agentkit.metrictype import MetricType
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.metricsexporter import MetricsExporter


# ---- Helper Classes ----


class RecordingExporter(MetricsExporter):
    """
        A MetricsExporter that records all exported measurements
        in a list for test verification.
    """

    def __init__(self) -> None:
        super().__init__()
        self.exported_measurements = []
        return

    def export(self, measurements: list) -> None:
        self.exported_measurements.extend(measurements)
        return

    def flush(self) -> None:
        return

    def shutdown(self) -> None:
        return


# ---- Helper Functions ----


def _create_registry_with_all_types():
    """
        Creates a MetricsRegistry with one COUNTER, one GAUGE, and
        one HISTOGRAM metric registered.

        :returns: A MetricsRegistry instance.
    """
    registry = MetricsRegistry()
    registry.register(MetricDefinition(
        name="test.counter", description="A counter", unit="count",
        metric_type=MetricType.COUNTER
    ))
    registry.register(MetricDefinition(
        name="test.gauge", description="A gauge", unit="count",
        metric_type=MetricType.GAUGE
    ))
    registry.register(MetricDefinition(
        name="test.histogram", description="A histogram", unit="seconds",
        metric_type=MetricType.HISTOGRAM
    ))
    return registry


# ---- Construction ----


def test_collector_accepts_registry():
    """
        Verify that MetricsCollector accepts a MetricsRegistry at
        construction.
    """
    registry = MetricsRegistry()
    collector = MetricsCollector(registry=registry)

    assert collector is not None, "Collector should be created"
    return


# ---- increment_counter ----


def test_increment_counter_accumulates_value():
    """
        Verify that increment_counter accumulates the counter value.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    collector.increment_counter("test.counter", value=5.0)
    collector.increment_counter("test.counter", value=3.0)

    snap = collector.snapshot()
    metric = snap.get_metric("test.counter")

    assert metric is not None, "Counter should appear in snapshot"
    assert metric["value"] == 8.0, "Counter should accumulate to 8.0"
    return


def test_increment_counter_default_value():
    """
        Verify that increment_counter defaults to 1.0.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    collector.increment_counter("test.counter")

    snap = collector.snapshot()
    metric = snap.get_metric("test.counter")

    assert metric["value"] == 1.0, "Counter should default to 1.0"
    return


def test_increment_counter_unregistered_raises_semantic_error():
    """
        Verify that increment_counter raises SemanticError for an
        unregistered metric name.
    """
    registry = MetricsRegistry()
    collector = MetricsCollector(registry=registry)

    raised = False
    try:
        collector.increment_counter("nonexistent.counter")
    except SemanticError:
        raised = True

    assert raised is True, "Unregistered metric should raise SemanticError"
    return


def test_increment_counter_wrong_type_raises_semantic_error():
    """
        Verify that increment_counter raises SemanticError when the
        metric is not a COUNTER type.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    raised = False
    try:
        collector.increment_counter("test.gauge")
    except SemanticError:
        raised = True

    assert raised is True, "Wrong type should raise SemanticError"
    return


# ---- set_gauge ----


def test_set_gauge_sets_value():
    """
        Verify that set_gauge sets the gauge value.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    collector.set_gauge("test.gauge", value=42.0)

    snap = collector.snapshot()
    metric = snap.get_metric("test.gauge")

    assert metric is not None, "Gauge should appear in snapshot"
    assert metric["value"] == 42.0, "Gauge should be set to 42.0"
    return


def test_set_gauge_overwrites_previous_value():
    """
        Verify that set_gauge overwrites the previous gauge value.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    collector.set_gauge("test.gauge", value=10.0)
    collector.set_gauge("test.gauge", value=20.0)

    snap = collector.snapshot()
    metric = snap.get_metric("test.gauge")

    assert metric["value"] == 20.0, "Gauge should be overwritten to 20.0"
    return


def test_set_gauge_wrong_type_raises_semantic_error():
    """
        Verify that set_gauge raises SemanticError when the metric
        is not a GAUGE type.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    raised = False
    try:
        collector.set_gauge("test.counter", value=5.0)
    except SemanticError:
        raised = True

    assert raised is True, "Wrong type should raise SemanticError"
    return


def test_set_gauge_unregistered_raises_semantic_error():
    """
        Verify that set_gauge raises SemanticError for an unregistered
        metric name.
    """
    registry = MetricsRegistry()
    collector = MetricsCollector(registry=registry)

    raised = False
    try:
        collector.set_gauge("nonexistent.gauge", value=1.0)
    except SemanticError:
        raised = True

    assert raised is True, "Unregistered metric should raise SemanticError"
    return


# ---- record_histogram ----


def test_record_histogram_appends_values():
    """
        Verify that record_histogram appends values to the histogram.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    collector.record_histogram("test.histogram", value=1.5)
    collector.record_histogram("test.histogram", value=2.5)

    snap = collector.snapshot()
    metric = snap.get_metric("test.histogram")

    assert metric is not None, "Histogram should appear in snapshot"
    assert metric["values"] == [1.5, 2.5], "Histogram should contain both values"
    return


def test_record_histogram_wrong_type_raises_semantic_error():
    """
        Verify that record_histogram raises SemanticError when the
        metric is not a HISTOGRAM type.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    raised = False
    try:
        collector.record_histogram("test.counter", value=1.0)
    except SemanticError:
        raised = True

    assert raised is True, "Wrong type should raise SemanticError"
    return


def test_record_histogram_unregistered_raises_semantic_error():
    """
        Verify that record_histogram raises SemanticError for an
        unregistered metric name.
    """
    registry = MetricsRegistry()
    collector = MetricsCollector(registry=registry)

    raised = False
    try:
        collector.record_histogram("nonexistent.histogram", value=1.0)
    except SemanticError:
        raised = True

    assert raised is True, "Unregistered metric should raise SemanticError"
    return


# ---- snapshot ----


def test_snapshot_returns_metrics_snapshot():
    """
        Verify that snapshot returns a MetricsSnapshot with current values.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    collector.increment_counter("test.counter", value=3.0)
    collector.set_gauge("test.gauge", value=7.0)
    collector.record_histogram("test.histogram", value=0.5)

    snap = collector.snapshot()

    assert snap.get_metric("test.counter")["value"] == 3.0
    assert snap.get_metric("test.gauge")["value"] == 7.0
    assert snap.get_metric("test.histogram")["values"] == [0.5]
    return


def test_snapshot_empty_collector():
    """
        Verify that snapshot on an empty collector returns empty metrics.
    """
    registry = MetricsRegistry()
    collector = MetricsCollector(registry=registry)

    snap = collector.snapshot()

    assert snap.metrics == {}, "Empty collector should produce empty metrics"
    return


# ---- reset ----


def test_reset_clears_all_values():
    """
        Verify that reset clears all accumulated metric values.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)

    collector.increment_counter("test.counter", value=5.0)
    collector.set_gauge("test.gauge", value=10.0)
    collector.record_histogram("test.histogram", value=1.0)

    collector.reset()

    snap = collector.snapshot()
    assert snap.metrics == {}, "Reset should clear all metrics"
    return


# ---- exporter delivery ----


def test_exporter_receives_counter_measurement():
    """
        Verify that registered exporters receive measurements from
        increment_counter.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)
    exporter = RecordingExporter()
    collector.register_exporter(exporter)

    collector.increment_counter("test.counter", value=2.0)

    assert len(exporter.exported_measurements) == 1
    assert exporter.exported_measurements[0].metric_name == "test.counter"
    assert exporter.exported_measurements[0].value == 2.0
    return


def test_exporter_receives_gauge_measurement():
    """
        Verify that registered exporters receive measurements from
        set_gauge.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)
    exporter = RecordingExporter()
    collector.register_exporter(exporter)

    collector.set_gauge("test.gauge", value=15.0)

    assert len(exporter.exported_measurements) == 1
    assert exporter.exported_measurements[0].metric_name == "test.gauge"
    assert exporter.exported_measurements[0].value == 15.0
    return


def test_exporter_receives_histogram_measurement():
    """
        Verify that registered exporters receive measurements from
        record_histogram.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)
    exporter = RecordingExporter()
    collector.register_exporter(exporter)

    collector.record_histogram("test.histogram", value=0.75)

    assert len(exporter.exported_measurements) == 1
    assert exporter.exported_measurements[0].metric_name == "test.histogram"
    assert exporter.exported_measurements[0].value == 0.75
    return


def test_multiple_exporters_receive_measurements():
    """
        Verify that multiple registered exporters all receive
        measurements.
    """
    registry = _create_registry_with_all_types()
    collector = MetricsCollector(registry=registry)
    exporter1 = RecordingExporter()
    exporter2 = RecordingExporter()
    collector.register_exporter(exporter1)
    collector.register_exporter(exporter2)

    collector.increment_counter("test.counter", value=1.0)

    assert len(exporter1.exported_measurements) == 1
    assert len(exporter2.exported_measurements) == 1
    return


# ---- __repr__ and __str__ ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name.
    """
    registry = MetricsRegistry()
    collector = MetricsCollector(registry=registry)
    repr_str = repr(collector)

    assert "MetricsCollector" in repr_str, "repr should contain 'MetricsCollector'"
    return


def test_str_contains_class_name():
    """
        Verify that __str__ includes the class name.
    """
    registry = MetricsRegistry()
    collector = MetricsCollector(registry=registry)
    str_val = str(collector)

    assert "MetricsCollector" in str_val, "str should contain 'MetricsCollector'"
    return
