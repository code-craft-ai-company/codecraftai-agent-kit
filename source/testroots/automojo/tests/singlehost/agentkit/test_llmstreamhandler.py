"""
    Unit tests for the automojo.agentkit.llmstreamhandler module.

    Tests LlmStreamHandler abstract method enforcement, ensuring that
    the class cannot be instantiated directly and that subclasses must
    implement all three abstract methods (on_chunk, on_complete, on_error).

    Feature: llm-integration, Task 5.3
    **Validates: Requirements 6.3**
"""

from automojo.agentkit.llmstreamhandler import LlmStreamHandler


# ---------------------------------------------------------------------------
# Abstract method enforcement
# ---------------------------------------------------------------------------


def test_llm_stream_handler_cannot_instantiate_directly():
    """
        LlmStreamHandler cannot be instantiated directly because it has
        abstract methods.

        **Validates: Requirements 6.3**
    """
    caught = False

    try:
        LlmStreamHandler()
    except TypeError:
        caught = True

    assert caught is True, (
        "LlmStreamHandler should raise TypeError when instantiated directly"
    )

    return


def test_llm_stream_handler_partial_on_chunk_only():
    """
        A subclass that only implements on_chunk cannot be instantiated.

        **Validates: Requirements 6.3**
    """

    class _PartialHandler(LlmStreamHandler):
        def on_chunk(self, chunk):
            return

    caught = False

    try:
        _PartialHandler()
    except TypeError:
        caught = True

    assert caught is True, (
        "Partial subclass with only on_chunk should raise TypeError"
    )

    return


def test_llm_stream_handler_partial_on_chunk_and_on_complete():
    """
        A subclass that implements on_chunk and on_complete but not
        on_error cannot be instantiated.

        **Validates: Requirements 6.3**
    """

    class _PartialHandler(LlmStreamHandler):
        def on_chunk(self, chunk):
            return

        def on_complete(self, response):
            return

    caught = False

    try:
        _PartialHandler()
    except TypeError:
        caught = True

    assert caught is True, (
        "Partial subclass missing on_error should raise TypeError"
    )

    return


def test_llm_stream_handler_partial_on_error_only():
    """
        A subclass that only implements on_error cannot be instantiated.

        **Validates: Requirements 6.3**
    """

    class _PartialHandler(LlmStreamHandler):
        def on_error(self, error):
            return

    caught = False

    try:
        _PartialHandler()
    except TypeError:
        caught = True

    assert caught is True, (
        "Partial subclass with only on_error should raise TypeError"
    )

    return


def test_llm_stream_handler_complete_subclass_can_instantiate():
    """
        A subclass that implements all three abstract methods can be
        instantiated successfully.

        **Validates: Requirements 6.3**
    """

    class _CompleteHandler(LlmStreamHandler):
        def on_chunk(self, chunk):
            return

        def on_complete(self, response):
            return

        def on_error(self, error):
            return

    handler = _CompleteHandler()

    assert handler is not None, (
        "Complete subclass should be instantiable"
    )

    return


def test_llm_stream_handler_complete_subclass_methods_callable():
    """
        A complete subclass has callable on_chunk, on_complete, and
        on_error methods.

        **Validates: Requirements 6.3**
    """

    class _CompleteHandler(LlmStreamHandler):
        def on_chunk(self, chunk):
            return

        def on_complete(self, response):
            return

        def on_error(self, error):
            return

    handler = _CompleteHandler()

    assert callable(handler.on_chunk), (
        "on_chunk should be callable"
    )
    assert callable(handler.on_complete), (
        "on_complete should be callable"
    )
    assert callable(handler.on_error), (
        "on_error should be callable"
    )

    return
