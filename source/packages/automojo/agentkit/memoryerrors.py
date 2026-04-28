"""
    Exception classes for the Memory & Context Management feature.

    Provides MemoryStoreError for memory backend operation failures
    and ContextWindowError for context window fitting failures.
"""

from typing import Optional

from automojo.agentkit.errors import AgentKitError


class MemoryStoreError(AgentKitError):
    """
        Raised when a MemoryStore operation fails due to a backend error
        (connection failure, write error, query error).

        :param store_name: The name of the store where the error occurred.
        :param operation: The operation that failed (store, retrieve, search, etc.).
        :param cause: The original exception that caused the failure.
    """

    def __init__(self, store_name: str, operation: str, cause: Optional[Exception] = None) -> None:
        self._store_name = store_name
        self._operation = operation

        errmsg = self._format_message(store_name=store_name, operation=operation, cause=cause)
        super().__init__(errmsg, cause=cause)

        return

    @property
    def store_name(self) -> str:
        """
            The name of the store where the error occurred.

            :returns: The store name string.
        """
        return self._store_name

    @property
    def operation(self) -> str:
        """
            The operation that failed.

            :returns: The operation name string.
        """
        return self._operation

    def _format_message(self, store_name: str, operation: str, cause: Optional[Exception] = None) -> str:
        """
            Builds a descriptive error message from the store name, operation, and cause.

            :param store_name: The name of the store where the error occurred.
            :param operation: The operation that failed.
            :param cause: The original exception.

            :returns: A formatted error message string.
        """
        cause_str = str(cause) if cause is not None else "unknown error"
        errmsg = "MemoryStoreError in store {!r} during operation {!r}: {}".format(
            store_name, operation, cause_str
        )
        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            store name, and operation.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(store_name={!r}, operation={!r})".format(
            self.__class__.__name__, self._store_name, self._operation
        )
        return repr_str


class ContextWindowError(AgentKitError):
    """
        Raised when the ContextWindow cannot produce a valid context
        within the configured token limit or when summarization fails.

        :param max_tokens: The maximum token count that was configured.
        :param strategy: The strategy name that was in use.
        :param message: A descriptive error message.
    """

    def __init__(self, max_tokens: int, strategy: str, message: str) -> None:
        self._max_tokens = max_tokens
        self._strategy = strategy
        self._error_message = message

        super().__init__(message)

        return

    @property
    def max_tokens(self) -> int:
        """
            The maximum token count that was configured.

            :returns: The max tokens integer.
        """
        return self._max_tokens

    @property
    def strategy(self) -> str:
        """
            The strategy name that was in use when the error occurred.

            :returns: The strategy name string.
        """
        return self._strategy

    @property
    def error_message(self) -> str:
        """
            The descriptive error message.

            :returns: The error message string.
        """
        return self._error_message

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            max tokens, strategy, and message.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(max_tokens={}, strategy={!r}, message={!r})".format(
            self.__class__.__name__, self._max_tokens, self._strategy, self._error_message
        )
        return repr_str
