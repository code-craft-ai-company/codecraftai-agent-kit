"""
    Defines the FallbackChain class for configuring fallback provider
    sequences in the automojo-agent-kit framework.

    FallbackChain maintains an ordered list of LlmProvider name-model pairs
    that defines the fallback sequence when a provider fails. The chain is
    traversed in order until a provider succeeds or all providers have been
    exhausted.
"""


class FallbackChain:
    """
        An ordered list of LlmProvider name-model pairs defining
        the fallback sequence when a provider fails.

        :param providers: An ordered list of (provider_name, model_name) tuples.
    """

    def __init__(self, providers: list) -> None:
        self._providers = list(providers)
        return

    @property
    def providers(self) -> list:
        """
            Returns the ordered list of provider name-model pairs.

            :returns: A copy of the list of (provider_name, model_name) tuples.
        """
        rtnval = list(self._providers)
        return rtnval

    def next_provider(self, current_provider_name: str,
                      current_model_name: str) -> tuple:
        """
            Returns the next provider in the fallback sequence after the
            specified current provider.

            :param current_provider_name: The current provider name.
            :param current_model_name: The current model name.

            :returns: A (provider_name, model_name) tuple, or None if end of chain.
        """
        current = (current_provider_name, current_model_name)

        for i in range(len(self._providers)):
            provider_entry = self._providers[i]
            is_match = provider_entry == current

            if is_match is True:
                next_index = i + 1
                has_next = next_index < len(self._providers)

                if has_next is True:
                    rtnval = self._providers[next_index]
                    return rtnval

                return None

        return None

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name
            and the count of providers in the chain.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(count={})".format(self.__class__.__name__, len(self._providers))
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the provider name-model
            pairs in the fallback chain.

            :returns: A human-readable string.
        """
        pairs = ["{}/{}".format(p[0], p[1]) for p in self._providers]
        rtnval = "FallbackChain: [{}]".format(", ".join(pairs))
        return rtnval
