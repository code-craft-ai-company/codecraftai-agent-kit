"""
    Defines the JsonMessageSerializer class for serializing Python
    objects to JSON-encoded bytes and deserializing JSON-encoded bytes
    to Python objects.

    Uses the standard library json module for encoding and decoding.
    Raises MessageSerializationError with the object type on
    non-serializable input and with the bytes length on invalid JSON
    input.

    .. module:: ccai.agentkit.jsonmessageserializer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: JSON serialization implementation for message payloads.

    Requirements: 9.5, 9.8, 9.9
"""

import json

from ccai.agentkit.messageserializer import MessageSerializer
from ccai.agentkit.messagingerrors import MessageSerializationError


class JsonMessageSerializer(MessageSerializer):
    """
        Serializes Python objects to JSON-encoded bytes and deserializes
        JSON-encoded bytes to Python objects.

        Uses UTF-8 encoding for the JSON byte representation.
    """

    def __init__(self) -> None:
        super().__init__(format_name="json", content_type="application/json")
        return

    def serialize(self, obj: object) -> bytes:
        """
            Serializes a Python object to JSON-encoded bytes.

            :param obj: The Python object to serialize. Must be
                JSON-serializable (dict, list, str, int, float, bool,
                None).

            :returns: The JSON-encoded bytes using UTF-8 encoding.
            :raises MessageSerializationError: If the object is not
                JSON-serializable. The error detail includes the
                object type.
        """
        try:
            json_str = json.dumps(obj)
            rtnval = json_str.encode("utf-8")
        except (TypeError, ValueError) as ex:
            object_type = type(obj).__name__
            detail = "Object of type '{}' is not JSON serializable: {}".format(
                object_type, ex
            )
            raise MessageSerializationError(
                format_name="json",
                direction="serialize",
                detail=detail
            ) from ex

        return rtnval

    def deserialize(self, data: bytes) -> object:
        """
            Deserializes JSON-encoded bytes to a Python object.

            :param data: The JSON-encoded bytes to deserialize.

            :returns: The deserialized Python object.
            :raises MessageSerializationError: If the bytes are not
                valid JSON. The error detail includes the bytes length.
        """
        try:
            json_str = data.decode("utf-8")
            rtnval = json.loads(json_str)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as ex:
            bytes_length = len(data)
            detail = "Invalid JSON input ({} bytes): {}".format(
                bytes_length, ex
            )
            raise MessageSerializationError(
                format_name="json",
                direction="deserialize",
                detail=detail
            ) from ex

        return rtnval
