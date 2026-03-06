"""
    Exception classes for the LLM Integration feature.

    Provides LlmRequestError for LLM provider request failures and
    LlmResponseParsingError for output parsing and validation failures.
"""

import os

from typing import Optional

from automojo.agentkit.errors import AgentKitError


class LlmRequestError(AgentKitError):
    """
        Raised when an LLM provider request fails due to a provider-side error.

        :param provider_name: The provider that failed.
        :param model_name: The model that failed.
        :param category: The error category string.
        :param cause: The original exception.
    """

    VALID_CATEGORIES = {
        "rate_limit", "authentication", "server_error",
        "timeout", "connection", "invalid_request"
    }

    def __init__(self, provider_name: str, model_name: str,
                 category: str, cause: Exception = None) -> None:

        if category not in self.VALID_CATEGORIES:
            errmsg = "Invalid error category {!r}. Valid categories are: {}".format(
                category, ", ".join(sorted(self.VALID_CATEGORIES))
            )
            raise ValueError(errmsg)

        self._provider_name = provider_name
        self._model_name = model_name
        self._category = category
        self._cause = cause

        errmsg = self._format_message()
        super().__init__(errmsg, cause=cause)

        return

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the provider name,
            model name, category, and optional cause.

            :returns: A formatted error message string.
        """
        lines = [
            "LLM request failed for provider {!r} model {!r}.".format(
                self._provider_name, self._model_name
            ),
            "Category: {}".format(self._category)
        ]

        if self._cause is not None:
            lines.append("Cause: {}".format(str(self._cause)))

        rtnval = os.linesep.join(lines)

        return rtnval

    @property
    def provider_name(self) -> str:
        """
            The provider that failed.

            :returns: The provider name string.
        """
        return self._provider_name

    @property
    def model_name(self) -> str:
        """
            The model that failed.

            :returns: The model name string.
        """
        return self._model_name

    @property
    def category(self) -> str:
        """
            The error category string.

            :returns: The category string.
        """
        return self._category

    @property
    def cause(self) -> Optional[Exception]:
        """
            The original exception that caused the failure.

            :returns: The cause exception or None.
        """
        return self._cause

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            provider name, model name, and category.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(provider={!r}, model={!r}, category={!r})".format(
            self.__class__.__name__, self._provider_name,
            self._model_name, self._category
        )
        return rtnval


class LlmResponseParsingError(AgentKitError):
    """
        Raised when an OutputParser fails to parse or validate LLM response text.

        :param parser_name: The parser class name.
        :param raw_text: The raw response text that failed parsing.
        :param message: A descriptive error message.
    """

    def __init__(self, parser_name: str, raw_text: str, message: str) -> None:
        self._parser_name = parser_name
        self._raw_text = raw_text
        self._error_message = message

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the parser name,
            error message, and a truncated preview of the raw text.

            :returns: A formatted error message string.
        """
        lines = [
            "LLM response parsing failed in {!r}.".format(self._parser_name),
            "Error: {}".format(self._error_message),
            "Raw text (first 200 chars): {!r}".format(self._raw_text[:200])
        ]

        rtnval = os.linesep.join(lines)

        return rtnval

    @property
    def parser_name(self) -> str:
        """
            The parser class name.

            :returns: The parser name string.
        """
        return self._parser_name

    @property
    def raw_text(self) -> str:
        """
            The raw response text that failed parsing.

            :returns: The raw text string.
        """
        return self._raw_text

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
            parser name, and error message.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(parser={!r}, message={!r})".format(
            self.__class__.__name__, self._parser_name, self._error_message
        )
        return rtnval
