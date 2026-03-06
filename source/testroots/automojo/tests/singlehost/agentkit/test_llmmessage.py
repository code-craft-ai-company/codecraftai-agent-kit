"""
    Unit tests for the automojo.agentkit.llmmessage module.

    Tests LlmMessage construction, role validation, read-only properties,
    serialization, and string representations.

    Feature: llm-integration, Task 2.4
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 17.1, 17.2, 17.9, 19.3, 19.4**
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmmessage import LlmMessage


# ---------------------------------------------------------------------------
# Construction with valid roles
# ---------------------------------------------------------------------------


def test_llm_message_system_role():
    """
        LlmMessage accepts the 'system' role.

        **Validates: Requirements 2.1**
    """
    msg = LlmMessage(role="system", content="You are a helpful assistant.")

    assert msg.role == "system", (
        "role mismatch: {!r}".format(msg.role)
    )
    assert msg.content == "You are a helpful assistant.", (
        "content mismatch: {!r}".format(msg.content)
    )

    return


def test_llm_message_user_role():
    """
        LlmMessage accepts the 'user' role.

        **Validates: Requirements 2.1**
    """
    msg = LlmMessage(role="user", content="Hello!")

    assert msg.role == "user", (
        "role mismatch: {!r}".format(msg.role)
    )

    return


def test_llm_message_assistant_role():
    """
        LlmMessage accepts the 'assistant' role.

        **Validates: Requirements 2.1**
    """
    msg = LlmMessage(role="assistant", content="Hi there!")

    assert msg.role == "assistant", (
        "role mismatch: {!r}".format(msg.role)
    )

    return


def test_llm_message_tool_role():
    """
        LlmMessage accepts the 'tool' role.

        **Validates: Requirements 2.1**
    """
    msg = LlmMessage(role="tool", content='{"result": 42}')

    assert msg.role == "tool", (
        "role mismatch: {!r}".format(msg.role)
    )

    return


# ---------------------------------------------------------------------------
# Invalid role raises SemanticError
# ---------------------------------------------------------------------------


def test_llm_message_invalid_role_raises_semantic_error():
    """
        LlmMessage raises SemanticError for an invalid role value.

        **Validates: Requirements 2.3**
    """
    caught = False

    try:
        LlmMessage(role="admin", content="test")
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmMessage should raise SemanticError for invalid role"
    )

    return


def test_llm_message_empty_role_raises_semantic_error():
    """
        LlmMessage raises SemanticError for an empty string role.

        **Validates: Requirements 2.3**
    """
    caught = False

    try:
        LlmMessage(role="", content="test")
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmMessage should raise SemanticError for empty role"
    )

    return



# ---------------------------------------------------------------------------
# Empty metadata and special characters in content
# ---------------------------------------------------------------------------


def test_llm_message_empty_metadata_default():
    """
        LlmMessage defaults to an empty metadata dictionary when none is provided.

        **Validates: Requirements 2.1, 2.2**
    """
    msg = LlmMessage(role="user", content="Hello")

    assert msg.metadata == {}, (
        "metadata should default to empty dict, got: {!r}".format(msg.metadata)
    )

    return


def test_llm_message_explicit_empty_metadata():
    """
        LlmMessage accepts an explicitly empty metadata dictionary.

        **Validates: Requirements 2.1**
    """
    msg = LlmMessage(role="user", content="Hello", metadata={})

    assert msg.metadata == {}, (
        "metadata should be empty dict, got: {!r}".format(msg.metadata)
    )

    return


def test_llm_message_with_metadata():
    """
        LlmMessage stores and returns metadata correctly.

        **Validates: Requirements 2.1, 2.2**
    """
    meta = {"tool_call_id": "call_123", "function": "search"}
    msg = LlmMessage(role="tool", content="result", metadata=meta)

    assert msg.metadata == meta, (
        "metadata mismatch: {!r}".format(msg.metadata)
    )

    return


def test_llm_message_metadata_returns_copy():
    """
        LlmMessage metadata property returns a copy, not the internal dict.

        **Validates: Requirements 2.2**
    """
    meta = {"key": "value"}
    msg = LlmMessage(role="user", content="test", metadata=meta)

    returned = msg.metadata
    returned["injected"] = "bad"

    assert "injected" not in msg.metadata, (
        "Modifying returned metadata should not affect the message"
    )

    return


def test_llm_message_special_characters_in_content():
    """
        LlmMessage handles special characters in content correctly.

        **Validates: Requirements 2.1**
    """
    special_content = 'Line1\nLine2\t"quoted" <html>&amp; ñ 日本語'
    msg = LlmMessage(role="user", content=special_content)

    assert msg.content == special_content, (
        "content with special characters mismatch: {!r}".format(msg.content)
    )

    return


def test_llm_message_empty_content():
    """
        LlmMessage accepts empty string content.

        **Validates: Requirements 2.1**
    """
    msg = LlmMessage(role="user", content="")

    assert msg.content == "", (
        "content should be empty string, got: {!r}".format(msg.content)
    )

    return


# ---------------------------------------------------------------------------
# Serialization: as_dict, to_json, from_dict, from_json
# ---------------------------------------------------------------------------


def test_llm_message_as_dict():
    """
        LlmMessage as_dict returns a dictionary with role, content, and metadata.

        **Validates: Requirements 2.4**
    """
    msg = LlmMessage(role="user", content="Hello", metadata={"key": "val"})
    result = msg.as_dict()

    assert result["role"] == "user", "as_dict role mismatch"
    assert result["content"] == "Hello", "as_dict content mismatch"
    assert result["metadata"] == {"key": "val"}, "as_dict metadata mismatch"

    return


def test_llm_message_to_json():
    """
        LlmMessage to_json returns a valid JSON string.

        **Validates: Requirements 2.5, 17.1**
    """
    msg = LlmMessage(role="assistant", content="Hi")
    json_str = msg.to_json()

    assert isinstance(json_str, str), "to_json should return a string"
    assert '"role"' in json_str, "JSON should contain role key"
    assert '"assistant"' in json_str, "JSON should contain role value"

    return


def test_llm_message_from_dict():
    """
        LlmMessage from_dict constructs a message from a dictionary.

        **Validates: Requirements 2.6**
    """
    data = {"role": "user", "content": "test message", "metadata": {"k": "v"}}
    msg = LlmMessage.from_dict(data)

    assert msg.role == "user", "from_dict role mismatch"
    assert msg.content == "test message", "from_dict content mismatch"
    assert msg.metadata == {"k": "v"}, "from_dict metadata mismatch"

    return


def test_llm_message_from_dict_without_metadata():
    """
        LlmMessage from_dict handles missing metadata key gracefully.

        **Validates: Requirements 2.6**
    """
    data = {"role": "system", "content": "instructions"}
    msg = LlmMessage.from_dict(data)

    assert msg.role == "system", "from_dict role mismatch"
    assert msg.metadata == {}, "from_dict should default metadata to empty dict"

    return


def test_llm_message_from_json():
    """
        LlmMessage from_json deserializes a JSON string into an LlmMessage.

        **Validates: Requirements 2.7, 17.2**
    """
    json_str = '{"role": "user", "content": "hello", "metadata": {}}'
    msg = LlmMessage.from_json(json_str)

    assert msg.role == "user", "from_json role mismatch"
    assert msg.content == "hello", "from_json content mismatch"

    return


def test_llm_message_json_round_trip():
    """
        LlmMessage to_json followed by from_json produces an equivalent message.

        **Validates: Requirements 2.8, 17.9**
    """
    original = LlmMessage(role="assistant", content="response text", metadata={"id": "abc"})
    restored = LlmMessage.from_json(original.to_json())

    assert restored == original, (
        "JSON round-trip should produce an equivalent LlmMessage"
    )

    return


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_llm_message_repr_contains_class_name_and_role():
    """
        LlmMessage __repr__ includes the class name and role.

        **Validates: Requirements 19.3**
    """
    msg = LlmMessage(role="user", content="Hello world")
    repr_str = repr(msg)

    assert "LlmMessage" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "user" in repr_str, (
        "repr should contain role, got: {!r}".format(repr_str)
    )

    return


def test_llm_message_repr_truncates_long_content():
    """
        LlmMessage __repr__ truncates content longer than 50 characters.

        **Validates: Requirements 19.3**
    """
    long_content = "a" * 100
    msg = LlmMessage(role="user", content=long_content)
    repr_str = repr(msg)

    assert ("a" * 100) not in repr_str, (
        "repr should not contain the full 100-char content"
    )
    assert "..." in repr_str, (
        "repr should contain truncation indicator '...'"
    )

    return


def test_llm_message_repr_short_content_not_truncated():
    """
        LlmMessage __repr__ does not truncate short content.

        **Validates: Requirements 19.3**
    """
    msg = LlmMessage(role="user", content="short")
    repr_str = repr(msg)

    assert "short" in repr_str, (
        "repr should contain the full short content, got: {!r}".format(repr_str)
    )
    assert "..." not in repr_str, (
        "repr should not contain truncation indicator for short content"
    )

    return


# ---------------------------------------------------------------------------
# __str__
# ---------------------------------------------------------------------------


def test_llm_message_str_contains_role_and_content():
    """
        LlmMessage __str__ returns a string with role and content.

        **Validates: Requirements 19.4**
    """
    msg = LlmMessage(role="system", content="Be helpful")
    str_val = str(msg)

    assert "system" in str_val, (
        "str should contain role, got: {!r}".format(str_val)
    )
    assert "Be helpful" in str_val, (
        "str should contain content, got: {!r}".format(str_val)
    )

    return


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_llm_message_eq_same_values():
    """
        LlmMessage __eq__ returns True for messages with identical fields.

        **Validates: Requirements 2.1**
    """
    a = LlmMessage(role="user", content="hello", metadata={"k": "v"})
    b = LlmMessage(role="user", content="hello", metadata={"k": "v"})

    assert a == b, "LlmMessages with same values should be equal"

    return


def test_llm_message_eq_different_role():
    """
        LlmMessage __eq__ returns False for messages with different roles.

        **Validates: Requirements 2.1**
    """
    a = LlmMessage(role="user", content="hello")
    b = LlmMessage(role="assistant", content="hello")

    assert (a == b) is False, "LlmMessages with different roles should not be equal"

    return


def test_llm_message_eq_different_content():
    """
        LlmMessage __eq__ returns False for messages with different content.

        **Validates: Requirements 2.1**
    """
    a = LlmMessage(role="user", content="hello")
    b = LlmMessage(role="user", content="goodbye")

    assert (a == b) is False, "LlmMessages with different content should not be equal"

    return


def test_llm_message_eq_different_metadata():
    """
        LlmMessage __eq__ returns False for messages with different metadata.

        **Validates: Requirements 2.1**
    """
    a = LlmMessage(role="user", content="hello", metadata={"a": 1})
    b = LlmMessage(role="user", content="hello", metadata={"b": 2})

    assert (a == b) is False, "LlmMessages with different metadata should not be equal"

    return


def test_llm_message_eq_non_llm_message():
    """
        LlmMessage __eq__ returns False when compared to a non-LlmMessage object.

        **Validates: Requirements 2.1**
    """
    msg = LlmMessage(role="user", content="hello")

    assert (msg == "not a message") is False, (
        "LlmMessage should not be equal to a string"
    )

    return
