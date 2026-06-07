"""
    Abstract base class for generating embedding vectors from text content.

    Concrete implementations wrap specific embedding services or local models.
    The EmbeddingProvider is used by MemoryStore implementations that support
    semantic similarity search.
"""

import abc
from typing import Optional

from ccai.agentkit.errors import SemanticError


class EmbeddingProvider(abc.ABC):
    """
        Abstract base class for generating embedding vectors from text content.
        Concrete implementations wrap specific embedding services or local models.
    """

    def __init__(self, provider_name: str, embedding_dimension: int,
                 credential_names: list = None) -> None:
        """
            Constructs an EmbeddingProvider.

            :param provider_name: The name of the embedding provider.
            :param embedding_dimension: The length of output embedding vectors.
            :param credential_names: Optional list of CredentialReference names.

            :raises: SemanticError if provider_name is empty or embedding_dimension <= 0.
        """
        if provider_name is None or len(str(provider_name).strip()) == 0:
            errmsg = "A provider name is required when constructing an EmbeddingProvider."
            raise SemanticError(errmsg)

        if embedding_dimension is None or embedding_dimension <= 0:
            errmsg = "The embedding_dimension must be a positive integer, got {!r}.".format(
                embedding_dimension
            )
            raise SemanticError(errmsg)

        self._provider_name = provider_name
        self._embedding_dimension = embedding_dimension
        self._credential_names = list(credential_names) if credential_names is not None else []
        return

    @property
    def provider_name(self) -> str:
        """
            The name of the embedding provider.

            :returns: The provider name string.
        """
        return self._provider_name

    @property
    def embedding_dimension(self) -> int:
        """
            The length of output embedding vectors.

            :returns: The embedding dimension as an integer.
        """
        return self._embedding_dimension

    @property
    def credential_names(self) -> list:
        """
            The list of CredentialReference names required by this provider.
            Returns a defensive copy.

            :returns: A list of credential name strings.
        """
        rtnval = list(self._credential_names)
        return rtnval

    @abc.abstractmethod
    def embed(self, text: str) -> list:
        """
            Generates an embedding vector from a text string.

            :param text: The text to embed.

            :returns: An embedding vector as a list of floats.
            :raises: SemanticError if text is empty.
        """
        ...

    @abc.abstractmethod
    def embed_batch(self, texts: list) -> list:
        """
            Generates embedding vectors from a list of text strings.

            :param texts: A list of text strings to embed.

            :returns: A list of embedding vectors, each as a list of floats.
        """
        ...

    def __repr__(self) -> str:
        rtnval = "{}(provider_name={!r}, dimension={})".format(
            self.__class__.__name__, self._provider_name, self._embedding_dimension
        )
        return rtnval

    def __str__(self) -> str:
        rtnval = "EmbeddingProvider: {} (dimension={})".format(
            self._provider_name, self._embedding_dimension
        )
        return rtnval
