"""
    Property-based tests for the automojo.agentkit.metricssnapshot module.

    Uses automojo.testbase.properties to verify:
    - Property 23: MetricsSnapshot JSON round-trip

    **Validates: Requirements 15.5, 15.7, 15.8**
"""

from datetime import datetime

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.metricssnapshot import MetricsSnapshot


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_timestamp_strategy = _datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 12, 31),
)

_metrics_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.one_of(
            st.floats(),
            st.text(max_size=20),
        ),
        max_size=3,
    ),
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 23: MetricsSnapshot JSON round-trip
# ---------------------------------------------------------------------------

@given(
    timestamp=_timestamp_strategy,
    metrics=_metrics_strategy,
    settings=settings(max_examples=100),
)
def test_metricssnapshot_json_round_trip(
    timestamp: datetime,
    metrics: dict,
) -> None:
    """
        Property 23: For any valid MetricsSnapshot, calling to_json()
        and then from_json() produces an equivalent MetricsSnapshot
        with all fields preserved.

        **Validates: Requirements 15.5, 15.7, 15.8**
    """
    original = MetricsSnapshot(
        timestamp=timestamp,
        metrics=metrics,
    )

    json_str = original.to_json()
    restored = MetricsSnapshot.from_json(json_str)

    assert restored.timestamp == original.timestamp, \
        "Round-trip should preserve timestamp"
    assert restored.metrics == original.metrics, \
        "Round-trip should preserve metrics"

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
