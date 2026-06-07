"""
    Unit tests for the ccai.agentkit.metricsregistry module.

    Tests the MetricsRegistry class covering register, deregister,
    lookup, has_metric, list_all, count, duplicate error, and string
    representations.

    Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9
"""

from ccai.agentkit.metricsregistry import MetricsRegistry
from ccai.agentkit.metricdefinition import MetricDefinition
from ccai.agentkit.metrictype import MetricType
from ccai.agentkit.errors import SemanticError


# ---- Helper Functions ----


def _create_counter_definition(name: str = "test.counter") -> MetricDefinition:
    """
        Creates a standard COUNTER MetricDefinition for testing.

        :param name: The metric name string.
        :returns: A MetricDefinition instance.
    """
    definition = MetricDefinition(
        name=name,
        description="A test counter",
        unit="count",
        metric_type=MetricType.COUNTER
    )
    return definition


def _create_gauge_definition(name: str = "test.gauge") -> MetricDefinition:
    """
        Creates a standard GAUGE MetricDefinition for testing.

        :param name: The metric name string.
        :returns: A MetricDefinition instance.
    """
    definition = MetricDefinition(
        name=name,
        description="A test gauge",
        unit="count",
        metric_type=MetricType.GAUGE
    )
    return definition


# ---- Construction ----


def test_registry_starts_empty():
    """
        Verify that a new MetricsRegistry has zero registered metrics.
    """
    registry = MetricsRegistry()

    assert registry.count == 0, "New registry should have count 0"
    return


# ---- Register ----


def test_register_adds_definition():
    """
        Verify that registering a MetricDefinition increases the count.
    """
    registry = MetricsRegistry()
    defn = _create_counter_definition()

    registry.register(defn)

    assert registry.count == 1, "Registry should have count 1 after registering one definition"
    return


def test_register_duplicate_raises_semantic_error():
    """
        Verify that registering a MetricDefinition with a duplicate
        name raises SemanticError.
    """
    registry = MetricsRegistry()
    defn1 = _create_counter_definition("dup.metric")
    defn2 = _create_counter_definition("dup.metric")

    registry.register(defn1)

    raised = False
    try:
        registry.register(defn2)
    except SemanticError:
        raised = True

    assert raised is True, "Duplicate registration should raise SemanticError"
    return


# ---- Deregister ----


def test_deregister_removes_definition():
    """
        Verify that deregistering a metric removes it from the registry.
    """
    registry = MetricsRegistry()
    defn = _create_counter_definition()

    registry.register(defn)
    registry.deregister("test.counter")

    assert registry.count == 0, "Registry should have count 0 after deregistering"
    assert registry.has_metric("test.counter") is False, "Metric should not exist after deregister"
    return


def test_deregister_nonexistent_does_not_raise():
    """
        Verify that deregistering a non-existent metric does not raise.
    """
    registry = MetricsRegistry()

    registry.deregister("nonexistent.metric")

    assert registry.count == 0, "Registry should remain empty"
    return


# ---- Lookup ----


def test_lookup_returns_definition():
    """
        Verify that lookup returns the registered MetricDefinition.
    """
    registry = MetricsRegistry()
    defn = _create_counter_definition()

    registry.register(defn)
    result = registry.lookup("test.counter")

    assert result is defn, "Lookup should return the registered definition"
    return


def test_lookup_returns_none_for_unknown():
    """
        Verify that lookup returns None for an unregistered name.
    """
    registry = MetricsRegistry()

    result = registry.lookup("unknown.metric")

    assert result is None, "Lookup should return None for unknown metric"
    return


# ---- has_metric ----


def test_has_metric_returns_true_for_registered():
    """
        Verify that has_metric returns True for a registered metric.
    """
    registry = MetricsRegistry()
    defn = _create_counter_definition()

    registry.register(defn)

    assert registry.has_metric("test.counter") is True, "has_metric should return True"
    return


def test_has_metric_returns_false_for_unregistered():
    """
        Verify that has_metric returns False for an unregistered metric.
    """
    registry = MetricsRegistry()

    assert registry.has_metric("unknown") is False, "has_metric should return False"
    return


# ---- list_all ----


def test_list_all_returns_all_definitions():
    """
        Verify that list_all returns all registered definitions.
    """
    registry = MetricsRegistry()
    defn1 = _create_counter_definition("metric.a")
    defn2 = _create_gauge_definition("metric.b")

    registry.register(defn1)
    registry.register(defn2)

    result = registry.list_all()

    assert len(result) == 2, "list_all should return 2 definitions"
    names = [d.name for d in result]
    assert "metric.a" in names, "list_all should include metric.a"
    assert "metric.b" in names, "list_all should include metric.b"
    return


def test_list_all_returns_empty_for_empty_registry():
    """
        Verify that list_all returns an empty list for an empty registry.
    """
    registry = MetricsRegistry()

    result = registry.list_all()

    assert result == [], "list_all should return empty list"
    return


# ---- count ----


def test_count_reflects_registrations():
    """
        Verify that count reflects the number of registered metrics.
    """
    registry = MetricsRegistry()

    assert registry.count == 0

    registry.register(_create_counter_definition("m1"))
    assert registry.count == 1

    registry.register(_create_gauge_definition("m2"))
    assert registry.count == 2

    registry.deregister("m1")
    assert registry.count == 1

    return


# ---- __repr__ and __str__ ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name.
    """
    registry = MetricsRegistry()
    repr_str = repr(registry)

    assert "MetricsRegistry" in repr_str, "repr should contain 'MetricsRegistry'"
    return


def test_repr_contains_count():
    """
        Verify that __repr__ includes the count.
    """
    registry = MetricsRegistry()
    registry.register(_create_counter_definition())
    repr_str = repr(registry)

    assert "1" in repr_str, "repr should contain the count"
    return


def test_str_contains_class_name():
    """
        Verify that __str__ includes the class name.
    """
    registry = MetricsRegistry()
    str_val = str(registry)

    assert "MetricsRegistry" in str_val, "str should contain 'MetricsRegistry'"
    return


def test_str_contains_metric_names():
    """
        Verify that __str__ lists registered metric names.
    """
    registry = MetricsRegistry()
    registry.register(_create_counter_definition("my.counter"))
    str_val = str(registry)

    assert "my.counter" in str_val, "str should contain the metric name"
    return
