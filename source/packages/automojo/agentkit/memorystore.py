"""
    Abstract base class for memory storage backends.

    Provides a common interface for storing, retrieving, searching,
    updating, and deleting MemoryEntry objects. Concrete implementations
    wrap specific backends (in-memory, file-based, vector store, database).
"""

import abc
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from automojo.agentkit.embeddingprovider import EmbeddingProvider
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.expirationpolicy import ExpirationPolicy
from automojo.agentkit.memoryentry import MemoryEntry
from automojo.agentkit.memoryquery import MemoryQuery
from automojo.agentkit.memoryqueryresult import MemoryQueryResult


logger = logging.getLogger("automojo.agentkit.memory")


class MemoryStore(abc.ABC):
    """
        Abstract base class for memory storage backends.
        Provides a common interface for storing, retrieving, searching,
        updating, and deleting MemoryEntry objects.
    """

    def __init__(self, store_name: str, embedding_provider: EmbeddingProvider = None,
                 expiration_policy: ExpirationPolicy = None,
                 credential_names: list = None) -> None:
        """
            Constructs a MemoryStore.

            :param store_name: The name of this memory store.
            :param embedding_provider: Optional EmbeddingProvider for generating embeddings.
            :param expiration_policy: Optional ExpirationPolicy for entry lifecycle.
            :param credential_names: Optional list of CredentialReference names.

            :raises: SemanticError if store_name is empty.
        """
        if store_name is None or len(str(store_name).strip()) == 0:
            errmsg = "A store name is required when constructing a MemoryStore."
            raise SemanticError(errmsg)

        self._store_name = store_name
        self._embedding_provider = embedding_provider
        self._expiration_policy = expiration_policy
        self._credential_names = list(credential_names) if credential_names is not None else []
        return

    @property
    def store_name(self) -> str:
        """
            The name of this memory store.

            :returns: The store name string.
        """
        return self._store_name

    @property
    def embedding_provider(self) -> Optional[EmbeddingProvider]:
        """
            The optional EmbeddingProvider for generating embeddings.

            :returns: The EmbeddingProvider instance or None.
        """
        return self._embedding_provider

    @property
    def expiration_policy(self) -> Optional[ExpirationPolicy]:
        """
            The optional ExpirationPolicy for entry lifecycle management.

            :returns: The ExpirationPolicy instance or None.
        """
        return self._expiration_policy

    @property
    @abc.abstractmethod
    def count(self) -> int:
        """
            Returns the count of stored MemoryEntry objects.

            :returns: The entry count as an integer.
        """
        ...

    @abc.abstractmethod
    def store(self, entry: MemoryEntry) -> MemoryEntry:
        """
            Stores a MemoryEntry. If the entry has no embedding and an
            EmbeddingProvider is configured, generates an embedding first.

            :param entry: The MemoryEntry to store.

            :returns: The stored MemoryEntry (potentially with generated embedding).
            :raises: MemoryStoreError, SemanticError
        """
        ...

    @abc.abstractmethod
    def retrieve(self, identifier: str) -> Optional[MemoryEntry]:
        """
            Retrieves a MemoryEntry by identifier.

            :param identifier: The entry identifier.

            :returns: The MemoryEntry, or None if not found.
            :raises: MemoryStoreError
        """
        ...

    @abc.abstractmethod
    def search(self, query: MemoryQuery) -> MemoryQueryResult:
        """
            Executes a MemoryQuery against the store.

            :param query: The MemoryQuery with filter criteria.

            :returns: A MemoryQueryResult with matching entries.
            :raises: MemoryStoreError
        """
        ...

    @abc.abstractmethod
    def update(self, identifier: str, entry: MemoryEntry) -> MemoryEntry:
        """
            Replaces a MemoryEntry by identifier.

            :param identifier: The identifier of the entry to replace.
            :param entry: The new MemoryEntry.

            :returns: The updated MemoryEntry.
            :raises: MemoryStoreError
        """
        ...

    @abc.abstractmethod
    def delete(self, identifier: str) -> None:
        """
            Removes a MemoryEntry by identifier.

            :param identifier: The entry identifier to remove.
            :raises: MemoryStoreError
        """
        ...

    @abc.abstractmethod
    def clear(self) -> None:
        """
            Removes all entries from the store.

            :raises: MemoryStoreError
        """
        ...

    def contains(self, identifier: str) -> bool:
        """
            Returns True if an entry with the given identifier exists.

            :param identifier: The entry identifier.

            :returns: True if the entry exists, False otherwise.
        """
        entry = self.retrieve(identifier=identifier)
        rtnval = entry is not None
        return rtnval

    def cleanup_expired(self, reference_time: datetime = None) -> int:
        """
            Removes all MemoryEntry objects whose expiration timestamp has passed.

            :param reference_time: Optional reference timestamp. Defaults to current UTC time.

            :returns: The count of removed entries.
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)

        removed_count = 0
        all_result = self.search(MemoryQuery())
        for entry in all_result.entries:
            if entry.is_expired(reference_time=reference_time):
                self.delete(identifier=entry.identifier)
                removed_count = removed_count + 1

        if removed_count > 0:
            logger.info(
                "MemoryStore %r cleaned up %d expired entries.",
                self._store_name, removed_count
            )

        rtnval = removed_count
        return rtnval

    def _generate_embedding_if_needed(self, entry: MemoryEntry) -> MemoryEntry:
        """
            If the entry has no embedding and an EmbeddingProvider is configured,
            generates an embedding and returns a new MemoryEntry with the embedding.

            :param entry: The MemoryEntry to check.

            :returns: The original entry or a new entry with embedding.
        """
        if entry.embedding is not None:
            return entry

        if self._embedding_provider is None:
            return entry

        embedding = self._embedding_provider.embed(text=entry.content)
        rtnval = MemoryEntry(
            content=entry.content,
            scope=entry.scope,
            identifier=entry.identifier,
            embedding=embedding,
            metadata=entry.metadata,
            tags=entry.tags,
            created_at=entry.created_at,
            expires_at=entry.expires_at,
        )
        return rtnval

    def _apply_expiration_policy(self, entry: MemoryEntry) -> MemoryEntry:
        """
            If the entry has no expiration and the ExpirationPolicy defines a
            default TTL, returns a new MemoryEntry with the expiration set.

            :param entry: The MemoryEntry to check.

            :returns: The original entry or a new entry with expiration.
        """
        if entry.expires_at is not None:
            return entry

        if self._expiration_policy is None:
            return entry

        if self._expiration_policy.default_ttl is None:
            return entry

        expires_at = entry.created_at + timedelta(seconds=self._expiration_policy.default_ttl)
        rtnval = MemoryEntry(
            content=entry.content,
            scope=entry.scope,
            identifier=entry.identifier,
            embedding=entry.embedding,
            metadata=entry.metadata,
            tags=entry.tags,
            created_at=entry.created_at,
            expires_at=expires_at,
        )
        return rtnval

    def __repr__(self) -> str:
        rtnval = "{}(store_name={!r}, count={})".format(
            self.__class__.__name__, self._store_name, self.count
        )
        return rtnval

    def __str__(self) -> str:
        rtnval = "MemoryStore: {} ({} entries)".format(self._store_name, self.count)
        return rtnval
