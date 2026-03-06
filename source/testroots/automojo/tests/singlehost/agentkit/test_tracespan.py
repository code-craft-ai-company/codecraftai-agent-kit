"""
    Unit tests for the automojo.agentkit.tracespan module.

    Tests the TraceSpan class: construction, set_status valid/invalid,
    set_attribute, add_event, end/double-end error, duration,
    serialization (as_dict, to_json, from_dict, from_json),
    __repr__, and __str__.
"""

import json
import time

from datetime import datetime

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.tracecontext import TraceContext
from automojo.agentkit.traceevent import TraceEvent
from automojo.agentkit.tracespan import TraceSpan


def test_construction_with_all_fields() -> None:
    """
        Verify that a TraceSpan can be constructed with all fields
        explicitly provided.
    """
    ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    ts = datetime(2025, 1, 15, 10, 30, 0)
    attrs = {"key1": "value1"}

    span = TraceSpan(
        name="test-span",
        trace_context=ctx,
        start_time=ts,
        status="ok",
        attributes=attrs
    )

    assert span.name == "test-span", "Name should match"
    assert span.trace_context is ctx, "TraceContext should match"
    assert span.start_time == ts, "Start time should match"
    assert span.status == "ok", "Status should match"
    assert span.attributes == attrs, "Attributes should match"
    return


def test_auto_generated_start_time() -> None:
    """
        Verify that when no start_time is provided, the current UTC
        time is used automatically.
    """
    ctx = TraceContext()
    before = datetime.utcnow()
    span = TraceSpan(name="auto-start", trace_context=ctx)
    after = datetime.utcnow()

    assert before <= span.start_time <= after, \
        "Auto-generated start_time should be between before and after"
    return


def test_default_status_is_unset() -> None:
    """
        Verify that the default status is 'unset'.
    """
    ctx = TraceContext()
    span = TraceSpan(name="default-status", trace_context=ctx)

    assert span.status == "unset", "Default status should be 'unset'"
    return


def test_default_end_time_is_none() -> None:
    """
        Verify that end_time defaults to None.
    """
    ctx = TraceContext()
    span = TraceSpan(name="no-end", trace_context=ctx)

    assert span.end_time is None, "Default end_time should be None"
    return


def test_default_status_description_is_none() -> None:
    """
        Verify that status_description defaults to None.
    """
    ctx = TraceContext()
    span = TraceSpan(name="no-desc", trace_context=ctx)

    assert span.status_description is None, \
        "Default status_description should be None"
    return


def test_default_events_is_empty() -> None:
    """
        Verify that events defaults to an empty list.
    """
    ctx = TraceContext()
    span = TraceSpan(name="no-events", trace_context=ctx)

    assert span.events == [], "Default events should be empty list"
    return


def test_default_attributes_is_empty() -> None:
    """
        Verify that attributes defaults to an empty dict when not provided.
    """
    ctx = TraceContext()
    span = TraceSpan(name="no-attrs", trace_context=ctx)

    assert span.attributes == {}, "Default attributes should be empty dict"
    return


def test_set_status_unset() -> None:
    """
        Verify that set_status accepts 'unset' as a valid status.
    """
    ctx = TraceContext()
    span = TraceSpan(name="status-unset", trace_context=ctx)
    span.set_status("unset")

    assert span.status == "unset", "Status should be 'unset'"
    return


def test_set_status_ok() -> None:
    """
        Verify that set_status accepts 'ok' as a valid status.
    """
    ctx = TraceContext()
    span = TraceSpan(name="status-ok", trace_context=ctx)
    span.set_status("ok")

    assert span.status == "ok", "Status should be 'ok'"
    return


def test_set_status_error() -> None:
    """
        Verify that set_status accepts 'error' as a valid status.
    """
    ctx = TraceContext()
    span = TraceSpan(name="status-error", trace_context=ctx)
    span.set_status("error")

    assert span.status == "error", "Status should be 'error'"
    return


def test_set_status_with_description() -> None:
    """
        Verify that set_status stores the description string.
    """
    ctx = TraceContext()
    span = TraceSpan(name="status-desc", trace_context=ctx)
    span.set_status("error", description="Something went wrong")

    assert span.status == "error", "Status should be 'error'"
    assert span.status_description == "Something went wrong", \
        "Status description should match"
    return


def test_set_status_invalid_raises_semantic_error() -> None:
    """
        Verify that set_status raises SemanticError for an invalid
        status value.
    """
    ctx = TraceContext()
    span = TraceSpan(name="bad-status", trace_context=ctx)

    raised = False
    try:
        span.set_status("invalid_status")
    except SemanticError:
        raised = True

    assert raised is True, \
        "set_status should raise SemanticError for invalid status"
    return


