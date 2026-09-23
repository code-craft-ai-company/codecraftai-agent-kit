"""
    Defines the LLMProvider abstract base class for Large Language Model providers.

    LLMProvider establishes the common interface that all LLM provider
    implementations must follow. Subclasses implement the complete and
    complete_stream methods for a specific LLM service. The base class
    manages provider identity, configuration, credential references, and
    tags for categorization and discovery.
"""

import abc

from ccai.agentkit.errors import SemanticError


class LLMProvider(abc.ABC):
    """
        Abstract base class for Large Language Model providers.

        Subclasses implement the complete and complete_stream methods
        for a specific LLM service. The base class validates that a
        provider name and model name are supplied at construction time,
        and exposes read-only properties for all provider metadata.

        :param provider_name: The name of the LLM provider (e.g. "openai").
        :param model_name: The name of the model (e.g. "gpt-4").
        :param config: Optional provider configuration dictionary.
        :param credential_names: Optional list of CredentialReference names.
        :param tags: Optional dictionary of tags for categorization.
    """

    def __init__(self, provider_name: str, model_name: str,
                 config: dict = None, credential_names: list = None,
                 tags: dict = None) -> None:
        if provider_name is None or len(str(provider_name).strip()) == 0:
            errmsg = "A provider name is required when constructing an LLMProvider."
            raise SemanticError(errmsg)

        if model_name is None or len(str(model_name).strip()) == 0:
            errmsg = "A model name is required when constructing an LLMProvider."
            raise SemanticError(errmsg)

        self._provider_name = provider_name
        self._model_name = model_name
        self._config = dict(config) if config is not None else {}
        self._credential_names = list(credential_names) if credential_names is not None else []
        self._tags = dict(tags) if tags is not None else {}
        return

    @property
    def provider_name(self) -> str:
        """
            The name of the LLM provider.

            :returns: The provider name as a string.
        """
        rtnval = self._provider_name
        return rtnval

    @property
    def model_name(self) -> str:
        """
            The name of the model.

            :returns: The model name as a string.
        """
        rtnval = self._model_name
        return rtnval

    @property
    def config(self) -> dict:
        """
            A copy of the provider configuration dictionary.

            :returns: A dictionary copy of the configuration.
        """
        rtnval = dict(self._config)
        return rtnval

    @property
    def credential_names(self) -> list:
        """
            A copy of the list of CredentialReference names.

            :returns: A list copy of the credential names.
        """
        rtnval = list(self._credential_names)
        return rtnval

    @property
    def tags(self) -> dict:
        """
            A copy of the tags dictionary.

            :returns: A dictionary copy of the tags.
        """
        rtnval = dict(self._tags)
        return rtnval

    @abc.abstractmethod
    def complete(self, conversation, **kwargs):
        """
            Executes a synchronous completion request.

            :param conversation: The conversation history as an LLMConversation.

            :returns: An LLMResponse with the completion result.

            :raises: LLMRequestError on provider-side failure.
        """

    @abc.abstractmethod
    def complete_stream(self, conversation, handler, **kwargs):
        """
            Executes a streaming completion request.

            :param conversation: The conversation history as an LLMConversation.
            :param handler: The LLMStreamHandler to receive chunks.

            :returns: The final assembled LLMResponse.

            :raises: LLMRequestError on provider-side failure.
        """

    def get_model_info(self) -> dict:
        """
            Returns provider and model metadata.

            :returns: A dictionary with provider_name, model_name, and config keys.
        """
        rtnval = {
            "provider_name": self._provider_name,
            "model_name": self._model_name,
            "config": dict(self._config)
        }
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            provider name, and model name.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(provider_name={!r}, model_name={!r})".format(
            self.__class__.__name__, self._provider_name, self._model_name
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the provider name
            and model name.

            :returns: A human-readable string.
        """
        rtnval = "LLMProvider: {} / {}".format(self._provider_name, self._model_name)
        return rtnval
