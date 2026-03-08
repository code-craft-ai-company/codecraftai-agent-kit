"""
    Property-based tests for the automojo.agentkit.tracer module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 16: Tracer span stack follows LIFO semantics
    - Property 17: Tracer child spans share parent trace_id
    - Property 34: Tracer sampling rate boundaries

    **Validates: Requirements 9.2, 9.3, 9.4, 9.5, 9.6, 30.1, 30.2, 30.3, 30.4**
"""

from typing import List

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.tracer import Tracer
from automojo.agentkit.traceexporter import TraceExporter


# ---------------------------------------------------------------------------
# Helper: RecordingExporter
# ---------------------------------------------------------------------------

class RecordingExporter(TraceExporter):
    """
        A TraceExporter that records all exported spans in a list
        for test verification.
    """

    def __init__(self) -> None:
        super().__init__()
        self.exported_spans = []
        return

    def export(self, spans: list) -> None:
        """
            Records the exported spans.

            :param spans: A list of completed TraceSpan objects.
        """
        self.exported_spans.extend(spans)
        return

    def flush(self) -> None:
        """
            No-op flush for the recording exporter.
        """
        return

    def shutdown(self) -> None:
        """
            No-op shutdown for the recording exporter.
        """
        return


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_span_name_strategy = st.text(min_size=1, max_size=20)