def test_set_attribute_adds_key_value() -> None:
    """
        Verify that set_attribute adds a key-value pair to the
        attributes dictionary.
    """
    ctx = TraceContext()
    span = TraceSpan(name="set-attr", trace_context=ctx)
    span.set_attribute("http.method", "GET")
    span.set_attribute("http.status_code", 200)

    attrs = span.attributes
    assert attrs["http.method"] == "GET", "Attribute key should be set"
    assert attrs["http.status_code"] == 200, "Attribute key should be set"
    return


def test_set_attribute_overwrites_existing() -> None:
    """
        Verify that set_attribute overwrites an existing key.
    """
    ctx = TraceContext()
    span = TraceSpan(name="overwrite-attr", trace_context=ctx)
    span.set_attribute("key", "old")
    span.set_attribute("key", "new")

    assert span.attributes["key"] == "new", \
        "set_attribute should overwrite existing key"
    return


def test_add_event_appends_trace_event() -> None:
    """
        Verify that add_event appends a TraceEvent to the events list.
    """
    ctx = TraceContext()
    span = TraceSpan(name="add-event", trace_context=ctx)
    span.add_event("event-1", attributes={"detail": "info"})

    events = span.events
    assert len(events) == 1, "Should have one event"
    assert events[0].name == "event-1", "Event name should match"
    assert events[0].attributes == {"detail": "info"}, \
        "Event attributes should match"
    return


def test_add_event_multiple() -> None:
    """
        Verify that multiple add_event calls accumulate events.
    """
    ctx = TraceContext()
    span = TraceSpan(name="multi-event", trace_context=ctx)
    span.add_event("event-1")
    span.add_event("event-2")
    span.add_event("event-3")

    events = span.events
    assert len(events) == 3, "Should have three events"
    assert events[0].name == "event-1", "First event name should match"
    assert events[1].name == "event-2", "Second event name should match"
    assert events[2].name == "event-3", "Third event name should match"
    return


def test_end_sets_end_time() -> None:
    """
        Verify that end() sets the end_time to the current UTC time.
    """
    ctx = TraceContext()
    span = TraceSpan(name="end-span", trace_context=ctx)

    before = datetime.utcnow()
    span.end()
    after = datetime.utcnow()

    assert span.end_time is not None, "end_time should be set after end()"
    assert before <= span.end_time <= after, \
        "end_time should be between before and after"
    return


def test_end_double_end_raises_semantic_error() -> None:
    """
        Verify that calling end() on an already-ended span raises
        SemanticError.
    """
    ctx = TraceContext()
    span = TraceSpan(name="double-end", trace_context=ctx)
    span.end()

    raised = False
    try:
        span.end()
    except SemanticError:
        raised = True

    assert raised is True, \
        "Calling end() twice should raise SemanticError"
    return


def test_duration_returns_none_when_not_ended() -> None:
    """
        Verify that duration returns None when the span has not been ended.
    """
    ctx = TraceContext()
    span = TraceSpan(name="no-duration", trace_context=ctx)

    assert span.duration is None, "Duration should be None when not ended"
    return


def test_duration_returns_correct_elapsed_seconds() -> None:
    """
        Verify that duration returns the correct elapsed time in seconds
        when the span has been ended.
    """
    ctx = TraceContext()
    start = datetime(2025, 1, 15, 10, 0, 0)
    span = TraceSpan(name="duration-span", trace_context=ctx, start_time=start)

    span._end_time = datetime(2025, 1, 15, 10, 0, 5)

    duration = span.duration
    assert duration == 5.0, "Duration should be 5.0 seconds"
    return


def test_attributes_returns_copy() -> None:
    """
        Verify that the attributes property returns a copy so that
        external mutations do not affect the span.
    """
    ctx = TraceContext()
    span = TraceSpan(name="attr-copy", trace_context=ctx, attributes={"k": "v"})

    returned = span.attributes
    returned["injected"] = "bad"

    assert "injected" not in span.attributes, \
        "Modifying returned attributes should not affect the span"
    return


def test_events_returns_copy() -> None:
    """
        Verify that the events property returns a copy so that
        external mutations do not affect the span.
    """
    ctx = TraceContext()
    span = TraceSpan(name="events-copy", trace_context=ctx)
    span.add_event("event-1")

    returned = span.events
    returned.append("injected")

    assert len(span.events) == 1, \
        "Modifying returned events should not affect the span"
    return


