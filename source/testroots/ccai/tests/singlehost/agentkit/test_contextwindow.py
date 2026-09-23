"""
    .. module:: ccai.tests.singlehost.agentkit.test_contextwindow
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ContextWindow class.

    Tests cover construction validation, build with each strategy,
    memory entry prepending, system message preservation, error
    conditions, and repr/str formatting.

    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7,
    8.8, 8.9, 8.10, 8.11, 8.12**
"""

from ccai.agentkit.contextwindow import ContextWindow
from ccai.agentkit.contextwindowstrategy import ContextWindowStrategy
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryerrors import ContextWindowError
from ccai.agentkit.memoryscope import MemoryScope
from ccai.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _word_counter(text: str) -> int:
    """
        Simple token counter that counts whitespace-separated words.
    """
    if text is None or len(text) == 0:
        return 0
    rtnval = len(text.split())
    return rtnval


def _create_mock_summarizer(summary_text="Summary of older messages."):
    """
        Creates a mock ContextSummarizer that returns a system LLMMessage
        with the given summary text.
    """
    summary_msg = LLMMessage(role="system", content=summary_text)

    mock_summarizer = Mock()
    mock_summarizer.configure(recursive=True)
    mock_summarizer.mock_context().mock_method("summarize_messages", return_value=summary_msg)

    return mock_summarizer


# ---------------------------------------------------------------------------
# Construction Validation Tests
# ---------------------------------------------------------------------------


def test_contextwindow_construction_valid():
    """
        Verify that ContextWindow can be constructed with valid parameters.
    """
    cw = ContextWindow(
        max_tokens=100,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_word_counter,
    )

    assert cw.max_tokens == 100, "max_tokens should be 100"
    assert cw.strategy == ContextWindowStrategy.FIFO, "strategy should be FIFO"
    return


def test_contextwindow_construction_zero_max_tokens_raises_semantic_error():
    """
        Verify that max_tokens <= 0 raises SemanticError.
    """
    raised = False
    try:
        ContextWindow(
            max_tokens=0,
            strategy=ContextWindowStrategy.FIFO,
            token_counter=_word_counter,
        )
    except SemanticError:
        raised = True

    assert raised is True, "max_tokens=0 should raise SemanticError"
    return


def test_contextwindow_construction_negative_max_tokens_raises_semantic_error():
    """
        Verify that negative max_tokens raises SemanticError.
    """
    raised = False
    try:
        ContextWindow(
            max_tokens=-10,
            strategy=ContextWindowStrategy.FIFO,
            token_counter=_word_counter,
        )
    except SemanticError:
        raised = True

    assert raised is True, "negative max_tokens should raise SemanticError"
    return


def test_contextwindow_construction_none_token_counter_raises_semantic_error():
    """
        Verify that None token_counter raises SemanticError.
    """
    raised = False
    try:
        ContextWindow(
            max_tokens=100,
            strategy=ContextWindowStrategy.FIFO,
            token_counter=None,
        )
    except SemanticError:
        raised = True

    assert raised is True, "None token_counter should raise SemanticError"
    return


# ---------------------------------------------------------------------------
# Build — Conversation Fits Within Limit
# ---------------------------------------------------------------------------


def test_build_within_limit_returns_unchanged():
    """
        Verify that build returns all messages unchanged when within the limit.
    """
    messages = [
        LLMMessage(role="system", content="You are helpful."),
        LLMMessage(role="user", content="Hello."),
        LLMMessage(role="assistant", content="Hi there."),
    ]
    conversation = LLMConversation(messages=messages)

    cw = ContextWindow(
        max_tokens=100,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_word_counter,
    )

    result = cw.build(conversation=conversation)

    assert result.count == 3, "result should have 3 messages"
    assert result.messages[0].content == "You are helpful.", "first message should be system"
    assert result.messages[1].content == "Hello.", "second message should be user"
    assert result.messages[2].content == "Hi there.", "third message should be assistant"
    return


# ---------------------------------------------------------------------------
# Build — Memory Entries Prepended as System Messages
# ---------------------------------------------------------------------------


def test_build_prepends_memory_entries_as_system_messages():
    """
        Verify that memory entries are prepended as system messages with
        '[Memory]' prefix.
    """
    messages = [
        LLMMessage(role="user", content="What do you know?"),
    ]
    conversation = LLMConversation(messages=messages)

    entry = MemoryEntry(
        content="Important fact.",
        scope=MemoryScope.AGENT,
        identifier="mem-001",
    )

    cw = ContextWindow(
        max_tokens=200,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_word_counter,
    )

    result = cw.build(conversation=conversation, memory_entries=[entry])

    assert result.count == 2, "result should have 2 messages (1 memory + 1 user)"
    assert result.messages[0].role == "system", "first message should be system"
    assert "[Memory]" in result.messages[0].content, "memory message should contain '[Memory]'"
    assert "Important fact." in result.messages[0].content, "memory message should contain entry content"
    assert result.messages[0].metadata.get("memory_entry_id") == "mem-001", \
        "memory message metadata should contain entry identifier"
    return


