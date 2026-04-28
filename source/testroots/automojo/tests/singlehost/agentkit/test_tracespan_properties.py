"""
    Property-based tests for the automojo.agentkit.tracespan module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 12: TraceSpan JSON round-trip for completed spans
    - Property 13: TraceSpan set_attribute accumulates attributes
    - Property 14: TraceSpan add_event accumulates events
    - Property 15: TraceSpan duration equals elapsed time

    **Validates: Requirements 7.5, 7.6, 7.9, 7.11, 7.13, 7.14**
"""

from datetime import datetime, timedelta

from automojo.testbase.properties import given, assume
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.tracecontext import TraceContext
from automojo.agentkit.traceevent import TraceEvent
from automojo.agentkit.tracespan import TraceSpan


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_hex_alphabet = "0123456789abcdef"

_trace_id_strategy = st.text(
    alphabet=_hex_alphabet,
    min_size=32,
    max_size=32,
)

_span_id_strategy = st.text(
    alphabet=_hex_alphabet,
    min_size=16,
    max_size=16,
)

_trace_flags_strategy = st.integers(min_value=0, max_value=255)


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

_span_name_strategy = st.text(min_size=1, max_size=50)

_status_strategy = st.sampled_from(["unset", "ok", "error"])

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

_event_name_strategy = st.text(min_size=1, max_size=50)


# ---------------------------------------------------------------------------
# Property 12: TraceSpan JSON round-trip for completed spans
# ---------------------------------------------------------------------------

@given(
    span_name=_span_name_strategy,
    trace_id=_trace_id_strategy,
    span_id=_span_id_strategy,
    trace_flags=_trace_flags_strategy,
    start_time=_timestamp_strategy,
    seconds_elapsed=st.integers(min_value=1, max_value=86400),
    status=_status_strategy,
    attributes=_attributes_strategy,
    event_names=st.lists(_event_name_strategy, min_size=0, max_size=3),
    event_timestamps=st.lists(_timestamp_strategy, min_size=3, max_size=3),
    constraints={"max_examples": 50},
)
def test_tracespan_json_round_trip_completed(
    span_name: str,
    trace_id: str,
    span_id: str,
    trace_flags: int,
    start_time: datetime,
    seconds_elapsed: int,
    status: str,
    attributes: dict,
    event_names: list,
    event_timestamps: list,
) -> None:
    """
        **Validates: Requirements 7.11, 7.13, 7.14**

        For any valid completed TraceSpan instance (with end_time set),
        calling to_json() and then from_json() shall produce a TraceSpan
        whose name, trace_context fields, start_time, end_time, status,
        attributes, and events are equal to the original.
    """
    end_time = start_time + timedelta(seconds=seconds_elapsed)

    trace_context = TraceContext(
        trace_id=trace_id,
        span_id=span_id,
        trace_flags=trace_flags,
    )

    span = TraceSpan(
        name=span_name,
        trace_context=trace_context,
        start_time=start_time,
        status=status,
        attributes=attributes,
    )

    # Add events using internal list to control timestamps
    for idx in range(len(event_names)):
        event = TraceEvent(
            name=event_names[idx],
            timestamp=event_timestamps[idx],
        )
        span._events.append(event)

    # Set end_time directly to avoid timing issues
    span._end_time = end_time

    json_str = span.to_json()
    reconstructed = TraceSpan.from_json(json_str)

    assert reconstructed.name == span_name, (
        "Round-trip name mismatch: expected {!r}, got {!r}".format(
            span_name, reconstructed.name)
    )

    assert reconstructed.trace_context.trace_id == trace_id, (
        "Round-trip trace_id mismatch: expected {!r}, got {!r}".format(
            trace_id, reconstructed.trace_context.trace_id)
    )

    assert reconstructed.trace_context.span_id == span_id, (
        "Round-trip span_id mismatch: expected {!r}, got {!r}".format(
            span_id, reconstructed.trace_context.span_id)
    )

    assert reconstructed.trace_context.trace_flags == trace_flags, (
        "Round-trip trace_flags mismatch: expected {!r}, got {!r}".format(
            trace_flags, reconstructed.trace_context.trace_flags)
    )

    assert reconstructed.start_time == start_time, (
        "Round-trip start_time mismatch: expected {!r}, got {!r}".format(
            start_time, reconstructed.start_time)
    )

    assert reconstructed.end_time == end_time, (
        "Round-trip end_time mismatch: expected {!r}, got {!r}".format(
            end_time, reconstructed.end_time)
    )

    assert reconstructed.status == status, (
        "Round-trip status mismatch: expected {!r}, got {!r}".format(
            status, reconstructed.status)
    )

    assert reconstructed.attributes == attributes, (
        "Round-trip attributes mismatch: expected {!r}, got {!r}".format(
            attributes, reconstructed.attributes)
    )

    reconstructed_events = reconstructed.events
    assert len(reconstructed_events) == len(event_names), (
        "Round-trip events count mismatch: expected {}, got {}".format(
            len(event_names), len(reconstructed_events))
    )

    for idx in range(len(event_names)):
        assert reconstructed_events[idx].name == event_names[idx], (
            "Round-trip event name mismatch at index {}: expected {!r}, got {!r}".format(
                idx, event_names[idx], reconstructed_events[idx].name)
        )

    return


