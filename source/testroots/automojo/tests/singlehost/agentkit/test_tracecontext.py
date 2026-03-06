"""
    Unit tests for the automojo.agentkit.tracecontext module.

    Tests the TraceContext class: auto-generated identifiers,
    create_child_span_context, traceparent round-trip, malformed
    traceparent error handling, serialization (as_dict, to_json,
    from_dict, from_json), __repr__, and __str__.
"""

import json
import re

from automojo.agentkit.tracecontext import TraceContext
from automojo.agentkit.errors import SemanticError


HEX_32_PATTERN = re.compile(r"^[0-9a-f]{32}$")
HEX_16_PATTERN = re.compile(r"^[0-9a-f]{16}$")


def test_auto_generated_trace_id_is_32_char_lowercase_hex() -> None:
    """
        Verify that when no trace_id is provided, a 32-character
        lowercase hexadecimal string is generated automatically.
    """
    ctx = TraceContext()
    trace_id = ctx.trace_id

    assert len(trace_id) == 32, "Auto-generated trace_id should be 32 characters"
    assert HEX_32_PATTERN.match(trace_id) is not None, \
        "Auto-generated trace_id should be lowercase hex"
    return


def test_auto_generated_span_id_is_16_char_lowercase_hex() -> None:
    """
        Verify that when no span_id is provided, a 16-character
        lowercase hexadecimal string is generated automatically.
    """
    ctx = TraceContext()
    span_id = ctx.span_id

    assert len(span_id) == 16, "Auto-generated span_id should be 16 characters"
    assert HEX_16_PATTERN.match(span_id) is not None, \
        "Auto-generated span_id should be lowercase hex"
    return


def test_auto_generated_ids_are_unique() -> None:
    """
        Verify that two TraceContext instances get different auto-generated
        trace_id and span_id values.
    """
    ctx1 = TraceContext()
    ctx2 = TraceContext()

    assert ctx1.trace_id != ctx2.trace_id, \
        "Each TraceContext should get a unique auto-generated trace_id"
    assert ctx1.span_id != ctx2.span_id, \
        "Each TraceContext should get a unique auto-generated span_id"
    return


def test_explicit_trace_id_is_preserved() -> None:
    """
        Verify that an explicitly provided trace_id is used as-is.
    """
    ctx = TraceContext(trace_id="a" * 32)
    trace_id = ctx.trace_id

    assert trace_id == "a" * 32, "Explicit trace_id should be preserved"
    return


def test_explicit_span_id_is_preserved() -> None:
    """
        Verify that an explicitly provided span_id is used as-is.
    """
    ctx = TraceContext(span_id="b" * 16)
    span_id = ctx.span_id

    assert span_id == "b" * 16, "Explicit span_id should be preserved"
    return


def test_parent_span_id_defaults_to_none() -> None:
    """
        Verify that parent_span_id defaults to None when not provided.
    """
    ctx = TraceContext()
    parent_span_id = ctx.parent_span_id

    assert parent_span_id is None, "parent_span_id should default to None"
    return


def test_trace_flags_defaults_to_zero() -> None:
    """
        Verify that trace_flags defaults to 0 when not provided.
    """
    ctx = TraceContext()
    trace_flags = ctx.trace_flags

    assert trace_flags == 0, "trace_flags should default to 0"
    return


def test_explicit_parent_span_id_is_preserved() -> None:
    """
        Verify that an explicitly provided parent_span_id is used as-is.
    """
    ctx = TraceContext(parent_span_id="c" * 16)
    parent_span_id = ctx.parent_span_id

    assert parent_span_id == "c" * 16, "Explicit parent_span_id should be preserved"
    return


def test_explicit_trace_flags_is_preserved() -> None:
    """
        Verify that an explicitly provided trace_flags value is used as-is.
    """
    ctx = TraceContext(trace_flags=1)
    trace_flags = ctx.trace_flags

    assert trace_flags == 1, "Explicit trace_flags should be preserved"
    return