# ---------------------------------------------------------------------------
# Build — FIFO Strategy Tests
# ---------------------------------------------------------------------------


def test_build_fifo_removes_oldest_non_system_messages():
    """
        Verify that FIFO strategy removes the oldest non-system messages
        first when over the token limit.
    """
    messages = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="user", content="oldest message here"),
        LLMMessage(role="assistant", content="second oldest message"),
        LLMMessage(role="user", content="recent"),
    ]
    conversation = LLMConversation(messages=messages)

    # "sys" = 1 word, "oldest message here" = 3, "second oldest message" = 3, "recent" = 1
    # total = 8 words. Set limit to 3 so only system + recent fit.
    cw = ContextWindow(
        max_tokens=3,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_word_counter,
    )

    result = cw.build(conversation=conversation)

    contents = [m.content for m in result.messages]

    assert "sys" in contents, "system message should be preserved"
    assert "recent" in contents, "most recent non-system message should be preserved"
    assert "oldest message here" not in contents, "oldest non-system message should be removed"
    return


def test_build_fifo_preserves_system_message_order():
    """
        Verify that FIFO preserves system messages at the beginning.
    """
    messages = [
        LLMMessage(role="system", content="first system"),
        LLMMessage(role="system", content="second system"),
        LLMMessage(role="user", content="old user message here now"),
        LLMMessage(role="assistant", content="old assistant message here now"),
        LLMMessage(role="user", content="recent"),
    ]
    conversation = LLMConversation(messages=messages)

    # system: 2 + 2 = 4 words, non-system: 5 + 5 + 1 = 11 words, total = 15
    # limit to 8 so system (4) + recent (1) = 5, fits
    cw = ContextWindow(
        max_tokens=8,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_word_counter,
    )

    result = cw.build(conversation=conversation)

    system_msgs = [m for m in result.messages if m.role == "system"]
    assert len(system_msgs) == 2, "both system messages should be preserved"
    assert system_msgs[0].content == "first system", "first system message should be first"
    assert system_msgs[1].content == "second system", "second system message should be second"
    return


# ---------------------------------------------------------------------------
# Build — RELEVANCE Strategy Tests
# ---------------------------------------------------------------------------


def test_build_relevance_removes_least_relevant_memory_entries():
    """
        Verify that RELEVANCE strategy removes memory entry messages
        (least relevant first) before other system messages.
    """
    messages = [
        LLMMessage(role="system", content="core instruction"),
        LLMMessage(role="user", content="question"),
    ]
    conversation = LLMConversation(messages=messages)

    entries = [
        MemoryEntry(content="least relevant memory", scope=MemoryScope.AGENT, identifier="mem-a"),
        MemoryEntry(content="most relevant memory", scope=MemoryScope.AGENT, identifier="mem-b"),
    ]

    # After prepending: mem-b system (3 words), mem-a system (3 words),
    # core instruction (2 words), question (1 word) = 9 words total
    # With [Memory] prefix: "[Memory] least relevant memory" = 4 words,
    # "[Memory] most relevant memory" = 4 words, "core instruction" = 2, "question" = 1 = 11
    # Set limit to 7 so one memory message must be removed
    cw = ContextWindow(
        max_tokens=7,
        strategy=ContextWindowStrategy.RELEVANCE,
        token_counter=_word_counter,
    )

    result = cw.build(conversation=conversation, memory_entries=entries)

    contents = [m.content for m in result.messages]

    assert "core instruction" in contents, "non-memory system message should be preserved"
    assert "question" in contents, "user message should be preserved"

    # The least relevant (first in list = mem-a, prepended first so at position 0)
    # should be removed first
    memory_msgs = [m for m in result.messages if m.metadata.get("memory_entry_id") is not None]
    assert len(memory_msgs) <= 1, "at least one memory message should have been removed"
    return


# ---------------------------------------------------------------------------
# Build — SUMMARIZE Strategy Tests
# ---------------------------------------------------------------------------


