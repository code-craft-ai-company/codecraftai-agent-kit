"""
    .. module:: ccai.tests.singlehost.agentkit.test_inmemorystore
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the InMemoryStore class.

    Tests store, retrieve, search, update, delete, clear operations,
    duplicate identifier rejection, filter-based search, semantic search,
    auto-embedding generation, expiration policy application, and
    cleanup of expired entries.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 13.3, 13.4, 13.5**
"""

from datetime import datetime, timedelta, timezone

from ccai.agentkit.embeddingprovider import EmbeddingProvider
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.expirationpolicy import ExpirationPolicy
from ccai.agentkit.inmemorystore import InMemoryStore
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


# ---- Store and Retrieve Tests ----


def test_inmemorystore_store_and_retrieve():
    """
        Storing an entry and retrieving by identifier returns the same entry.
    """
    store = InMemoryStore(store_name="test-store")
    entry = _create_entry(identifier="abc-123", content="hello world")

    store.store(entry=entry)
    retrieved = store.retrieve(identifier="abc-123")

    assert retrieved is not None, "Retrieved entry should not be None."
    assert retrieved.identifier == "abc-123", "Identifier should match."
    assert retrieved.content == "hello world", "Content should match."
    return


def test_inmemorystore_retrieve_nonexistent_returns_none():
    """
        Retrieving a non-existent identifier returns None.
    """
    store = InMemoryStore(store_name="test-store")

    retrieved = store.retrieve(identifier="does-not-exist")

    assert retrieved is None, "Retrieving a non-existent identifier should return None."
    return


def test_inmemorystore_count_reflects_stored_entries():
    """
        The count property reflects the number of stored entries.
    """
    store = InMemoryStore(store_name="test-store")

    assert store.count == 0, "Empty store should have count 0."

    store.store(entry=_create_entry(identifier="e1"))
    assert store.count == 1, "Count should be 1 after storing one entry."

    store.store(entry=_create_entry(identifier="e2"))
    assert store.count == 2, "Count should be 2 after storing two entries."
    return


# ---- Duplicate Identifier Tests ----


def test_inmemorystore_store_duplicate_identifier_raises_semantic_error():
    """
        Storing an entry with a duplicate identifier raises SemanticError.
    """
    store = InMemoryStore(store_name="test-store")
    entry_one = _create_entry(identifier="dup-id", content="first")
    entry_two = _create_entry(identifier="dup-id", content="second")

    store.store(entry=entry_one)

    raised = False
    try:
        store.store(entry=entry_two)
    except SemanticError:
        raised = True

    assert raised, "Storing a duplicate identifier should raise SemanticError."
    return


# ---- Update Tests ----


def test_inmemorystore_update_replaces_entry():
    """
        Updating an entry replaces the old entry with the new one.
    """
    store = InMemoryStore(store_name="test-store")
    original = _create_entry(identifier="upd-1", content="original content")
    store.store(entry=original)

    replacement = _create_entry(identifier="upd-1", content="updated content")
    store.update(identifier="upd-1", entry=replacement)

    retrieved = store.retrieve(identifier="upd-1")
    assert retrieved is not None, "Updated entry should be retrievable."
    assert retrieved.content == "updated content", "Content should be updated."
    return


# ---- Delete Tests ----


def test_inmemorystore_delete_removes_entry():
    """
        Deleting an entry removes it from the store.
    """
    store = InMemoryStore(store_name="test-store")
    entry = _create_entry(identifier="del-1")
    store.store(entry=entry)

    store.delete(identifier="del-1")

    retrieved = store.retrieve(identifier="del-1")
    assert retrieved is None, "Deleted entry should not be retrievable."
    assert store.count == 0, "Count should be 0 after deleting the only entry."
    return


def test_inmemorystore_delete_nonexistent_does_not_raise():
    """
        Deleting a non-existent identifier does not raise an error.
    """
    store = InMemoryStore(store_name="test-store")

    store.delete(identifier="nonexistent")
    assert store.count == 0, "Count should remain 0."
    return


