"""
    Defines the MessageSerializer abstract base class for serializing
    and deserializing message payloads between Python objects and wire
    format bytes.

    Concrete implementations handle specific formats such as JSON,
    MessagePack, and Protobuf. Each serializer exposes a format name
    and content type, and provides serialize and deserialize methods.

    .. module:: ccai.agentkit.messageserializer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract base class for message payload serializers.

    Requirements: 9.1-9.4, 9.14, 9.15
"""

import abc


class MessageSerializer(abc.ABC):
    """
        Abstract base class for serializing and deserializing message
        payloads between Python objects and wire format bytes.

        Subclasses must implement the serialize and deserialize methods
        for their specific wire format. Each serializer is identified
        by a format name (e.g. 'json', 'msgpack', 'protobuf') and a
        content type (e.g. 'application/json').

        :param format_name: The serializer format name string.
        :param content_type: The MIME content type string for the
            serialized format.
    """

    def __init__(self, format_name: str, content_type: str) -> None:
        self._format_name = format_name
        self._content_type = content_type
        return

    @property
    def format_name(self) -> str:
        """
            The serializer format name.

            :returns: The format name string (e.g. 'json', 'msgpack',
                'protobuf').
        """
        return self._format_name

    @property
    def content_type(self) -> str:
        """
            The MIME content type for the serialized format.

            :returns: The content type string (e.g. 'application/json',
                'application/x-msgpack', 'application/x-protobuf').
        """
        return self._content_type

    @abc.abstractmethod
    def serialize(self, obj: object) -> bytes:
        """
            Serializes a Python object to bytes.

            :param obj: The Python object to serialize.

            :returns: The serialized bytes.
            :raises MessageSerializationError: If the object cannot be
                serialized.
        """

    @abc.abstractmethod
    def deserialize(self, data: bytes) -> object:
        """
            Deserializes bytes to a Python object.

            :param data: The bytes to deserialize.

            :returns: The deserialized Python object.
            :raises MessageSerializationError: If the bytes cannot be
                deserialized.
        """

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and format name.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(format_name={!r})".format(
            self.__class__.__name__, self._format_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the format name
            and content type.

            :returns: A human-readable string describing the serializer.
        """
        str_val = "MessageSerializer: format={}, content_type={}".format(
            self._format_name, self._content_type
        )
        return str_val
