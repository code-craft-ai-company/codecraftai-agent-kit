"""
    Property-based tests for the automojo.agentkit.llmconversation module.

    Uses automojo.testbase.properties to verify:
    - Property 2: LLMConversation JSON round-trip
    - Property 10: LLMConversation append increases count and preserves order
    - Property 11: LLMConversation messages property returns a copy
    - Property 12: LLMConversation truncate preserves system messages

    **Validates: Requirements 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 17.3, 17.4, 17.10**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.llmmessage import LLMMessage
from automojo.agentkit.llmconversation import LLMConversation


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

VALID_ROLES = ["system", "user", "assistant", "tool"]

_valid_role = st.sampled_from(VALID_ROLES)

_content = st.text(min_size=0, max_size=200)

_metadata_value = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
    st.none(),
)

_metadata = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=_metadata_value,
    max_size=5,
)

_llm_message = st.builds(
    LLMMessage,
    role=_valid_role,
    content=_content,
    metadata=_metadata,
)

_llm_message_list = st.lists(_llm_message, min_size=0, max_size=20)


# ---------------------------------------------------------------------------
# Property 2: LLMConversation JSON round-trip
# ---------------------------------------------------------------------------

@given(
    messages=_llm_message_list,
    constraints={"max_examples": 50},
)
def test_llmconversation_json_roundtrip(
    messages: list,
) -> None:
    """
        **Validates: Requirements 2.14, 2.15, 2.16, 17.3, 17.4, 17.10**

        For any valid LLMConversation instance (containing zero or more valid
        LLMMessage objects), calling to_json() and then from_json() on the
        resulting string shall produce an LLMConversation whose messages list
        is equal to the original.
    """
    original = LLMConversation(messages=messages)

    json_str = original.to_json()
    restored = LLMConversation.from_json(json_str)

    assert original == restored, (
        "LLMConversation JSON round-trip failed. "
        "Original count: {}, Restored count: {}.".format(
            original.count, restored.count,
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 10: LLMConversation append increases count and preserves order
# ---------------------------------------------------------------------------

@given(
    initial_messages=_llm_message_list,
    new_message=_llm_message,
    constraints={"max_examples": 50},
)
def test_llmconversation_append_increases_count_and_preserves_order(
    initial_messages: list,
    new_message: LLMMessage,
) -> None:
    """
        **Validates: Requirements 2.9, 2.10, 2.11**

        For any LLMConversation and any valid LLMMessage, calling
        append(message) shall increase the conversation's count by one,
        and the last element of the messages list shall be the appended
        message.
    """
    conversation = LLMConversation(messages=list(initial_messages))
    count_before = conversation.count

    conversation.append(new_message)

    assert conversation.count == count_before + 1, (
        "Append should increase count by 1. "
        "Before: {}, After: {}.".format(count_before, conversation.count)
    )

    last_message = conversation.messages[-1]
    assert last_message == new_message, (
        "Last message after append should be the appended message. "
        "Expected role={!r}, content={!r}. "
        "Got role={!r}, content={!r}.".format(
            new_message.role, new_message.content,
            last_message.role, last_message.content,
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 11: LLMConversation messages property returns a copy
# ---------------------------------------------------------------------------

@given(
    messages=_llm_message_list,
    constraints={"max_examples": 50},
)
def test_llmconversation_messages_returns_copy(
    messages: list,
) -> None:
    """
        **Validates: Requirements 2.12**

        For any LLMConversation, the list returned by the messages property
        shall be a separate copy. Modifying the returned list shall not
        affect the conversation's internal state.
    """
    conversation = LLMConversation(messages=list(messages))
    count_before = conversation.count

    returned_list = conversation.messages
    extra_message = LLMMessage(role="user", content="injected message")
    returned_list.append(extra_message)

    assert conversation.count == count_before, (
        "Modifying the returned messages list should not affect the "
        "conversation's internal state. Count before: {}, after: {}.".format(
            count_before, conversation.count
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 12: LLMConversation truncate preserves system messages
# ---------------------------------------------------------------------------

@given(
    messages=_llm_message_list,
    max_messages=st.integers(min_value=0, max_value=30),
    constraints={"max_examples": 50},
)
def test_llmconversation_truncate_preserves_system_messages(
    messages: list,
    max_messages: int,
) -> None:
    """
        **Validates: Requirements 2.13**

        For any LLMConversation containing a mix of system and non-system
        messages, and any max_messages limit, calling truncate(max_messages)
        shall preserve all system messages and remove the oldest non-system
        messages first, resulting in a conversation with at most max_messages
        total messages (or all system messages if max_messages is less than
        the system message count).
    """
    conversation = LLMConversation(messages=list(messages))

    system_count = sum(1 for m in messages if m.role == "system")

    conversation.truncate(max_messages)

    truncated_system_count = sum(
        1 for m in conversation.messages if m.role == "system"
    )
    assert truncated_system_count == system_count, (
        "Truncate should preserve all system messages. "
        "Expected {} system messages, got {}.".format(
            system_count, truncated_system_count
        )
    )

    expected_max = max(max_messages, system_count)
    assert conversation.count <= expected_max, (
        "After truncate({}), conversation should have at most {} messages "
        "(system_count={}). Got {}.".format(
            max_messages, expected_max, system_count, conversation.count
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
