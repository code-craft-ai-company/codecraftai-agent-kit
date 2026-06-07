"""
    .. module:: ccai.tests.singlehost.agentkit.test_contextsummarizer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ContextSummarizer class.
"""

from ccai.agentkit.contextsummarizer import ContextSummarizer
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryerrors import ContextWindowError
from ccai.agentkit.memoryscope import MemoryScope
from ccai.testbase.mocking import Mock


def _create_mock_llm_provider(summary_text="This is a summary."):
    """
        Creates a mock LLMProvider that returns a response with the given summary text.
    """
    mock_message = LLMMessage(role="assistant", content=summary_text)

    mock_response = Mock()
    mock_response.configure(recursive=True)
    mock_response.mock_context().set_attribute("message", mock_message)

    mock_provider = Mock()
    mock_provider.configure(recursive=True)
    mock_provider.mock_context().set_attribute("provider_name", "test-provider")
    mock_provider.mock_context().mock_method("complete", return_value=mock_response)

    return mock_provider


def _create_failing_llm_provider():
    """
        Creates a mock LLMProvider whose complete method raises an exception.
    """
    def _raise_error(**kwargs):
        raise RuntimeError("LLM failure")

    mock_provider = Mock()
    mock_provider.configure(recursive=True)
    mock_provider.mock_context().set_attribute("provider_name", "failing-provider")
    mock_provider.mock_context().mock_method("complete", side_effect=_raise_error)

    return mock_provider


# ---- ContextSummarizer Construction Tests ----


def test_context_summarizer_construction():
    """
        Verify that ContextSummarizer can be constructed with an LLMProvider.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    assert summarizer.llm_provider is mock_provider, "llm_provider should be the provided mock"
    assert summarizer.max_summary_tokens is None, "max_summary_tokens should default to None"
    return


def test_context_summarizer_construction_with_max_tokens():
    """
        Verify that ContextSummarizer accepts max_summary_tokens.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider, max_summary_tokens=500)

    assert summarizer.max_summary_tokens == 500, "max_summary_tokens should be 500"
    return


# ---- summarize_messages Tests ----


def test_summarize_messages_returns_llm_message():
    """
        Verify that summarize_messages returns an LLMMessage with role 'system'.
    """
    mock_provider = _create_mock_llm_provider(summary_text="Condensed summary.")
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    messages = [
        LLMMessage(role="user", content="Hello, how are you?"),
        LLMMessage(role="assistant", content="I am fine, thank you."),
    ]

    result = summarizer.summarize_messages(messages=messages)

    assert isinstance(result, LLMMessage), "result should be an LLMMessage"
    assert result.role == "system", "result role should be 'system'"
    assert result.content == "Condensed summary.", "result content should match the mock summary"
    return


def test_summarize_messages_calls_llm_provider():
    """
        Verify that summarize_messages calls the LLMProvider complete method.
    """
    mock_message = LLMMessage(role="assistant", content="Summary output.")

    mock_response = Mock()
    mock_response.configure(recursive=True)
    mock_response.mock_context().set_attribute("message", mock_message)

    mock_provider = Mock()
    mock_provider.configure(recursive=True)
    mock_provider.mock_context().set_attribute("provider_name", "test-provider")

    complete_mock = Mock()
    complete_mock.configure(return_value=mock_response)
    mock_provider.mock_context().mock_method("complete", return_value=mock_response)

    summarizer = ContextSummarizer(llm_provider=mock_provider)

    messages = [
        LLMMessage(role="user", content="Tell me about Python."),
    ]

    result = summarizer.summarize_messages(messages=messages)

    assert result.content == "Summary output.", "result content should match the mock summary"
    return


def test_summarize_messages_empty_raises_semantic_error():
    """
        Verify that summarize_messages raises SemanticError for empty input.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    raised = False
    try:
        summarizer.summarize_messages(messages=[])
    except SemanticError:
        raised = True

    assert raised is True, "summarize_messages([]) should raise SemanticError"
    return


def test_summarize_messages_none_raises_semantic_error():
    """
        Verify that summarize_messages raises SemanticError for None input.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    raised = False
    try:
        summarizer.summarize_messages(messages=None)
    except SemanticError:
        raised = True

    assert raised is True, "summarize_messages(None) should raise SemanticError"
    return