def test_as_dict_returns_dictionary() -> None:
    """
        Verify that as_dict returns a dictionary with all expected fields.
    """
    ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    start = datetime(2025, 1, 15, 10, 0, 0)
    span = TraceSpan(
        name="dict-span",
        trace_context=ctx,
        start_time=start,
        attributes={"key": "value"}
    )
    span.set_status("ok", description="all good")

    data = span.as_dict()

    assert isinstance(data, dict), "as_dict should return a dict"
    assert data["name"] == "dict-span", "name should match"
    assert data["start_time"] == start.isoformat(), "start_time should be ISO format"
    assert data["end_time"] is None, "end_time should be None"
    assert data["status"] == "ok", "status should match"
    assert data["status_description"] == "all good", "status_description should match"
    assert data["attributes"] == {"key": "value"}, "attributes should match"
    assert data["events"] == [], "events should be empty list"
    assert data["trace_context"]["trace_id"] == "a" * 32, \
        "trace_context trace_id should match"
    return


def test_as_dict_with_events() -> None:
    """
        Verify that as_dict includes serialized events.
    """
    ctx = TraceContext()
    span = TraceSpan(name="events-dict", trace_context=ctx)
    span.add_event("event-1", attributes={"detail": "info"})

    data = span.as_dict()

    assert len(data["events"]) == 1, "Should have one event in dict"
    assert data["events"][0]["name"] == "event-1", "Event name should match"
    return


def test_as_dict_with_end_time() -> None:
    """
        Verify that as_dict includes the end_time when the span is ended.
    """
    ctx = TraceContext()
    span = TraceSpan(name="ended-dict", trace_context=ctx)
    span.end()

    data = span.as_dict()

    assert data["end_time"] is not None, "end_time should be set in dict"
    return


def test_from_dict_reconstructs_span() -> None:
    """
        Verify that from_dict correctly reconstructs a TraceSpan
        from a dictionary.
    """
    data = {
        "name": "restored-span",
        "trace_context": {
            "trace_id": "a" * 32,
            "span_id": "b" * 16,
            "parent_span_id": None,
            "trace_flags": 0
        },
        "start_time": "2025-01-15T10:00:00",
        "end_time": "2025-01-15T10:00:05",
        "status": "ok",
        "status_description": "completed",
        "attributes": {"key": "value"},
        "events": [
            {
                "name": "event-1",
                "timestamp": "2025-01-15T10:00:02",
                "attributes": {"detail": "info"}
            }
        ]
    }
    span = TraceSpan.from_dict(data)

    assert span.name == "restored-span", "Reconstructed name should match"
    assert span.trace_context.trace_id == "a" * 32, \
        "Reconstructed trace_id should match"
    assert span.start_time == datetime(2025, 1, 15, 10, 0, 0), \
        "Reconstructed start_time should match"
    assert span.end_time == datetime(2025, 1, 15, 10, 0, 5), \
        "Reconstructed end_time should match"
    assert span.status == "ok", "Reconstructed status should match"
    assert span.status_description == "completed", \
        "Reconstructed status_description should match"
    assert span.attributes == {"key": "value"}, \
        "Reconstructed attributes should match"
    assert len(span.events) == 1, "Should have one reconstructed event"
    assert span.events[0].name == "event-1", \
        "Reconstructed event name should match"
    return


def test_dict_round_trip() -> None:
    """
        Verify that as_dict followed by from_dict produces an equivalent
        TraceSpan.
    """
    ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    start = datetime(2025, 1, 15, 10, 0, 0)
    original = TraceSpan(
        name="round-trip",
        trace_context=ctx,
        start_time=start,
        attributes={"key": "value"}
    )
    original.set_status("ok", description="done")
    original.add_event("event-1")
    original.end()

    data = original.as_dict()
    restored = TraceSpan.from_dict(data)

    assert restored.name == original.name, "Round-trip name should match"
    assert restored.trace_context.trace_id == original.trace_context.trace_id, \
        "Round-trip trace_id should match"
    assert restored.start_time == original.start_time, \
        "Round-trip start_time should match"
    assert restored.end_time == original.end_time, \
        "Round-trip end_time should match"
    assert restored.status == original.status, \
        "Round-trip status should match"
    assert restored.status_description == original.status_description, \
        "Round-trip status_description should match"
    assert restored.attributes == original.attributes, \
        "Round-trip attributes should match"
    assert len(restored.events) == len(original.events), \
        "Round-trip events count should match"
    return


