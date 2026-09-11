"""
    .. module:: ccai.tests.singlehost.agentkit.test_filememorystore
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the FileMemoryStore class.

    Tests store, retrieve, search, update, delete, clear operations,
    directory creation, loading existing entries from disk, duplicate
    identifier rejection, and I/O failure handling.

    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8**
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone

from ccai.agentkit.embeddingprovider import EmbeddingProvider
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.expirationpolicy import ExpirationPolicy
from ccai.agentkit.filememorystore import FileMemoryStore
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryerrors import MemoryStoreError
from ccai.agentkit.memoryquery import MemoryQuery
from ccai.agentkit.memoryscope import MemoryScope


# ---- Concrete Test Helpers ----


class StubEmbeddingProvider(EmbeddingProvider):
    """
        A minimal concrete subclass of EmbeddingProvider for testing.
        Returns a fixed embedding vector based on text length for
        deterministic similarity ranking.
    """

    def __init__(self, provider_name: str = "stub-provider",
                 embedding_dimension: int = 3) -> None:
        super().__init__(
            provider_name=provider_name,
            embedding_dimension=embedding_dimension,
        )
        return

    def embed(self, text: str) -> list:
        length = len(text)
        rtnval = [float(length) * 0.1, float(length) * 0.2, float(length) * 0.3]
        return rtnval

    def embed_batch(self, texts: list) -> list:
        rtnval = [self.embed(text=t) for t in texts]
        return rtnval


def _create_entry(identifier: str = "entry-1", content: str = "test content",
                  scope: MemoryScope = MemoryScope.AGENT,
                  embedding: list = None, metadata: dict = None,
                  tags: list = None, created_at: datetime = None,
                  expires_at: datetime = None) -> MemoryEntry:
    """
        Creates a MemoryEntry with sensible defaults for testing.
    """
    entry = MemoryEntry(
        content=content,
        scope=scope,
        identifier=identifier,
        embedding=embedding,
        metadata=metadata,
        tags=tags,
        created_at=created_at,
        expires_at=expires_at,
    )
    return entry


def _make_tmpdir() -> str:
    """
        Creates a temporary directory for test isolation.
    """
    rtnval = tempfile.mkdtemp(prefix="filememorystore_test_")
    return rtnval


def _cleanup_tmpdir(tmpdir: str) -> None:
    """
        Removes a temporary directory and all its contents.
    """
    shutil.rmtree(tmpdir, ignore_errors=True)
    return


# ---- Store and Retrieve Tests ----


def test_filememorystore_store_creates_json_file():
    """
        Storing an entry creates a JSON file in the configured directory.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        entry = _create_entry(identifier="file-1", content="hello world")

        store.store(entry=entry)

        filepath = os.path.join(tmpdir, "file-1.json")
        assert os.path.isfile(filepath), "JSON file should exist after store."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


def test_filememorystore_retrieve_returns_stored_entry():
    """
        Storing an entry and retrieving by identifier returns the same entry.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        entry = _create_entry(identifier="ret-1", content="retrieve me",
                              tags=["tag1"], metadata={"key": "val"})

        store.store(entry=entry)
        retrieved = store.retrieve(identifier="ret-1")

        assert retrieved is not None, "Retrieved entry should not be None."
        assert retrieved.identifier == "ret-1", "Identifier should match."
        assert retrieved.content == "retrieve me", "Content should match."
        assert retrieved.tags == ["tag1"], "Tags should match."
        assert retrieved.metadata == {"key": "val"}, "Metadata should match."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


def test_filememorystore_retrieve_nonexistent_returns_none():
    """
        Retrieving a non-existent identifier returns None.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)

        retrieved = store.retrieve(identifier="does-not-exist")

        assert retrieved is None, "Retrieving a non-existent identifier should return None."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Constructor Tests ----


def test_filememorystore_constructor_loads_existing_entries():
    """
        Constructing a FileMemoryStore from a directory with existing JSON
        files loads those entries into the index.
    """
    tmpdir = _make_tmpdir()
    try:
        store_one = FileMemoryStore(store_name="store-one", directory_path=tmpdir)
        store_one.store(entry=_create_entry(identifier="exist-1", content="first"))
        store_one.store(entry=_create_entry(identifier="exist-2", content="second"))

        store_two = FileMemoryStore(store_name="store-two", directory_path=tmpdir)

        assert store_two.count == 2, "New store should load 2 existing entries, got {}.".format(store_two.count)
        assert store_two.retrieve(identifier="exist-1") is not None, "Entry exist-1 should be loaded."
        assert store_two.retrieve(identifier="exist-2") is not None, "Entry exist-2 should be loaded."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


