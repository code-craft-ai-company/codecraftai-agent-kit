"""
    Unit tests for the automojo.agentkit.llmconversation module.

    Tests LlmConversation construction, append, truncate, serialization,
    and string representations.

    Feature: llm-integration, Task 2.4
    **Validates: Requirements 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 17.3, 17.4, 17.10, 19.5, 19.6**
"""

from automojo.agentkit.llmmessage import LlmMessage
from automojo.agentkit.llmconversation import LlmConversation


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_llm_conversation_empty_construction():
    """
        LlmConversation defaults to an empty message list.

        **Validates: Requirements 2.9**
    """
    conv = LlmConversation()

    assert conv.count == 0, (
        "Empty conversation should have count 0, got: {}".format(conv.count)
    )
    assert conv.messages == [], (
        "Empty conversation should have empty messages list"
    )

    return


def test_llm_conversation_construction_with_messages():
    """
        LlmConversation accepts an initial list of messages.

        **Validates: Requirements 2.9**
    """
    msgs = [
        LlmMessage(role="system", content="Be helpful"),
        LlmMessage(role="user", content="Hello"),
    ]
    conv = LlmConversation(messages=msgs)

    assert conv.count == 2, (
        "Conversation should have count 2, got: {}".format(conv.count)
    )

    return


# ---------------------------------------------------------------------------
# Append
# ---------------------------------------------------------------------------


def test_llm_conversation_append_increases_count():
    """
        LlmConversation append adds a message and increases the count.

        **Validates: Requirements 2.10, 2.11**
    """
    conv = LlmConversation()
    msg = LlmMessage(role="user", content="Hello")

    conv.append(msg)

    assert conv.count == 1, (
        "Count should be 1 after append, got: {}".format(conv.count)
    )

    return


def test_llm_conversation_append_preserves_order():
    """
        LlmConversation append preserves message order.

        **Validates: Requirements 2.9, 2.10**
    """
    conv = LlmConversation()
    msg1 = LlmMessage(role="user", content="First")
    msg2 = LlmMessage(role="assistant", content="Second")
    msg3 = LlmMessage(role="user", content="Third")

    conv.append(msg1)
    conv.append(msg2)
    conv.append(msg3)

    messages = conv.messages
    assert messages[0].content == "First", "First message content mismatch"
    assert messages[1].content == "Second", "Second message content mismatch"
    assert messages[2].content == "Third", "Third message content mismatch"

    return


def test_llm_conversation_append_multiple_roles():
    """
        LlmConversation append works with all valid roles.

        **Validates: Requirements 2.10**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="system", content="sys"))
    conv.append(LlmMessage(role="user", content="usr"))
    conv.append(LlmMessage(role="assistant", content="ast"))
    conv.append(LlmMessage(role="tool", content="tl"))

    assert conv.count == 4, (
        "Count should be 4 after appending all roles, got: {}".format(conv.count)
    )

    return


# ---------------------------------------------------------------------------
# Messages property returns a copy
# ---------------------------------------------------------------------------


def test_llm_conversation_messages_returns_copy():
    """
        LlmConversation messages property returns a copy of the internal list.

        **Validates: Requirements 2.12**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="user", content="Hello"))

    returned = conv.messages
    returned.append(LlmMessage(role="user", content="Injected"))

    assert conv.count == 1, (
        "Modifying returned list should not affect the conversation"
    )

    return



# ---------------------------------------------------------------------------
# Truncate
# ---------------------------------------------------------------------------


def test_llm_conversation_truncate_no_op_when_under_limit():
    """
        LlmConversation truncate does nothing when count is within the limit.

        **Validates: Requirements 2.13**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="user", content="Hello"))
    conv.append(LlmMessage(role="assistant", content="Hi"))

    conv.truncate(max_messages=5)

    assert conv.count == 2, (
        "Truncate should not remove messages when under limit, got: {}".format(conv.count)
    )

    return


def test_llm_conversation_truncate_removes_oldest_non_system():
    """
        LlmConversation truncate removes the oldest non-system messages first.

        **Validates: Requirements 2.13**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="user", content="First"))
    conv.append(LlmMessage(role="assistant", content="Second"))
    conv.append(LlmMessage(role="user", content="Third"))

    conv.truncate(max_messages=2)

    assert conv.count == 2, (
        "Count should be 2 after truncate, got: {}".format(conv.count)
    )
    messages = conv.messages
    assert messages[0].content == "Second", (
        "Oldest non-system message should be removed, got: {!r}".format(messages[0].content)
    )
    assert messages[1].content == "Third", (
        "Most recent message should be kept, got: {!r}".format(messages[1].content)
    )

    return