def test_summarize_messages_llm_failure_raises_context_window_error():
    """
        Verify that summarize_messages raises ContextWindowError on LLM failure.
    """
    mock_provider = _create_failing_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    messages = [
        LLMMessage(role="user", content="Some content."),
    ]

    raised = False
    caught_error = None
    try:
        summarizer.summarize_messages(messages=messages)
    except ContextWindowError as exc:
        raised = True
        caught_error = exc

    assert raised is True, "summarize_messages should raise ContextWindowError on LLM failure"
    assert caught_error.strategy == "SUMMARIZE", "error strategy should be 'SUMMARIZE'"
    return


# ---- summarize_entries Tests ----


def test_summarize_entries_returns_llm_message():
    """
        Verify that summarize_entries returns an LLMMessage with role 'system'.
    """
    mock_provider = _create_mock_llm_provider(summary_text="Entry summary.")
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    entries = [
        MemoryEntry(content="First memory entry.", scope=MemoryScope.AGENT),
        MemoryEntry(content="Second memory entry.", scope=MemoryScope.SHARED),
    ]

    result = summarizer.summarize_entries(entries=entries)

    assert isinstance(result, LLMMessage), "result should be an LLMMessage"
    assert result.role == "system", "result role should be 'system'"
    assert result.content == "Entry summary.", "result content should match the mock summary"
    return


def test_summarize_entries_empty_raises_semantic_error():
    """
        Verify that summarize_entries raises SemanticError for empty input.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    raised = False
    try:
        summarizer.summarize_entries(entries=[])
    except SemanticError:
        raised = True

    assert raised is True, "summarize_entries([]) should raise SemanticError"
    return


def test_summarize_entries_none_raises_semantic_error():
    """
        Verify that summarize_entries raises SemanticError for None input.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    raised = False
    try:
        summarizer.summarize_entries(entries=None)
    except SemanticError:
        raised = True

    assert raised is True, "summarize_entries(None) should raise SemanticError"
    return


def test_summarize_entries_llm_failure_raises_context_window_error():
    """
        Verify that summarize_entries raises ContextWindowError on LLM failure.
    """
    mock_provider = _create_failing_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    entries = [
        MemoryEntry(content="Some memory.", scope=MemoryScope.GLOBAL),
    ]

    raised = False
    caught_error = None
    try:
        summarizer.summarize_entries(entries=entries)
    except ContextWindowError as exc:
        raised = True
        caught_error = exc

    assert raised is True, "summarize_entries should raise ContextWindowError on LLM failure"
    assert caught_error.strategy == "SUMMARIZE", "error strategy should be 'SUMMARIZE'"
    return


# ---- __repr__ and __str__ Tests ----


def test_context_summarizer_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    repr_str = repr(summarizer)
    has_class_name = "ContextSummarizer" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_context_summarizer_repr_contains_provider_name():
    """
        Verify that __repr__ contains the LLMProvider name.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    repr_str = repr(summarizer)
    has_provider = "test-provider" in repr_str
    assert has_provider is True, "repr should contain the provider name"
    return


def test_context_summarizer_str_contains_provider_name():
    """
        Verify that __str__ contains the LLMProvider name.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider)

    str_val = str(summarizer)
    has_provider = "test-provider" in str_val
    assert has_provider is True, "__str__ should contain the provider name"
    return


def test_context_summarizer_str_contains_max_tokens():
    """
        Verify that __str__ contains the max_summary_tokens value.
    """
    mock_provider = _create_mock_llm_provider()
    summarizer = ContextSummarizer(llm_provider=mock_provider, max_summary_tokens=1000)

    str_val = str(summarizer)
    has_tokens = "1000" in str_val
    assert has_tokens is True, "__str__ should contain the max_summary_tokens value"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