# ---------------------------------------------------------------------------
# Property 13: TraceSpan set_attribute accumulates attributes
# ---------------------------------------------------------------------------

@given(
    span_name=_span_name_strategy,
    kv_pairs=st.lists(
        st.tuples(_attr_key_strategy, _attr_value_strategy),
        min_size=1,
        max_size=20,
    ),
    constraints={"max_examples": 50},
)
def test_tracespan_set_attribute_accumulates(
    span_name: str,
    kv_pairs: list,
) -> None:
    """
        **Validates: Requirements 7.5**

        For any TraceSpan and any sequence of N distinct key-value pairs
        passed to set_attribute(), the span's attributes dictionary shall
        contain all N key-value pairs.
    """
    # Deduplicate keys, keeping the last value for each key
    unique_pairs = {}
    for key, value in kv_pairs:
        unique_pairs[key] = value

    trace_context = TraceContext()
    span = TraceSpan(name=span_name, trace_context=trace_context)

    for key, value in kv_pairs:
        span.set_attribute(key, value)

    result_attrs = span.attributes

    for key, expected_value in unique_pairs.items():
        assert key in result_attrs, (
            "Attribute key {!r} not found in span attributes".format(key)
        )
        assert result_attrs[key] == expected_value, (
            "Attribute value mismatch for key {!r}: expected {!r}, got {!r}".format(
                key, expected_value, result_attrs[key])
        )

    assert len(result_attrs) == len(unique_pairs), (
        "Attribute count mismatch: expected {}, got {}".format(
            len(unique_pairs), len(result_attrs))
    )

    return


# ---------------------------------------------------------------------------
# Property 14: TraceSpan add_event accumulates events
# ---------------------------------------------------------------------------

@given(
    span_name=_span_name_strategy,
    event_names=st.lists(
        _event_name_strategy,
        min_size=1,
        max_size=20,
    ),
    constraints={"max_examples": 50},
)
def test_tracespan_add_event_accumulates(
    span_name: str,
    event_names: list,
) -> None:
    """
        **Validates: Requirements 7.6**

        For any TraceSpan and any sequence of N add_event() calls with
        distinct names, the span's events list shall contain N TraceEvent
        objects in order with matching names.
    """
    # Ensure distinct names for the property statement
    distinct_names = list(dict.fromkeys(event_names))
    assume(len(distinct_names) >= 1)

    trace_context = TraceContext()
    span = TraceSpan(name=span_name, trace_context=trace_context)

    for event_name in distinct_names:
        span.add_event(event_name)

    result_events = span.events

    assert len(result_events) == len(distinct_names), (
        "Event count mismatch: expected {}, got {}".format(
            len(distinct_names), len(result_events))
    )

    for idx in range(len(distinct_names)):
        assert result_events[idx].name == distinct_names[idx], (
            "Event name mismatch at index {}: expected {!r}, got {!r}".format(
                idx, distinct_names[idx], result_events[idx].name)
        )

    return


# ---------------------------------------------------------------------------
# Property 15: TraceSpan duration equals elapsed time
# ---------------------------------------------------------------------------

@given(
    span_name=_span_name_strategy,
    start_time=_timestamp_strategy,
    seconds_elapsed=st.integers(min_value=1, max_value=86400),
    constraints={"max_examples": 50},
)
def test_tracespan_duration_equals_elapsed_time(
    span_name: str,
    start_time: datetime,
    seconds_elapsed: int,
) -> None:
    """
        **Validates: Requirements 7.9**

        For any completed TraceSpan, the duration property shall equal
        (end_time - start_time).total_seconds().
    """
    end_time = start_time + timedelta(seconds=seconds_elapsed)

    trace_context = TraceContext()
    span = TraceSpan(
        name=span_name,
        trace_context=trace_context,
        start_time=start_time,
    )

    # Set end_time directly to avoid timing issues
    span._end_time = end_time

    expected_duration = (end_time - start_time).total_seconds()
    actual_duration = span.duration

    assert actual_duration is not None, (
        "Duration should not be None for a completed span"
    )

    assert actual_duration == expected_duration, (
        "Duration mismatch: expected {!r}, got {!r}".format(
            expected_duration, actual_duration)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