def test_llm_conversation_truncate_preserves_system_messages():
    """
        LlmConversation truncate preserves all system messages.

        **Validates: Requirements 2.13**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="system", content="System prompt"))
    conv.append(LlmMessage(role="user", content="First user"))
    conv.append(LlmMessage(role="assistant", content="First reply"))
    conv.append(LlmMessage(role="user", content="Second user"))

    conv.truncate(max_messages=3)

    messages = conv.messages
    system_msgs = [m for m in messages if m.role == "system"]
    assert len(system_msgs) == 1, (
        "System message should be preserved, got {} system messages".format(len(system_msgs))
    )
    assert system_msgs[0].content == "System prompt", (
        "System message content mismatch"
    )
    assert conv.count == 3, (
        "Count should be 3 after truncate, got: {}".format(conv.count)
    )

    return


def test_llm_conversation_truncate_multiple_system_messages():
    """
        LlmConversation truncate preserves multiple system messages.

        **Validates: Requirements 2.13**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="system", content="System 1"))
    conv.append(LlmMessage(role="system", content="System 2"))
    conv.append(LlmMessage(role="user", content="User 1"))
    conv.append(LlmMessage(role="assistant", content="Reply 1"))
    conv.append(LlmMessage(role="user", content="User 2"))

    conv.truncate(max_messages=3)

    messages = conv.messages
    system_msgs = [m for m in messages if m.role == "system"]
    assert len(system_msgs) == 2, (
        "Both system messages should be preserved, got {}".format(len(system_msgs))
    )
    assert conv.count == 3, (
        "Count should be 3 after truncate, got: {}".format(conv.count)
    )

    return


def test_llm_conversation_truncate_all_system_exceeds_limit():
    """
        LlmConversation truncate keeps all system messages even when they
        exceed the limit, removing all non-system messages.

        **Validates: Requirements 2.13**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="system", content="System 1"))
    conv.append(LlmMessage(role="system", content="System 2"))
    conv.append(LlmMessage(role="system", content="System 3"))
    conv.append(LlmMessage(role="user", content="User 1"))

    conv.truncate(max_messages=2)

    messages = conv.messages
    system_msgs = [m for m in messages if m.role == "system"]
    non_system_msgs = [m for m in messages if m.role != "system"]
    assert len(system_msgs) == 3, (
        "All system messages should be preserved"
    )
    assert len(non_system_msgs) == 0, (
        "All non-system messages should be removed"
    )

    return


def test_llm_conversation_truncate_with_tool_messages():
    """
        LlmConversation truncate treats tool messages as non-system.

        **Validates: Requirements 2.13**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="system", content="System"))
    conv.append(LlmMessage(role="user", content="User"))
    conv.append(LlmMessage(role="assistant", content="Call tool"))
    conv.append(LlmMessage(role="tool", content="Tool result"))
    conv.append(LlmMessage(role="assistant", content="Final reply"))

    conv.truncate(max_messages=3)

    messages = conv.messages
    system_msgs = [m for m in messages if m.role == "system"]
    assert len(system_msgs) == 1, "System message should be preserved"
    assert conv.count == 3, (
        "Count should be 3 after truncate, got: {}".format(conv.count)
    )

    return


# ---------------------------------------------------------------------------
# Serialization: to_json, from_json
# ---------------------------------------------------------------------------


def test_llm_conversation_empty_serialization():
    """
        LlmConversation serializes an empty conversation correctly.

        **Validates: Requirements 2.14, 17.3**
    """
    conv = LlmConversation()
    json_str = conv.to_json()

    assert isinstance(json_str, str), "to_json should return a string"
    assert '"messages"' in json_str, "JSON should contain messages key"

    restored = LlmConversation.from_json(json_str)
    assert restored.count == 0, (
        "Restored empty conversation should have count 0"
    )

    return


