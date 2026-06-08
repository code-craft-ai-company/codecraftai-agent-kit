"""
    Defines the Tracer class that creates and manages TraceSpan objects
    for an Agent.

    The Tracer maintains an active span stack, supports nested span
    creation for hierarchical tracing, and delivers completed spans
    to registered TraceExporter instances. It implements probabilistic
    sampling at the root span level, where non-sampled spans propagate
    context but are not exported.
"""

import contextlib
import random

from typing import Optional

from ccai.agentkit.tracecontext import TraceContext
from ccai.agentkit.traceexporter import TraceExporter
from ccai.agentkit.tracespan import TraceSpan


class Tracer:
    """
        A component that creates and manages TraceSpan objects for an
        Agent.

        The Tracer maintains a stack of active spans. When start_span
        is called with no active span, a root span is created using
        the root trace context if provided, or a new TraceContext
        otherwise. When start_span is called with an active span, a
        child span is created using the active span's
        create_child_span_context method.

        Probabilistic sampling is applied at the root span level. When
        a root span is not sampled, the span and all its children
        propagate context but are not delivered to exporters.

        :param agent_id: The agent identifier string.
        :param trace_context: Optional root TraceContext for establishing
            the root trace context.
        :param sampling_rate: The sampling rate as a float between 0.0
            and 1.0 inclusive, defaulting to 1.0 (sample all spans).
    """

    def __init__(self, agent_id: str, trace_context: TraceContext = None,
                 sampling_rate: float = 1.0) -> None:

        self._agent_id = agent_id
        self._root_trace_context = trace_context
        self._sampling_rate = sampling_rate
        self._active_span_stack = []
        self._exporters = []
        self._sampled_traces = {}

        return

    @property
    def active_span(self) -> Optional[TraceSpan]:
        """
            The current active TraceSpan at the top of the span stack,
            or None when no span is active.

            :returns: The active TraceSpan instance, or None.
        """
        if len(self._active_span_stack) > 0:
            return self._active_span_stack[-1]

        return None

    @property
    def sampling_rate(self) -> float:
        """
            The configured sampling rate as a float between 0.0 and 1.0
            inclusive.

            :returns: The sampling rate float.
        """
        return self._sampling_rate

    def start_span(self, name: str, attributes: dict = None) -> TraceSpan:
        """
            Creates a new TraceSpan and pushes it onto the active span
            stack.

            When no active span exists, a root span is created. If a
            root trace context was provided at construction, it is used
            for the root span. Otherwise, a new TraceContext is generated.
            A probabilistic sampling decision is made for root spans
            using the configured sampling rate.

            When an active span exists, a child span is created using
            the active span's trace context create_child_span_context
            method. Child spans inherit the sampling decision of their
            root span.

            :param name: The name string identifying the new span.
            :param attributes: Optional dictionary of key-value attributes
                for the new span.

            :returns: The newly created TraceSpan instance.
        """
        if len(self._active_span_stack) == 0:
            # Root span creation
            if self._root_trace_context is not None:
                trace_context = self._root_trace_context
                self._root_trace_context = None
            else:
                trace_context = TraceContext()

            # Make sampling decision for this trace
            trace_id = trace_context.trace_id
            is_sampled = random.random() < self._sampling_rate
            self._sampled_traces[trace_id] = is_sampled
        else:
            # Child span creation
            parent_span = self._active_span_stack[-1]
            trace_context = parent_span.trace_context.create_child_span_context()

        span = TraceSpan(
            name=name,
            trace_context=trace_context,
            attributes=attributes
        )
        self._active_span_stack.append(span)

        return span

    def end_span(self) -> None:
        """
            Pops the current active span from the stack, ends it, and
            delivers it to all registered exporters if the trace is
            sampled.

            If the span's trace is sampled, the completed span is
            delivered to each registered TraceExporter via the export
            method. If the trace is not sampled, the span is ended but
            not exported.

            When the last span for a trace is ended (stack becomes empty
            or next span has a different trace_id), the sampling decision
            for that trace is cleaned up.
        """
        if len(self._active_span_stack) == 0:
            return

        span = self._active_span_stack.pop()
        span.end()

        trace_id = span.trace_context.trace_id
        is_sampled = self._sampled_traces.get(trace_id, True)

        if is_sampled:
            for exporter in self._exporters:
                exporter.export([span])

        # Clean up sampling decision when no more spans for this trace
        if len(self._active_span_stack) == 0:
            self._sampled_traces.pop(trace_id, None)
        else:
            remaining_trace_id = self._active_span_stack[-1].trace_context.trace_id
            if remaining_trace_id != trace_id:
                self._sampled_traces.pop(trace_id, None)

        return

    @contextlib.contextmanager
    def span(self, name: str, attributes: dict = None):
        """
            A context manager that starts a span on entry and ends
            the span on exit.

            If an exception occurs within the context, the span's
            status is set to "error" with the exception message as
            the description before the span is ended. The exception
            is then re-raised.

            :param name: The name string identifying the span.
            :param attributes: Optional dictionary of key-value attributes
                for the span.

            :yields: The newly created TraceSpan instance.
        """
        span = self.start_span(name=name, attributes=attributes)

        try:
            yield span
        except Exception as exc:
            span.set_status("error", description=str(exc))
            raise
        finally:
            self.end_span()

    def register_exporter(self, exporter: TraceExporter) -> None:
        """
            Registers a TraceExporter instance to receive completed
            spans.

            :param exporter: The TraceExporter instance to register.
        """
        self._exporters.append(exporter)

        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, agent identifier, and whether an active span
            exists.

            :returns: A repr string for debugging.
        """
        has_active = self.active_span is not None
        repr_str = "Tracer(agent_id={!r}, has_active_span={})".format(
            self._agent_id, has_active
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent
            identifier and active span name.

            :returns: A human-readable string.
        """
        active = self.active_span
        if active is not None:
            active_name = active.name
        else:
            active_name = None

        str_val = "Tracer: agent_id={}, active_span={}".format(
            self._agent_id, active_name
        )
        return str_val