# ---- Clear Tests ----


def test_inmemorystore_clear_removes_all_entries():
    """
        Clearing the store removes all entries.
    """
    store = InMemoryStore(store_name="test-store")
    store.store(entry=_create_entry(identifier="c1"))
    store.store(entry=_create_entry(identifier="c2"))
    store.store(entry=_create_entry(identifier="c3"))

    store.clear()

    assert store.count == 0, "Count should be 0 after clear."
    assert store.retrieve(identifier="c1") is None, "Entry c1 should be gone."
    assert store.retrieve(identifier="c2") is None, "Entry c2 should be gone."
    assert store.retrieve(identifier="c3") is None, "Entry c3 should be gone."
    return


# ---- Search with Tag Filter Tests ----


def test_inmemorystore_search_by_tags():
    """
        Searching by tags returns only entries that contain all specified tags.
    """
    store = InMemoryStore(store_name="test-store")
    store.store(entry=_create_entry(identifier="t1", tags=["python", "ai"]))
    store.store(entry=_create_entry(identifier="t2", tags=["python"]))
    store.store(entry=_create_entry(identifier="t3", tags=["java"]))

    query = MemoryQuery(tags=["python"])
    result = store.search(query=query)

    ids = [e.identifier for e in result.entries]
    assert "t1" in ids, "Entry t1 should match tag 'python'."
    assert "t2" in ids, "Entry t2 should match tag 'python'."
    assert "t3" not in ids, "Entry t3 should not match tag 'python'."
    return


def test_inmemorystore_search_by_multiple_tags():
    """
        Searching by multiple tags uses AND logic.
    """
    store = InMemoryStore(store_name="test-store")
    store.store(entry=_create_entry(identifier="t1", tags=["python", "ai"]))
    store.store(entry=_create_entry(identifier="t2", tags=["python"]))

    query = MemoryQuery(tags=["python", "ai"])
    result = store.search(query=query)

    ids = [e.identifier for e in result.entries]
    assert "t1" in ids, "Entry t1 should match both tags."
    assert "t2" not in ids, "Entry t2 should not match both tags."
    return


# ---- Search with Metadata Filter Tests ----


def test_inmemorystore_search_by_metadata():
    """
        Searching by metadata returns only entries with matching key-value pairs.
    """
    store = InMemoryStore(store_name="test-store")
    store.store(entry=_create_entry(identifier="m1", metadata={"source": "web", "priority": "high"}))
    store.store(entry=_create_entry(identifier="m2", metadata={"source": "web", "priority": "low"}))
    store.store(entry=_create_entry(identifier="m3", metadata={"source": "file"}))

    query = MemoryQuery(metadata={"source": "web"})
    result = store.search(query=query)

    ids = [e.identifier for e in result.entries]
    assert "m1" in ids, "Entry m1 should match metadata source=web."
    assert "m2" in ids, "Entry m2 should match metadata source=web."
    assert "m3" not in ids, "Entry m3 should not match metadata source=web."
    return


# ---- Search with Scope Filter Tests ----


def test_inmemorystore_search_by_scope():
    """
        Searching by scope returns only entries with the matching scope.
    """
    store = InMemoryStore(store_name="test-store")
    store.store(entry=_create_entry(identifier="s1", scope=MemoryScope.AGENT))
    store.store(entry=_create_entry(identifier="s2", scope=MemoryScope.SHARED))
    store.store(entry=_create_entry(identifier="s3", scope=MemoryScope.GLOBAL))

    query = MemoryQuery(scope=MemoryScope.SHARED)
    result = store.search(query=query)

    ids = [e.identifier for e in result.entries]
    assert ids == ["s2"], "Only entry s2 should match scope SHARED, got {}.".format(ids)
    return


# ---- Search with Time Range Filter Tests ----


