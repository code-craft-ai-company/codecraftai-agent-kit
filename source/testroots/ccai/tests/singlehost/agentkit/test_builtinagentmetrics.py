"""
    Unit tests for the ccai.agentkit.builtinagentmetrics module.

    Tests the register_builtin_agent_metrics function verifying that
    all 13 standard agent metrics are registered with correct names,
    types, and units.

    Requirements: 17.1
"""

from ccai.agentkit.builtinagentmetrics import register_builtin_agent_metrics
from ccai.agentkit.metricsregistry import MetricsRegistry
from ccai.agentkit.metrictype import MetricType


# ---- Expected metrics specification ----

EXPECTED_METRICS = [
    ("agent.lifecycle.transitions", MetricType.COUNTER, "count"),
    ("agent.tool.execution.duration", MetricType.HISTOGRAM, "seconds"),
    ("agent.tool.execution.errors", MetricType.COUNTER, "count"),
    ("agent.llm.request.duration", MetricType.HISTOGRAM, "seconds"),
    ("agent.llm.token.usage.prompt", MetricType.COUNTER, "tokens"),
    ("agent.llm.token.usage.completion", MetricType.COUNTER, "tokens"),
    ("agent.llm.request.errors", MetricType.COUNTER, "count"),
    ("agent.memory.operations", MetricType.COUNTER, "count"),
    ("agent.message.sent", MetricType.COUNTER, "count"),
    ("agent.message.received", MetricType.COUNTER, "count"),
    ("agent.workflow.step.duration", MetricType.HISTOGRAM, "seconds"),
    ("agent.workflow.step.errors", MetricType.COUNTER, "count"),
    ("agent.active.spans", MetricType.GAUGE, "count"),
]


# ---- Tests ----


def test_registers_all_13_metrics():
    """
        Verify that register_builtin_agent_metrics registers exactly
        13 metrics.
    """
    registry = MetricsRegistry()

    register_builtin_agent_metrics(registry)

    assert registry.count == 13, (
        "Expected 13 built-in metrics, got {}".format(registry.count)
    )
    return


def test_all_metric_names_registered():
    """
        Verify that all expected metric names are registered.
    """
    registry = MetricsRegistry()
    register_builtin_agent_metrics(registry)

    for name, _, _ in EXPECTED_METRICS:
        assert registry.has_metric(name) is True, (
            "Expected metric {!r} to be registered".format(name)
        )
    return


def test_all_metric_types_correct():
    """
        Verify that all registered metrics have the correct MetricType.
    """
    registry = MetricsRegistry()
    register_builtin_agent_metrics(registry)

    for name, expected_type, _ in EXPECTED_METRICS:
        defn = registry.lookup(name)
        assert defn is not None, "Metric {!r} should be registered".format(name)
        assert defn.metric_type == expected_type, (
            "Metric {!r} should have type {}, got {}".format(
                name, expected_type.value, defn.metric_type.value
            )
        )
    return


def test_all_metric_units_correct():
    """
        Verify that all registered metrics have the correct unit.
    """
    registry = MetricsRegistry()
    register_builtin_agent_metrics(registry)

    for name, _, expected_unit in EXPECTED_METRICS:
        defn = registry.lookup(name)
        assert defn is not None, "Metric {!r} should be registered".format(name)
        assert defn.unit == expected_unit, (
            "Metric {!r} should have unit {!r}, got {!r}".format(
                name, expected_unit, defn.unit
            )
        )
    return


def test_lifecycle_transitions_is_counter():
    """
        Verify agent.lifecycle.transitions is a COUNTER with unit count.
    """
    registry = MetricsRegistry()
    register_builtin_agent_metrics(registry)

    defn = registry.lookup("agent.lifecycle.transitions")
    assert defn is not None
    assert defn.metric_type == MetricType.COUNTER
    assert defn.unit == "count"
    return


def test_tool_execution_duration_is_histogram():
    """
        Verify agent.tool.execution.duration is a HISTOGRAM with unit seconds.
    """
    registry = MetricsRegistry()
    register_builtin_agent_metrics(registry)

    defn = registry.lookup("agent.tool.execution.duration")
    assert defn is not None
    assert defn.metric_type == MetricType.HISTOGRAM
    assert defn.unit == "seconds"
    return


def test_active_spans_is_gauge():
    """
        Verify agent.active.spans is a GAUGE with unit count.
    """
    registry = MetricsRegistry()
    register_builtin_agent_metrics(registry)

    defn = registry.lookup("agent.active.spans")
    assert defn is not None
    assert defn.metric_type == MetricType.GAUGE
    assert defn.unit == "count"
    return


def test_all_metrics_have_descriptions():
    """
        Verify that all registered metrics have non-empty descriptions.
    """
    registry = MetricsRegistry()
    register_builtin_agent_metrics(registry)

    for defn in registry.list_all():
        assert len(defn.description) > 0, (
            "Metric {!r} should have a non-empty description".format(defn.name)
        )
    return