def test_llm_conversation_to_json():
    """
        LlmConversation to_json returns a valid JSON string.

        **Validates: Requirements 2.14, 17.3**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="user", content="Hello"))
    conv.append(LlmMessage(role="assistant", content="Hi"))

    json_str = conv.to_json()

    assert isinstance(json_str, str), "to_json should return a string"
    assert '"messages"' in json_str, "JSON should contain messages key"

    return


def test_llm_conversation_from_json():
    """
        LlmConversation from_json deserializes a JSON string.

        **Validates: Requirements 2.15, 17.4**
    """
    json_str = '{"messages": [{"role": "user", "content": "Hello", "metadata": {}}]}'
    conv = LlmConversation.from_json(json_str)

    assert conv.count == 1, "from_json should produce a conversation with 1 message"
    assert conv.messages[0].role == "user", "from_json message role mismatch"
    assert conv.messages[0].content == "Hello", "from_json message content mismatch"

    return


def test_llm_conversation_json_round_trip():
    """
        LlmConversation to_json followed by from_json produces an equivalent conversation.

        **Validates: Requirements 2.16, 17.10**
    """
    original = LlmConversation()
    original.append(LlmMessage(role="system", content="Be helpful"))
    original.append(LlmMessage(role="user", content="Hello", metadata={"id": "1"}))
    original.append(LlmMessage(role="assistant", content="Hi there"))

    restored = LlmConversation.from_json(original.to_json())

    assert restored == original, (
        "JSON round-trip should produce an equivalent LlmConversation"
    )

    return


def test_llm_conversation_json_round_trip_with_all_roles():
    """
        LlmConversation JSON round-trip preserves messages with all role types.

        **Validates: Requirements 2.16, 17.10**
    """
    original = LlmConversation()
    original.append(LlmMessage(role="system", content="sys"))
    original.append(LlmMessage(role="user", content="usr"))
    original.append(LlmMessage(role="assistant", content="ast"))
    original.append(LlmMessage(role="tool", content="tl", metadata={"tool_id": "t1"}))

    restored = LlmConversation.from_json(original.to_json())

    assert restored == original, (
        "JSON round-trip should preserve all role types"
    )

    return


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_llm_conversation_repr_contains_class_name_and_count():
    """
        LlmConversation __repr__ includes the class name and message count.

        **Validates: Requirements 19.5**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="user", content="Hello"))
    conv.append(LlmMessage(role="assistant", content="Hi"))

    repr_str = repr(conv)

    assert "LlmConversation" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "2" in repr_str, (
        "repr should contain message count, got: {!r}".format(repr_str)
    )

    return


def test_llm_conversation_repr_empty():
    """
        LlmConversation __repr__ shows count=0 for empty conversation.

        **Validates: Requirements 19.5**
    """
    conv = LlmConversation()
    repr_str = repr(conv)

    assert "0" in repr_str, (
        "repr should show count 0 for empty conversation, got: {!r}".format(repr_str)
    )

    return


# ---------------------------------------------------------------------------
# __str__
# ---------------------------------------------------------------------------


def test_llm_conversation_str_lists_roles():
    """
        LlmConversation __str__ returns a string listing the message roles.

        **Validates: Requirements 19.6**
    """
    conv = LlmConversation()
    conv.append(LlmMessage(role="system", content="sys"))
    conv.append(LlmMessage(role="user", content="usr"))
    conv.append(LlmMessage(role="assistant", content="ast"))

    str_val = str(conv)

    assert "system" in str_val, "str should contain 'system' role"
    assert "user" in str_val, "str should contain 'user' role"
    assert "assistant" in str_val, "str should contain 'assistant' role"

    return


def test_llm_conversation_str_empty():
    """
        LlmConversation __str__ handles empty conversation.

        **Validates: Requirements 19.6**
    """
    conv = LlmConversation()
    str_val = str(conv)

    assert "LlmConversation" in str_val, (
        "str should contain class name, got: {!r}".format(str_val)
    )

    return


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_llm_conversation_eq_same_messages():
    """
        LlmConversation __eq__ returns True for conversations with identical messages.

        **Validates: Requirements 2.9**
    """
    a = LlmConversation()
    a.append(LlmMessage(role="user", content="Hello"))

    b = LlmConversation()
    b.append(LlmMessage(role="user", content="Hello"))

    assert a == b, "Conversations with same messages should be equal"

    return


def test_llm_conversation_eq_different_messages():
    """
        LlmConversation __eq__ returns False for conversations with different messages.

        **Validates: Requirements 2.9**
    """
    a = LlmConversation()
    a.append(LlmMessage(role="user", content="Hello"))

    b = LlmConversation()
    b.append(LlmMessage(role="user", content="Goodbye"))

    assert (a == b) is False, "Conversations with different messages should not be equal"

    return


def test_llm_conversation_eq_different_count():
    """
        LlmConversation __eq__ returns False for conversations with different counts.

        **Validates: Requirements 2.9**
    """
    a = LlmConversation()
    a.append(LlmMessage(role="user", content="Hello"))

    b = LlmConversation()
    a_eq_b = (a == b)

    assert a_eq_b is False, "Conversations with different counts should not be equal"

    return


def test_llm_conversation_eq_non_conversation():
    """
        LlmConversation __eq__ returns False when compared to a non-LlmConversation.

        **Validates: Requirements 2.9**
    """
    conv = LlmConversation()

    assert (conv == "not a conversation") is False, (
        "LlmConversation should not be equal to a string"
    )

    return


def test_llm_conversation_eq_empty_conversations():
    """
        Two empty LlmConversation instances are equal.

        **Validates: Requirements 2.9**
    """
    a = LlmConversation()
    b = LlmConversation()

    assert a == b, "Two empty conversations should be equal"

    return
