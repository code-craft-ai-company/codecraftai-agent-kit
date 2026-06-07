"""
    Property-based tests for the ccai.agentkit.configurationchangeevent module.

    Uses the ccai.testbase.properties engine to verify that ConfigurationChangeEvent instances
    survive a JSON round-trip (to_json followed by from_json) with all fields
    preserved.

    **Validates: Requirement 8 AC 7**
"""

from datetime import datetime

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.configurationchangeevent import ConfigurationChangeEvent
from ccai.agentkit.configurationlayersource import ConfigurationLayerSource


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_json_serializable_values = st.one_of(
    st.text(),
    st.integers(),
    st.booleans(),
    st.floats(),
    st.none(),
)

_source_strategy = st.sampled_from([
    ConfigurationLayerSource.DEFAULTS,
    ConfigurationLayerSource.FILE,
    ConfigurationLayerSource.ENVIRONMENT,
    ConfigurationLayerSource.RUNTIME,
    ConfigurationLayerSource.OVERRIDE,
])

_timestamp_strategy = _datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 1, 1),
)


# ---------------------------------------------------------------------------
# Property 4: ConfigurationChangeEvent JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    field_path=st.text(min_size=1, max_size=50),
    previous_value=_json_serializable_values,
    new_value=_json_serializable_values,
    source=_source_strategy,
    timestamp=_timestamp_strategy,
    constraints={"max_examples": 50},
)
def test_configurationchangeevent_json_round_trip(field_path, previous_value, new_value, source, timestamp):
    """
        **Validates: Requirement 8 AC 7**

        FOR ALL valid ConfigurationChangeEvent instances with JSON-serializable
        values, calling to_json and then from_json SHALL produce an equivalent
        ConfigurationChangeEvent object with the same field_path, previous_value,
        new_value, source, and timestamp.
    """
    original = ConfigurationChangeEvent(
        field_path=field_path,
        previous_value=previous_value,
        new_value=new_value,
        source=source,
        timestamp=timestamp,
    )

    json_str = original.to_json()
    reconstructed = ConfigurationChangeEvent.from_json(json_str)

    reconstructed_field_path = reconstructed.field_path
    assert reconstructed_field_path == field_path, (
        "Round-trip field_path mismatch: expected {!r}, got {!r}".format(
            field_path, reconstructed_field_path)
    )

    reconstructed_previous_value = reconstructed.previous_value
    assert reconstructed_previous_value == previous_value, (
        "Round-trip previous_value mismatch: expected {!r}, got {!r}".format(
            previous_value, reconstructed_previous_value)
    )

    reconstructed_new_value = reconstructed.new_value
    assert reconstructed_new_value == new_value, (
        "Round-trip new_value mismatch: expected {!r}, got {!r}".format(
            new_value, reconstructed_new_value)
    )

    reconstructed_source = reconstructed.source
    assert reconstructed_source == source, (
        "Round-trip source mismatch: expected {!r}, got {!r}".format(
            source, reconstructed_source)
    )

    reconstructed_timestamp = reconstructed.timestamp
    assert reconstructed_timestamp == timestamp, (
        "Round-trip timestamp mismatch: expected {!r}, got {!r}".format(
            timestamp, reconstructed_timestamp)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