def test_create_child_span_context_preserves_trace_id() -> None:
    """
        Verify that create_child_span_context returns a new TraceContext
        with the same trace_id.
    """
    parent = TraceContext(trace_id="d" * 32, span_id="e" * 16)
    child = parent.create_child_span_context()

    assert child.trace_id == parent.trace_id, \
        "Child should have the same trace_id as parent"
    return


def test_create_child_span_context_sets_parent_span_id() -> None:
    """
        Verify that create_child_span_context sets the parent_span_id
        to the current span_id.
    """
    parent = TraceContext(trace_id="d" * 32, span_id="e" * 16)
    child = parent.create_child_span_context()

    assert child.parent_span_id == parent.span_id, \
        "Child parent_span_id should be the parent's span_id"
    return


def test_create_child_span_context_generates_new_span_id() -> None:
    """
        Verify that create_child_span_context generates a new span_id
        different from the parent's span_id.
    """
    parent = TraceContext(trace_id="d" * 32, span_id="e" * 16)
    child = parent.create_child_span_context()

    assert child.span_id != parent.span_id, \
        "Child should have a new span_id"
    assert HEX_16_PATTERN.match(child.span_id) is not None, \
        "Child span_id should be 16-char lowercase hex"
    return


def test_create_child_span_context_preserves_trace_flags() -> None:
    """
        Verify that create_child_span_context preserves the trace_flags.
    """
    parent = TraceContext(trace_flags=1)
    child = parent.create_child_span_context()

    assert child.trace_flags == parent.trace_flags, \
        "Child should preserve the parent's trace_flags"
    return


def test_to_traceparent_format() -> None:
    """
        Verify that to_traceparent returns the correct W3C format
        "00-{trace_id}-{span_id}-{trace_flags:02x}".
    """
    ctx = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16,
        trace_flags=1
    )
    traceparent = ctx.to_traceparent()

    expected = "00-{}-{}-01".format("a" * 32, "b" * 16)
    assert traceparent == expected, \
        "to_traceparent should produce W3C format string"
    return


def test_to_traceparent_default_flags() -> None:
    """
        Verify that to_traceparent formats default trace_flags as '00'.
    """
    ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    traceparent = ctx.to_traceparent()

    assert traceparent.endswith("-00"), \
        "Default trace_flags should be formatted as '00'"
    return


def test_from_traceparent_parses_valid_string() -> None:
    """
        Verify that from_traceparent correctly parses a valid
        traceparent string.
    """
    traceparent = "00-{}-{}-01".format("a" * 32, "b" * 16)
    ctx = TraceContext.from_traceparent(traceparent)

    assert ctx.trace_id == "a" * 32, "Parsed trace_id should match"
    assert ctx.span_id == "b" * 16, "Parsed span_id should match"
    assert ctx.trace_flags == 1, "Parsed trace_flags should match"
    return


def test_traceparent_round_trip() -> None:
    """
        Verify that to_traceparent followed by from_traceparent
        produces an equivalent TraceContext.
    """
    original = TraceContext(
        trace_id="abcdef0123456789abcdef0123456789",
        span_id="0123456789abcdef",
        trace_flags=1
    )
    traceparent = original.to_traceparent()
    restored = TraceContext.from_traceparent(traceparent)

    assert restored.trace_id == original.trace_id, \
        "Round-trip trace_id should match"
    assert restored.span_id == original.span_id, \
        "Round-trip span_id should match"
    assert restored.trace_flags == original.trace_flags, \
        "Round-trip trace_flags should match"
    return


def test_from_traceparent_raises_on_wrong_parts_count() -> None:
    """
        Verify that from_traceparent raises SemanticError when the
        traceparent string does not have exactly 4 parts.
    """
    raised = False
    try:
        TraceContext.from_traceparent("00-abc-def")
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_traceparent should raise SemanticError for wrong parts count"
    return


