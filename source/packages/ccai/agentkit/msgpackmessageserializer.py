"""
    Defines the MsgpackMessageSerializer class for serializing Python
    objects to MessagePack-encoded bytes and deserializing MessagePack-
    encoded bytes to Python objects.

    Uses the msgpack library for encoding and decoding. The msgpack
    package (msgpack-python) must be installed for this serializer to
    function. If msgpack is not available, importing this module will
    succeed but instantiation will raise an ImportError.

    .. module:: ccai.agentkit.msgpackmessageserializer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: MessagePack serialization implementation for message payloads.

    Requirements: 9.6, 9.10
"""

from ccai.agentkit.messageserializer import MessageSerializer
from ccai.agentkit.messagingerrors import MessageSerializationError

try:
    import msgpack
    _MSGPACK_AVAILABLE = True
except ImportError:
    _MSGPACK_AVAILABLE = False


class MsgpackMessageSerializer(MessageSerializer):
    """
        Serializes Python objects to MessagePack-encoded bytes and
        deserializes MessagePack-encoded bytes to Python objects.

        Requires the msgpack package to be installed. Raises
        ImportError at construction time if msgpack is not available.
    """

    def __init__(self) -> None:
        if _MSGPACK_AVAILABLE is not True:
            raise ImportError(
                "The 'msgpack' package is required for MsgpackMessageSerializer. "
                "Install it with: pip install msgpack"
            )

        super().__init__(format_name="msgpack", content_type="application/x-msgpack")
        return

    def serialize(self, obj: object) -> bytes:
        """
            Serializes a Python object to MessagePack-encoded bytes.

            :param obj: The Python object to serialize. Must be
                MessagePack-serializable.

            :returns: The MessagePack-encoded bytes.
            :raises MessageSerializationError: If the object cannot be
                serialized to MessagePack format.
        """
        try:
            rtnval = msgpack.packb(obj, use_bin_type=True)
        except (TypeError, ValueError, OverflowError) as ex:
            object_type = type(obj).__name__
            detail = "Object of type '{}' is not MessagePack serializable: {}".format(
                object_type, ex
            )
            raise MessageSerializationError(
                format_name="msgpack",
                direction="serialize",
                detail=detail
            ) from ex

        return rtnval

    def deserialize(self, data: bytes) -> object:
        """
            Deserializes MessagePack-encoded bytes to a Python object.

            :param data: The MessagePack-encoded bytes to deserialize.

            :returns: The deserialized Python object.
            :raises MessageSerializationError: If the bytes are not
                valid MessagePack. The error detail includes the bytes
                length.
        """
        try:
            rtnval = msgpack.unpackb(data, raw=False)
        except (msgpack.UnpackException, ValueError, TypeError) as ex:
            bytes_length = len(data)
            detail = "Invalid MessagePack input ({} bytes): {}".format(
                bytes_length, ex
            )
            raise MessageSerializationError(
                format_name="msgpack",
                direction="deserialize",
                detail=detail
            ) from ex

        return rtnval