def test_inmemorystore_search_by_time_range():
    """
        Searching by time range returns entries within the specified range.
    """
    store = InMemoryStore(store_name="test-store")
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    store.store(entry=_create_entry(
        identifier="tr1", created_at=base_time - timedelta(hours=2)))
    store.store(entry=_create_entry(
        identifier="tr2", created_at=base_time))
    store.store(entry=_create_entry(
        identifier="tr3", created_at=base_time + timedelta(hours=2)))

    query = MemoryQuery(
        start_time=base_time - timedelta(hours=1),
        end_time=base_time + timedelta(hours=1),
    )
    result = store.search(query=query)

    ids = [e.identifier for e in result.entries]
    assert "tr2" in ids, "Entry tr2 should be within the time range."
    assert "tr1" not in ids, "Entry tr1 should be outside the time range."
    assert "tr3" not in ids, "Entry tr3 should be outside the time range."
    return


# ---- Semantic Search Tests ----


def test_inmemorystore_search_semantic_no_provider_raises_error():
    """
        Searching with semantic text when no EmbeddingProvider is configured
        raises MemoryStoreError.
    """
    store = InMemoryStore(store_name="test-store")
    store.store(entry=_create_entry(identifier="sem-1"))

    query = MemoryQuery(semantic_text="find something similar")

    raised = False
    try:
        store.search(query=query)
    except MemoryStoreError:
        raised = True

    assert raised, "Semantic search without EmbeddingProvider should raise MemoryStoreError."
    return


def test_inmemorystore_search_semantic_with_provider_returns_ranked_results():
    """
        Searching with semantic text and a configured EmbeddingProvider
        returns results ranked by cosine similarity.
    """
    provider = StubEmbeddingProvider()
    store = InMemoryStore(store_name="test-store", embedding_provider=provider)

    store.store(entry=_create_entry(
        identifier="sem-short", content="hi"))
    store.store(entry=_create_entry(
        identifier="sem-medium", content="hello world"))
    store.store(entry=_create_entry(
        identifier="sem-long", content="this is a much longer piece of content"))

    query = MemoryQuery(semantic_text="hello world")
    result = store.search(query=query)

    assert result.total_count == 3, "All three entries should be returned."
    assert result.scores is not None, "Scores should be present for semantic search."
    assert len(result.scores) == 3, "Should have a score for each entry."

    for i in range(len(result.scores) - 1):
        assert result.scores[i] >= result.scores[i + 1], \
            "Scores should be in descending order."
    return


# ---- Auto-Embedding Generation Tests ----


def test_inmemorystore_store_generates_embedding_when_provider_configured():
    """
        Storing an entry without an embedding when an EmbeddingProvider is
        configured auto-generates the embedding.
    """
    provider = StubEmbeddingProvider()
    store = InMemoryStore(store_name="test-store", embedding_provider=provider)

    entry = _create_entry(identifier="emb-1", content="generate my embedding")
    stored = store.store(entry=entry)

    assert stored.embedding is not None, "Stored entry should have an auto-generated embedding."
    assert len(stored.embedding) == 3, "Embedding should have 3 dimensions."

    retrieved = store.retrieve(identifier="emb-1")
    assert retrieved.embedding is not None, "Retrieved entry should have the embedding."
    return


def test_inmemorystore_store_preserves_existing_embedding():
    """
        Storing an entry that already has an embedding does not overwrite it.
    """
    provider = StubEmbeddingProvider()
    store = InMemoryStore(store_name="test-store", embedding_provider=provider)

    original_embedding = [1.0, 2.0, 3.0]
    entry = _create_entry(identifier="emb-2", content="keep my embedding",
                          embedding=original_embedding)
    stored = store.store(entry=entry)

    assert stored.embedding == original_embedding, \
        "Existing embedding should be preserved, not overwritten."
    return


# ---- Expiration Policy Tests ----