def test_filememorystore_constructor_creates_directory_if_missing():
    """
        Constructing a FileMemoryStore with a non-existent directory creates it.
    """
    tmpdir = _make_tmpdir()
    nested_dir = os.path.join(tmpdir, "sub", "nested")
    try:
        assert not os.path.exists(nested_dir), "Nested directory should not exist yet."

        store = FileMemoryStore(store_name="test-store", directory_path=nested_dir)

        assert os.path.isdir(nested_dir), "Directory should be created by constructor."
        assert store.count == 0, "New store in new directory should be empty."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Duplicate Identifier Tests ----


def test_filememorystore_store_duplicate_identifier_raises_semantic_error():
    """
        Storing an entry with a duplicate identifier raises SemanticError.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        entry_one = _create_entry(identifier="dup-id", content="first")
        entry_two = _create_entry(identifier="dup-id", content="second")

        store.store(entry=entry_one)

        raised = False
        try:
            store.store(entry=entry_two)
        except SemanticError:
            raised = True

        assert raised, "Storing a duplicate identifier should raise SemanticError."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Count Tests ----


def test_filememorystore_count_reflects_stored_entries():
    """
        The count property reflects the number of stored entries.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)

        assert store.count == 0, "Empty store should have count 0."

        store.store(entry=_create_entry(identifier="c1"))
        assert store.count == 1, "Count should be 1 after storing one entry."

        store.store(entry=_create_entry(identifier="c2"))
        assert store.count == 2, "Count should be 2 after storing two entries."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Update Tests ----


def test_filememorystore_update_replaces_entry():
    """
        Updating an entry replaces the old entry with the new one on disk and in index.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        original = _create_entry(identifier="upd-1", content="original content")
        store.store(entry=original)

        replacement = _create_entry(identifier="upd-1", content="updated content")
        store.update(identifier="upd-1", entry=replacement)

        retrieved = store.retrieve(identifier="upd-1")
        assert retrieved is not None, "Updated entry should be retrievable."
        assert retrieved.content == "updated content", "Content should be updated."

        reloaded = FileMemoryStore(store_name="reload", directory_path=tmpdir)
        reloaded_entry = reloaded.retrieve(identifier="upd-1")
        assert reloaded_entry is not None, "Updated entry should persist on disk."
        assert reloaded_entry.content == "updated content", "Persisted content should be updated."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Delete Tests ----


def test_filememorystore_delete_removes_json_file():
    """
        Deleting an entry removes the JSON file from disk and the entry from the index.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        entry = _create_entry(identifier="del-1")
        store.store(entry=entry)

        filepath = os.path.join(tmpdir, "del-1.json")
        assert os.path.isfile(filepath), "JSON file should exist before delete."

        store.delete(identifier="del-1")

        assert not os.path.isfile(filepath), "JSON file should be removed after delete."
        assert store.retrieve(identifier="del-1") is None, "Deleted entry should not be retrievable."
        assert store.count == 0, "Count should be 0 after deleting the only entry."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


def test_filememorystore_delete_nonexistent_does_not_raise():
    """
        Deleting a non-existent identifier does not raise an error.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)

        store.delete(identifier="nonexistent")
        assert store.count == 0, "Count should remain 0."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Clear Tests ----


def test_filememorystore_clear_removes_all_json_files():
    """
        Clearing the store removes all JSON files and all entries from the index.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        store.store(entry=_create_entry(identifier="clr-1"))
        store.store(entry=_create_entry(identifier="clr-2"))
        store.store(entry=_create_entry(identifier="clr-3"))

        store.clear()

        assert store.count == 0, "Count should be 0 after clear."
        json_files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
        assert len(json_files) == 0, "No JSON files should remain after clear, found {}.".format(json_files)
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Search Tests ----


def test_filememorystore_search_by_tags():
    """
        Searching by tags returns only entries that contain all specified tags.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        store.store(entry=_create_entry(identifier="t1", tags=["python", "ai"]))
        store.store(entry=_create_entry(identifier="t2", tags=["python"]))
        store.store(entry=_create_entry(identifier="t3", tags=["java"]))

        query = MemoryQuery(tags=["python"])
        result = store.search(query=query)

        ids = [e.identifier for e in result.entries]
        assert "t1" in ids, "Entry t1 should match tag 'python'."
        assert "t2" in ids, "Entry t2 should match tag 'python'."
        assert "t3" not in ids, "Entry t3 should not match tag 'python'."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


def test_filememorystore_search_semantic_no_provider_raises_error():
    """
        Searching with semantic text when no EmbeddingProvider is configured
        raises MemoryStoreError.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        store.store(entry=_create_entry(identifier="sem-1"))

        query = MemoryQuery(semantic_text="find something similar")

        raised = False
        try:
            store.search(query=query)
        except MemoryStoreError:
            raised = True

        assert raised, "Semantic search without EmbeddingProvider should raise MemoryStoreError."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


