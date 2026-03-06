"""
    Defines the LlmProviderRegistry class for tracking available LlmProvider
    instances within an Agent in the automojo-agent-kit framework.

    LlmProviderRegistry provides registration, deregistration, lookup by
    provider name and model name, lookup by provider name only, lookup by
    tags, enumeration, and count operations for LlmProvider instances.
    Each Agent maintains its own LlmProviderRegistry instance.
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmprovider import LlmProvider


class LlmProviderRegistry:
    """
        Registry tracking available LlmProvider instances for an Agent.

        Provides lookup by provider name + model name, by provider name only,
        by tags, and enumeration. Uses a composite key of (provider_name,
        model_name) for unique identification of registered providers.
    """

    def __init__(self) -> None:
        self._providers: dict = {}
        return

    def register(self, provider: LlmProvider) -> None:
        """
            Registers an LlmProvider using provider_name + model_name as
            a composite key.

            :param provider: The LlmProvider instance to register.

            :raises: SemanticError if a provider with the same name+model
                     is already registered.
        """
        provider_name = provider.provider_name
        model_name = provider.model_name
        key = (provider_name, model_name)

        is_duplicate = key in self._providers

        if is_duplicate is True:
            errmsg = "LlmProvider {!r} model {!r} is already registered.".format(
                provider_name, model_name
            )
            raise SemanticError(errmsg)

        self._providers[key] = provider

        return

    def deregister(self, provider_name: str, model_name: str) -> None:
        """
            Removes an LlmProvider by provider name and model name.

            If the provider is not found, the operation is a no-op.

            :param provider_name: The provider name.
            :param model_name: The model name.
        """
        key = (provider_name, model_name)

        is_present = key in self._providers

        if is_present is True:
            del self._providers[key]

        return

    def lookup(self, provider_name: str, model_name: str) -> LlmProvider:
        """
            Looks up a registered LlmProvider by provider name and model name.

            :param provider_name: The provider name.
            :param model_name: The model name.

            :returns: The LlmProvider instance, or None if not found.
        """
        key = (provider_name, model_name)
        rtnval = self._providers.get(key, None)
        return rtnval

    def lookup_by_provider(self, provider_name: str) -> list:
        """
            Returns all LlmProvider instances for a given provider name.

            :param provider_name: The provider name.

            :returns: A list of LlmProvider instances matching the provider name.
        """
        matching_providers = []

        for key, provider in self._providers.items():
            key_provider_name = key[0]
            is_match = key_provider_name == provider_name

            if is_match is True:
                matching_providers.append(provider)

        rtnval = matching_providers
        return rtnval

    def lookup_by_tags(self, **tags) -> list:
        """
            Returns LlmProvider instances matching all provided tag criteria.

            Returns providers whose tags dictionary contains all the specified
            key-value pairs.

            :param tags: Keyword arguments representing tag key-value pairs to match.

            :returns: A list of matching LlmProvider instances.
        """
        matching_providers = []

        for provider in self._providers.values():
            provider_tags = provider.tags
            all_match = True

            for tag_key, tag_value in tags.items():
                has_key = tag_key in provider_tags

                if has_key is not True:
                    all_match = False
                    break

                provider_tag_value = provider_tags[tag_key]
                values_match = provider_tag_value == tag_value

                if values_match is not True:
                    all_match = False
                    break

            if all_match is True:
                matching_providers.append(provider)

        rtnval = matching_providers
        return rtnval

    def list_all(self) -> list:
        """
            Returns all registered LlmProvider instances.

            :returns: A list of all registered LlmProvider instances.
        """
        rtnval = list(self._providers.values())
        return rtnval

    def has_provider(self, provider_name: str, model_name: str) -> bool:
        """
            Checks whether a provider with the given name and model is registered.

            :param provider_name: The provider name.
            :param model_name: The model name.

            :returns: True if registered, False otherwise.
        """
        key = (provider_name, model_name)
        rtnval = key in self._providers
        return rtnval

    def clear(self) -> None:
        """
            Removes all registered providers from the registry.
        """
        self._providers.clear()
        return

    @property
    def count(self) -> int:
        """
            The number of currently registered providers.

            :returns: The count of registered providers.
        """
        rtnval = len(self._providers)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name
            and the count of registered providers.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(count={})".format(self.__class__.__name__, len(self._providers))
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered
            provider name / model name pairs.

            :returns: A human-readable string.
        """
        pairs = ["{}/{}".format(k[0], k[1]) for k in self._providers.keys()]
        rtnval = "LlmProviderRegistry: [{}]".format(", ".join(pairs))
        return rtnval
