"""
    Defines the TraceContext class representing an immutable distributed
    tracing context for a single operation, compatible with the W3C
    Trace Context specification.

    TraceContext contains a trace identifier, a span identifier, an
    optional parent span identifier, and trace flags. It supports
    creation of child span contexts, serialization to and from JSON
    and dictionary representations, and conversion to and from the
    W3C traceparent header format.
"""

import json
import os

from typing import Optional

from ccai.agentkit.errors import SemanticError


class TraceContext:
    """
        An immutable object representing the distributed tracing context
        for a single operation, compatible with the W3C Trace Context
        specification.

        Contains a trace identifier as a 32-character lowercase hexadecimal
        string, a span identifier as a 16-character lowercase hexadecimal
        string, an optional parent span identifier, and trace flags as
        an integer.

        :param trace_id: Optional trace identifier string. Auto-generates
            a 32-character hex string if not provided.
        :param span_id: Optional span identifier string. Auto-generates
            a 16-character hex string if not provided.
        :param parent_span_id: Optional parent span identifier string.
        :param trace_flags: Trace flags integer, defaults to 0.
    """

    def __init__(self, trace_id: str = None, span_id: str = None,
                 parent_span_id: str = None, trace_flags: int = 0) -> None:

        if trace_id is not None:
            self._trace_id = trace_id
        else:
            self._trace_id = os.urandom(16).hex()

        if span_id is not None:
            self._span_id = span_id
        else:
            self._span_id = os.urandom(8).hex()

        self._parent_span_id = parent_span_id
        self._trace_flags = trace_flags

        return

    @property
    def trace_id(self) -> str:
        """
            The trace identifier as a 32-character lowercase hexadecimal
            string.

            :returns: The trace identifier string.
        """
        return self._trace_id

    @property
    def span_id(self) -> str:
        """
            The span identifier as a 16-character lowercase hexadecimal
            string.

            :returns: The span identifier string.
        """
        return self._span_id

    @property
    def parent_span_id(self) -> Optional[str]:
        """
            The optional parent span identifier as a 16-character lowercase
            hexadecimal string.

            :returns: The parent span identifier string, or None.
        """
        return self._parent_span_id

    @property
    def trace_flags(self) -> int:
        """
            The trace flags integer.

            :returns: The trace flags value.
        """
        return self._trace_flags

    def create_child_span_context(self) -> "TraceContext":
        """
            Creates a new TraceContext with the same trace identifier,
            a new auto-generated span identifier, and the current span
            identifier set as the parent span identifier.

            :returns: A new TraceContext instance representing a child
                span within the same trace.
        """
        child = TraceContext(
            trace_id=self._trace_id,
            parent_span_id=self._span_id,
            trace_flags=self._trace_flags
        )
        return child

    def to_traceparent(self) -> str:
        """
            Returns a W3C traceparent header string in the format
            "00-{trace_id}-{span_id}-{trace_flags:02x}".

            :returns: A W3C traceparent header string.
        """
        traceparent = "00-{}-{}-{:02x}".format(
            self._trace_id, self._span_id, self._trace_flags
        )
        return traceparent

    @classmethod
    def from_traceparent(cls, traceparent: str) -> "TraceContext":
        """
            Parses a W3C traceparent header string and returns a
            TraceContext instance.

            The traceparent string must be in the format
            "00-{trace_id}-{span_id}-{trace_flags}" where trace_id
            is a 32-character hex string, span_id is a 16-character
            hex string, and trace_flags is a 2-character hex string.

            :param traceparent: A W3C traceparent header string.

            :returns: A TraceContext instance parsed from the traceparent
                string.

            :raises SemanticError: If the traceparent string is malformed.
        """
        parts = traceparent.split("-")

        if len(parts) != 4:
            raise SemanticError(
                "Malformed traceparent string: expected 4 parts separated by '-', got {}: {!r}".format(
                    len(parts), traceparent
                )
            )

        version = parts[0]
        trace_id = parts[1]
        span_id = parts[2]
        flags_str = parts[3]

        if len(trace_id) != 32:
            raise SemanticError(
                "Malformed traceparent string: trace_id must be 32 hex characters, got {}: {!r}".format(
                    len(trace_id), traceparent
                )
            )

        try:
            int(trace_id, 16)
        except ValueError:
            raise SemanticError(
                "Malformed traceparent string: trace_id contains non-hex characters: {!r}".format(
                    traceparent
                )
            )

        if len(span_id) != 16:
            raise SemanticError(
                "Malformed traceparent string: span_id must be 16 hex characters, got {}: {!r}".format(
                    len(span_id), traceparent
                )
            )

        try:
            int(span_id, 16)
        except ValueError:
            raise SemanticError(
                "Malformed traceparent string: span_id contains non-hex characters: {!r}".format(
                    traceparent
                )
            )

        if len(flags_str) != 2:
            raise SemanticError(
                "Malformed traceparent string: trace_flags must be 2 hex characters, got {}: {!r}".format(
                    len(flags_str), traceparent
                )
            )

        try:
            trace_flags = int(flags_str, 16)
        except ValueError:
            raise SemanticError(
                "Malformed traceparent string: trace_flags contains non-hex characters: {!r}".format(
                    traceparent
                )
            )

        context = cls(
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=trace_flags
        )
        return context

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the context fields.

            :returns: A dictionary containing trace_id, span_id,
                parent_span_id, and trace_flags.
        """
        result = {
            "trace_id": self._trace_id,
            "span_id": self._span_id,
            "parent_span_id": self._parent_span_id,
            "trace_flags": self._trace_flags
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the context fields.

            :returns: A JSON string containing all context fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "TraceContext":
        """
            Constructs a TraceContext from a dictionary.

            :param data: A dictionary containing trace_id, span_id,
                and optionally parent_span_id and trace_flags.

            :returns: A TraceContext instance reconstructed from
                the dictionary.
        """
        trace_id = data["trace_id"]
        span_id = data["span_id"]
        parent_span_id = data.get("parent_span_id", None)
        trace_flags = data.get("trace_flags", 0)

        context = cls(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            trace_flags=trace_flags
        )
        return context

    @classmethod
    def from_json(cls, json_str: str) -> "TraceContext":
        """
            Deserializes a JSON string into a TraceContext instance.

            :param json_str: A JSON string containing context fields.

            :returns: A TraceContext instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        context = cls.from_dict(data)
        return context

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            trace identifier, and span identifier.

            :returns: A repr string for debugging.
        """
        repr_str = "TraceContext(trace_id={!r}, span_id={!r})".format(
            self._trace_id, self._span_id
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the trace identifier,
            span identifier, and parent span identifier.

            :returns: A human-readable string.
        """
        str_val = "TraceContext: trace_id={}, span_id={}, parent_span_id={}".format(
            self._trace_id, self._span_id, self._parent_span_id
        )
        return str_val
