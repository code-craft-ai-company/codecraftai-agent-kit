"""
    Property-based tests for the automojo.agentkit.metricscollector module.

    Uses automojo.testbase.properties to verify:
    - Property 21: MetricsCollector counter accumulation
    - Property 22: MetricsCollector type enforcement

    **Validates: Requirements 13.2, 13.4, 13.6, 13.8, 13.10**
"""

from typing import List

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.metricdefinition import MetricDefinition
from automojo.agentkit.metricscollector import MetricsCollector
from automojo.agentkit.metricsregistry import MetricsRegistry
from automojo.agentkit.metrictype import MetricType


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_positive_float_strategy = st.floats(
    min_value=0.01,
    max_value=1000.0,
)

_increment_values_strategy = st.lists(
    _positive_float_strategy,
    min_size=1,
    max_size=50,
)


# ---------------------------------------------------------------------------
# Property 21: MetricsCollector counter accumulation
# ---------------------------------------------------------------------------

@given(
    values=_increment_values_strategy,
    settings=settings(max_examples=50),
)
def test_counter_accumulation(
    values: List[float],
) -> None:
    """
        **Validates: Requirements 13.2, 13.10**

        For any registered COUNTER metric and any sequence of N
        increment_counter() calls with values v1..vN, the snapshot
        value equals sum v1+...+vN.
    """
    registry = MetricsRegistry()
    registry.register(MetricDefinition(
        name="test.counter",
        description="Test counter",
        unit="count",
        metric_type=MetricType.COUNTER
    ))
    collector = MetricsCollector(registry=registry)

    expected_sum = 0.0
    for value in values:
        collector.increment_counter("test.counter", value=value)
        expected_sum += value

    snap = collector.snapshot()
    metric = snap.get_metric("test.counter")

    assert metric is not None, "Counter should appear in snapshot"

    actual_value = metric["value"]

    # Use a relative tolerance for floating point comparison
    assert abs(actual_value - expected_sum) < 1e-6, (
        "Counter snapshot value {} should equal sum of increments {}, "
        "difference is {}".format(
            actual_value, expected_sum, abs(actual_value - expected_sum)
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 22: MetricsCollector type enforcement
# ---------------------------------------------------------------------------

@given(
    metric_type=st.sampled_from([MetricType.COUNTER, MetricType.GAUGE, MetricType.HISTOGRAM]),
    settings=settings(max_examples=50),
)
def test_type_enforcement(
    metric_type: MetricType,
) -> None:
    """
        **Validates: Requirements 13.4, 13.6, 13.8**

        For any registered metric, calling the wrong recording method
        raises SemanticError. Specifically:
        - A COUNTER metric rejects set_gauge and record_histogram
        - A GAUGE metric rejects increment_counter and record_histogram
        - A HISTOGRAM metric rejects increment_counter and set_gauge
    """
    registry = MetricsRegistry()
    registry.register(MetricDefinition(
        name="test.metric",
        description="Test metric",
        unit="count",
        metric_type=metric_type
    ))
    collector = MetricsCollector(registry=registry)

    if metric_type == MetricType.COUNTER:
        # set_gauge should raise
        raised_gauge = False
        try:
            collector.set_gauge("test.metric", value=1.0)
        except SemanticError:
            raised_gauge = True
        assert raised_gauge is True, (
            "set_gauge on COUNTER metric should raise SemanticError"
        )

        # record_histogram should raise
        raised_hist = False
        try:
            collector.record_histogram("test.metric", value=1.0)
        except SemanticError:
            raised_hist = True
        assert raised_hist is True, (
            "record_histogram on COUNTER metric should raise SemanticError"
        )

        # increment_counter should succeed
        collector.increment_counter("test.metric", value=1.0)

    elif metric_type == MetricType.GAUGE:
        # increment_counter should raise
        raised_counter = False
        try:
            collector.increment_counter("test.metric", value=1.0)
        except SemanticError:
            raised_counter = True
        assert raised_counter is True, (
            "increment_counter on GAUGE metric should raise SemanticError"
        )

        # record_histogram should raise
        raised_hist = False
        try:
            collector.record_histogram("test.metric", value=1.0)
        except SemanticError:
            raised_hist = True
        assert raised_hist is True, (
            "record_histogram on GAUGE metric should raise SemanticError"
        )

        # set_gauge should succeed
        collector.set_gauge("test.metric", value=1.0)

    elif metric_type == MetricType.HISTOGRAM:
        # increment_counter should raise
        raised_counter = False
        try:
            collector.increment_counter("test.metric", value=1.0)
        except SemanticError:
            raised_counter = True
        assert raised_counter is True, (
            "increment_counter on HISTOGRAM metric should raise SemanticError"
        )

        # set_gauge should raise
        raised_gauge = False
        try:
            collector.set_gauge("test.metric", value=1.0)
        except SemanticError:
            raised_gauge = True
        assert raised_gauge is True, (
            "set_gauge on HISTOGRAM metric should raise SemanticError"
        )

        # record_histogram should succeed
        collector.record_histogram("test.metric", value=1.0)

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
