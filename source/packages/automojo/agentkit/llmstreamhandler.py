"""
    Defines the LlmStreamHandler abstract base class for streaming LLM
    response processing.

    LlmStreamHandler establishes the callback interface that streaming
    consumers must implement. The handler receives LlmStreamChunk objects
    as they arrive from the provider, a final LlmResponse when the stream
    completes, and an exception if an error occurs during streaming.
"""

import abc


class LlmStreamHandler(abc.ABC):
    """
        Abstract callback interface for receiving streaming LLM response chunks.

        Subclasses implement the on_chunk, on_complete, and on_error methods
        to process streaming responses from an LlmProvider. The provider
        invokes on_chunk for each partial content chunk, on_complete with
        the final assembled LlmResponse when the stream finishes, and
        on_error if an exception occurs during streaming.
    """

    @abc.abstractmethod
    def on_chunk(self, chunk) -> None:
        """
            Called for each chunk received during streaming.

            :param chunk: The LlmStreamChunk with partial content.
        """
        ...

    @abc.abstractmethod
    def on_complete(self, response) -> None:
        """
            Called when the streaming response completes successfully.

            :param response: The final assembled LlmResponse including
                complete TokenUsage.
        """
        ...

    @abc.abstractmethod
    def on_error(self, error: Exception) -> None:
        """
            Called when an error occurs during streaming.

            :param error: The exception that occurred.
        """
        ...
