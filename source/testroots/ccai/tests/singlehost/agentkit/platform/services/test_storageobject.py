"""
    Tests for the ccai.agentkit.platform.services.storageobject module.

    Contains unit tests for the StorageObject immutable data transfer object
    including read-only properties, base64 encoding in as_dict, JSON
    round-trip serialization, and __repr__/__str__ output.

    Feature: cross-platform-runtime
"""

import base64
import json

from datetime import datetime

from ccai.agentkit.platform.services.storageobject import StorageObject


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _create_sample_storage_object() -> StorageObject:
    """
        Creates a sample StorageObject for testing.

        :returns: A StorageObject instance with known test values.
    """
    obj = StorageObject(
        key="documents/report.pdf",
        content=b"Hello, World!",
        content_type="application/pdf",
        metadata={"author": "test-user", "version": "1"},
        size=13,
        last_modified=datetime(2026, 1, 15, 10, 30, 0)
    )
    return obj


# ---------------------------------------------------------------------------
# Read-only property tests
# ---------------------------------------------------------------------------

def test_key_property_returns_correct_value():
    """
        Verify that the key property returns the key passed at construction.
    """
    obj = _create_sample_storage_object()

    actual = obj.key

    assert actual == "documents/report.pdf", (
        "key should be 'documents/report.pdf', got: {!r}".format(actual)
    )
    return


def test_content_property_returns_correct_bytes():
    """
        Verify that the content property returns the bytes passed at construction.
    """
    obj = _create_sample_storage_object()

    actual = obj.content

    assert actual == b"Hello, World!", (
        "content should be b'Hello, World!', got: {!r}".format(actual)
    )
    return


def test_content_type_property_returns_correct_value():
    """
        Verify that the content_type property returns the value passed at construction.
    """
    obj = _create_sample_storage_object()

    actual = obj.content_type

    assert actual == "application/pdf", (
        "content_type should be 'application/pdf', got: {!r}".format(actual)
    )
    return


def test_metadata_property_returns_defensive_copy():
    """
        Verify that the metadata property returns a copy and modifying it
        does not affect the internal state.
    """
    obj = _create_sample_storage_object()

    metadata_copy = obj.metadata
    metadata_copy["injected"] = "bad-value"

    original_metadata = obj.metadata
    has_injected = "injected" in original_metadata

    assert has_injected is False, (
        "Modifying returned metadata should not affect internal state"
    )
    return


def test_size_property_returns_correct_value():
    """
        Verify that the size property returns the size passed at construction.
    """
    obj = _create_sample_storage_object()

    actual = obj.size

    assert actual == 13, (
        "size should be 13, got: {!r}".format(actual)
    )
    return


def test_last_modified_property_returns_correct_value():
    """
        Verify that the last_modified property returns the datetime passed
        at construction.
    """
    obj = _create_sample_storage_object()

    actual = obj.last_modified

    expected = datetime(2026, 1, 15, 10, 30, 0)
    assert actual == expected, (
        "last_modified should be {!r}, got: {!r}".format(expected, actual)
    )
    return


def test_none_metadata_defaults_to_empty_dict():
    """
        Verify that passing None for metadata results in an empty dictionary.
    """
    obj = StorageObject(
        key="test.txt",
        content=b"data",
        content_type="text/plain",
        metadata=None,
        size=4,
        last_modified=datetime(2026, 1, 1)
    )

    metadata = obj.metadata

    assert metadata == {}, (
        "None metadata should default to empty dict, got: {!r}".format(metadata)
    )
    return


# ---------------------------------------------------------------------------
# as_dict tests
# ---------------------------------------------------------------------------

def test_as_dict_encodes_content_as_base64():
    """
        Verify that as_dict encodes the content field as a base64 string.
    """
    obj = _create_sample_storage_object()

    result = obj.as_dict()

    expected_b64 = base64.b64encode(b"Hello, World!").decode("utf-8")
    actual_content = result["content"]

    assert actual_content == expected_b64, (
        "as_dict content should be base64 encoded, got: {!r}".format(actual_content)
    )
    return


