"""
    Defines the TraceSpan class representing a mutable unit of work
    within a distributed trace.

    TraceSpan objects have a name, a TraceContext, a start timestamp,
    an optional end timestamp, a status, an attributes dictionary,
    and a list of TraceEvent objects. The span supports mutation of
    status and attributes during its lifetime, and provides methods
    for adding events and ending the span.
"""

import json

from datetime import datetime
from typing import Optional

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.tracecontext import TraceContext
from automojo.agentkit.traceevent import TraceEvent


class TraceSpan:
    """
        A mutable object representing a single unit of work within a
        distributed trace.

        Contains a name, a TraceContext, a start timestamp, an optional
        end timestamp, a status string, an attributes dictionary, and
        a list of TraceEvent objects. The status must be one of the
        values in VALID_STATUSES.

        :param name: The name string identifying this span.
        :param trace_context: The TraceContext for this span.
        :param start_time: Optional start timestamp. Defaults to the
            current UTC time if not provided.
        :param status: The initial status string, defaults to "unset".
        :param attributes: Optional dictionary of key-value attributes.
    """

    VALID_STATUSES = ("unset", "ok", "error")

    def __init__(self, name: str, trace_context: TraceContext,
                 start_time: datetime = None, status: str = "unset",
                 attributes: dict = None) -> None:

        self._name = name
        self._trace_context = trace_context

        if start_time is not None:
            self._start_time = start_time
        else:
            self._start_time = datetime.utcnow()

        self._end_time = None
        self._status = status
        self._status_description = None

        if attributes is not None:
            self._attributes = dict(attributes)
        else:
            self._attributes = {}

        self._events = []

        return

    @property
    def name(self) -> str:
        """
            The name string identifying this span.

            :returns: The span name string.
        """
        return self._name

    @property
    def trace_context(self) -> TraceContext:
        """
            The TraceContext for this span.

            :returns: The TraceContext instance.
        """
        return self._trace_context

    @property
    def start_time(self) -> datetime:
        """
            The start timestamp for this span.

            :returns: The datetime start timestamp.
        """
        return self._start_time

    @property
    def end_time(self) -> Optional[datetime]:
        """
            The optional end timestamp for this span.

            :returns: The datetime end timestamp, or None if the span
                has not been ended.
        """
        return self._end_time

    @property
    def status(self) -> str:
        """
            The current status string for this span.

            :returns: The status string, one of "unset", "ok", or "error".
        """
        return self._status

    @property
    def status_description(self) -> Optional[str]:
        """
            The optional status description string.

            :returns: The status description string, or None.
        """
        return self._status_description

    @property
    def attributes(self) -> dict:
        """
            A copy of the attributes dictionary of key-value pairs
            for this span.

            :returns: A dictionary copy of the span attributes.
        """
        result = dict(self._attributes)
        return result

    @property
    def events(self) -> list:
        """
            A copy of the list of TraceEvent objects for this span.

            :returns: A list copy of the span events.
        """
        result = list(self._events)
        return result

    @property
    def duration(self) -> Optional[float]:
        """
            The elapsed time in seconds between the start and end
            timestamps, or None when the span has not been ended.

            :returns: The duration in seconds as a float, or None.
        """
        if self._end_time is None:
            return None

        elapsed = (self._end_time - self._start_time).total_seconds()
        return elapsed

    def set_status(self, status: str, description: str = None) -> None:
        """
            Updates the span status to the given value.

            The status must be one of the values in VALID_STATUSES.
            An optional description string provides additional context
            for the status.

            :param status: The new status string.
            :param description: Optional description string for the status.

            :raises SemanticError: If the status value is not valid.
        """
        if status not in self.VALID_STATUSES:
            raise SemanticError(
                "Invalid status value: {!r}. Valid values are: {}".format(
                    status, ", ".join(self.VALID_STATUSES)
                )
            )

        self._status = status
        self._status_description = description

        return

    def set_attribute(self, key: str, value) -> None:
        """
            Adds a key-value pair to the span attributes dictionary.

            :param key: The attribute key string.
            :param value: The attribute value.
        """
        self._attributes[key] = value

        return

    def add_event(self, name: str, attributes: dict = None) -> None:
        """
            Appends a TraceEvent with the current timestamp to the
            span's event list.

            :param name: The event name string.
            :param attributes: Optional dictionary of key-value attributes
                for the event.
        """
        event = TraceEvent(
            name=name,
            timestamp=datetime.utcnow(),
            attributes=attributes
        )
        self._events.append(event)

        return

    def end(self) -> None:
        """
            Sets the end timestamp to the current UTC time and marks
            the span as completed.

            :raises SemanticError: If the span has already been ended.
        """
        if self._end_time is not None:
            raise SemanticError(
                "Span {!r} has already been ended.".format(self._name)
            )

        self._end_time = datetime.utcnow()

        return

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the span fields
            including events.

            Timestamps are serialized as ISO format strings. The
            trace_context is serialized using its own as_dict method.
            Events are serialized as a list of dictionaries.

            :returns: A dictionary containing all span fields.
        """
        end_time_val = None
        if self._end_time is not None:
            end_time_val = self._end_time.isoformat()

        events_list = []
        for event in self._events:
            events_list.append(event.as_dict())

        result = {
            "name": self._name,
            "trace_context": self._trace_context.as_dict(),
            "start_time": self._start_time.isoformat(),
            "end_time": end_time_val,
            "status": self._status,
            "status_description": self._status_description,
            "attributes": dict(self._attributes),
            "events": events_list
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the span fields.

            :returns: A JSON string containing all span fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "TraceSpan":
        """
            Constructs a TraceSpan from a dictionary.

            Timestamps are expected to be ISO format strings and are
            parsed back into datetime objects. The trace_context is
            reconstructed using TraceContext.from_dict. Events are
            reconstructed using TraceEvent.from_dict.

            :param data: A dictionary containing span fields.

            :returns: A TraceSpan instance reconstructed from
                the dictionary.
        """
        name = data["name"]
        trace_context = TraceContext.from_dict(data["trace_context"])
        start_time = datetime.fromisoformat(data["start_time"])
        status = data.get("status", "unset")
        attributes = data.get("attributes", None)

        span = cls(
            name=name,
            trace_context=trace_context,
            start_time=start_time,
            status=status,
            attributes=attributes
        )

        end_time_val = data.get("end_time", None)
        if end_time_val is not None:
            span._end_time = datetime.fromisoformat(end_time_val)

        status_description = data.get("status_description", None)
        span._status_description = status_description

        events_data = data.get("events", [])
        for event_data in events_data:
            event = TraceEvent.from_dict(event_data)
            span._events.append(event)

        return span

    @classmethod
    def from_json(cls, json_str: str) -> "TraceSpan":
        """
            Deserializes a JSON string into a TraceSpan instance.

            :param json_str: A JSON string containing span fields.

            :returns: A TraceSpan instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        span = cls.from_dict(data)
        return span

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            name, trace identifier, span identifier, and status.

            :returns: A repr string for debugging.
        """
        repr_str = "TraceSpan(name={!r}, trace_id={!r}, span_id={!r}, status={!r})".format(
            self._name, self._trace_context.trace_id,
            self._trace_context.span_id, self._status
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the name, status,
            and duration.

            :returns: A human-readable string.
        """
        duration_val = self.duration
        str_val = "TraceSpan: name={}, status={}, duration={}".format(
            self._name, self._status, duration_val
        )
        return str_val
