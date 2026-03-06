"""
    Unit tests for the automojo.agentkit.llmstreamchunk module.

    Tests LlmStreamChunk construction with various content lengths,
    empty metadata, metadata copy behavior, __repr__ truncation at
    30 characters, and __str__ returning the content string.

    Feature: llm-integration, Task 5.3
    **Validates: Requirements 6.1, 6.2, 6.7, 6.8**
"""

from automojo.agentkit.llmstreamchunk import LlmStreamChunk


# ---------------------------------------------------------------------------
# Construction with various content lengths
# ---------------------------------------------------------------------------


def test_llm_stream_chunk_short_content():
    """
        LlmStreamChunk stores a short content string.

        **Validates: Requirements 6.1, 6.2**
    """
    chunk = LlmStreamChunk(content="Hello")

    assert chunk.content == "Hello", (
        "content mismatch: {!r}".format(chunk.content)
    )

    return


def test_llm_stream_chunk_empty_content():
    """
        LlmStreamChunk accepts an empty content string.

        **Validates: Requirements 6.1, 6.2**
    """
    chunk = LlmStreamChunk(content="")

    assert chunk.content == "", (
        "content should be empty: {!r}".format(chunk.content)
    )

    return


def test_llm_stream_chunk_long_content():
    """
        LlmStreamChunk stores a long content string without truncation.

        **Validates: Requirements 6.1, 6.2**
    """
    long_text = "a" * 500
    chunk = LlmStreamChunk(content=long_text)

    assert chunk.content == long_text, (
        "content should preserve full length: got {} chars".format(len(chunk.content))
    )

    return


def test_llm_stream_chunk_special_characters_in_content():
    """
        LlmStreamChunk preserves special characters in content.

        **Validates: Requirements 6.1, 6.2**
    """
    content = "line1\nline2\ttab \"quotes\" 'single' <html>&amp;"
    chunk = LlmStreamChunk(content=content)

    assert chunk.content == content, (
        "content should preserve special characters: {!r}".format(chunk.content)
    )

    return


# ---------------------------------------------------------------------------
# Metadata handling
# ---------------------------------------------------------------------------


def test_llm_stream_chunk_default_metadata_is_empty():
    """
        LlmStreamChunk defaults to an empty metadata dictionary when
        no metadata is provided.

        **Validates: Requirements 6.1**
    """
    chunk = LlmStreamChunk(content="hello")

    assert chunk.metadata == {}, (
        "metadata should default to empty dict: {!r}".format(chunk.metadata)
    )

    return


def test_llm_stream_chunk_none_metadata_is_empty():
    """
        LlmStreamChunk treats None metadata as an empty dictionary.

        **Validates: Requirements 6.1**
    """
    chunk = LlmStreamChunk(content="hello", metadata=None)

    assert chunk.metadata == {}, (
        "metadata should be empty dict when None: {!r}".format(chunk.metadata)
    )

    return


def test_llm_stream_chunk_with_metadata():
    """
        LlmStreamChunk stores provided metadata.

        **Validates: Requirements 6.1, 6.2**
    """
    meta = {"index": 3, "finish_reason": None}
    chunk = LlmStreamChunk(content="partial", metadata=meta)

    assert chunk.metadata == meta, (
        "metadata mismatch: {!r}".format(chunk.metadata)
    )

    return


def test_llm_stream_chunk_metadata_returns_copy():
    """
        LlmStreamChunk metadata property returns a copy so that
        external mutations do not affect the chunk.

        **Validates: Requirements 6.2**
    """
    meta = {"key": "value"}
    chunk = LlmStreamChunk(content="test", metadata=meta)

    returned = chunk.metadata
    returned["key"] = "modified"

    assert chunk.metadata["key"] == "value", (
        "metadata should not be affected by external mutation: {!r}".format(
            chunk.metadata
        )
    )

    return


def test_llm_stream_chunk_constructor_copies_metadata():
    """
        LlmStreamChunk copies the metadata dictionary at construction
        so that later mutations to the original do not affect the chunk.

        **Validates: Requirements 6.2**
    """
    meta = {"key": "original"}
    chunk = LlmStreamChunk(content="test", metadata=meta)

    meta["key"] = "mutated"

    assert chunk.metadata["key"] == "original", (
        "chunk metadata should not reflect external mutation: {!r}".format(
            chunk.metadata
        )
    )

    return


# ---------------------------------------------------------------------------
# __repr__ truncation at 30 characters
# ---------------------------------------------------------------------------


def test_llm_stream_chunk_repr_short_content():
    """
        __repr__ includes the full content when it is 30 characters or fewer.

        **Validates: Requirements 6.7**
    """
    content = "a" * 30
    chunk = LlmStreamChunk(content=content)
    result = repr(chunk)

    assert "LlmStreamChunk" in result, (
        "repr should contain class name: {!r}".format(result)
    )
    assert "..." not in result, (
        "repr should not truncate content at exactly 30 chars: {!r}".format(result)
    )

    return


def test_llm_stream_chunk_repr_truncates_at_31_chars():
    """
        __repr__ truncates content and appends '...' when content
        exceeds 30 characters.

        **Validates: Requirements 6.7**
    """
    content = "a" * 31
    chunk = LlmStreamChunk(content=content)
    result = repr(chunk)

    assert "LlmStreamChunk" in result, (
        "repr should contain class name: {!r}".format(result)
    )
    assert "..." in result, (
        "repr should truncate content beyond 30 chars: {!r}".format(result)
    )

    return


def test_llm_stream_chunk_repr_long_content():
    """
        __repr__ truncates long content to 30 characters plus '...'.

        **Validates: Requirements 6.7**
    """
    content = "b" * 200
    chunk = LlmStreamChunk(content=content)
    result = repr(chunk)

    expected_preview = "b" * 30 + "..."
    assert expected_preview in result, (
        "repr should contain truncated preview: {!r}".format(result)
    )

    return


def test_llm_stream_chunk_repr_empty_content():
    """
        __repr__ handles empty content without truncation.

        **Validates: Requirements 6.7**
    """
    chunk = LlmStreamChunk(content="")
    result = repr(chunk)

    assert "LlmStreamChunk" in result, (
        "repr should contain class name: {!r}".format(result)
    )
    assert "..." not in result, (
        "repr should not truncate empty content: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# __str__ returns content
# ---------------------------------------------------------------------------


def test_llm_stream_chunk_str_returns_content():
    """
        __str__ returns the content string directly.

        **Validates: Requirements 6.8**
    """
    chunk = LlmStreamChunk(content="Hello world")
    result = str(chunk)

    assert result == "Hello world", (
        "str should return content: {!r}".format(result)
    )

    return


def test_llm_stream_chunk_str_returns_empty_for_empty_content():
    """
        __str__ returns an empty string when content is empty.

        **Validates: Requirements 6.8**
    """
    chunk = LlmStreamChunk(content="")
    result = str(chunk)

    assert result == "", (
        "str should return empty string: {!r}".format(result)
    )

    return


def test_llm_stream_chunk_str_returns_full_long_content():
    """
        __str__ returns the full content string even when it is long,
        unlike __repr__ which truncates.

        **Validates: Requirements 6.8**
    """
    content = "x" * 200
    chunk = LlmStreamChunk(content=content)
    result = str(chunk)

    assert result == content, (
        "str should return full content without truncation: got {} chars".format(
            len(result)
        )
    )

    return
