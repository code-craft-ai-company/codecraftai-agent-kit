"""
    Defines the ProtobufMessageSerializer class for serializing
    Protobuf message objects to Protobuf-encoded bytes and
    deserializing Protobuf-encoded bytes to Protobuf message objects.

    Uses the google.protobuf library for encoding and decoding. The
    protobuf package must be installed for this serializer to function.
    If google.protobuf is not available, importing this module will
    succeed but instantiation will raise an ImportError.

    The serializer is constructed with a message_type parameter that
    specifies the expected Protobuf message class for deserialization.

    .. module:: ccai.agentkit.protobufmessageserializer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Protobuf serialization implementation for message payloads.

    Requirements: 9.7, 9.11
"""

from ccai.agentkit.messageserializer import MessageSerializer
from ccai.agentkit.messagingerrors import MessageSerializationError

try:
    from google.protobuf import message as protobuf_message
    _PROTOBUF_AVAILABLE = True
except ImportError:
    _PROTOBUF_AVAILABLE = False


class ProtobufMessageSerializer(MessageSerializer):
    """
        Serializes Protobuf message objects to Protobuf-encoded bytes
        and deserializes Protobuf-encoded bytes to Protobuf message
        objects.

        Requires the google-protobuf package to be installed. Raises
        ImportError at construction time if google.protobuf is not
        available.

        :param message_type: The expected Protobuf message class used
            for deserialization. Must be a subclass of
            google.protobuf.message.Message.
    """

    def __init__(self, message_type=None) -> None:
        if _PROTOBUF_AVAILABLE is not True:
            raise ImportError(
                "The 'protobuf' package is required for ProtobufMessageSerializer. "
                "Install it with: pip install protobuf"
            )

        super().__init__(format_name="protobuf", content_type="application/x-protobuf")
        self._message_type = message_type
        return

    @property
    def message_type(self):
        """
            The expected Protobuf message class for deserialization.

            :returns: The Protobuf message class, or None if not set.
        """
        return self._message_type

    def serialize(self, obj: object) -> bytes:
        """
            Serializes a Protobuf message object to bytes.

            :param obj: The Protobuf message object to serialize. Must
                be an instance of google.protobuf.message.Message.

            :returns: The Protobuf-encoded bytes.
            :raises MessageSerializationError: If the object is not a
                valid Protobuf message or cannot be serialized.
        """
        is_protobuf_message = isinstance(obj, protobuf_message.Message)

        if is_protobuf_message is not True:
            object_type = type(obj).__name__
            detail = "Object of type '{}' is not a Protobuf message".format(
                object_type
            )
            raise MessageSerializationError(
                format_name="protobuf",
                direction="serialize",
                detail=detail
            )

        try:
            rtnval = obj.SerializeToString()
        except Exception as ex:
            object_type = type(obj).__name__
            detail = "Failed to serialize Protobuf message of type '{}': {}".format(
                object_type, ex
            )
            raise MessageSerializationError(
                format_name="protobuf",
                direction="serialize",
                detail=detail
            ) from ex

        return rtnval

    def deserialize(self, data: bytes) -> object:
        """
            Deserializes Protobuf-encoded bytes to a Protobuf message
            object.

            Uses the message_type provided at construction time to
            create and populate the message instance.

            :param data: The Protobuf-encoded bytes to deserialize.

            :returns: The deserialized Protobuf message object.
            :raises MessageSerializationError: If the bytes are not
                valid Protobuf for the expected message type. The error
                detail includes the expected message type.
        """
        if self._message_type is None:
            detail = "No message_type configured for deserialization"
            raise MessageSerializationError(
                format_name="protobuf",
                direction="deserialize",
                detail=detail
            )

        expected_type_name = self._message_type.DESCRIPTOR.full_name

        try:
            message_instance = self._message_type()
            message_instance.ParseFromString(data)
            rtnval = message_instance
        except Exception as ex:
            detail = "Invalid Protobuf input for expected message type '{}': {}".format(
                expected_type_name, ex
            )
            raise MessageSerializationError(
                format_name="protobuf",
                direction="deserialize",
                detail=detail
            ) from ex

        return rtnval
