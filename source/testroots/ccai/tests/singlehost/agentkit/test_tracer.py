"""
    Unit tests for the ccai.agentkit.tracer module.

    Tests the Tracer class covering start_span/end_span stack behavior,
    context manager, exporter delivery, sampling at 0.0/1.0/0.5, and
    nested spans sharing trace_id.

    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10,
                  30.1, 30.2, 30.3, 30.4, 30.5
"""

import random

from ccai.agentkit.tracer import Tracer
from ccai.agentkit.tracecontext import TraceContext
from ccai.agentkit.traceexporter import TraceExporter
from ccai.testbase.mocking import Mock, create_module_patch


# ---- Helper Functions ----


def _create_mock_exporter():
    """
        Creates a mock TraceExporter that records exported spans.

        :returns: A tuple of (mock_exporter, exported_spans_list).
    """
    exported = []

    class RecordingExporter(TraceExporter):
        def export(self, spans: list) -> None:
            exported.extend(spans)
            return

        def flush(self) -> None:
            return

        def shutdown(self) -> None:
            return

    exporter = RecordingExporter()
    return exporter, exported


# ---- Root span creation ----


def test_start_span_creates_root_span_when_stack_empty():
    """
        Verify that start_span creates a root span when no active
        span exists on the stack.
    """
    tracer = Tracer(agent_id="agent-001")
    span = tracer.start_span("root-op")

    assert span is not None, "start_span should return a TraceSpan"
    assert span.name == "root-op", "span name should match"
    assert span.trace_context.parent_span_id is None, "root span should have no parent_span_id"

    tracer.end_span()
    return


def test_start_span_creates_child_span_when_stack_has_active():
    """
        Verify that start_span creates a child span when an active
        span exists on the stack.
    """
    tracer = Tracer(agent_id="agent-001")
    parent = tracer.start_span("parent-op")
    child = tracer.start_span("child-op")

    assert child.name == "child-op", "child span name should match"
    assert child.trace_context.parent_span_id == parent.trace_context.span_id, \
        "child parent_span_id should equal parent span_id"

    tracer.end_span()
    tracer.end_span()
    return


# ---- active_span property ----


def test_active_span_returns_none_when_stack_empty():
    """
        Verify that active_span returns None when no span is active.
    """
    tracer = Tracer(agent_id="agent-001")

    assert tracer.active_span is None, "active_span should be None when stack is empty"
    return


def test_active_span_returns_top_of_stack():
    """
        Verify that active_span returns the most recently started span.
    """
    tracer = Tracer(agent_id="agent-001")
    tracer.start_span("first")
    second = tracer.start_span("second")

    assert tracer.active_span is second, "active_span should be the top of the stack"

    tracer.end_span()
    tracer.end_span()
    return


# ---- end_span behavior ----


def test_end_span_pops_span_from_stack():
    """
        Verify that end_span removes the top span from the stack.
    """
    tracer = Tracer(agent_id="agent-001")
    first = tracer.start_span("first")
    tracer.start_span("second")

    tracer.end_span()

    assert tracer.active_span is first, "after end_span, active should be the first span"

    tracer.end_span()
    return


def test_end_span_calls_span_end():
    """
        Verify that end_span ends the popped span (sets end_time).
    """
    tracer = Tracer(agent_id="agent-001")
    span = tracer.start_span("op")

    tracer.end_span()

    assert span.end_time is not None, "span should have end_time set after end_span"
    return


def test_end_span_delivers_span_to_registered_exporters():
    """
        Verify that end_span delivers the completed span to all
        registered exporters.
    """
    tracer = Tracer(agent_id="agent-001", sampling_rate=1.0)
    exporter, exported = _create_mock_exporter()
    tracer.register_exporter(exporter)

    tracer.start_span("op")
    tracer.end_span()

    assert len(exported) == 1, "exporter should receive one span"
    assert exported[0].name == "op", "exported span name should match"
    return


# ---- Nested spans share trace_id ----


def test_nested_spans_share_trace_id():
    """
        Verify that nested spans share the same trace_id.
    """
    tracer = Tracer(agent_id="agent-001")
    parent = tracer.start_span("parent")
    child = tracer.start_span("child")
    grandchild = tracer.start_span("grandchild")

    parent_trace_id = parent.trace_context.trace_id
    child_trace_id = child.trace_context.trace_id
    grandchild_trace_id = grandchild.trace_context.trace_id

    assert child_trace_id == parent_trace_id, "child should share parent trace_id"
    assert grandchild_trace_id == parent_trace_id, "grandchild should share parent trace_id"

    tracer.end_span()
    tracer.end_span()
    tracer.end_span()
    return


def test_child_span_parent_span_id_equals_parent_span_id():
    """
        Verify that a child span's parent_span_id equals the parent's
        span_id.
    """
    tracer = Tracer(agent_id="agent-001")
    parent = tracer.start_span("parent")
    child = tracer.start_span("child")

    assert child.trace_context.parent_span_id == parent.trace_context.span_id, \
        "child parent_span_id should equal parent span_id"

    tracer.end_span()
    tracer.end_span()
    return


# ---- Context manager ----


def test_context_manager_starts_and_ends_span():
    """
        Verify that the span context manager starts a span on entry
        and ends it on exit.
    """
    tracer = Tracer(agent_id="agent-001")

    with tracer.span("ctx-op") as span:
        assert tracer.active_span is span, "span should be active inside context"
        assert span.name == "ctx-op", "span name should match"

    assert tracer.active_span is None, "span should be ended after context exit"
    assert span.end_time is not None, "span should have end_time after context exit"
    return