def test_filememorystore_search_semantic_with_provider():
    """
        Searching with semantic text and a configured EmbeddingProvider
        returns results ranked by cosine similarity.
    """
    tmpdir = _make_tmpdir()
    try:
        provider = StubEmbeddingProvider()
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir,
                                embedding_provider=provider)

        store.store(entry=_create_entry(identifier="sem-short", content="hi"))
        store.store(entry=_create_entry(identifier="sem-medium", content="hello world"))
        store.store(entry=_create_entry(identifier="sem-long",
                                        content="this is a much longer piece of content"))

        query = MemoryQuery(semantic_text="hello world")
        result = store.search(query=query)

        assert result.total_count == 3, "All three entries should be returned."
        assert result.scores is not None, "Scores should be present for semantic search."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- I/O Failure Tests ----


def test_filememorystore_load_failure_raises_memorystoreerror():
    """
        Loading a corrupt JSON file raises MemoryStoreError with file path detail.
    """
    tmpdir = _make_tmpdir()
    try:
        corrupt_filepath = os.path.join(tmpdir, "corrupt.json")
        with open(corrupt_filepath, "w", encoding="utf-8") as fh:
            fh.write("{this is not valid json}")

        raised = False
        caught_error = None
        try:
            FileMemoryStore(store_name="test-store", directory_path=tmpdir)
        except MemoryStoreError as exc:
            raised = True
            caught_error = exc

        assert raised, "Loading a corrupt JSON file should raise MemoryStoreError."
        assert caught_error.store_name == "test-store", "Error should reference the store name."
        assert caught_error.operation == "load", "Error operation should be 'load'."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


def test_filememorystore_write_failure_raises_memorystoreerror():
    """
        A write failure while storing an entry raises MemoryStoreError.

        The entry file path is occupied by a directory so that opening it
        for writing fails on every platform; POSIX permission bits are
        ignored on Windows.
    """
    tmpdir = _make_tmpdir()
    try:
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir)

        os.makedirs(os.path.join(tmpdir, "fail-write.json"))

        entry = _create_entry(identifier="fail-write", content="should fail")

        raised = False
        caught_error = None
        try:
            store.store(entry=entry)
        except MemoryStoreError as exc:
            raised = True
            caught_error = exc

        assert raised, "A write failure while storing should raise MemoryStoreError."
        assert caught_error.store_name == "test-store", "Error should reference the store name."
        assert caught_error.operation == "store", "Error operation should be 'store'."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Expiration Policy Tests ----


def test_filememorystore_store_applies_expiration_policy():
    """
        Storing an entry without an expiration when an ExpirationPolicy with
        a default TTL is configured sets the expiration timestamp.
    """
    tmpdir = _make_tmpdir()
    try:
        policy = ExpirationPolicy(default_ttl=3600.0)
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir,
                                expiration_policy=policy)

        entry = _create_entry(identifier="exp-1", content="will expire")
        stored = store.store(entry=entry)

        assert stored.expires_at is not None, "Stored entry should have an expiration timestamp."
        expected_expires = stored.created_at + timedelta(seconds=3600.0)
        assert stored.expires_at == expected_expires, "Expiration should be created_at + TTL."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


# ---- Auto-Embedding Generation Tests ----


def test_filememorystore_store_generates_embedding_when_provider_configured():
    """
        Storing an entry without an embedding when an EmbeddingProvider is
        configured auto-generates the embedding.
    """
    tmpdir = _make_tmpdir()
    try:
        provider = StubEmbeddingProvider()
        store = FileMemoryStore(store_name="test-store", directory_path=tmpdir,
                                embedding_provider=provider)

        entry = _create_entry(identifier="emb-1", content="generate my embedding")
        stored = store.store(entry=entry)

        assert stored.embedding is not None, "Stored entry should have an auto-generated embedding."
        assert len(stored.embedding) == 3, "Embedding should have 3 dimensions."
    finally:
        _cleanup_tmpdir(tmpdir)
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
