"""
    Defines the LLMResponse class for immutable LLM completion results.

    LLMResponse encapsulates the response message, token usage, provider name,
    model name, and request duration for a single LLM completion request.
    Supports serialization to and from JSON representations.
"""

import json

from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.tokenusage import TokenUsage


class LLMResponse:
    """
        Immutable result of an LLM completion request.

        Provides read-only access to the response message, token usage,
        provider name, model name, and request duration. Supports
        serialization to dictionary and JSON representations, and
        deserialization from JSON.

        :param message: The response LLMMessage.
        :param token_usage: The TokenUsage for this request.
        :param provider_name: The provider name string.
        :param model_name: The model name string.
        :param duration: The request duration in seconds.
    """

    def __init__(self, message: LLMMessage, token_usage: TokenUsage,
                 provider_name: str, model_name: str, duration: float) -> None:
        self._message = message
        self._token_usage = token_usage
        self._provider_name = provider_name
        self._model_name = model_name
        self._duration = duration
        return

    @property
    def message(self) -> LLMMessage:
        """
            The response LLMMessage.

            :returns: The LLMMessage instance.
        """
        rtnval = self._message
        return rtnval

    @property
    def token_usage(self) -> TokenUsage:
        """
            The TokenUsage for this request.

            :returns: The TokenUsage instance.
        """
        rtnval = self._token_usage
        return rtnval

    @property
    def provider_name(self) -> str:
        """
            The provider name string.

            :returns: The provider name as a string.
        """
        rtnval = self._provider_name
        return rtnval

    @property
    def model_name(self) -> str:
        """
            The model name string.

            :returns: The model name as a string.
        """
        rtnval = self._model_name
        return rtnval

    @property
    def duration(self) -> float:
        """
            The request duration in seconds.

            :returns: The duration as a float.
        """
        rtnval = self._duration
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the response fields.

            :returns: A dictionary with message, token_usage, provider_name,
                model_name, and duration keys.
        """
        rtnval = {
            "message": self._message.as_dict(),
            "token_usage": self._token_usage.as_dict(),
            "provider_name": self._provider_name,
            "model_name": self._model_name,
            "duration": self._duration
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the response fields.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "LLMResponse":
        """
            Deserializes a JSON string into an LLMResponse instance.

            Reconstructs the LLMMessage and TokenUsage from their
            dictionary representations contained in the JSON data.

            :param json_str: A JSON string.

            :returns: An LLMResponse instance.
        """
        data = json.loads(json_str)

        message = LLMMessage.from_dict(data["message"])

        token_usage = TokenUsage(
            prompt_tokens=data["token_usage"]["prompt_tokens"],
            completion_tokens=data["token_usage"]["completion_tokens"],
            total_tokens=data["token_usage"]["total_tokens"]
        )

        rtnval = cls(
            message=message,
            token_usage=token_usage,
            provider_name=data["provider_name"],
            model_name=data["model_name"],
            duration=data["duration"]
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            provider name, model name, and total token count.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(provider={!r}, model={!r}, tokens={})".format(
            self.__class__.__name__, self._provider_name,
            self._model_name, self._token_usage.total_tokens
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the provider name,
            model name, token usage, and duration.

            :returns: A human-readable string.
        """
        rtnval = "LLMResponse: {} / {} | {} | {:.2f}s".format(
            self._provider_name, self._model_name,
            str(self._token_usage), self._duration
        )
        return rtnval

    def __eq__(self, other) -> bool:
        """
            Checks equality based on all response fields.

            Duration comparison uses a floating-point tolerance of 1e-9.

            :param other: The object to compare against.

            :returns: True if all fields are equal, False otherwise.
        """
        if not isinstance(other, LLMResponse):
            return False

        rtnval = (self._message == other._message and
                  self._token_usage == other._token_usage and
                  self._provider_name == other._provider_name and
                  self._model_name == other._model_name and
                  abs(self._duration - other._duration) < 1e-9)
        return rtnval