def test_to_json_returns_valid_json_string() -> None:
    """
        Verify that to_json returns a valid JSON string.
    """
    ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    span = TraceSpan(name="json-span", trace_context=ctx)

    json_str = span.to_json()
    data = json.loads(json_str)

    assert isinstance(data, dict), "to_json should produce valid JSON"
    assert data["name"] == "json-span", "JSON name should match"
    return


def test_from_json_reconstructs_span() -> None:
    """
        Verify that from_json correctly reconstructs a TraceSpan
        from a JSON string.
    """
    data = {
        "name": "json-restored",
        "trace_context": {
            "trace_id": "a" * 32,
            "span_id": "b" * 16,
            "parent_span_id": None,
            "trace_flags": 0
        },
        "start_time": "2025-01-15T10:00:00",
        "end_time": None,
        "status": "unset",
        "status_description": None,
        "attributes": {},
        "events": []
    }
    json_str = json.dumps(data)
    span = TraceSpan.from_json(json_str)

    assert span.name == "json-restored", "Reconstructed name should match"
    assert span.status == "unset", "Reconstructed status should match"
    return


def test_json_round_trip() -> None:
    """
        Verify that to_json followed by from_json produces an equivalent
        TraceSpan.
    """
    ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    start = datetime(2025, 1, 15, 10, 0, 0)
    original = TraceSpan(
        name="json-round-trip",
        trace_context=ctx,
        start_time=start,
        attributes={"key": "value"}
    )
    original.set_status("error", description="failed")
    original.add_event("event-1", attributes={"detail": "info"})
    original.end()

    json_str = original.to_json()
    restored = TraceSpan.from_json(json_str)

    assert restored.name == original.name, "Round-trip name should match"
    assert restored.trace_context.trace_id == original.trace_context.trace_id, \
        "Round-trip trace_id should match"
    assert restored.status == original.status, \
        "Round-trip status should match"
    assert restored.status_description == original.status_description, \
        "Round-trip status_description should match"
    assert len(restored.events) == len(original.events), \
        "Round-trip events count should match"
    return


def test_repr_contains_class_name() -> None:
    """
        Verify that __repr__ includes the class name 'TraceSpan'.
    """
    ctx = TraceContext()
    span = TraceSpan(name="repr-span", trace_context=ctx)
    repr_str = repr(span)

    assert "TraceSpan" in repr_str, "__repr__ should include class name"
    return


def test_repr_contains_name() -> None:
    """
        Verify that __repr__ includes the span name.
    """
    ctx = TraceContext()
    span = TraceSpan(name="repr-name-span", trace_context=ctx)
    repr_str = repr(span)

    assert "repr-name-span" in repr_str, "__repr__ should include name"
    return


def test_repr_contains_trace_id() -> None:
    """
        Verify that __repr__ includes the trace_id.
    """
    ctx = TraceContext(trace_id="a" * 32)
    span = TraceSpan(name="repr-tid", trace_context=ctx)
    repr_str = repr(span)

    assert "a" * 32 in repr_str, "__repr__ should include trace_id"
    return


def test_repr_contains_span_id() -> None:
    """
        Verify that __repr__ includes the span_id.
    """
    ctx = TraceContext(span_id="b" * 16)
    span = TraceSpan(name="repr-sid", trace_context=ctx)
    repr_str = repr(span)

    assert "b" * 16 in repr_str, "__repr__ should include span_id"
    return


def test_repr_contains_status() -> None:
    """
        Verify that __repr__ includes the status.
    """
    ctx = TraceContext()
    span = TraceSpan(name="repr-status", trace_context=ctx)
    span.set_status("error")
    repr_str = repr(span)

    assert "error" in repr_str, "__repr__ should include status"
    return


def test_str_contains_name() -> None:
    """
        Verify that __str__ includes the span name.
    """
    ctx = TraceContext()
    span = TraceSpan(name="str-name-span", trace_context=ctx)
    str_val = str(span)

    assert "str-name-span" in str_val, "__str__ should include name"
    return


def test_str_contains_status() -> None:
    """
        Verify that __str__ includes the status.
    """
    ctx = TraceContext()
    span = TraceSpan(name="str-status", trace_context=ctx)
    span.set_status("ok")
    str_val = str(span)

    assert "ok" in str_val, "__str__ should include status"
    return


def test_str_contains_duration() -> None:
    """
        Verify that __str__ includes the duration value.
    """
    ctx = TraceContext()
    start = datetime(2025, 1, 15, 10, 0, 0)
    span = TraceSpan(name="str-duration", trace_context=ctx, start_time=start)
    span._end_time = datetime(2025, 1, 15, 10, 0, 5)
    str_val = str(span)

    assert "5.0" in str_val, "__str__ should include duration"
    return
