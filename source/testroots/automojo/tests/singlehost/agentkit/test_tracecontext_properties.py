"""
    Property-based tests for the automojo.agentkit.tracecontext module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 7: TraceContext auto-generates valid identifiers
    - Property 8: TraceContext JSON round-trip
    - Property 9: TraceContext traceparent round-trip
    - Property 10: TraceContext create_child_span_context preserves trace_id

    **Validates: Requirements 6.1, 6.2, 6.3, 6.5, 6.6, 6.7, 6.10, 6.12, 6.13, 6.14**
"""

import re

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.tracecontext import TraceContext


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

_parent_span_id_strategy = st.one_of(
    st.none(),
    st.text(alphabet=_hex_alphabet, min_size=16, max_size=16),
)

_hex_pattern_32 = re.compile(r"^[0-9a-f]{32}$")
_hex_pattern_16 = re.compile(r"^[0-9a-f]{16}$")


# ---------------------------------------------------------------------------
# Property 7: TraceContext auto-generates valid identifiers
# ---------------------------------------------------------------------------

@given(
    dummy=st.integers(min_value=0, max_value=10000),
    settings=settings(max_examples=50),
)
def test_tracecontext_auto_generates_valid_identifiers(dummy: int) -> None:
    """
        **Validates: Requirements 6.1, 6.2, 6.3**

        For any TraceContext created without explicit trace_id or span_id,
        the trace_id shall be a 32-character lowercase hexadecimal string
        and the span_id shall be a 16-character lowercase hexadecimal string.
    """
    context = TraceContext()

    trace_id = context.trace_id
    assert _hex_pattern_32.match(trace_id) is not None, (
        "trace_id is not a valid 32-char hex string: {!r}".format(trace_id)
    )

    span_id = context.span_id
    assert _hex_pattern_16.match(span_id) is not None, (
        "span_id is not a valid 16-char hex string: {!r}".format(span_id)
    )

    return


# ---------------------------------------------------------------------------
# Property 8: TraceContext JSON round-trip
# ---------------------------------------------------------------------------

@given(
    trace_id=_trace_id_strategy,
    span_id=_span_id_strategy,
    parent_span_id=_parent_span_id_strategy,
    trace_flags=_trace_flags_strategy,
    settings=settings(max_examples=50),
)
def test_tracecontext_json_round_trip(
    trace_id: str,
    span_id: str,
    parent_span_id: str,
    trace_flags: int,
) -> None:
    """
        **Validates: Requirements 6.10, 6.12, 6.13**

        For any valid TraceContext instance, calling to_json() and then
        from_json() shall produce a TraceContext whose trace_id, span_id,
        parent_span_id, and trace_flags are equal to the original.
    """
    original = TraceContext(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        trace_flags=trace_flags,
    )

    json_str = original.to_json()
    reconstructed = TraceContext.from_json(json_str)

    assert reconstructed.trace_id == trace_id, (
        "Round-trip trace_id mismatch: expected {!r}, got {!r}".format(
            trace_id, reconstructed.trace_id)
    )

    assert reconstructed.span_id == span_id, (
        "Round-trip span_id mismatch: expected {!r}, got {!r}".format(
            span_id, reconstructed.span_id)
    )

    assert reconstructed.parent_span_id == parent_span_id, (
        "Round-trip parent_span_id mismatch: expected {!r}, got {!r}".format(
            parent_span_id, reconstructed.parent_span_id)
    )

    assert reconstructed.trace_flags == trace_flags, (
        "Round-trip trace_flags mismatch: expected {!r}, got {!r}".format(
            trace_flags, reconstructed.trace_flags)
    )

    return


# ---------------------------------------------------------------------------
# Property 9: TraceContext traceparent round-trip
# ---------------------------------------------------------------------------

@given(
    trace_id=_trace_id_strategy,
    span_id=_span_id_strategy,
    trace_flags=_trace_flags_strategy,
    settings=settings(max_examples=50),
)
def test_tracecontext_traceparent_round_trip(
    trace_id: str,
    span_id: str,
    trace_flags: int,
) -> None:
    """
        **Validates: Requirements 6.6, 6.7, 6.14**

        For any valid TraceContext instance, calling to_traceparent() and
        then from_traceparent() shall produce a TraceContext with equivalent
        trace_id, span_id, and trace_flags.
    """
    original = TraceContext(
        trace_id=trace_id,
        span_id=span_id,
        trace_flags=trace_flags,
    )

    traceparent_str = original.to_traceparent()
    reconstructed = TraceContext.from_traceparent(traceparent_str)

    assert reconstructed.trace_id == trace_id, (
        "Traceparent round-trip trace_id mismatch: expected {!r}, got {!r}".format(
            trace_id, reconstructed.trace_id)
    )

    assert reconstructed.span_id == span_id, (
        "Traceparent round-trip span_id mismatch: expected {!r}, got {!r}".format(
            span_id, reconstructed.span_id)
    )

    assert reconstructed.trace_flags == trace_flags, (
        "Traceparent round-trip trace_flags mismatch: expected {!r}, got {!r}".format(
            trace_flags, reconstructed.trace_flags)
    )

    return


# ---------------------------------------------------------------------------
# Property 10: TraceContext create_child_span_context preserves trace_id
# ---------------------------------------------------------------------------

@given(
    trace_id=_trace_id_strategy,
    span_id=_span_id_strategy,
    parent_span_id=_parent_span_id_strategy,
    trace_flags=_trace_flags_strategy,
    settings=settings(max_examples=50),
)
def test_tracecontext_create_child_preserves_trace_id(
    trace_id: str,
    span_id: str,
    parent_span_id: str,
    trace_flags: int,
) -> None:
    """
        **Validates: Requirements 6.5**

        For any valid TraceContext instance, calling create_child_span_context()
        shall produce a new TraceContext with the same trace_id, a different
        span_id, and parent_span_id equal to the original's span_id.
    """
    original = TraceContext(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        trace_flags=trace_flags,
    )

    child = original.create_child_span_context()

    assert child.trace_id == trace_id, (
        "Child trace_id mismatch: expected {!r}, got {!r}".format(
            trace_id, child.trace_id)
    )

    assert child.span_id != span_id, (
        "Child span_id should differ from parent span_id: both are {!r}".format(
            span_id)
    )

    assert child.parent_span_id == span_id, (
        "Child parent_span_id should equal original span_id: expected {!r}, got {!r}".format(
            span_id, child.parent_span_id)
    )

    assert _hex_pattern_16.match(child.span_id) is not None, (
        "Child span_id is not a valid 16-char hex string: {!r}".format(
            child.span_id)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