def test_as_dict_contains_all_fields():
    """
        Verify that as_dict returns a dictionary with all expected keys.
    """
    obj = _create_sample_storage_object()

    result = obj.as_dict()

    expected_keys = {"key", "content", "content_type", "metadata", "size", "last_modified"}
    actual_keys = set(result.keys())

    assert actual_keys == expected_keys, (
        "as_dict should contain keys {}, got: {}".format(expected_keys, actual_keys)
    )
    return


def test_as_dict_last_modified_is_isoformat():
    """
        Verify that as_dict serializes last_modified as an ISO format string.
    """
    obj = _create_sample_storage_object()

    result = obj.as_dict()

    actual = result["last_modified"]
    expected = datetime(2026, 1, 15, 10, 30, 0).isoformat()

    assert actual == expected, (
        "last_modified should be ISO format {!r}, got: {!r}".format(expected, actual)
    )
    return


# ---------------------------------------------------------------------------
# JSON round-trip tests
# ---------------------------------------------------------------------------

def test_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    obj = _create_sample_storage_object()

    json_str = obj.to_json()
    parsed = json.loads(json_str)

    has_key = "key" in parsed
    assert has_key is True, "JSON should contain 'key' field"
    return


def test_json_round_trip_preserves_all_fields():
    """
        Verify that serializing to JSON and deserializing back produces
        an equivalent StorageObject.
    """
    original = _create_sample_storage_object()

    json_str = original.to_json()
    restored = StorageObject.from_json(json_str)

    assert restored.key == original.key, (
        "Round-trip key mismatch: {!r} != {!r}".format(restored.key, original.key)
    )
    assert restored.content == original.content, (
        "Round-trip content mismatch: {!r} != {!r}".format(restored.content, original.content)
    )
    assert restored.content_type == original.content_type, (
        "Round-trip content_type mismatch: {!r} != {!r}".format(
            restored.content_type, original.content_type)
    )
    assert restored.metadata == original.metadata, (
        "Round-trip metadata mismatch: {!r} != {!r}".format(
            restored.metadata, original.metadata)
    )
    assert restored.size == original.size, (
        "Round-trip size mismatch: {!r} != {!r}".format(restored.size, original.size)
    )
    assert restored.last_modified == original.last_modified, (
        "Round-trip last_modified mismatch: {!r} != {!r}".format(
            restored.last_modified, original.last_modified)
    )
    return


def test_from_dict_decodes_base64_content():
    """
        Verify that from_dict correctly decodes base64-encoded content
        back to bytes.
    """
    data = {
        "key": "test.bin",
        "content": base64.b64encode(b"\x00\x01\x02\x03").decode("utf-8"),
        "content_type": "application/octet-stream",
        "metadata": {},
        "size": 4,
        "last_modified": "2026-03-01T12:00:00"
    }

    obj = StorageObject.from_dict(data)

    assert obj.content == b"\x00\x01\x02\x03", (
        "from_dict should decode base64 content, got: {!r}".format(obj.content)
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_contains_class_name_key_content_type_size():
    """
        Verify that __repr__ includes the class name, key, content type,
        and size.
    """
    obj = _create_sample_storage_object()

    repr_str = repr(obj)

    has_class_name = "StorageObject" in repr_str
    has_key = "documents/report.pdf" in repr_str
    has_content_type = "application/pdf" in repr_str
    has_size = "13" in repr_str

    assert has_class_name is True, "repr should contain 'StorageObject'"
    assert has_key is True, "repr should contain the key"
    assert has_content_type is True, "repr should contain the content type"
    assert has_size is True, "repr should contain the size"
    return


def test_str_contains_key_content_type_size():
    """
        Verify that __str__ returns a human-readable summary with key,
        content type, and size.
    """
    obj = _create_sample_storage_object()

    str_val = str(obj)

    has_key = "documents/report.pdf" in str_val
    has_content_type = "application/pdf" in str_val
    has_size = "13" in str_val

    assert has_key is True, "str should contain the key"
    assert has_content_type is True, "str should contain the content type"
    assert has_size is True, "str should contain the size"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
