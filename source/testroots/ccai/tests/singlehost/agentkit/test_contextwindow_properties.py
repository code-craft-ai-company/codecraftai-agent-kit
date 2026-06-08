"""
    .. module:: ccai.tests.singlehost.agentkit.test_contextwindow_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for ContextWindow correctness invariants.

    Uses ccai.testbase.properties to verify:
    - Property 7: ContextWindow build output fits within token limit
    - Property 8: ContextWindow FIFO preserves system messages

    **Validates: Requirements 8.3, 8.4, 8.5, 8.10**
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given, assume
from ccai.testbase.properties import strategies as st

from ccai.agentkit.contextwindow import ContextWindow
from ccai.agentkit.contextwindowstrategy import ContextWindowStrategy
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryerrors import ContextWindowError
from ccai.agentkit.memoryscope import MemoryScope


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_token_counter(text: str) -> int:
    """
        A simple token counter that counts whitespace-separated words.
    """
    if text is None or len(text) == 0:
        return 0
    rtnval = len(text.split())
    return rtnval


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_role = st.sampled_from(["user", "assistant"])

_system_content = st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz ")

_message_content = st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz ")

_max_tokens = st.integers(min_value=50, max_value=500)

_system_message_count = st.integers(min_value=0, max_value=3)

_non_system_message_count = st.integers(min_value=1, max_value=10)

_memory_content = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz ")

_scope = st.sampled_from([MemoryScope.AGENT, MemoryScope.SHARED, MemoryScope.GLOBAL])

_identifier = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789")


# ---------------------------------------------------------------------------
# Property 7: ContextWindow build output fits within token limit
# ---------------------------------------------------------------------------

@given(
    max_tokens=_max_tokens,
    sys_count=_system_message_count,
    nonsys_count=_non_system_message_count,
    constraints={"max_examples": 50},
)
def test_contextwindow_build_output_fits_within_token_limit(
    max_tokens: int,
    sys_count: int,
    nonsys_count: int,
) -> None:
    """
        For all valid conversations and max_tokens, the output of build
        has total tokens <= max_tokens (when build does not raise
        ContextWindowError).

        **Validates: Requirements 8.3, 8.4**
    """
    messages = []
    for i in range(sys_count):
        messages.append(LLMMessage(role="system", content="system instruction {}".format(i)))
    for i in range(nonsys_count):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append(LLMMessage(role=role, content="message content {}".format(i)))

    conversation = LLMConversation(messages=messages)

    cw = ContextWindow(
        max_tokens=max_tokens,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_simple_token_counter,
    )

    try:
        result = cw.build(conversation=conversation)
    except ContextWindowError:
        # If the context cannot fit, the property does not apply.
        return

    total_tokens = 0
    for msg in result.messages:
        total_tokens = total_tokens + _simple_token_counter(msg.content)

    testbase.assert_true(
        total_tokens <= max_tokens,
        "Build output should fit within {} tokens, but got {} tokens.".format(
            max_tokens, total_tokens)
    )
    return


# ---------------------------------------------------------------------------
# Property 8: ContextWindow FIFO preserves system messages
# ---------------------------------------------------------------------------

@given(
    max_tokens=_max_tokens,
    sys_count=st.integers(min_value=1, max_value=4),
    nonsys_count=_non_system_message_count,
    constraints={"max_examples": 50},
)
def test_contextwindow_fifo_preserves_system_messages(
    max_tokens: int,
    sys_count: int,
    nonsys_count: int,
) -> None:
    """
        For all conversations with system messages, applying FIFO strategy
        never removes system messages.

        **Validates: Requirements 8.5, 8.10**
    """
    system_messages = []
    for i in range(sys_count):
        system_messages.append(LLMMessage(role="system", content="sys {}".format(i)))

    non_system_messages = []
    for i in range(nonsys_count):
        role = "user" if i % 2 == 0 else "assistant"
        non_system_messages.append(LLMMessage(role=role, content="msg {}".format(i)))

    all_messages = system_messages + non_system_messages
    conversation = LLMConversation(messages=all_messages)

    cw = ContextWindow(
        max_tokens=max_tokens,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_simple_token_counter,
    )

    try:
        result = cw.build(conversation=conversation)
    except ContextWindowError:
        # If the context cannot fit even after trimming, the property
        # still holds: system messages were never removed, the error
        # means non-system removal was insufficient.
        return

    result_system = [m for m in result.messages if m.role == "system"]

    testbase.assert_equal(
        len(result_system), sys_count,
        "FIFO should preserve all {} system messages, but found {}.".format(
            sys_count, len(result_system))
    )

    for i in range(sys_count):
        testbase.assert_equal(
            result_system[i].content, system_messages[i].content,
            "System message {} content mismatch after FIFO trimming.".format(i)
        )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
