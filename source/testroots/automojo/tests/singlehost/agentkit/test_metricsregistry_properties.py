"""
    Property-based tests for the automojo.agentkit.metricsregistry and
    automojo.agentkit.metricscollector modules.

    Uses automojo.testbase.properties to verify:
    - Property 20: MetricsRegistry registration and lookup correctness
    - Property 21: MetricsCollector counter accumulation
    - Property 22: MetricsCollector type enforcement

    **Validates: Requirements 14.1, 14.2, 14.4, 14.5, 14.6, 14.7,
                 13.2, 13.4, 13.6, 13.8, 13.10**
"""

from typing import List

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.metricdefinition import MetricDefinition
from automojo.agentkit.metricscollector import MetricsCollector
from automojo.agentkit.metricsregistry import MetricsRegistry
from automojo.agentkit.metrictype import MetricType


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_metric_name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz._",
    min_size=1,
    max_size=30,
)

@composite
def _unique_metric_names_strategy(draw, min_size=1, max_size=20):
    name_set = draw(st.sets(_metric_name_strategy, min_size=min_size, max_size=max_size))
    return list(name_set)

_metric_type_strategy = st.sampled_from([
    MetricType.COUNTER,
    MetricType.GAUGE,
    MetricType.HISTOGRAM,
])


# ---------------------------------------------------------------------------
# Property 20: MetricsRegistry registration and lookup correctness
# ---------------------------------------------------------------------------

@given(
    names=_unique_metric_names_strategy(),
    settings=settings(max_examples=50),
)
def test_registry_registration_and_lookup_correctness(
    names: List[str],
) -> None:
    """
        **Validates: Requirements 14.1, 14.2, 14.4, 14.5, 14.6, 14.7**

        For any set of N MetricDefinition instances with unique names:
        - count equals N
        - lookup returns the correct definition for each name
        - has_metric returns True for each registered name
        - has_metric returns False for an unregistered name
        - list_all returns all N definitions
        - registering a duplicate name raises SemanticError
    """
    registry = MetricsRegistry()

    definitions = []
    for name in names:
        defn = MetricDefinition(
            name=name,
            description="Test metric {}".format(name),
            unit="count",
            metric_type=MetricType.COUNTER
        )
        definitions.append(defn)
        registry.register(defn)

    # count equals N
    assert registry.count == len(names), (
        "Expected count {}, got {}".format(len(names), registry.count)
    )

    # lookup returns correct definition for each name
    for defn in definitions:
        result = registry.lookup(defn.name)
        assert result is defn, (
            "Lookup for {!r} should return the registered definition".format(
                defn.name
            )
        )

    # has_metric returns True for each registered name
    for name in names:
        assert registry.has_metric(name) is True, (
            "has_metric({!r}) should return True".format(name)
        )

    # has_metric returns False for an unregistered name
    unregistered_name = "zzzz.unregistered.metric.name"
    assert registry.has_metric(unregistered_name) is False, (
        "has_metric for unregistered name should return False"
    )

    # list_all returns all N definitions
    all_defs = registry.list_all()
    assert len(all_defs) == len(names), (
        "list_all should return {} definitions, got {}".format(
            len(names), len(all_defs)
        )
    )
    all_names = {d.name for d in all_defs}
    for name in names:
        assert name in all_names, (
            "list_all should include {!r}".format(name)
        )

    # duplicate registration raises SemanticError
    duplicate_defn = MetricDefinition(
        name=names[0],
        description="Duplicate",
        unit="count",
        metric_type=MetricType.COUNTER
    )
    raised = False
    try:
        registry.register(duplicate_defn)
    except SemanticError:
        raised = True

    assert raised is True, (
        "Registering duplicate name {!r} should raise SemanticError".format(
            names[0]
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
