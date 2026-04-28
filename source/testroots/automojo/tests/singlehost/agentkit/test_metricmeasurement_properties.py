"""
    Property-based tests for the automojo.agentkit.metricmeasurement module.

    Uses automojo.testbase.properties to verify:
    - Property 19: MetricMeasurement JSON round-trip

    **Validates: Requirements 12.5, 12.7, 12.8**
"""

from datetime import datetime

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.metricmeasurement import MetricMeasurement


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_metric_name_strategy = st.text(min_size=1, max_size=50)

_value_strategy = st.floats()

_timestamp_strategy = _datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 12, 31),
)

_labels_strategy = st.dictionaries(
    keys=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(categories=("L", "N")),
    ),
    values=st.text(max_size=50),
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 19: MetricMeasurement JSON round-trip
# ---------------------------------------------------------------------------

@given(
    metric_name=_metric_name_strategy,
    value=_value_strategy,
    timestamp=_timestamp_strategy,
    labels=_labels_strategy,
    constraints={"max_examples": 50},
)
def test_metricmeasurement_json_round_trip(
    metric_name: str,
    value: float,
    timestamp: datetime,
    labels: dict,
) -> None:
    """
        Property 19: For any valid MetricMeasurement, calling to_json()
        and then from_json() produces an equivalent MetricMeasurement
        with all fields preserved.

        **Validates: Requirements 12.5, 12.7, 12.8**
    """
    original = MetricMeasurement(
        metric_name=metric_name,
        value=value,
        timestamp=timestamp,
        labels=labels,
    )

    json_str = original.to_json()
    restored = MetricMeasurement.from_json(json_str)

    assert restored.metric_name == original.metric_name, \
        "Round-trip should preserve metric_name"
    assert restored.value == original.value, \
        "Round-trip should preserve value"
    assert restored.timestamp == original.timestamp, \
        "Round-trip should preserve timestamp"
    assert restored.labels == original.labels, \
        "Round-trip should preserve labels"

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
