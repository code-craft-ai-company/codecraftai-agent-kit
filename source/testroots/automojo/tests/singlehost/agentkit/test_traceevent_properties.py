"""
    Property-based tests for the automojo.agentkit.traceevent module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 11: TraceEvent JSON round-trip

    **Validates: Requirements 8.5, 8.7, 8.8**
"""

from datetime import datetime

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.traceevent import TraceEvent


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

_event_name_strategy = st.text(min_size=1, max_size=50)

_attr_key_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(categories=("L", "N")),
)

_attr_value_strategy = st.one_of(
    st.text(max_size=100),
    st.integers(),
    st.floats(),
)

_attributes_strategy = st.dictionaries(
    keys=_attr_key_strategy,
    values=_attr_value_strategy,
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 11: TraceEvent JSON round-trip
# ---------------------------------------------------------------------------

@given(
    name=_event_name_strategy,
    timestamp=_timestamp_strategy,
    attributes=_attributes_strategy,
    settings=settings(max_examples=50),
)
def test_traceevent_json_round_trip(
    name: str,
    timestamp: datetime,
    attributes: dict,
) -> None:
    """
        **Validates: Requirements 8.5, 8.7, 8.8**

        For any valid TraceEvent instance with any name, timestamp, and
        attributes, calling to_json() and then from_json() shall produce
        a TraceEvent whose fields are equal to the original.
    """
    original = TraceEvent(
        name=name,
        timestamp=timestamp,
        attributes=attributes,
    )

    json_str = original.to_json()
    reconstructed = TraceEvent.from_json(json_str)

    assert reconstructed.name == name, (
        "Round-trip name mismatch: expected {!r}, got {!r}".format(
            name, reconstructed.name)
    )

    assert reconstructed.timestamp == timestamp, (
        "Round-trip timestamp mismatch: expected {!r}, got {!r}".format(
            timestamp, reconstructed.timestamp)
    )

    reconstructed_attrs = reconstructed.attributes
    assert reconstructed_attrs == attributes, (
        "Round-trip attributes mismatch: expected {!r}, got {!r}".format(
            attributes, reconstructed_attrs)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
