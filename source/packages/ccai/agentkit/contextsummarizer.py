"""
    Summarizes lists of LLMMessage objects or MemoryEntry objects into
    condensed summaries using an LLMProvider.

    The ContextSummarizer builds a summary prompt from the input messages
    or entries, calls the LLMProvider to generate a summary, and returns
    the result as a single LLMMessage. Raises SemanticError for empty
    input and ContextWindowError when the LLMProvider request fails.
"""

import logging

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.memoryerrors import ContextWindowError


logger = logging.getLogger("ccai.agentkit.memory")


class ContextSummarizer:
    """
        Summarizes a list of LLMMessage objects or MemoryEntry objects
        into a condensed summary using an LLMProvider.

        :param llm_provider: The LLMProvider to use for generating summaries.
        :param max_summary_tokens: Optional maximum token count for summaries.
    """

    def __init__(self, llm_provider, max_summary_tokens: int = None):
        """
            Constructs a ContextSummarizer.

            :param llm_provider: The LLMProvider to use for generating summaries.
            :param max_summary_tokens: Optional maximum token count for summaries.
        """
        self._llm_provider = llm_provider
        self._max_summary_tokens = max_summary_tokens
        return

    @property
    def llm_provider(self):
        """
            The LLMProvider used for generating summaries.

            :returns: The LLMProvider instance.
        """
        return self._llm_provider

    @property
    def max_summary_tokens(self) -> int:
        """
            The optional maximum token count for summaries.

            :returns: The max summary tokens integer, or None.
        """
        return self._max_summary_tokens

    def summarize_messages(self, messages: list) -> LLMMessage:
        """
            Summarizes a list of LLMMessage objects into a single summary message.

            :param messages: A list of LLMMessage objects to summarize.

            :returns: A single LLMMessage containing the condensed summary.
            :raises: SemanticError if messages is empty.
            :raises: ContextWindowError if the LLMProvider request fails.
        """
        if messages is None or len(messages) == 0:
            errmsg = "Cannot summarize an empty list of messages."
            raise SemanticError(errmsg)

        content_parts = []
        for msg in messages:
            content_parts.append("[{}] {}".format(msg.role, msg.content))
        combined_content = "\n".join(content_parts)

        prompt_content = "Summarize the following conversation concisely, preserving key information:\n\n{}".format(
            combined_content
        )

        summary_conversation = LLMConversation(messages=[
            LLMMessage(role="system", content="You are a concise summarizer."),
            LLMMessage(role="user", content=prompt_content),
        ])

        try:
            response = self._llm_provider.complete(conversation=summary_conversation)
            summary_text = response.message.content
        except Exception as exc:
            errmsg = "Summarization failed using LLMProvider {!r}.".format(
                self._llm_provider.provider_name
            )
            raise ContextWindowError(
                max_tokens=self._max_summary_tokens,
                strategy="SUMMARIZE",
                message=errmsg,
            ) from exc

        rtnval = LLMMessage(role="system", content=summary_text)

        logger.info(
            "ContextSummarizer generated summary from %d messages.",
            len(messages)
        )

        return rtnval

    def summarize_entries(self, entries: list) -> LLMMessage:
        """
            Summarizes a list of MemoryEntry objects into a single summary message.

            :param entries: A list of MemoryEntry objects to summarize.

            :returns: A single LLMMessage containing the condensed summary.
            :raises: SemanticError if entries is empty.
            :raises: ContextWindowError if the LLMProvider request fails.
        """
        if entries is None or len(entries) == 0:
            errmsg = "Cannot summarize an empty list of memory entries."
            raise SemanticError(errmsg)

        content_parts = []
        for entry in entries:
            content_parts.append("[{}] {}".format(entry.scope.value, entry.content))
        combined_content = "\n".join(content_parts)

        prompt_content = "Summarize the following memory entries concisely, preserving key information:\n\n{}".format(
            combined_content
        )

        summary_conversation = LLMConversation(messages=[
            LLMMessage(role="system", content="You are a concise summarizer."),
            LLMMessage(role="user", content=prompt_content),
        ])

        try:
            response = self._llm_provider.complete(conversation=summary_conversation)
            summary_text = response.message.content
        except Exception as exc:
            errmsg = "Summarization failed using LLMProvider {!r}.".format(
                self._llm_provider.provider_name
            )
            raise ContextWindowError(
                max_tokens=self._max_summary_tokens,
                strategy="SUMMARIZE",
                message=errmsg,
            ) from exc

        rtnval = LLMMessage(role="system", content=summary_text)

        logger.info(
            "ContextSummarizer generated summary from %d memory entries.",
            len(entries)
        )

        return rtnval

    def __repr__(self) -> str:
        rtnval = "{}(llm_provider={!r})".format(
            self.__class__.__name__, self._llm_provider.provider_name
        )
        return rtnval

    def __str__(self) -> str:
        rtnval = "ContextSummarizer: provider={}, max_tokens={}".format(
            self._llm_provider.provider_name, self._max_summary_tokens
        )
        return rtnval
