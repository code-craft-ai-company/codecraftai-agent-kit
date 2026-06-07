"""
    Defines the TokenUsage class for immutable token count records.

    TokenUsage encapsulates the prompt token count, completion token count,
    and total token count for a single LLM request. The total must equal
    the sum of prompt and completion tokens.
"""

from ccai.agentkit.errors import SemanticError


class TokenUsage:
    """
        Immutable record of token counts for a single LLM request.

        Provides read-only access to prompt tokens, completion tokens,
        and total tokens. Validates that the total equals the sum of
        prompt and completion tokens at construction time.

        :param prompt_tokens: Number of prompt tokens consumed.
        :param completion_tokens: Number of completion tokens consumed.
        :param total_tokens: Total token count.
    """

    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
        expected_total = prompt_tokens + completion_tokens

        if total_tokens != expected_total:
            errmsg = "TokenUsage total_tokens ({}) does not equal prompt_tokens ({}) + completion_tokens ({}) = {}.".format(
                total_tokens, prompt_tokens, completion_tokens, expected_total
            )
            raise SemanticError(errmsg)

        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._total_tokens = total_tokens
        return

    @property
    def prompt_tokens(self) -> int:
        """
            The number of prompt tokens consumed.

            :returns: The prompt token count as an integer.
        """
        rtnval = self._prompt_tokens
        return rtnval

    @property
    def completion_tokens(self) -> int:
        """
            The number of completion tokens consumed.

            :returns: The completion token count as an integer.
        """
        rtnval = self._completion_tokens
        return rtnval

    @property
    def total_tokens(self) -> int:
        """
            The total token count.

            :returns: The total token count as an integer.
        """
        rtnval = self._total_tokens
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the token counts.

            :returns: A dictionary with prompt_tokens, completion_tokens,
                and total_tokens keys.
        """
        rtnval = {
            "prompt_tokens": self._prompt_tokens,
            "completion_tokens": self._completion_tokens,
            "total_tokens": self._total_tokens
        }
        return rtnval

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """
            Returns a new TokenUsage whose counts are the sum of the two operands.

            :param other: The other TokenUsage to add.

            :returns: A new TokenUsage with summed counts.
        """
        rtnval = TokenUsage(
            prompt_tokens=self._prompt_tokens + other._prompt_tokens,
            completion_tokens=self._completion_tokens + other._completion_tokens,
            total_tokens=self._total_tokens + other._total_tokens
        )
        return rtnval

    def __eq__(self, other) -> bool:
        """
            Checks equality based on all three token count fields.

            :param other: The object to compare against.

            :returns: True if all token counts are equal, False otherwise.
        """
        if not isinstance(other, TokenUsage):
            return False

        rtnval = (self._prompt_tokens == other._prompt_tokens and
                  self._completion_tokens == other._completion_tokens and
                  self._total_tokens == other._total_tokens)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name
            and all token counts.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(prompt={}, completion={}, total={})".format(
            self.__class__.__name__, self._prompt_tokens,
            self._completion_tokens, self._total_tokens
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the token counts.

            :returns: A human-readable string.
        """
        rtnval = "Tokens: {} prompt, {} completion, {} total".format(
            self._prompt_tokens, self._completion_tokens, self._total_tokens
        )
        return rtnval
