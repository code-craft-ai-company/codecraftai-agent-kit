"""
    Defines the LLMStreamHandler abstract base class for streaming LLM
    response processing.

    LLMStreamHandler establishes the callback interface that streaming
    consumers must implement. The handler receives LLMStreamChunk objects
    as they arrive from the provider, a final LLMResponse when the stream
    completes, and an exception if an error occurs during streaming.
"""

import abc


class LLMStreamHandler(abc.ABC):
    """
        Abstract callback interface for receiving streaming LLM response chunks.

        Subclasses implement the on_chunk, on_complete, and on_error methods
        to process streaming responses from an LLMProvider. The provider
        invokes on_chunk for each partial content chunk, on_complete with
        the final assembled LLMResponse when the stream finishes, and
        on_error if an exception occurs during streaming.
    """

    @abc.abstractmethod
    def on_chunk(self, chunk) -> None:
        """
            Called for each chunk received during streaming.

            :param chunk: The LLMStreamChunk with partial content.
        """
        ...

    @abc.abstractmethod
    def on_complete(self, response) -> None:
        """
            Called when the streaming response completes successfully.

            :param response: The final assembled LLMResponse including
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
