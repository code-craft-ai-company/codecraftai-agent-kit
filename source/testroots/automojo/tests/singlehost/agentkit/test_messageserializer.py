"""
    Unit tests for the automojo.agentkit message serializer modules and
    the MessageSerializerRegistry.

    Tests cover:
    - MessageSerializer base class properties (__repr__, __str__)
    - JsonMessageSerializer serialize/deserialize and error cases
    - MsgpackMessageSerializer serialize/deserialize and error cases
    - ProtobufMessageSerializer serialize/deserialize and error cases
    - MessageSerializerRegistry register, deregister, lookup, list_all,
      has_serializer, count, duplicate error, __repr__, __str__

    .. module:: automojo.tests.singlehost.agentkit.test_messageserializer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for message serializers and registry.

    Requirements: 9.1-9.15, 10.1-10.9
"""

import json

import automojo.testbase as testbase

from automojo.agentkit.jsonmessageserializer import JsonMessageSerializer
from automojo.agentkit.messageserializerregistry import MessageSerializerRegistry
from automojo.agentkit.messagingerrors import MessageSerializationError
from automojo.agentkit.errors import SemanticError


# ===================================================================
# JsonMessageSerializer Tests
# ===================================================================

def test_json_serializer_format_name():
    """JsonMessageSerializer has format_name 'json'."""
    serializer = JsonMessageSerializer()
    testbase.assert_equal(serializer.format_name, "json",
        "format_name should be 'json', got {!r}".format(serializer.format_name))
    return


def test_json_serializer_content_type():
    """JsonMessageSerializer has content_type 'application/json'."""
    serializer = JsonMessageSerializer()
    testbase.assert_equal(serializer.content_type, "application/json",
        "content_type should be 'application/json', got {!r}".format(serializer.content_type))
    return


def test_json_serializer_serialize_dict():
    """JsonMessageSerializer serializes a dict to JSON bytes."""
    serializer = JsonMessageSerializer()
    obj = {"key": "value", "count": 42}
    result = serializer.serialize(obj)

    testbase.assert_true(isinstance(result, bytes),
        "serialize should return bytes, got {!r}".format(type(result).__name__))

    decoded = json.loads(result.decode("utf-8"))
    testbase.assert_equal(decoded, obj,
        "Serialized JSON should decode to original dict.")
    return


def test_json_serializer_serialize_list():
    """JsonMessageSerializer serializes a list to JSON bytes."""
    serializer = JsonMessageSerializer()
    obj = [1, "two", True, None]
    result = serializer.serialize(obj)
    decoded = json.loads(result.decode("utf-8"))
    testbase.assert_equal(decoded, obj,
        "Serialized JSON should decode to original list.")
    return


def test_json_serializer_serialize_string():
    """JsonMessageSerializer serializes a string to JSON bytes."""
    serializer = JsonMessageSerializer()
    obj = "hello world"
    result = serializer.serialize(obj)
    decoded = json.loads(result.decode("utf-8"))
    testbase.assert_equal(decoded, obj,
        "Serialized JSON should decode to original string.")
    return


def test_json_serializer_serialize_number():
    """JsonMessageSerializer serializes an integer to JSON bytes."""
    serializer = JsonMessageSerializer()
    obj = 12345
    result = serializer.serialize(obj)
    decoded = json.loads(result.decode("utf-8"))
    testbase.assert_equal(decoded, obj,
        "Serialized JSON should decode to original integer.")
    return


def test_json_serializer_serialize_none():
    """JsonMessageSerializer serializes None to JSON bytes."""
    serializer = JsonMessageSerializer()
    result = serializer.serialize(None)
    decoded = json.loads(result.decode("utf-8"))
    testbase.assert_equal(decoded, None,
        "Serialized JSON should decode to None.")
    return


def test_json_serializer_deserialize_dict():
    """JsonMessageSerializer deserializes JSON bytes to a dict."""
    serializer = JsonMessageSerializer()
    data = b'{"key": "value", "count": 42}'
    result = serializer.deserialize(data)
    testbase.assert_equal(result, {"key": "value", "count": 42},
        "Deserialized JSON should produce the expected dict.")
    return