def test_inmemorystore_store_applies_expiration_policy():
    """
        Storing an entry without an expiration when an ExpirationPolicy with
        a default TTL is configured sets the expiration timestamp.
    """
    policy = ExpirationPolicy(default_ttl=3600.0)
    store = InMemoryStore(store_name="test-store", expiration_policy=policy)

    entry = _create_entry(identifier="exp-1", content="will expire")
    stored = store.store(entry=entry)

    assert stored.expires_at is not None, "Stored entry should have an expiration timestamp."
    expected_expires = stored.created_at + timedelta(seconds=3600.0)
    assert stored.expires_at == expected_expires, \
        "Expiration should be created_at + TTL."
    return


def test_inmemorystore_store_preserves_existing_expiration():
    """
        Storing an entry that already has an expiration does not overwrite it.
    """
    policy = ExpirationPolicy(default_ttl=3600.0)
    store = InMemoryStore(store_name="test-store", expiration_policy=policy)

    custom_expires = datetime(2030, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    entry = _create_entry(identifier="exp-2", content="custom expiration",
                          expires_at=custom_expires)
    stored = store.store(entry=entry)

    assert stored.expires_at == custom_expires, \
        "Existing expiration should be preserved, not overwritten."
    return


# ---- Cleanup Expired Tests ----


def test_inmemorystore_cleanup_expired_removes_expired_entries():
    """
        cleanup_expired removes entries whose expiration has passed and
        returns the count of removed entries.
    """
    store = InMemoryStore(store_name="test-store")

    now = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    past = now - timedelta(hours=1)
    future = now + timedelta(hours=1)

    store.store(entry=_create_entry(
        identifier="alive", content="still valid", expires_at=future))
    store.store(entry=_create_entry(
        identifier="expired", content="should be removed", expires_at=past))
    store.store(entry=_create_entry(
        identifier="no-expiry", content="never expires"))

    removed = store.cleanup_expired(reference_time=now)

    assert removed == 1, "Should have removed 1 expired entry, got {}.".format(removed)
    assert store.count == 2, "Two entries should remain."
    assert store.retrieve(identifier="alive") is not None, "Alive entry should remain."
    assert store.retrieve(identifier="expired") is None, "Expired entry should be removed."
    assert store.retrieve(identifier="no-expiry") is not None, "No-expiry entry should remain."
    return


def test_inmemorystore_cleanup_expired_returns_zero_when_none_expired():
    """
        cleanup_expired returns 0 when no entries are expired.
    """
    store = InMemoryStore(store_name="test-store")

    now = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    future = now + timedelta(hours=1)

    store.store(entry=_create_entry(
        identifier="valid", content="still valid", expires_at=future))

    removed = store.cleanup_expired(reference_time=now)

    assert removed == 0, "Should have removed 0 entries, got {}.".format(removed)
    assert store.count == 1, "Entry should remain."
    return


# ---- Search with No Filters (All Entries) ----


def test_inmemorystore_search_no_filters_returns_all():
    """
        Searching with no filters returns all stored entries.
    """
    store = InMemoryStore(store_name="test-store")
    store.store(entry=_create_entry(identifier="all-1"))
    store.store(entry=_create_entry(identifier="all-2"))
    store.store(entry=_create_entry(identifier="all-3"))

    query = MemoryQuery()
    result = store.search(query=query)

    assert result.total_count == 3, "Should return all 3 entries, got {}.".format(result.total_count)
    return


# ---- Search with max_results ----


def test_inmemorystore_search_max_results_limits_output():
    """
        Searching with max_results limits the number of returned entries.
    """
    store = InMemoryStore(store_name="test-store")
    for i in range(10):
        store.store(entry=_create_entry(identifier="lim-{}".format(i)))

    query = MemoryQuery(max_results=3)
    result = store.search(query=query)

    assert len(result.entries) == 3, "Should return at most 3 entries, got {}.".format(len(result.entries))
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