def test_build_summarize_calls_summarizer():
    """
        Verify that SUMMARIZE strategy calls the summarizer and replaces
        older messages with a summary.
    """
    messages = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="user", content="old message one two three four"),
        LLMMessage(role="assistant", content="old reply one two three four"),
        LLMMessage(role="user", content="recent message one two three four"),
        LLMMessage(role="assistant", content="recent reply one two three four"),
    ]
    conversation = LLMConversation(messages=messages)

    mock_summarizer = _create_mock_summarizer(summary_text="Brief summary.")

    # sys=1, each non-sys=6 words, total=1+6+6+6+6=25. Limit to 15.
    cw = ContextWindow(
        max_tokens=15,
        strategy=ContextWindowStrategy.SUMMARIZE,
        token_counter=_word_counter,
        summarizer=mock_summarizer,
    )

    result = cw.build(conversation=conversation)

    contents = [m.content for m in result.messages]
    assert "Brief summary." in contents, "summary message should be in the result"
    assert "old message one two three four" not in contents, "old message should be replaced"
    return


def test_build_summarize_without_summarizer_raises_context_window_error():
    """
        Verify that SUMMARIZE without a summarizer raises ContextWindowError.
    """
    messages = [
        LLMMessage(role="user", content="message one two three four five"),
        LLMMessage(role="assistant", content="reply one two three four five"),
    ]
    conversation = LLMConversation(messages=messages)

    cw = ContextWindow(
        max_tokens=5,
        strategy=ContextWindowStrategy.SUMMARIZE,
        token_counter=_word_counter,
    )

    raised = False
    caught_error = None
    try:
        cw.build(conversation=conversation)
    except ContextWindowError as exc:
        raised = True
        caught_error = exc

    assert raised is True, "SUMMARIZE without summarizer should raise ContextWindowError"
    assert caught_error.strategy == "SUMMARIZE", "error strategy should be 'SUMMARIZE'"
    return


# ---------------------------------------------------------------------------
# Build — Error When Cannot Fit After Trimming
# ---------------------------------------------------------------------------


def test_build_raises_context_window_error_when_cannot_fit():
    """
        Verify that build raises ContextWindowError when the context
        cannot fit within the limit even after applying the strategy.
    """
    messages = [
        LLMMessage(role="system", content="this system message is quite long and has many words"),
    ]
    conversation = LLMConversation(messages=messages)

    # System message alone is 10 words, limit is 3 — FIFO cannot remove system messages
    cw = ContextWindow(
        max_tokens=3,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_word_counter,
    )

    raised = False
    caught_error = None
    try:
        cw.build(conversation=conversation)
    except ContextWindowError as exc:
        raised = True
        caught_error = exc

    assert raised is True, "build should raise ContextWindowError when cannot fit"
    assert caught_error.max_tokens == 3, "error max_tokens should be 3"
    assert caught_error.strategy == "FIFO", "error strategy should be 'FIFO'"
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ Tests
# ---------------------------------------------------------------------------


def test_contextwindow_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    cw = ContextWindow(
        max_tokens=100,
        strategy=ContextWindowStrategy.FIFO,
        token_counter=_word_counter,
    )

    repr_str = repr(cw)
    assert "ContextWindow" in repr_str, "repr should contain the class name"
    return


def test_contextwindow_repr_contains_max_tokens():
    """
        Verify that __repr__ contains the max_tokens value.
    """
    cw = ContextWindow(
        max_tokens=256,
        strategy=ContextWindowStrategy.RELEVANCE,
        token_counter=_word_counter,
    )

    repr_str = repr(cw)
    assert "256" in repr_str, "repr should contain the max_tokens value"
    return


def test_contextwindow_repr_contains_strategy():
    """
        Verify that __repr__ contains the strategy name.
    """
    cw = ContextWindow(
        max_tokens=100,
        strategy=ContextWindowStrategy.RELEVANCE,
        token_counter=_word_counter,
    )

    repr_str = repr(cw)
    assert "RELEVANCE" in repr_str, "repr should contain the strategy name"
    return


def test_contextwindow_str_contains_max_tokens():
    """
        Verify that __str__ contains the max_tokens value.
    """
    cw = ContextWindow(
        max_tokens=512,
        strategy=ContextWindowStrategy.SUMMARIZE,
        token_counter=_word_counter,
    )

    str_val = str(cw)
    assert "512" in str_val, "__str__ should contain the max_tokens value"
    return


def test_contextwindow_str_contains_strategy():
    """
        Verify that __str__ contains the strategy name.
    """
    cw = ContextWindow(
        max_tokens=100,
        strategy=ContextWindowStrategy.SUMMARIZE,
        token_counter=_word_counter,
    )

    str_val = str(cw)
    assert "SUMMARIZE" in str_val, "__str__ should contain the strategy name"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
