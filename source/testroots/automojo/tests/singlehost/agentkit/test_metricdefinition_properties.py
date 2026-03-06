"""
    Property-based tests for the automojo.agentkit.metricdefinition module.

    Uses automojo.testbase.properties to verify:
    - Property 18: MetricDefinition JSON round-trip

    **Validates: Requirements 11.4, 11.6, 11.7**
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.metricdefinition import MetricDefinition
from automojo.agentkit.metrictype import MetricType


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_metric_type_strategy = st.sampled_from([
    MetricType.COUNTER,
    MetricType.GAUGE,
    MetricType.HISTOGRAM,
])

_name_strategy = st.text(min_size=1, max_size=50)

_description_strategy = st.text(min_size=1, max_size=100)

_unit_strategy = st.text(min_size=1, max_size=100)


# ---------------------------------------------------------------------------
# Property 18: MetricDefinition JSON round-trip
# ---------------------------------------------------------------------------

@given(
    name=_name_strategy,
    description=_description_strategy,
    unit=_unit_strategy,
    metric_type=_metric_type_strategy,
    settings=settings(max_examples=100),
)
def test_metricdefinition_json_round_trip(
    name: str,
    description: str,
    unit: str,
    metric_type: MetricType,
) -> None:
    """
        Property 18: For any valid MetricDefinition, calling to_json()
        and then from_json() produces an equivalent MetricDefinition
        with all fields preserved.

        **Validates: Requirements 11.4, 11.6, 11.7**
    """
    original = MetricDefinition(
        name=name,
        description=description,
        unit=unit,
        metric_type=metric_type,
    )

    json_str = original.to_json()
    restored = MetricDefinition.from_json(json_str)

    assert restored.name == original.name, \
        "Round-trip should preserve name"
    assert restored.description == original.description, \
        "Round-trip should preserve description"
    assert restored.unit == original.unit, \
        "Round-trip should preserve unit"
    assert restored.metric_type == original.metric_type, \
        "Round-trip should preserve metric_type"

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
