"""
    Defines the QueueMessage class representing an immutable message in a
    queue with identifier, queue name, body, attributes, receipt handle,
    and timestamp. Supports serialization to and from dictionary and JSON
    representations.

    .. module:: ccai.agentkit.platform.services.queuemessage
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable queue message representation for platform messaging services.
"""

import json

from datetime import datetime
from typing import Dict
from typing import Optional


class QueueMessage:
    """
        Immutable object representing a message in a queue. Contains a
        unique identifier, queue name, body as a Python object, attributes
        dictionary, receipt handle string for acknowledgment, and timestamp.

        All fields are exposed as read-only properties.

        :param identifier: A unique identifier string for this message.
        :param queue_name: The name of the queue this message belongs to.
        :param body: The message body as a Python object.
        :param attributes: A dictionary of message attributes.
        :param receipt_handle: A receipt handle string for acknowledgment.
        :param timestamp: The timestamp when the message was created.
    """

    def __init__(self, identifier: str, queue_name: str, body: object,
                 attributes: Optional[Dict[str, str]] = None,
                 receipt_handle: str = "",
                 timestamp: Optional[datetime] = None) -> None:
        self._identifier = identifier
        self._queue_name = queue_name
        self._body = body
        self._attributes = dict(attributes) if attributes is not None else {}
        self._receipt_handle = receipt_handle
        self._timestamp = timestamp
        return

    @property
    def identifier(self) -> str:
        """
            The unique identifier string for this message.

            :returns: The identifier string.
        """
        rtnval = self._identifier
        return rtnval

    @property
    def queue_name(self) -> str:
        """
            The name of the queue this message belongs to.

            :returns: The queue name string.
        """
        rtnval = self._queue_name
        return rtnval

    @property
    def body(self) -> object:
        """
            The message body as a Python object.

            :returns: The body object.
        """
        rtnval = self._body
        return rtnval

    @property
    def attributes(self) -> dict:
        """
            A defensive copy of the message attributes dictionary.

            :returns: A dictionary copy of the attributes.
        """
        rtnval = dict(self._attributes)
        return rtnval

    @property
    def receipt_handle(self) -> str:
        """
            The receipt handle string for message acknowledgment.

            :returns: The receipt handle string.
        """
        rtnval = self._receipt_handle
        return rtnval

    @property
    def timestamp(self) -> datetime:
        """
            The timestamp when the message was created.

            :returns: The timestamp datetime.
        """
        rtnval = self._timestamp
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the message fields.

            :returns: A dictionary with all message fields.
        """
        timestamp_str = self._timestamp.isoformat() if self._timestamp is not None else None
        rtnval = {
            "identifier": self._identifier,
            "queue_name": self._queue_name,
            "body": self._body,
            "attributes": dict(self._attributes),
            "receipt_handle": self._receipt_handle,
            "timestamp": timestamp_str
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the message fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "QueueMessage":
        """
            Constructs a QueueMessage from a dictionary.

            :param data: Dictionary containing message fields.

            :returns: A QueueMessage instance.
        """
        timestamp_raw = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_raw) if timestamp_raw is not None else None
        rtnval = cls(
            identifier=data["identifier"],
            queue_name=data["queue_name"],
            body=data["body"],
            attributes=data.get("attributes", {}),
            receipt_handle=data.get("receipt_handle", ""),
            timestamp=timestamp
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "QueueMessage":
        """
            Deserializes a JSON string into a QueueMessage instance.

            :param json_str: A JSON string containing message fields.

            :returns: A QueueMessage instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            identifier, and queue name.

            :returns: A repr string for debugging.
        """
        rtnval = "QueueMessage(identifier={}, queue_name={})".format(
            self._identifier, self._queue_name
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the identifier,
            queue name, and a truncated body preview (max 50 chars).

            :returns: A human-readable string.
        """
        body_preview = str(self._body)
        if len(body_preview) > 50:
            body_preview = body_preview[:50] + "..."
        rtnval = "QueueMessage: id={}, queue={}, body={}".format(
            self._identifier, self._queue_name, body_preview
        )
        return rtnval
