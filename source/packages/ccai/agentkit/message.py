"""
    Defines the Message class representing an immutable unit of communication
    between agents in the Communication & Messaging feature.

    A Message contains a unique identifier, sender and recipient AgentAddress
    instances, a payload, a MessagePattern, optional headers, an optional
    correlation identifier for request/response tracking, a UTC timestamp,
    and an optional serialization format name that selects the
    MessageSerializer a Transport uses to put the message on the wire.
    It supports serialization to dictionary and JSON formats, and
    deserialization from dictionary and JSON.

    .. module:: ccai.agentkit.message
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable message object for agent-to-agent communication.
"""

import json
import uuid

from datetime import datetime
from datetime import timezone
from typing import Dict
from typing import Optional

from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.messagepattern import MessagePattern


PAYLOAD_PREVIEW_MAX_LENGTH = 50


class Message:
    """
        Immutable object representing a unit of communication between agents.

        Contains a unique identifier, sender AgentAddress, recipient AgentAddress,
        payload (dictionary, list, string, or bytes), headers dictionary, optional
        correlation identifier for request/response tracking, a MessagePattern
        value, a UTC timestamp, and an optional serialization format name.

        When created without an explicit identifier, a UUID-based identifier is
        generated automatically. When created without an explicit timestamp, the
        current UTC time is used.

        The serialization format name (e.g. 'json', 'msgpack') selects the
        MessageSerializer that a Transport uses to encode the message. The Agent
        sets it from the serialization_format passed to send_message or request,
        or from the MessagingConfiguration default. When it is None, the
        Transport uses its own default format.

        :param sender: The AgentAddress of the sending agent.
        :param recipient: The AgentAddress of the receiving agent.
        :param payload: The message payload as a Python object (dictionary, list,
            string, or bytes).
        :param pattern: The MessagePattern value indicating the communication pattern.
        :param headers: Optional dictionary of message headers.
        :param correlation_id: Optional correlation identifier for request/response
            tracking.
        :param identifier: Optional unique identifier. If not provided, a UUID is
            generated.
        :param timestamp: Optional UTC timestamp. If not provided, the current UTC
            time is used.
        :param serialization_format: Optional serialization format name that
            selects the MessageSerializer used by the Transport. If not provided,
            the Transport default is used.
    """

    def __init__(self, sender: AgentAddress, recipient: AgentAddress,
                 payload: object, pattern: MessagePattern,
                 headers: Optional[Dict] = None,
                 correlation_id: Optional[str] = None,
                 identifier: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 serialization_format: Optional[str] = None) -> None:

        if identifier is not None:
            self._identifier = identifier
        else:
            self._identifier = str(uuid.uuid4())

        self._sender = sender
        self._recipient = recipient
        self._payload = payload
        self._pattern = pattern

        if headers is not None:
            self._headers = dict(headers)
        else:
            self._headers = {}

        self._correlation_id = correlation_id

        if timestamp is not None:
            self._timestamp = timestamp
        else:
            self._timestamp = datetime.now(timezone.utc)

        self._serialization_format = serialization_format

        return

    @property
    def identifier(self) -> str:
        """
            The unique identifier of the message.

            :returns: The identifier string.
        """
        return self._identifier

    @property
    def sender(self) -> AgentAddress:
        """
            The AgentAddress of the sending agent.

            :returns: The sender AgentAddress.
        """
        return self._sender

    @property
    def recipient(self) -> AgentAddress:
        """
            The AgentAddress of the receiving agent.

            :returns: The recipient AgentAddress.
        """
        return self._recipient

    @property
    def payload(self) -> object:
        """
            The message payload.

            :returns: The payload as a Python object.
        """
        return self._payload

    @property
    def pattern(self) -> MessagePattern:
        """
            The communication pattern of the message.

            :returns: The MessagePattern value.
        """
        return self._pattern

    @property
    def headers(self) -> Dict:
        """
            A defensive copy of the message headers dictionary.

            :returns: A dictionary copy of the headers.
        """
        return dict(self._headers)

    @property
    def correlation_id(self) -> Optional[str]:
        """
            The optional correlation identifier for request/response tracking.

            :returns: The correlation identifier string or None.
        """
        return self._correlation_id

    @property
    def timestamp(self) -> datetime:
        """
            The UTC timestamp of the message.

            :returns: The timestamp as a datetime object.
        """
        return self._timestamp

    @property
    def serialization_format(self) -> Optional[str]:
        """
            The optional serialization format name that selects the
            MessageSerializer a Transport uses to encode the message.

            :returns: The serialization format name string or None when the
                Transport default should be used.
        """
        return self._serialization_format

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the message fields.

            Converts sender and recipient to dictionaries via their as_dict
            methods, converts the pattern to its string value, and converts
            the timestamp to ISO format.

            :returns: A dictionary with all message fields.
        """
        result = {
            "identifier": self._identifier,
            "sender": self._sender.as_dict(),
            "recipient": self._recipient.as_dict(),
            "payload": self._payload,
            "pattern": self._pattern.value,
            "headers": dict(self._headers),
            "correlation_id": self._correlation_id,
            "timestamp": self._timestamp.isoformat(),
            "serialization_format": self._serialization_format
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the message fields.

            :returns: A JSON string containing all message fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """
            Constructs a Message from a dictionary.

            Reconstructs AgentAddress instances from nested dictionaries,
            the MessagePattern from its string value, and the timestamp
            from an ISO format string. The serialization format is
            optional so dictionaries written before the field existed
            can still be read.

            :param data: A dictionary containing message fields.

            :returns: A Message instance reconstructed from the dictionary data.
        """
        sender = AgentAddress.from_dict(data["sender"])
        recipient = AgentAddress.from_dict(data["recipient"])
        pattern = MessagePattern.from_string(data["pattern"])
        payload = data["payload"]
        headers = data.get("headers", {})
        correlation_id = data.get("correlation_id", None)
        identifier = data["identifier"]
        timestamp_str = data["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str)
        serialization_format = data.get("serialization_format", None)

        message = cls(
            sender=sender,
            recipient=recipient,
            payload=payload,
            pattern=pattern,
            headers=headers,
            correlation_id=correlation_id,
            identifier=identifier,
            timestamp=timestamp,
            serialization_format=serialization_format
        )
        return message

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """
            Deserializes a JSON string into a Message instance.

            :param json_str: A JSON string containing message fields.

            :returns: A Message instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        message = cls.from_dict(data)
        return message

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            identifier, pattern, and a truncated payload preview.

            The payload preview is truncated to the first 50 characters.

            :returns: A repr string for debugging.
        """
        payload_str = repr(self._payload)
        if len(payload_str) > PAYLOAD_PREVIEW_MAX_LENGTH:
            payload_preview = payload_str[:PAYLOAD_PREVIEW_MAX_LENGTH] + "..."
        else:
            payload_preview = payload_str

        repr_str = "Message(identifier={!r}, pattern={!r}, payload={})".format(
            self._identifier, self._pattern.value, payload_preview
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the sender, recipient,
            pattern, and a truncated payload preview.

            The payload preview is truncated to the first 50 characters.

            :returns: A human-readable string.
        """
        payload_str = repr(self._payload)
        if len(payload_str) > PAYLOAD_PREVIEW_MAX_LENGTH:
            payload_preview = payload_str[:PAYLOAD_PREVIEW_MAX_LENGTH] + "..."
        else:
            payload_preview = payload_str

        str_val = "Message: sender={}, recipient={}, pattern={}, payload={}".format(
            self._sender.agent_identifier, self._recipient.agent_identifier,
            self._pattern.value, payload_preview
        )
        return str_val
