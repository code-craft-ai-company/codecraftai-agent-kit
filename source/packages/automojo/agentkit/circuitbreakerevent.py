"""
    Defines the CircuitBreakerEvent class representing a state transition
    in a CircuitBreaker in the Error Handling & Resilience feature.
"""

import json

from datetime import datetime

from automojo.agentkit.circuitbreakerstate import CircuitBreakerState


class CircuitBreakerEvent:
    """
        Immutable object representing a state transition or significant event
        in a CircuitBreaker.

        :param name: The circuit breaker name.
        :param previous_state: The state before the transition.
        :param new_state: The state after the transition.
        :param reason: The reason for the transition.
        :param timestamp: The datetime of the event. Defaults to UTC now.
    """

    def __init__(self, name: str, previous_state: CircuitBreakerState,
                 new_state: CircuitBreakerState, reason: str,
                 timestamp: datetime = None) -> None:
        self._name = name
        self._previous_state = previous_state
        self._new_state = new_state
        self._reason = reason
        self._timestamp = timestamp if timestamp is not None else datetime.utcnow()
        return

    @property
    def name(self) -> str:
        """
            The circuit breaker name.

            :returns: The name string.
        """
        return self._name

    @property
    def previous_state(self) -> CircuitBreakerState:
        """
            The state before the transition.

            :returns: The previous CircuitBreakerState.
        """
        return self._previous_state

    @property
    def new_state(self) -> CircuitBreakerState:
        """
            The state after the transition.

            :returns: The new CircuitBreakerState.
        """
        return self._new_state

    @property
    def reason(self) -> str:
        """
            The reason for the transition.

            :returns: The reason string.
        """
        return self._reason

    @property
    def timestamp(self) -> datetime:
        """
            The datetime of the event.

            :returns: The timestamp as a datetime object.
        """
        return self._timestamp

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the event fields.

            :returns: A dictionary of event fields.
        """
        result = {
            "name": self._name,
            "previous_state": self._previous_state.value,
            "new_state": self._new_state.value,
            "reason": self._reason,
            "timestamp": self._timestamp.isoformat()
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the event fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerEvent":
        """
            Constructs a CircuitBreakerEvent from a dictionary.

            :param data: Dictionary containing event fields.

            :returns: A CircuitBreakerEvent instance.
        """
        event = cls(
            name=data["name"],
            previous_state=CircuitBreakerState.from_string(data["previous_state"]),
            new_state=CircuitBreakerState.from_string(data["new_state"]),
            reason=data["reason"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
        return event

    @classmethod
    def from_json(cls, json_str: str) -> "CircuitBreakerEvent":
        """
            Deserializes a JSON string into a CircuitBreakerEvent instance.

            :param json_str: JSON string to deserialize.

            :returns: A CircuitBreakerEvent instance.
        """
        data = json.loads(json_str)
        event = cls.from_dict(data)
        return event

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            circuit breaker name, previous state, and new state.

            :returns: A repr string for debugging.
        """
        repr_str = "CircuitBreakerEvent(name={!r}, {} -> {})".format(
            self._name, self._previous_state.value, self._new_state.value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the circuit breaker name,
            state transition, and reason.

            :returns: A human-readable string.
        """
        str_val = "CircuitBreakerEvent name='{}', {} -> {}, reason='{}'".format(
            self._name, self._previous_state.value, self._new_state.value, self._reason
        )
        return str_val
