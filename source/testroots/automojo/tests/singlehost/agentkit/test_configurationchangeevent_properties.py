"""
    Property-based tests for the automojo.agentkit.configurationchangeevent module.

    Uses the hypothesis library to verify that ConfigurationChangeEvent instances
    survive a JSON round-trip (to_json followed by from_json) with all fields
    preserved.

    **Validates: Requirement 8 AC 7**
"""

from datetime import datetime

from hypothesis import given, settings
from hypothesis.strategies import (
    booleans,
    datetimes,
    floats,
    integers,
    none,
    one_of,
    sampled_from,
    text,
)

from automojo.agentkit.configurationchangeevent import ConfigurationChangeEvent
from automojo.agentkit.configurationlayersource import ConfigurationLayerSource


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_json_serializable_values = one_of(
    text(),
    integers(),
    booleans(),
    floats(allow_nan=False, allow_infinity=False),
    none(),
)

_source_strategy = sampled_from([
    ConfigurationLayerSource.DEFAULTS,
    ConfigurationLayerSource.FILE,
    ConfigurationLayerSource.ENVIRONMENT,
    ConfigurationLayerSource.RUNTIME,
    ConfigurationLayerSource.OVERRIDE,
])

_timestamp_strategy = datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 1, 1),
)


# ---------------------------------------------------------------------------
# Property 4: ConfigurationChangeEvent JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    field_path=text(min_size=1, max_size=50),
    previous_value=_json_serializable_values,
    new_value=_json_serializable_values,
    source=_source_strategy,
    timestamp=_timestamp_strategy,
)
@settings(max_examples=200)
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
