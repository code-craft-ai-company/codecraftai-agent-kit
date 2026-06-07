"""
    Unit tests for the ccai.agentkit.llmconversation module.

    Tests LLMConversation construction, append, truncate, serialization,
    and string representations.

    Feature: llm-integration, Task 2.4
    **Validates: Requirements 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 17.3, 17.4, 17.10, 19.5, 19.6**
"""

from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.llmconversation import LLMConversation


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_llm_conversation_empty_construction():
    """
        LLMConversation defaults to an empty message list.

        **Validates: Requirements 2.9**
    """
    conv = LLMConversation()

    assert conv.count == 0, (
        "Empty conversation should have count 0, got: {}".format(conv.count)
    )
    assert conv.messages == [], (
        "Empty conversation should have empty messages list"
    )

    return


def test_llm_conversation_construction_with_messages():
    """
        LLMConversation accepts an initial list of messages.

        **Validates: Requirements 2.9**
    """
    msgs = [
        LLMMessage(role="system", content="Be helpful"),
        LLMMessage(role="user", content="Hello"),
    ]
    conv = LLMConversation(messages=msgs)

    assert conv.count == 2, (
        "Conversation should have count 2, got: {}".format(conv.count)
    )

    return


# ---------------------------------------------------------------------------
# Append
# ---------------------------------------------------------------------------


def test_llm_conversation_append_increases_count():
    """
        LLMConversation append adds a message and increases the count.

        **Validates: Requirements 2.10, 2.11**
    """
    conv = LLMConversation()
    msg = LLMMessage(role="user", content="Hello")

    conv.append(msg)

    assert conv.count == 1, (
        "Count should be 1 after append, got: {}".format(conv.count)
    )

    return


def test_llm_conversation_append_preserves_order():
    """
        LLMConversation append preserves message order.

        **Validates: Requirements 2.9, 2.10**
    """
    conv = LLMConversation()
    msg1 = LLMMessage(role="user", content="First")
    msg2 = LLMMessage(role="assistant", content="Second")
    msg3 = LLMMessage(role="user", content="Third")

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
        LLMConversation append works with all valid roles.

        **Validates: Requirements 2.10**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="system", content="sys"))
    conv.append(LLMMessage(role="user", content="usr"))
    conv.append(LLMMessage(role="assistant", content="ast"))
    conv.append(LLMMessage(role="tool", content="tl"))

    assert conv.count == 4, (
        "Count should be 4 after appending all roles, got: {}".format(conv.count)
    )

    return


# ---------------------------------------------------------------------------
# Messages property returns a copy
# ---------------------------------------------------------------------------


def test_llm_conversation_messages_returns_copy():
    """
        LLMConversation messages property returns a copy of the internal list.

        **Validates: Requirements 2.12**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="user", content="Hello"))

    returned = conv.messages
    returned.append(LLMMessage(role="user", content="Injected"))

    assert conv.count == 1, (
        "Modifying returned list should not affect the conversation"
    )

    return



# ---------------------------------------------------------------------------
# Truncate
# ---------------------------------------------------------------------------


def test_llm_conversation_truncate_no_op_when_under_limit():
    """
        LLMConversation truncate does nothing when count is within the limit.

        **Validates: Requirements 2.13**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="user", content="Hello"))
    conv.append(LLMMessage(role="assistant", content="Hi"))

    conv.truncate(max_messages=5)

    assert conv.count == 2, (
        "Truncate should not remove messages when under limit, got: {}".format(conv.count)
    )

    return


def test_llm_conversation_truncate_removes_oldest_non_system():
    """
        LLMConversation truncate removes the oldest non-system messages first.

        **Validates: Requirements 2.13**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="user", content="First"))
    conv.append(LLMMessage(role="assistant", content="Second"))
    conv.append(LLMMessage(role="user", content="Third"))

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
        LLMConversation truncate preserves all system messages.

        **Validates: Requirements 2.13**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="system", content="System prompt"))
    conv.append(LLMMessage(role="user", content="First user"))
    conv.append(LLMMessage(role="assistant", content="First reply"))
    conv.append(LLMMessage(role="user", content="Second user"))

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
        LLMConversation truncate preserves multiple system messages.

        **Validates: Requirements 2.13**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="system", content="System 1"))
    conv.append(LLMMessage(role="system", content="System 2"))
    conv.append(LLMMessage(role="user", content="User 1"))
    conv.append(LLMMessage(role="assistant", content="Reply 1"))
    conv.append(LLMMessage(role="user", content="User 2"))

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
        LLMConversation truncate keeps all system messages even when they
        exceed the limit, removing all non-system messages.

        **Validates: Requirements 2.13**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="system", content="System 1"))
    conv.append(LLMMessage(role="system", content="System 2"))
    conv.append(LLMMessage(role="system", content="System 3"))
    conv.append(LLMMessage(role="user", content="User 1"))

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
        LLMConversation truncate treats tool messages as non-system.

        **Validates: Requirements 2.13**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="system", content="System"))
    conv.append(LLMMessage(role="user", content="User"))
    conv.append(LLMMessage(role="assistant", content="Call tool"))
    conv.append(LLMMessage(role="tool", content="Tool result"))
    conv.append(LLMMessage(role="assistant", content="Final reply"))

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
        LLMConversation serializes an empty conversation correctly.

        **Validates: Requirements 2.14, 17.3**
    """
    conv = LLMConversation()
    json_str = conv.to_json()

    assert isinstance(json_str, str), "to_json should return a string"
    assert '"messages"' in json_str, "JSON should contain messages key"

    restored = LLMConversation.from_json(json_str)
    assert restored.count == 0, (
        "Restored empty conversation should have count 0"
    )

    return