def test_json_serializer_serialize_non_serializable_raises():
    """JsonMessageSerializer raises MessageSerializationError for non-serializable objects."""
    serializer = JsonMessageSerializer()

    caught = False
    try:
        serializer.serialize(object())
    except MessageSerializationError as ex:
        caught = True
        testbase.assert_equal(ex.format_name, "json",
            "Error format_name should be 'json'.")
        testbase.assert_equal(ex.direction, "serialize",
            "Error direction should be 'serialize'.")
        testbase.assert_true("object" in ex.detail.lower(),
            "Error detail should mention the object type.")

    testbase.assert_true(caught,
        "MessageSerializationError should be raised for non-serializable objects.")
    return


def test_json_serializer_deserialize_invalid_json_raises():
    """JsonMessageSerializer raises MessageSerializationError for invalid JSON bytes."""
    serializer = JsonMessageSerializer()

    caught = False
    try:
        serializer.deserialize(b"not valid json {{{")
    except MessageSerializationError as ex:
        caught = True
        testbase.assert_equal(ex.format_name, "json",
            "Error format_name should be 'json'.")
        testbase.assert_equal(ex.direction, "deserialize",
            "Error direction should be 'deserialize'.")
        testbase.assert_true("18 bytes" in ex.detail or "18" in ex.detail,
            "Error detail should mention the bytes length.")

    testbase.assert_true(caught,
        "MessageSerializationError should be raised for invalid JSON.")
    return


def test_json_serializer_repr():
    """JsonMessageSerializer __repr__ includes class name and format name."""
    serializer = JsonMessageSerializer()
    repr_str = repr(serializer)
    testbase.assert_true("JsonMessageSerializer" in repr_str,
        "__repr__ should contain 'JsonMessageSerializer'.")
    testbase.assert_true("json" in repr_str,
        "__repr__ should contain 'json'.")
    return


def test_json_serializer_str():
    """JsonMessageSerializer __str__ includes format name and content type."""
    serializer = JsonMessageSerializer()
    str_val = str(serializer)
    testbase.assert_true("json" in str_val,
        "__str__ should contain 'json'.")
    testbase.assert_true("application/json" in str_val,
        "__str__ should contain 'application/json'.")
    return


# ===================================================================
# MsgpackMessageSerializer Tests
# ===================================================================

try:
    from automojo.agentkit.msgpackmessageserializer import MsgpackMessageSerializer
    MsgpackMessageSerializer()
    _MSGPACK_AVAILABLE = True
except ImportError:
    _MSGPACK_AVAILABLE = False


def test_msgpack_import_guard():
    """MsgpackMessageSerializer raises ImportError when msgpack is not installed."""
    if _MSGPACK_AVAILABLE is True:
        # msgpack is installed, verify construction succeeds
        serializer = MsgpackMessageSerializer()
        testbase.assert_equal(serializer.format_name, "msgpack",
            "format_name should be 'msgpack'.")
    else:
        # msgpack is not installed, verify ImportError is raised
        caught = False
        try:
            from automojo.agentkit.msgpackmessageserializer import MsgpackMessageSerializer as MsgpackCls
            MsgpackCls()
        except ImportError:
            caught = True

        testbase.assert_true(caught,
            "MsgpackMessageSerializer should raise ImportError when msgpack is not installed.")
    return


if _MSGPACK_AVAILABLE:

    def test_msgpack_serializer_format_name():
        """MsgpackMessageSerializer has format_name 'msgpack'."""
        serializer = MsgpackMessageSerializer()
        testbase.assert_equal(serializer.format_name, "msgpack",
            "format_name should be 'msgpack'.")
        return

    def test_msgpack_serializer_content_type():
        """MsgpackMessageSerializer has content_type 'application/x-msgpack'."""
        serializer = MsgpackMessageSerializer()
        testbase.assert_equal(serializer.content_type, "application/x-msgpack",
            "content_type should be 'application/x-msgpack'.")
        return

    def test_msgpack_serializer_serialize_dict():
        """MsgpackMessageSerializer serializes a dict to bytes."""
        serializer = MsgpackMessageSerializer()
        obj = {"key": "value", "count": 42}
        result = serializer.serialize(obj)
        testbase.assert_true(isinstance(result, bytes),
            "serialize should return bytes.")
        deserialized = serializer.deserialize(result)
        testbase.assert_equal(deserialized, obj,
            "Deserialized MsgPack should match original dict.")
        return

    def test_msgpack_serializer_deserialize_invalid_raises():
        """MsgpackMessageSerializer raises MessageSerializationError for invalid bytes."""
        serializer = MsgpackMessageSerializer()
        caught = False
        try:
            serializer.deserialize(b"\xff\xfe\xfd\xfc\xfb")
        except MessageSerializationError as ex:
            caught = True
            testbase.assert_equal(ex.format_name, "msgpack",
                "Error format_name should be 'msgpack'.")
            testbase.assert_equal(ex.direction, "deserialize",
                "Error direction should be 'deserialize'.")

        testbase.assert_true(caught,
            "MessageSerializationError should be raised for invalid MsgPack bytes.")
        return

    def test_msgpack_serializer_repr():
        """MsgpackMessageSerializer __repr__ includes class name and format name."""
        serializer = MsgpackMessageSerializer()
        repr_str = repr(serializer)
        testbase.assert_true("MsgpackMessageSerializer" in repr_str,
            "__repr__ should contain 'MsgpackMessageSerializer'.")
        return