def test_from_traceparent_raises_on_bad_trace_id_length() -> None:
    """
        Verify that from_traceparent raises SemanticError when the
        trace_id is not 32 characters.
    """
    traceparent = "00-{}-{}-00".format("a" * 31, "b" * 16)
    raised = False
    try:
        TraceContext.from_traceparent(traceparent)
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_traceparent should raise SemanticError for bad trace_id length"
    return


def test_from_traceparent_raises_on_bad_span_id_length() -> None:
    """
        Verify that from_traceparent raises SemanticError when the
        span_id is not 16 characters.
    """
    traceparent = "00-{}-{}-00".format("a" * 32, "b" * 15)
    raised = False
    try:
        TraceContext.from_traceparent(traceparent)
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_traceparent should raise SemanticError for bad span_id length"
    return


def test_from_traceparent_raises_on_non_hex_trace_id() -> None:
    """
        Verify that from_traceparent raises SemanticError when the
        trace_id contains non-hex characters.
    """
    bad_trace_id = "g" * 32
    traceparent = "00-{}-{}-00".format(bad_trace_id, "b" * 16)
    raised = False
    try:
        TraceContext.from_traceparent(traceparent)
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_traceparent should raise SemanticError for non-hex trace_id"
    return


def test_from_traceparent_raises_on_non_hex_span_id() -> None:
    """
        Verify that from_traceparent raises SemanticError when the
        span_id contains non-hex characters.
    """
    bad_span_id = "z" * 16
    traceparent = "00-{}-{}-00".format("a" * 32, bad_span_id)
    raised = False
    try:
        TraceContext.from_traceparent(traceparent)
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_traceparent should raise SemanticError for non-hex span_id"
    return


def test_from_traceparent_raises_on_bad_flags_length() -> None:
    """
        Verify that from_traceparent raises SemanticError when the
        trace_flags field is not 2 characters.
    """
    traceparent = "00-{}-{}-0".format("a" * 32, "b" * 16)
    raised = False
    try:
        TraceContext.from_traceparent(traceparent)
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_traceparent should raise SemanticError for bad flags length"
    return


def test_as_dict_returns_dictionary() -> None:
    """
        Verify that as_dict returns a dictionary with all expected fields.
    """
    ctx = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16,
        parent_span_id="c" * 16,
        trace_flags=1
    )
    data = ctx.as_dict()

    assert isinstance(data, dict), "as_dict should return a dict"
    assert data["trace_id"] == "a" * 32, "trace_id should match"
    assert data["span_id"] == "b" * 16, "span_id should match"
    assert data["parent_span_id"] == "c" * 16, "parent_span_id should match"
    assert data["trace_flags"] == 1, "trace_flags should match"
    return


def test_as_dict_with_none_parent() -> None:
    """
        Verify that as_dict includes None for parent_span_id when not set.
    """
    ctx = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    data = ctx.as_dict()

    assert data["parent_span_id"] is None, \
        "parent_span_id should be None when not set"
    return


def test_from_dict_reconstructs_context() -> None:
    """
        Verify that from_dict correctly reconstructs a TraceContext
        from a dictionary.
    """
    data = {
        "trace_id": "a" * 32,
        "span_id": "b" * 16,
        "parent_span_id": "c" * 16,
        "trace_flags": 1
    }
    ctx = TraceContext.from_dict(data)

    assert ctx.trace_id == "a" * 32, "Reconstructed trace_id should match"
    assert ctx.span_id == "b" * 16, "Reconstructed span_id should match"
    assert ctx.parent_span_id == "c" * 16, "Reconstructed parent_span_id should match"
    assert ctx.trace_flags == 1, "Reconstructed trace_flags should match"
    return


def test_dict_round_trip() -> None:
    """
        Verify that as_dict followed by from_dict produces an equivalent
        TraceContext.
    """
    original = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16,
        parent_span_id="c" * 16,
        trace_flags=1
    )
    data = original.as_dict()
    restored = TraceContext.from_dict(data)

    assert restored.trace_id == original.trace_id, "Round-trip trace_id should match"
    assert restored.span_id == original.span_id, "Round-trip span_id should match"
    assert restored.parent_span_id == original.parent_span_id, \
        "Round-trip parent_span_id should match"
    assert restored.trace_flags == original.trace_flags, \
        "Round-trip trace_flags should match"
    return


