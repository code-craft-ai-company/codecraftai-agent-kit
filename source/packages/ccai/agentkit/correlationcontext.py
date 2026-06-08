"""
    Defines the CorrelationContext class representing a mutable context
    object that carries a correlation identifier and optional parent
    correlation identifier across agent operations.

    CorrelationContext is propagated through log entries, trace spans,
    and metric labels to enable end-to-end tracing of a logical
    operation. It supports serialization to and from JSON and
    dictionary representations, and creation of child contexts
    that preserve the parent chain.
"""

import json
import uuid

from typing import Optional


class CorrelationContext:
    """
        A mutable context object that carries a correlation identifier and
        optional parent correlation identifier across agent operations.

        The correlation identifier is auto-generated as a UUID when not
        explicitly provided. The parent correlation identifier links this
        context to a parent context, enabling hierarchical tracing of
        logical operations.

        :param correlation_id: Optional correlation identifier string.
            Auto-generates a UUID if not provided.
        :param parent_correlation_id: Optional parent correlation identifier string.
    """

    def __init__(self, correlation_id: str = None, parent_correlation_id: str = None) -> None:

        if correlation_id is not None:
            self._correlation_id = correlation_id
        else:
            self._correlation_id = str(uuid.uuid4())

        self._parent_correlation_id = parent_correlation_id

        return

    @property
    def correlation_id(self) -> str:
        """
            The correlation identifier string for this context.

            :returns: The correlation identifier string.
        """
        return self._correlation_id

    @property
    def parent_correlation_id(self) -> Optional[str]:
        """
            The optional parent correlation identifier string for this context.

            :returns: The parent correlation identifier string, or None.
        """
        return self._parent_correlation_id

    def create_child(self) -> "CorrelationContext":
        """
            Creates a new CorrelationContext with a new auto-generated
            correlation identifier and the current correlation identifier
            set as the parent.

            :returns: A new CorrelationContext instance with this context's
                correlation identifier as the parent.
        """
        child = CorrelationContext(
            parent_correlation_id=self._correlation_id
        )
        return child

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the context fields.

            :returns: A dictionary with correlation_id and parent_correlation_id.
        """
        result = {
            "correlation_id": self._correlation_id,
            "parent_correlation_id": self._parent_correlation_id
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the context fields.

            :returns: A JSON string containing correlation_id and
                parent_correlation_id.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "CorrelationContext":
        """
            Constructs a CorrelationContext from a dictionary.

            :param data: A dictionary containing correlation_id and
                optionally parent_correlation_id.

            :returns: A CorrelationContext instance reconstructed from
                the dictionary.
        """
        correlation_id = data["correlation_id"]
        parent_correlation_id = data.get("parent_correlation_id", None)

        context = cls(
            correlation_id=correlation_id,
            parent_correlation_id=parent_correlation_id
        )
        return context

    @classmethod
    def from_json(cls, json_str: str) -> "CorrelationContext":
        """
            Deserializes a JSON string into a CorrelationContext instance.

            :param json_str: A JSON string containing context fields.

            :returns: A CorrelationContext instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        context = cls.from_dict(data)
        return context

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            correlation identifier, and parent correlation identifier.

            :returns: A repr string for debugging.
        """
        repr_str = "CorrelationContext(correlation_id={!r}, parent_correlation_id={!r})".format(
            self._correlation_id, self._parent_correlation_id
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the correlation
            identifier and parent correlation identifier.

            :returns: A human-readable string.
        """
        str_val = "CorrelationContext: correlation_id={}, parent_correlation_id={}".format(
            self._correlation_id, self._parent_correlation_id
        )
        return str_val