# ===================================================================
# ProtobufMessageSerializer Tests
# ===================================================================

try:
    from automojo.agentkit.protobufmessageserializer import ProtobufMessageSerializer
    ProtobufMessageSerializer()
    _PROTOBUF_AVAILABLE = True
except ImportError:
    _PROTOBUF_AVAILABLE = False


def test_protobuf_import_guard():
    """ProtobufMessageSerializer raises ImportError when protobuf is not installed."""
    if _PROTOBUF_AVAILABLE is True:
        serializer = ProtobufMessageSerializer()
        testbase.assert_equal(serializer.format_name, "protobuf",
            "format_name should be 'protobuf'.")
    else:
        caught = False
        try:
            from automojo.agentkit.protobufmessageserializer import ProtobufMessageSerializer as PbCls
            PbCls()
        except ImportError:
            caught = True

        testbase.assert_true(caught,
            "ProtobufMessageSerializer should raise ImportError when protobuf is not installed.")
    return


if _PROTOBUF_AVAILABLE:

    def test_protobuf_serializer_format_name():
        """ProtobufMessageSerializer has format_name 'protobuf'."""
        serializer = ProtobufMessageSerializer()
        testbase.assert_equal(serializer.format_name, "protobuf",
            "format_name should be 'protobuf'.")
        return

    def test_protobuf_serializer_content_type():
        """ProtobufMessageSerializer has content_type 'application/x-protobuf'."""
        serializer = ProtobufMessageSerializer()
        testbase.assert_equal(serializer.content_type, "application/x-protobuf",
            "content_type should be 'application/x-protobuf'.")
        return

    def test_protobuf_serializer_serialize_non_protobuf_raises():
        """ProtobufMessageSerializer raises MessageSerializationError for non-protobuf objects."""
        serializer = ProtobufMessageSerializer()
        caught = False
        try:
            serializer.serialize({"not": "protobuf"})
        except MessageSerializationError as ex:
            caught = True
            testbase.assert_equal(ex.format_name, "protobuf",
                "Error format_name should be 'protobuf'.")
            testbase.assert_equal(ex.direction, "serialize",
                "Error direction should be 'serialize'.")

        testbase.assert_true(caught,
            "MessageSerializationError should be raised for non-protobuf objects.")
        return

    def test_protobuf_serializer_deserialize_no_message_type_raises():
        """ProtobufMessageSerializer raises MessageSerializationError when no message_type is set."""
        serializer = ProtobufMessageSerializer(message_type=None)
        caught = False
        try:
            serializer.deserialize(b"\x08\x01")
        except MessageSerializationError as ex:
            caught = True
            testbase.assert_equal(ex.direction, "deserialize",
                "Error direction should be 'deserialize'.")

        testbase.assert_true(caught,
            "MessageSerializationError should be raised when no message_type is configured.")
        return

    def test_protobuf_serializer_repr():
        """ProtobufMessageSerializer __repr__ includes class name."""
        serializer = ProtobufMessageSerializer()
        repr_str = repr(serializer)
        testbase.assert_true("ProtobufMessageSerializer" in repr_str,
            "__repr__ should contain 'ProtobufMessageSerializer'.")
        return


# ===================================================================
# MessageSerializerRegistry Tests
# ===================================================================

def test_registry_register_and_lookup():
    """Registry registers a serializer and looks it up by format name."""
    registry = MessageSerializerRegistry()
    serializer = JsonMessageSerializer()
    registry.register(serializer)

    result = registry.lookup("json")
    testbase.assert_true(result is serializer,
        "lookup should return the registered serializer instance.")
    return


def test_registry_lookup_returns_none_for_unknown():
    """Registry lookup returns None for an unregistered format name."""
    registry = MessageSerializerRegistry()
    result = registry.lookup("nonexistent")
    testbase.assert_equal(result, None,
        "lookup should return None for unknown format name.")
    return