def test_to_json_returns_valid_json_string() -> None:
    """
        Verify that to_json returns a valid JSON string.
    """
    ctx = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16,
        trace_flags=0
    )
    json_str = ctx.to_json()
    data = json.loads(json_str)

    assert isinstance(data, dict), "to_json should produce a valid JSON object"
    assert data["trace_id"] == "a" * 32, "JSON trace_id should match"
    return


def test_from_json_reconstructs_context() -> None:
    """
        Verify that from_json correctly reconstructs a TraceContext
        from a JSON string.
    """
    json_str = json.dumps({
        "trace_id": "a" * 32,
        "span_id": "b" * 16,
        "parent_span_id": "c" * 16,
        "trace_flags": 1
    })
    ctx = TraceContext.from_json(json_str)

    assert ctx.trace_id == "a" * 32, "Reconstructed trace_id should match"
    assert ctx.span_id == "b" * 16, "Reconstructed span_id should match"
    assert ctx.parent_span_id == "c" * 16, "Reconstructed parent_span_id should match"
    assert ctx.trace_flags == 1, "Reconstructed trace_flags should match"
    return


def test_json_round_trip() -> None:
    """
        Verify that to_json followed by from_json produces an equivalent
        TraceContext.
    """
    original = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16,
        parent_span_id="c" * 16,
        trace_flags=1
    )
    json_str = original.to_json()
    restored = TraceContext.from_json(json_str)

    assert restored.trace_id == original.trace_id, "Round-trip trace_id should match"
    assert restored.span_id == original.span_id, "Round-trip span_id should match"
    assert restored.parent_span_id == original.parent_span_id, \
        "Round-trip parent_span_id should match"
    assert restored.trace_flags == original.trace_flags, \
        "Round-trip trace_flags should match"
    return


def test_json_round_trip_with_none_parent() -> None:
    """
        Verify that JSON round-trip works when parent_span_id is None.
    """
    original = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    json_str = original.to_json()
    restored = TraceContext.from_json(json_str)

    assert restored.parent_span_id is None, \
        "Round-trip parent_span_id should remain None"
    return


def test_repr_contains_class_name() -> None:
    """
        Verify that __repr__ includes the class name 'TraceContext'.
    """
    ctx = TraceContext()
    repr_str = repr(ctx)

    assert "TraceContext" in repr_str, "__repr__ should include class name"
    return


def test_repr_contains_trace_id() -> None:
    """
        Verify that __repr__ includes the trace_id.
    """
    ctx = TraceContext(trace_id="a" * 32)
    repr_str = repr(ctx)

    assert "a" * 32 in repr_str, "__repr__ should include trace_id"
    return


def test_repr_contains_span_id() -> None:
    """
        Verify that __repr__ includes the span_id.
    """
    ctx = TraceContext(span_id="b" * 16)
    repr_str = repr(ctx)

    assert "b" * 16 in repr_str, "__repr__ should include span_id"
    return


def test_str_contains_trace_id() -> None:
    """
        Verify that __str__ includes the trace_id.
    """
    ctx = TraceContext(trace_id="a" * 32)
    str_val = str(ctx)

    assert "a" * 32 in str_val, "__str__ should include trace_id"
    return


def test_str_contains_span_id() -> None:
    """
        Verify that __str__ includes the span_id.
    """
    ctx = TraceContext(span_id="b" * 16)
    str_val = str(ctx)

    assert "b" * 16 in str_val, "__str__ should include span_id"
    return


def test_str_contains_parent_span_id() -> None:
    """
        Verify that __str__ includes the parent_span_id.
    """
    ctx = TraceContext(parent_span_id="c" * 16)
    str_val = str(ctx)

    assert "c" * 16 in str_val, "__str__ should include parent_span_id"
    return
