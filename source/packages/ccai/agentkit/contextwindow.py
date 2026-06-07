"""
    Manages the selection and arrangement of memory entries and
    conversation messages to fit within an LLM provider's token limit.

    The ContextWindow accepts a maximum token count, a trimming strategy,
    and a token counting callable. It builds a trimmed LLMConversation
    by prepending memory entries as system messages and applying the
    configured strategy when the token limit is exceeded.
"""

import logging

from ccai.agentkit.contextwindowstrategy import ContextWindowStrategy
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.memoryerrors import ContextWindowError


logger = logging.getLogger("ccai.agentkit.memory")


class ContextWindow:
    """
        Manages the selection and arrangement of memory entries and
        conversation messages to fit within an LLM provider's token limit.

        Produces a trimmed LLMConversation suitable for completion requests
        by applying the configured ContextWindowStrategy when the total
        token count exceeds the maximum.

        :param max_tokens: The maximum token count for the context window.
        :param strategy: The ContextWindowStrategy for trimming content.
        :param token_counter: A callable that accepts a string and returns token count.
        :param summarizer: Optional ContextSummarizer for the SUMMARIZE strategy.
    """

    def __init__(self, max_tokens: int, strategy: ContextWindowStrategy,
                 token_counter: callable, summarizer=None) -> None:
        """
            Constructs a ContextWindow.

            :param max_tokens: The maximum token count for the context window.
            :param strategy: The ContextWindowStrategy for trimming content.
            :param token_counter: A callable that accepts a string and returns token count.
            :param summarizer: Optional ContextSummarizer for the SUMMARIZE strategy.

            :raises: SemanticError if max_tokens <= 0 or token_counter is None.
        """
        if max_tokens is None or max_tokens <= 0:
            errmsg = "max_tokens must be a positive integer, got {!r}.".format(max_tokens)
            raise SemanticError(errmsg)

        if token_counter is None:
            errmsg = "A token_counter callable is required when constructing a ContextWindow."
            raise SemanticError(errmsg)

        self._max_tokens = max_tokens
        self._strategy = strategy
        self._token_counter = token_counter
        self._summarizer = summarizer
        return

    @property
    def max_tokens(self) -> int:
        """
            The maximum token count for the context window.

            :returns: The max tokens integer.
        """
        return self._max_tokens

    @property
    def strategy(self) -> ContextWindowStrategy:
        """
            The trimming strategy for the context window.

            :returns: The ContextWindowStrategy value.
        """
        return self._strategy

    def build(self, conversation: LLMConversation,
              memory_entries: list = None) -> LLMConversation:
        """
            Builds a trimmed LLMConversation that fits within the configured
            maximum token count.

            Memory entries are prepended as system messages with a '[Memory]'
            prefix. If the total token count exceeds the maximum, the configured
            strategy is applied to reduce the content.

            :param conversation: The input LLMConversation.
            :param memory_entries: Optional list of MemoryEntry objects to include.

            :returns: A new LLMConversation that fits within the token limit.
            :raises: ContextWindowError if the context cannot fit within the limit.
        """
        all_messages = list(conversation.messages)

        if memory_entries is not None and len(memory_entries) > 0:
            for entry in memory_entries:
                memory_msg = LLMMessage(
                    role="system",
                    content="[Memory] {}".format(entry.content),
                    metadata={"memory_entry_id": entry.identifier},
                )
                all_messages.insert(0, memory_msg)

        total_tokens = self._count_messages_tokens(messages=all_messages)

        if total_tokens <= self._max_tokens:
            rtnval = LLMConversation(messages=all_messages)
            return rtnval

        original_tokens = total_tokens

        if self._strategy == ContextWindowStrategy.FIFO:
            all_messages = self._apply_fifo(messages=all_messages)
        elif self._strategy == ContextWindowStrategy.RELEVANCE:
            all_messages = self._apply_relevance(
                messages=all_messages, memory_entries=memory_entries
            )
        elif self._strategy == ContextWindowStrategy.SUMMARIZE:
            all_messages = self._apply_summarize(messages=all_messages)

        final_tokens = self._count_messages_tokens(messages=all_messages)

        if final_tokens > self._max_tokens:
            errmsg = "Cannot fit context within {} tokens. Minimum required: {}.".format(
                self._max_tokens, final_tokens
            )
            raise ContextWindowError(
                max_tokens=self._max_tokens,
                strategy=self._strategy.value,
                message=errmsg,
            )

        logger.info(
            "ContextWindow trimmed context using %s: %d -> %d tokens.",
            self._strategy.value, original_tokens, final_tokens
        )

        rtnval = LLMConversation(messages=all_messages)
        return rtnval

    def _count_messages_tokens(self, messages: list) -> int:
        """
            Counts the total tokens across all messages by summing the
            token_counter result for each message content.

            :param messages: A list of LLMMessage objects.

            :returns: The total token count as an integer.
        """
        total = 0
        for msg in messages:
            total = total + self._token_counter(msg.content)
        rtnval = total
        return rtnval

    def _apply_fifo(self, messages: list) -> list:
        """
            Removes the oldest non-system messages first, preserving
            system messages and the most recent messages.

            :param messages: The list of LLMMessage objects.

            :returns: A trimmed list of messages fitting within the token limit.
        """
        system_messages = [m for m in messages if m.role == "system"]
        non_system_messages = [m for m in messages if m.role != "system"]

        while len(non_system_messages) > 0:
            candidate = system_messages + non_system_messages
            total = self._count_messages_tokens(messages=candidate)
            if total <= self._max_tokens:
                break
            non_system_messages.pop(0)

        rtnval = system_messages + non_system_messages
        return rtnval

    def _apply_relevance(self, messages: list, memory_entries: list = None) -> list:
        """
            Removes the least relevant memory entry messages first,
            preserving other system messages and recent conversation messages.

            Memory messages are identified by the presence of a
            'memory_entry_id' key in their metadata. The least relevant
            memory messages (earliest in the list) are removed first.

            :param messages: The list of LLMMessage objects.
            :param memory_entries: Optional list of MemoryEntry objects.

            :returns: A trimmed list of messages fitting within the token limit.
        """
        system_messages = [m for m in messages if m.role == "system"]
        non_system_messages = [m for m in messages if m.role != "system"]

        memory_messages = []
        other_system = []
        for msg in system_messages:
            if msg.metadata.get("memory_entry_id") is not None:
                memory_messages.append(msg)
            else:
                other_system.append(msg)

        while len(memory_messages) > 0:
            candidate = other_system + memory_messages + non_system_messages
            total = self._count_messages_tokens(messages=candidate)
            if total <= self._max_tokens:
                break
            memory_messages.pop(0)

        rtnval = other_system + memory_messages + non_system_messages
        return rtnval

    def _apply_summarize(self, messages: list) -> list:
        """
            Summarizes older non-system messages into a single summary message
            using the configured ContextSummarizer.

            Splits non-system messages at the midpoint, summarizes the older
            half, and replaces them with the summary message.

            :param messages: The list of LLMMessage objects.

            :returns: A trimmed list with older messages replaced by a summary.
            :raises: ContextWindowError if summarizer is not configured.
        """
        if self._summarizer is None:
            errmsg = "SUMMARIZE strategy requires a ContextSummarizer, but none is configured."
            raise ContextWindowError(
                max_tokens=self._max_tokens,
                strategy="SUMMARIZE",
                message=errmsg,
            )

        system_messages = [m for m in messages if m.role == "system"]
        non_system_messages = [m for m in messages if m.role != "system"]

        if len(non_system_messages) <= 1:
            rtnval = system_messages + non_system_messages
            return rtnval

        split_point = len(non_system_messages) // 2
        older_messages = non_system_messages[:split_point]
        recent_messages = non_system_messages[split_point:]

        summary_message = self._summarizer.summarize_messages(messages=older_messages)
        rtnval = system_messages + [summary_message] + recent_messages
        return rtnval

    def __repr__(self) -> str:
        rtnval = "{}(max_tokens={}, strategy={!r})".format(
            self.__class__.__name__, self._max_tokens, self._strategy.value
        )
        return rtnval

    def __str__(self) -> str:
        rtnval = "ContextWindow: max_tokens={}, strategy={}".format(
            self._max_tokens, self._strategy.value
        )
        return rtnval