def test_registry_duplicate_raises_semantic_error():
    """Registry raises SemanticError when registering a duplicate format name."""
    registry = MessageSerializerRegistry()
    serializer1 = JsonMessageSerializer()
    serializer2 = JsonMessageSerializer()
    registry.register(serializer1)

    caught = False
    try:
        registry.register(serializer2)
    except SemanticError as ex:
        caught = True
        testbase.assert_true("json" in str(ex).lower(),
            "SemanticError message should mention the duplicate format name 'json'.")

    testbase.assert_true(caught,
        "SemanticError should be raised for duplicate format name registration.")
    return


def test_registry_deregister():
    """Registry deregisters a serializer by format name."""
    registry = MessageSerializerRegistry()
    serializer = JsonMessageSerializer()
    registry.register(serializer)
    registry.deregister("json")

    result = registry.lookup("json")
    testbase.assert_equal(result, None,
        "lookup should return None after deregistration.")
    return


def test_registry_deregister_nonexistent_is_noop():
    """Registry deregister for a nonexistent format name is a no-op."""
    registry = MessageSerializerRegistry()
    registry.deregister("nonexistent")
    testbase.assert_equal(registry.count, 0,
        "count should remain 0 after deregistering a nonexistent format name.")
    return


def test_registry_list_all():
    """Registry list_all returns all registered serializers."""
    registry = MessageSerializerRegistry()
    serializer = JsonMessageSerializer()
    registry.register(serializer)

    all_serializers = registry.list_all()
    testbase.assert_equal(len(all_serializers), 1,
        "list_all should return 1 serializer.")
    testbase.assert_true(all_serializers[0] is serializer,
        "list_all should contain the registered serializer.")
    return


def test_registry_list_all_empty():
    """Registry list_all returns empty list when no serializers registered."""
    registry = MessageSerializerRegistry()
    all_serializers = registry.list_all()
    testbase.assert_equal(len(all_serializers), 0,
        "list_all should return empty list for empty registry.")
    return


def test_registry_has_serializer_true():
    """Registry has_serializer returns True for a registered format name."""
    registry = MessageSerializerRegistry()
    serializer = JsonMessageSerializer()
    registry.register(serializer)

    testbase.assert_true(registry.has_serializer("json"),
        "has_serializer should return True for 'json'.")
    return


def test_registry_has_serializer_false():
    """Registry has_serializer returns False for an unregistered format name."""
    registry = MessageSerializerRegistry()
    testbase.assert_false(registry.has_serializer("json"),
        "has_serializer should return False for unregistered format name.")
    return


def test_registry_count_empty():
    """Registry count is 0 when empty."""
    registry = MessageSerializerRegistry()
    testbase.assert_equal(registry.count, 0,
        "count should be 0 for empty registry.")
    return


def test_registry_count_after_register():
    """Registry count reflects the number of registered serializers."""
    registry = MessageSerializerRegistry()
    registry.register(JsonMessageSerializer())
    testbase.assert_equal(registry.count, 1,
        "count should be 1 after registering one serializer.")
    return


def test_registry_count_after_deregister():
    """Registry count decreases after deregistration."""
    registry = MessageSerializerRegistry()
    registry.register(JsonMessageSerializer())
    registry.deregister("json")
    testbase.assert_equal(registry.count, 0,
        "count should be 0 after deregistering the only serializer.")
    return


def test_registry_repr():
    """Registry __repr__ includes class name and count."""
    registry = MessageSerializerRegistry()
    registry.register(JsonMessageSerializer())
    repr_str = repr(registry)
    testbase.assert_true("MessageSerializerRegistry" in repr_str,
        "__repr__ should contain 'MessageSerializerRegistry'.")
    testbase.assert_true("1" in repr_str,
        "__repr__ should contain the count '1'.")
    return


def test_registry_str_empty():
    """Registry __str__ describes empty registry."""
    registry = MessageSerializerRegistry()
    str_val = str(registry)
    testbase.assert_true("0" in str_val,
        "__str__ should mention 0 serializers for empty registry.")
    return


def test_registry_str_with_serializers():
    """Registry __str__ lists registered format names."""
    registry = MessageSerializerRegistry()
    registry.register(JsonMessageSerializer())
    str_val = str(registry)
    testbase.assert_true("json" in str_val,
        "__str__ should list the 'json' format name.")
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