_span_names_strategy = st.lists(
    _span_name_strategy,
    min_size=1,
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property 16: Tracer span stack follows LIFO semantics
# ---------------------------------------------------------------------------

@given(
    span_names=_span_names_strategy,
    settings=settings(max_examples=50),
)
def test_tracer_span_stack_lifo_semantics(
    span_names: List[str],
) -> None:
    """
        **Validates: Requirements 9.2, 9.3, 9.4, 9.5, 9.6**

        For any sequence of N start_span() calls followed by N end_span()
        calls on a Tracer, the active_span after each start_span shall be
        the most recently started span, and after each end_span shall be
        the previously active span (or None when the stack is empty).
    """
    tracer = Tracer(agent_id="test-agent", sampling_rate=1.0)

    # Track all created spans in order
    created_spans = []

    # Push N spans and verify active_span after each push
    for idx, name in enumerate(span_names):
        span = tracer.start_span(name)
        created_spans.append(span)

        active = tracer.active_span
        assert active is span, (
            "After start_span({!r}), active_span should be the most "
            "recently started span (index {}), but got a different span".format(
                name, idx)
        )

    # Pop N spans and verify active_span after each pop
    for idx in range(len(span_names) - 1, -1, -1):
        # Before ending, active should be created_spans[idx]
        active_before = tracer.active_span
        assert active_before is created_spans[idx], (
            "Before end_span at index {}, active_span should be "
            "created_spans[{}]".format(idx, idx)
        )

        tracer.end_span()

        if idx > 0:
            expected_active = created_spans[idx - 1]
            actual_active = tracer.active_span
            assert actual_active is expected_active, (
                "After end_span at index {}, active_span should revert "
                "to created_spans[{}]".format(idx, idx - 1)
            )
        else:
            actual_active = tracer.active_span
            assert actual_active is None, (
                "After ending the last span, active_span should be None, "
                "but got {!r}".format(actual_active)
            )

    return


# ---------------------------------------------------------------------------
# Property 17: Tracer child spans share parent trace_id
# ---------------------------------------------------------------------------

@given(
    span_names=_span_names_strategy,
    settings=settings(max_examples=50),
)
def test_tracer_child_spans_share_parent_trace_id(
    span_names: List[str],
) -> None:
    """
        **Validates: Requirements 9.4**

        For any Tracer with nested start_span() calls, all created
        TraceSpan instances within the same trace shall share the same
        trace_id, and each child span's parent_span_id shall equal the
        parent span's span_id.
    """
    tracer = Tracer(agent_id="test-agent", sampling_rate=1.0)

    created_spans = []

    # Create nested spans
    for name in span_names:
        span = tracer.start_span(name)
        created_spans.append(span)

    # All spans must share the same trace_id
    root_trace_id = created_spans[0].trace_context.trace_id

    for idx, span in enumerate(created_spans):
        assert span.trace_context.trace_id == root_trace_id, (
            "Span at index {} has trace_id {!r}, expected {!r}".format(
                idx, span.trace_context.trace_id, root_trace_id)
        )

    # Each child span's parent_span_id must equal its parent's span_id
    for idx in range(1, len(created_spans)):
        child = created_spans[idx]
        parent = created_spans[idx - 1]

        assert child.trace_context.parent_span_id == parent.trace_context.span_id, (
            "Child span at index {} has parent_span_id {!r}, expected "
            "parent span_id {!r}".format(
                idx,
                child.trace_context.parent_span_id,
                parent.trace_context.span_id,
            )
        )

    # The root span should have no parent_span_id
    root_span = created_spans[0]
    assert root_span.trace_context.parent_span_id is None, (
        "Root span should have parent_span_id=None, got {!r}".format(
            root_span.trace_context.parent_span_id)
    )

    # Clean up the span stack
    for _ in span_names:
        tracer.end_span()

    return


# ---------------------------------------------------------------------------
# Property 34: Tracer sampling rate boundaries
# ---------------------------------------------------------------------------

@given(
    num_spans=st.integers(min_value=1, max_value=20),
    settings=settings(max_examples=50),
)
def test_tracer_sampling_rate_zero_exports_nothing(
    num_spans: int,
) -> None:
    """
        **Validates: Requirements 30.1, 30.2, 30.3**

        For any Tracer with sampling_rate=0.0, no root spans shall be
        exported.
    """
    exporter = RecordingExporter()
    tracer = Tracer(agent_id="test-agent", sampling_rate=0.0)
    tracer.register_exporter(exporter)

    for idx in range(num_spans):
        tracer.start_span("span-{}".format(idx))
        tracer.end_span()

    assert len(exporter.exported_spans) == 0, (
        "With sampling_rate=0.0, no spans should be exported, "
        "but {} were exported".format(len(exporter.exported_spans))
    )

    return


@given(
    num_spans=st.integers(min_value=1, max_value=20),
    settings=settings(max_examples=50),
)
def test_tracer_sampling_rate_one_exports_all(
    num_spans: int,
) -> None:
    """
        **Validates: Requirements 30.1, 30.4**

        For any Tracer with sampling_rate=1.0, all root spans shall be
        exported.
    """
    exporter = RecordingExporter()
    tracer = Tracer(agent_id="test-agent", sampling_rate=1.0)
    tracer.register_exporter(exporter)

    for idx in range(num_spans):
        tracer.start_span("span-{}".format(idx))
        tracer.end_span()

    assert len(exporter.exported_spans) == num_spans, (
        "With sampling_rate=1.0, all {} spans should be exported, "
        "but {} were exported".format(num_spans, len(exporter.exported_spans))
    )

    return


@given(
    sampling_rate=st.floats(min_value=0.01, max_value=0.99),
    settings=settings(max_examples=20),
)
def test_tracer_sampling_rate_approximate(
    sampling_rate: float,
) -> None:
    """
        **Validates: Requirements 30.2, 30.3, 30.4**

        For any sampling_rate between 0.0 and 1.0, the proportion of
        exported root spans over many samples shall approximate the
        sampling rate within a tolerance.
    """
    num_traces = 500
    exporter = RecordingExporter()
    tracer = Tracer(agent_id="test-agent", sampling_rate=sampling_rate)
    tracer.register_exporter(exporter)

    for idx in range(num_traces):
        tracer.start_span("span-{}".format(idx))
        tracer.end_span()

    exported_count = len(exporter.exported_spans)
    actual_rate = exported_count / num_traces

    # Allow a tolerance of 0.15 for statistical variation
    tolerance = 0.15
    lower_bound = max(0.0, sampling_rate - tolerance)
    upper_bound = min(1.0, sampling_rate + tolerance)

    assert lower_bound <= actual_rate <= upper_bound, (
        "With sampling_rate={}, expected export rate between {} and {}, "
        "but got {} ({}/{} spans exported)".format(
            sampling_rate, lower_bound, upper_bound,
            actual_rate, exported_count, num_traces,
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
