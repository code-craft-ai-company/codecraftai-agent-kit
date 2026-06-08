"""
    Built-in MemoryStore implementation that persists MemoryEntry objects
    to JSON files on the local file system.

    Each entry is stored as a separate JSON file using the entry identifier
    as the file name. On construction, existing JSON files in the configured
    directory are loaded into an in-memory index for efficient retrieval
    and search.

    Suitable for single-agent local deployments where persistence across
    process restarts is required without an external database.
"""

import logging
import os
from typing import Optional

from ccai.agentkit.embeddingprovider import EmbeddingProvider
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.expirationpolicy import ExpirationPolicy
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryerrors import MemoryStoreError
from ccai.agentkit.memoryindex import MemoryIndex
from ccai.agentkit.memoryquery import MemoryQuery
from ccai.agentkit.memoryqueryresult import MemoryQueryResult
from ccai.agentkit.memorystore import MemoryStore


logger = logging.getLogger("ccai.agentkit.memory")


class FileMemoryStore(MemoryStore):
    """
        Built-in MemoryStore implementation that persists MemoryEntry objects
        to JSON files on the local file system. Each entry is stored as a
        separate JSON file using the entry identifier as the file name.
    """

    def __init__(self, store_name: str, directory_path: str,
                 embedding_provider: EmbeddingProvider = None,
                 expiration_policy: ExpirationPolicy = None) -> None:
        """
            Constructs a FileMemoryStore.

            :param store_name: The name of this memory store.
            :param directory_path: The directory path for storing JSON files.
            :param embedding_provider: Optional EmbeddingProvider for generating embeddings.
            :param expiration_policy: Optional ExpirationPolicy for entry lifecycle.

            :raises: SemanticError if store_name is empty.
            :raises: MemoryStoreError if existing entry files cannot be loaded.
        """
        super().__init__(
            store_name=store_name,
            embedding_provider=embedding_provider,
            expiration_policy=expiration_policy,
        )
        self._directory_path = directory_path
        self._index = MemoryIndex()

        if not os.path.exists(self._directory_path):
            os.makedirs(self._directory_path, exist_ok=True)

        self._load_existing_entries()
        return

    @property
    def directory_path(self) -> str:
        """
            The directory path where JSON files are stored.

            :returns: The directory path string.
        """
        return self._directory_path

    @property
    def count(self) -> int:
        """
            Returns the count of stored MemoryEntry objects.

            :returns: The entry count as an integer.
        """
        rtnval = self._index.count
        return rtnval

    def _load_existing_entries(self) -> None:
        """
            Loads all existing MemoryEntry JSON files from the configured
            directory into the in-memory index.

            :raises: MemoryStoreError if a file cannot be read or parsed.
        """
        if not os.path.isdir(self._directory_path):
            return

        for filename in os.listdir(self._directory_path):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(self._directory_path, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    json_str = fh.read()
                entry = MemoryEntry.from_json(json_str=json_str)
                self._index.add(entry=entry)
            except Exception as exc:
                raise MemoryStoreError(
                    store_name=self._store_name,
                    operation="load",
                    cause=exc,
                ) from exc

        return

    def _entry_filepath(self, identifier: str) -> str:
        """
            Returns the file path for a given entry identifier.

            :param identifier: The entry identifier.

            :returns: The full file path string.
        """
        filename = "{}.json".format(identifier)
        rtnval = os.path.join(self._directory_path, filename)
        return rtnval

    def _write_entry_file(self, entry: MemoryEntry) -> None:
        """
            Writes a MemoryEntry to a JSON file.

            :param entry: The MemoryEntry to write.

            :raises: MemoryStoreError on I/O failure.
        """
        filepath = self._entry_filepath(identifier=entry.identifier)
        try:
            json_str = entry.to_json()
            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write(json_str)
        except Exception as exc:
            raise MemoryStoreError(
                store_name=self._store_name,
                operation="store",
                cause=exc,
            ) from exc
        return

    def _delete_entry_file(self, identifier: str) -> None:
        """
            Deletes the JSON file for a given entry identifier.

            :param identifier: The entry identifier.

            :raises: MemoryStoreError on I/O failure.
        """
        filepath = self._entry_filepath(identifier=identifier)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as exc:
            raise MemoryStoreError(
                store_name=self._store_name,
                operation="delete",
                cause=exc,
            ) from exc
        return

    def store(self, entry: MemoryEntry) -> MemoryEntry:
        """
            Stores a MemoryEntry as a JSON file and indexes it.

            :param entry: The MemoryEntry to store.

            :returns: The stored MemoryEntry (potentially with generated embedding and expiration).
            :raises: SemanticError if a MemoryEntry with the same identifier already exists.
            :raises: MemoryStoreError on I/O failure.
        """
        if self._index.contains(identifier=entry.identifier):
            errmsg = "A MemoryEntry with identifier {!r} already exists in store {!r}.".format(
                entry.identifier, self._store_name
            )
            raise SemanticError(errmsg)

        entry = self._apply_expiration_policy(entry=entry)
        entry = self._generate_embedding_if_needed(entry=entry)
        self._write_entry_file(entry=entry)
        self._index.add(entry=entry)

        logger.info(
            "FileMemoryStore %r stored entry %r with scope %s.",
            self._store_name, entry.identifier, entry.scope.value
        )

        rtnval = entry
        return rtnval

    def retrieve(self, identifier: str) -> Optional[MemoryEntry]:
        """
            Retrieves a MemoryEntry by identifier from the in-memory index.

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
            "FileMemoryStore %r search returned %d entries.",
            self._store_name, rtnval.total_count
        )

        return rtnval

    def update(self, identifier: str, entry: MemoryEntry) -> MemoryEntry:
        """
            Replaces a MemoryEntry by identifier. Deletes the old file,
            removes from the index, generates an embedding if needed,
            writes the new file, and adds to the index.

            :param identifier: The identifier of the entry to replace.
            :param entry: The new MemoryEntry.

            :returns: The updated MemoryEntry.
            :raises: MemoryStoreError on I/O failure.
        """
        self._delete_entry_file(identifier=identifier)
        self._index.remove(identifier=identifier)
        entry = self._generate_embedding_if_needed(entry=entry)
        self._write_entry_file(entry=entry)
        self._index.add(entry=entry)
        rtnval = entry
        return rtnval

    def delete(self, identifier: str) -> None:
        """
            Removes a MemoryEntry by identifier. Deletes the JSON file
            and removes the entry from the in-memory index.

            :param identifier: The entry identifier to remove.

            :raises: MemoryStoreError on I/O failure.
        """
        self._delete_entry_file(identifier=identifier)
        self._index.remove(identifier=identifier)

        logger.info(
            "FileMemoryStore %r deleted entry %r.",
            self._store_name, identifier
        )

        return

    def clear(self) -> None:
        """
            Removes all entries from the store. Deletes all JSON files
            and clears the in-memory index.

            :raises: MemoryStoreError on I/O failure.
        """
        for identifier in list(self._index._entries.keys()):
            self._delete_entry_file(identifier=identifier)
        self._index.clear()
        return
