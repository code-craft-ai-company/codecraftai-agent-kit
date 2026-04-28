"""
    Built-in MemoryStore implementation that stores MemoryEntry objects
    in process memory using dictionary-based indexing.

    Suitable for development, testing, and short-lived agents where
    persistence across process restarts is not required.
"""

import logging
from typing import Optional

from automojo.agentkit.embeddingprovider import EmbeddingProvider
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.expirationpolicy import ExpirationPolicy
from automojo.agentkit.memoryerrors import MemoryStoreError
from automojo.agentkit.memoryentry import MemoryEntry
from automojo.agentkit.memoryindex import MemoryIndex
from automojo.agentkit.memoryquery import MemoryQuery
from automojo.agentkit.memoryqueryresult import MemoryQueryResult
from automojo.agentkit.memorystore import MemoryStore


logger = logging.getLogger("automojo.agentkit.memory")


class InMemoryStore(MemoryStore):
    """
        Built-in MemoryStore implementation that stores MemoryEntry objects
        in process memory using dictionary-based indexing. Indexes entries
        by identifier, tags, and metadata keys for efficient retrieval.
    """

    def __init__(self, store_name: str,
                 embedding_provider: EmbeddingProvider = None,
                 expiration_policy: ExpirationPolicy = None) -> None:
        """
            Constructs an InMemoryStore.

            :param store_name: The name of this memory store.
            :param embedding_provider: Optional EmbeddingProvider for generating embeddings.
            :param expiration_policy: Optional ExpirationPolicy for entry lifecycle.

            :raises: SemanticError if store_name is empty.
        """
        super().__init__(
            store_name=store_name,
            embedding_provider=embedding_provider,
            expiration_policy=expiration_policy,
        )
        self._index = MemoryIndex()
        return

    @property
    def count(self) -> int:
        """
            Returns the count of stored MemoryEntry objects.

            :returns: The entry count as an integer.
        """
        rtnval = self._index.count
        return rtnval

    def store(self, entry: MemoryEntry) -> MemoryEntry:
        """
            Stores a MemoryEntry in the in-memory index. Checks for duplicate
            identifiers, applies the expiration policy, generates an embedding
            if needed, and adds the entry to the index.

            :param entry: The MemoryEntry to store.

            :returns: The stored MemoryEntry (potentially with generated embedding and expiration).
            :raises: SemanticError if a MemoryEntry with the same identifier already exists.
        """
        if self._index.contains(identifier=entry.identifier):
            errmsg = "A MemoryEntry with identifier {!r} already exists in store {!r}.".format(
                entry.identifier, self._store_name
            )
            raise SemanticError(errmsg)

        entry = self._apply_expiration_policy(entry=entry)
        entry = self._generate_embedding_if_needed(entry=entry)
        self._index.add(entry=entry)

        logger.info(
            "InMemoryStore %r stored entry %r with scope %s.",
            self._store_name, entry.identifier, entry.scope.value
        )

        rtnval = entry
        return rtnval

    def retrieve(self, identifier: str) -> Optional[MemoryEntry]:
        """
            Retrieves a MemoryEntry by identifier.

            :param identifier: The entry identifier.

            :returns: The MemoryEntry, or None if not found.
        """
        rtnval = self._index.get(identifier=identifier)
        return rtnval

    def search(self, query: MemoryQuery) -> MemoryQueryResult:
        """
            Executes a MemoryQuery against the in-memory index. When the query
            includes semantic text, generates a query embedding using the
            configured EmbeddingProvider and delegates to the index for
            cosine similarity ranking.

            :param query: The MemoryQuery with filter criteria.

            :returns: A MemoryQueryResult with matching entries.
            :raises: MemoryStoreError if semantic search is requested without an EmbeddingProvider.
        """
        query_embedding = None
        if query.semantic_text is not None:
            if self._embedding_provider is None:
                errmsg = "Semantic search requires an EmbeddingProvider, but none is configured for store {!r}.".format(
                    self._store_name
                )
                raise MemoryStoreError(
                    store_name=self._store_name,
                    operation="search",
                    cause=ValueError(errmsg),
                )
            query_embedding = self._embedding_provider.embed(text=query.semantic_text)

        rtnval = self._index.search(query=query, query_embedding=query_embedding)

        logger.info(
            "InMemoryStore %r search returned %d entries.",
            self._store_name, rtnval.total_count
        )

        return rtnval

    def update(self, identifier: str, entry: MemoryEntry) -> MemoryEntry:
        """
            Replaces a MemoryEntry by identifier. Removes the old entry from
            the index, generates an embedding if needed, and adds the new entry.

            :param identifier: The identifier of the entry to replace.
            :param entry: The new MemoryEntry.

            :returns: The updated MemoryEntry.
        """
        self._index.remove(identifier=identifier)
        entry = self._generate_embedding_if_needed(entry=entry)
        self._index.add(entry=entry)
        rtnval = entry
        return rtnval

    def delete(self, identifier: str) -> None:
        """
            Removes a MemoryEntry by identifier from the in-memory index.

            :param identifier: The entry identifier to remove.
        """
        self._index.remove(identifier=identifier)

        logger.info(
            "InMemoryStore %r deleted entry %r.",
            self._store_name, identifier
        )

        return

    def clear(self) -> None:
        """
            Removes all entries from the in-memory index.
        """
        self._index.clear()
        return