def test_llm_conversation_to_json():
    """
        LLMConversation to_json returns a valid JSON string.

        **Validates: Requirements 2.14, 17.3**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="user", content="Hello"))
    conv.append(LLMMessage(role="assistant", content="Hi"))

    json_str = conv.to_json()

    assert isinstance(json_str, str), "to_json should return a string"
    assert '"messages"' in json_str, "JSON should contain messages key"

    return


def test_llm_conversation_from_json():
    """
        LLMConversation from_json deserializes a JSON string.

        **Validates: Requirements 2.15, 17.4**
    """
    json_str = '{"messages": [{"role": "user", "content": "Hello", "metadata": {}}]}'
    conv = LLMConversation.from_json(json_str)

    assert conv.count == 1, "from_json should produce a conversation with 1 message"
    assert conv.messages[0].role == "user", "from_json message role mismatch"
    assert conv.messages[0].content == "Hello", "from_json message content mismatch"

    return


def test_llm_conversation_json_round_trip():
    """
        LLMConversation to_json followed by from_json produces an equivalent conversation.

        **Validates: Requirements 2.16, 17.10**
    """
    original = LLMConversation()
    original.append(LLMMessage(role="system", content="Be helpful"))
    original.append(LLMMessage(role="user", content="Hello", metadata={"id": "1"}))
    original.append(LLMMessage(role="assistant", content="Hi there"))

    restored = LLMConversation.from_json(original.to_json())

    assert restored == original, (
        "JSON round-trip should produce an equivalent LLMConversation"
    )

    return


def test_llm_conversation_json_round_trip_with_all_roles():
    """
        LLMConversation JSON round-trip preserves messages with all role types.

        **Validates: Requirements 2.16, 17.10**
    """
    original = LLMConversation()
    original.append(LLMMessage(role="system", content="sys"))
    original.append(LLMMessage(role="user", content="usr"))
    original.append(LLMMessage(role="assistant", content="ast"))
    original.append(LLMMessage(role="tool", content="tl", metadata={"tool_id": "t1"}))

    restored = LLMConversation.from_json(original.to_json())

    assert restored == original, (
        "JSON round-trip should preserve all role types"
    )

    return


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_llm_conversation_repr_contains_class_name_and_count():
    """
        LLMConversation __repr__ includes the class name and message count.

        **Validates: Requirements 19.5**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="user", content="Hello"))
    conv.append(LLMMessage(role="assistant", content="Hi"))

    repr_str = repr(conv)

    assert "LLMConversation" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "2" in repr_str, (
        "repr should contain message count, got: {!r}".format(repr_str)
    )

    return


def test_llm_conversation_repr_empty():
    """
        LLMConversation __repr__ shows count=0 for empty conversation.

        **Validates: Requirements 19.5**
    """
    conv = LLMConversation()
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
        LLMConversation __str__ returns a string listing the message roles.

        **Validates: Requirements 19.6**
    """
    conv = LLMConversation()
    conv.append(LLMMessage(role="system", content="sys"))
    conv.append(LLMMessage(role="user", content="usr"))
    conv.append(LLMMessage(role="assistant", content="ast"))

    str_val = str(conv)

    assert "system" in str_val, "str should contain 'system' role"
    assert "user" in str_val, "str should contain 'user' role"
    assert "assistant" in str_val, "str should contain 'assistant' role"

    return


def test_llm_conversation_str_empty():
    """
        LLMConversation __str__ handles empty conversation.

        **Validates: Requirements 19.6**
    """
    conv = LLMConversation()
    str_val = str(conv)

    assert "LLMConversation" in str_val, (
        "str should contain class name, got: {!r}".format(str_val)
    )

    return


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_llm_conversation_eq_same_messages():
    """
        LLMConversation __eq__ returns True for conversations with identical messages.

        **Validates: Requirements 2.9**
    """
    a = LLMConversation()
    a.append(LLMMessage(role="user", content="Hello"))

    b = LLMConversation()
    b.append(LLMMessage(role="user", content="Hello"))

    assert a == b, "Conversations with same messages should be equal"

    return


def test_llm_conversation_eq_different_messages():
    """
        LLMConversation __eq__ returns False for conversations with different messages.

        **Validates: Requirements 2.9**
    """
    a = LLMConversation()
    a.append(LLMMessage(role="user", content="Hello"))

    b = LLMConversation()
    b.append(LLMMessage(role="user", content="Goodbye"))

    assert (a == b) is False, "Conversations with different messages should not be equal"

    return


def test_llm_conversation_eq_different_count():
    """
        LLMConversation __eq__ returns False for conversations with different counts.

        **Validates: Requirements 2.9**
    """
    a = LLMConversation()
    a.append(LLMMessage(role="user", content="Hello"))

    b = LLMConversation()
    a_eq_b = (a == b)

    assert a_eq_b is False, "Conversations with different counts should not be equal"

    return


def test_llm_conversation_eq_non_conversation():
    """
        LLMConversation __eq__ returns False when compared to a non-LLMConversation.

        **Validates: Requirements 2.9**
    """
    conv = LLMConversation()

    assert (conv == "not a conversation") is False, (
        "LLMConversation should not be equal to a string"
    )

    return


def test_llm_conversation_eq_empty_conversations():
    """
        Two empty LLMConversation instances are equal.

        **Validates: Requirements 2.9**
    """
    a = LLMConversation()
    b = LLMConversation()

    assert a == b, "Two empty conversations should be equal"

    return