def test_context_manager_sets_error_status_on_exception():
    """
        Verify that the span context manager sets error status when
        an exception occurs.
    """
    tracer = Tracer(agent_id="agent-001")

    raised = False
    try:
        with tracer.span("error-op") as span:
            raise ValueError("test error")
    except ValueError:
        raised = True

    assert raised is True, "exception should be re-raised"
    assert span.status == "error", "span status should be 'error' after exception"
    return


def test_context_manager_reraises_exception():
    """
        Verify that the span context manager re-raises the exception
        after setting error status.
    """
    tracer = Tracer(agent_id="agent-001")

    caught_message = None
    try:
        with tracer.span("reraise-op"):
            raise RuntimeError("specific error")
    except RuntimeError as exc:
        caught_message = str(exc)

    assert caught_message == "specific error", "original exception should be re-raised"
    return


# ---- Sampling ----


def test_sampling_rate_1_0_exports_all_spans():
    """
        Verify that sampling rate 1.0 exports all spans.
    """
    tracer = Tracer(agent_id="agent-001", sampling_rate=1.0)
    exporter, exported = _create_mock_exporter()
    tracer.register_exporter(exporter)

    tracer.start_span("op-1")
    tracer.end_span()
    tracer.start_span("op-2")
    tracer.end_span()
    tracer.start_span("op-3")
    tracer.end_span()

    assert len(exported) == 3, "all spans should be exported at rate 1.0"
    return


def test_sampling_rate_0_0_exports_no_spans():
    """
        Verify that sampling rate 0.0 exports no spans.
    """
    tracer = Tracer(agent_id="agent-001", sampling_rate=0.0)
    exporter, exported = _create_mock_exporter()
    tracer.register_exporter(exporter)

    tracer.start_span("op-1")
    tracer.end_span()
    tracer.start_span("op-2")
    tracer.end_span()
    tracer.start_span("op-3")
    tracer.end_span()

    assert len(exported) == 0, "no spans should be exported at rate 0.0"
    return


def test_sampling_rate_0_5_controlled():
    """
        Verify that sampling rate 0.5 samples based on random value.
        Patches random.random to return a controlled value.
    """
    tracer = Tracer(agent_id="agent-001", sampling_rate=0.5)
    exporter, exported = _create_mock_exporter()
    tracer.register_exporter(exporter)

    # Patch random.random to return 0.3 (< 0.5, so sampled)
    patch = create_module_patch(random, "random")
    mock_random = patch.activate()
    mock_random.configure(return_value=0.3)

    try:
        tracer.start_span("sampled-op")
        tracer.end_span()
    finally:
        patch.deactivate()

    assert len(exported) == 1, "span should be exported when random < sampling_rate"

    # Patch random.random to return 0.7 (>= 0.5, so not sampled)
    patch2 = create_module_patch(random, "random")
    mock_random2 = patch2.activate()
    mock_random2.configure(return_value=0.7)

    try:
        tracer.start_span("unsampled-op")
        tracer.end_span()
    finally:
        patch2.deactivate()

    assert len(exported) == 1, "span should not be exported when random >= sampling_rate"
    return


# ---- register_exporter ----


def test_register_exporter_adds_exporter():
    """
        Verify that register_exporter adds the exporter to the list.
    """
    tracer = Tracer(agent_id="agent-001")
    exporter, _ = _create_mock_exporter()

    tracer.register_exporter(exporter)

    assert exporter in tracer._exporters, "exporter should be in the exporters list"
    return


def test_multiple_exporters_all_receive_spans():
    """
        Verify that all registered exporters receive completed spans.
    """
    tracer = Tracer(agent_id="agent-001", sampling_rate=1.0)
    exporter1, exported1 = _create_mock_exporter()
    exporter2, exported2 = _create_mock_exporter()
    tracer.register_exporter(exporter1)
    tracer.register_exporter(exporter2)

    tracer.start_span("multi-op")
    tracer.end_span()

    assert len(exported1) == 1, "first exporter should receive the span"
    assert len(exported2) == 1, "second exporter should receive the span"
    return


# ---- Root trace context ----


def test_root_span_uses_provided_trace_context():
    """
        Verify that the root span uses the provided trace_context
        and that it is consumed (used only once).
    """
    provided_ctx = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16
    )
    tracer = Tracer(agent_id="agent-001", trace_context=provided_ctx)

    first_span = tracer.start_span("first-root")
    assert first_span.trace_context.trace_id == "a" * 32, \
        "first root span should use provided trace_id"

    tracer.end_span()

    # Second root span should NOT use the provided context (consumed)
    second_span = tracer.start_span("second-root")
    assert second_span.trace_context.trace_id != "a" * 32, \
        "second root span should use a new trace_id (provided context consumed)"

    tracer.end_span()
    return


# ---- __repr__ and __str__ ----


def test_repr_includes_agent_id():
    """
        Verify that __repr__ includes the agent_id.
    """
    tracer = Tracer(agent_id="agent-repr-001")
    repr_str = repr(tracer)

    assert "agent-repr-001" in repr_str, "repr should contain agent_id"
    return


def test_str_includes_agent_id():
    """
        Verify that __str__ includes the agent_id.
    """
    tracer = Tracer(agent_id="agent-str-001")
    str_val = str(tracer)

    assert "agent-str-001" in str_val, "str should contain agent_id"
    return
