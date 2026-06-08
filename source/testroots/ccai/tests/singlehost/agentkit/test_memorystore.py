"""
    .. module:: ccai.tests.singlehost.agentkit.test_memorystore
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryStore abstract base class.
"""

from datetime import datetime, timedelta, timezone

from ccai.agentkit.embeddingprovider import EmbeddingProvider
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.expirationpolicy import ExpirationPolicy
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryquery import MemoryQuery
from ccai.agentkit.memoryqueryresult import MemoryQueryResult
from ccai.agentkit.memoryscope import MemoryScope
from ccai.agentkit.memorystore import MemoryStore


# ---- Concrete Test Subclass ----


class StubMemoryStore(MemoryStore):
    """
        A minimal concrete subclass of MemoryStore for testing the
        base class behavior. Uses a simple dictionary for storage.
    """

    def __init__(self, store_name: str, embedding_provider: EmbeddingProvider = None,
                 expiration_policy: ExpirationPolicy = None,
                 credential_names: list = None) -> None:
        super().__init__(
            store_name=store_name,
            embedding_provider=embedding_provider,
            expiration_policy=expiration_policy,
            credential_names=credential_names,
        )
        self._entries = {}
        return

    @property
    def count(self) -> int:
        rtnval = len(self._entries)
        return rtnval

    def store(self, entry: MemoryEntry) -> MemoryEntry:
        self._entries[entry.identifier] = entry
        rtnval = entry
        return rtnval

    def retrieve(self, identifier: str) -> MemoryEntry:
        rtnval = self._entries.get(identifier)
        return rtnval

    def search(self, query: MemoryQuery) -> MemoryQueryResult:
        entries = list(self._entries.values())
        rtnval = MemoryQueryResult(entries=entries)
        return rtnval

    def update(self, identifier: str, entry: MemoryEntry) -> MemoryEntry:
        self._entries[identifier] = entry
        rtnval = entry
        return rtnval

    def delete(self, identifier: str) -> None:
        if identifier in self._entries:
            del self._entries[identifier]
        return

    def clear(self) -> None:
        self._entries = {}
        return


class StubEmbeddingProvider(EmbeddingProvider):
    """
        A minimal concrete subclass of EmbeddingProvider for testing.
        Returns a fixed embedding vector.
    """

    def __init__(self, provider_name: str = "stub-provider",
                 embedding_dimension: int = 3) -> None:
        super().__init__(
            provider_name=provider_name,
            embedding_dimension=embedding_dimension,
        )
        return

    def embed(self, text: str) -> list:
        rtnval = [0.1, 0.2, 0.3]
        return rtnval

    def embed_batch(self, texts: list) -> list:
        rtnval = [[0.1, 0.2, 0.3] for _ in texts]
        return rtnval


# ---- Helper Factories ----


def _create_entry(identifier: str = "entry-1", content: str = "test content",
                  scope: MemoryScope = MemoryScope.AGENT,
                  embedding: list = None, expires_at: datetime = None,
                  created_at: datetime = None) -> MemoryEntry:
    """
        Creates a MemoryEntry with sensible defaults for testing.
    """
    entry = MemoryEntry(
        content=content,
        scope=scope,
        identifier=identifier,
        embedding=embedding,
        created_at=created_at,
        expires_at=expires_at,
    )
    return entry


# ---- Construction Validation Tests ----


def test_memorystore_construction_with_valid_name():
    """
        Verify that a MemoryStore can be constructed with a valid store name.
    """
    store = StubMemoryStore(store_name="test-store")

    assert store.store_name == "test-store", \
        "store_name should be 'test-store'"
    assert store.embedding_provider is None, \
        "embedding_provider should be None when not provided"
    assert store.expiration_policy is None, \
        "expiration_policy should be None when not provided"
    return


def test_memorystore_construction_empty_name_raises_semantic_error():
    """
        Verify that constructing a MemoryStore with an empty name raises SemanticError.
    """
    raised = False
    try:
        StubMemoryStore(store_name="")
    except SemanticError:
        raised = True

    assert raised is True, \
        "SemanticError should be raised for an empty store name"
    return


def test_memorystore_construction_none_name_raises_semantic_error():
    """
        Verify that constructing a MemoryStore with None name raises SemanticError.
    """
    raised = False
    try:
        StubMemoryStore(store_name=None)
    except SemanticError:
        raised = True

    assert raised is True, \
        "SemanticError should be raised for a None store name"
    return


def test_memorystore_construction_whitespace_name_raises_semantic_error():
    """
        Verify that constructing a MemoryStore with whitespace-only name raises SemanticError.
    """
    raised = False
    try:
        StubMemoryStore(store_name="   ")
    except SemanticError:
        raised = True

    assert raised is True, \
        "SemanticError should be raised for a whitespace-only store name"
    return


def test_memorystore_construction_with_embedding_provider():
    """
        Verify that a MemoryStore stores the embedding provider reference.
    """
    provider = StubEmbeddingProvider()
    store = StubMemoryStore(store_name="test-store", embedding_provider=provider)

    assert store.embedding_provider is provider, \
        "embedding_provider should be the provided instance"
    return


def test_memorystore_construction_with_expiration_policy():
    """
        Verify that a MemoryStore stores the expiration policy reference.
    """
    policy = ExpirationPolicy(default_ttl=60.0)
    store = StubMemoryStore(store_name="test-store", expiration_policy=policy)

    assert store.expiration_policy is policy, \
        "expiration_policy should be the provided instance"
    return


# ---- contains Tests ----


def test_memorystore_contains_returns_true_for_existing_entry():
    """
        Verify that contains returns True when the entry exists.
    """
    store = StubMemoryStore(store_name="test-store")
    entry = _create_entry(identifier="e1")
    store.store(entry=entry)

    result = store.contains(identifier="e1")
    assert result is True, \
        "contains should return True for an existing entry"
    return


def test_memorystore_contains_returns_false_for_missing_entry():
    """
        Verify that contains returns False when the entry does not exist.
    """
    store = StubMemoryStore(store_name="test-store")

    result = store.contains(identifier="nonexistent")
    assert result is False, \
        "contains should return False for a missing entry"
    return


def test_memorystore_contains_delegates_to_retrieve():
    """
        Verify that contains uses retrieve to check for entry existence.
        If retrieve returns an entry, contains returns True.
        If retrieve returns None, contains returns False.
    """
    store = StubMemoryStore(store_name="test-store")
    entry = _create_entry(identifier="e1")
    store.store(entry=entry)

    result_exists = store.contains(identifier="e1")
    result_missing = store.contains(identifier="e2")

    assert result_exists is True, \
        "contains should return True when retrieve returns an entry"
    assert result_missing is False, \
        "contains should return False when retrieve returns None"
    return


# ---- _generate_embedding_if_needed Tests ----


def test_generate_embedding_if_needed_no_provider_returns_original():
    """
        Verify that _generate_embedding_if_needed returns the original entry
        when no EmbeddingProvider is configured.
    """
    store = StubMemoryStore(store_name="test-store")
    entry = _create_entry(identifier="e1", content="hello world")

    result = store._generate_embedding_if_needed(entry=entry)
    assert result is entry, \
        "Should return the original entry when no provider is configured"
    assert result.embedding is None, \
        "Embedding should remain None"
    return


def test_generate_embedding_if_needed_entry_already_has_embedding():
    """
        Verify that _generate_embedding_if_needed returns the original entry
        when the entry already has an embedding, even if a provider is configured.
    """
    provider = StubEmbeddingProvider()
    store = StubMemoryStore(store_name="test-store", embedding_provider=provider)
    entry = _create_entry(identifier="e1", content="hello world", embedding=[1.0, 2.0, 3.0])

    result = store._generate_embedding_if_needed(entry=entry)
    assert result is entry, \
        "Should return the original entry when it already has an embedding"
    assert result.embedding == [1.0, 2.0, 3.0], \
        "Embedding should remain unchanged"
    return


def test_generate_embedding_if_needed_generates_embedding():
    """
        Verify that _generate_embedding_if_needed generates an embedding
        when the entry has no embedding and a provider is configured.
    """
    provider = StubEmbeddingProvider()
    store = StubMemoryStore(store_name="test-store", embedding_provider=provider)
    entry = _create_entry(identifier="e1", content="hello world")

    result = store._generate_embedding_if_needed(entry=entry)
    assert result is not entry, \
        "Should return a new entry with the generated embedding"
    assert result.embedding == [0.1, 0.2, 0.3], \
        "Embedding should be the value returned by the provider"
    assert result.identifier == entry.identifier, \
        "Identifier should be preserved"
    assert result.content == entry.content, \
        "Content should be preserved"
    assert result.scope == entry.scope, \
        "Scope should be preserved"
    assert result.created_at == entry.created_at, \
        "created_at should be preserved"
    return


# ---- _apply_expiration_policy Tests ----


def test_apply_expiration_policy_no_policy_returns_original():
    """
        Verify that _apply_expiration_policy returns the original entry
        when no ExpirationPolicy is configured.
    """
    store = StubMemoryStore(store_name="test-store")
    entry = _create_entry(identifier="e1")

    result = store._apply_expiration_policy(entry=entry)
    assert result is entry, \
        "Should return the original entry when no policy is configured"
    assert result.expires_at is None, \
        "expires_at should remain None"
    return


def test_apply_expiration_policy_no_ttl_returns_original():
    """
        Verify that _apply_expiration_policy returns the original entry
        when the ExpirationPolicy has no default_ttl.
    """
    policy = ExpirationPolicy(default_ttl=None)
    store = StubMemoryStore(store_name="test-store", expiration_policy=policy)
    entry = _create_entry(identifier="e1")

    result = store._apply_expiration_policy(entry=entry)
    assert result is entry, \
        "Should return the original entry when policy has no default_ttl"
    assert result.expires_at is None, \
        "expires_at should remain None"
    return


def test_apply_expiration_policy_entry_already_has_expiration():
    """
        Verify that _apply_expiration_policy returns the original entry
        when the entry already has an expiration timestamp.
    """
    policy = ExpirationPolicy(default_ttl=60.0)
    store = StubMemoryStore(store_name="test-store", expiration_policy=policy)
    existing_expiry = datetime(2026, 12, 31, tzinfo=timezone.utc)
    entry = _create_entry(identifier="e1", expires_at=existing_expiry)

    result = store._apply_expiration_policy(entry=entry)
    assert result is entry, \
        "Should return the original entry when it already has an expiration"
    assert result.expires_at == existing_expiry, \
        "expires_at should remain unchanged"
    return


def test_apply_expiration_policy_sets_expiration_from_ttl():
    """
        Verify that _apply_expiration_policy sets the expiration timestamp
        based on created_at + default_ttl when the entry has no expiration.
    """
    policy = ExpirationPolicy(default_ttl=120.0)
    store = StubMemoryStore(store_name="test-store", expiration_policy=policy)
    created = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    entry = _create_entry(identifier="e1", created_at=created)

    result = store._apply_expiration_policy(entry=entry)
    assert result is not entry, \
        "Should return a new entry with expiration set"

    expected_expiry = created + timedelta(seconds=120.0)
    assert result.expires_at == expected_expiry, \
        "expires_at should be created_at + default_ttl (120s), got {}".format(result.expires_at)
    assert result.identifier == entry.identifier, \
        "Identifier should be preserved"
    assert result.content == entry.content, \
        "Content should be preserved"
    assert result.scope == entry.scope, \
        "Scope should be preserved"
    assert result.created_at == entry.created_at, \
        "created_at should be preserved"
    return


# ---- cleanup_expired Tests ----


def test_cleanup_expired_removes_expired_entries():
    """
        Verify that cleanup_expired removes entries whose expiration has passed
        and returns the count of removed entries.
    """
    store = StubMemoryStore(store_name="test-store")

    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    expired_entry = _create_entry(
        identifier="expired-1",
        created_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=1),
    )
    valid_entry = _create_entry(
        identifier="valid-1",
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=1),
    )
    no_expiry_entry = _create_entry(
        identifier="no-expiry-1",
        created_at=now - timedelta(hours=1),
    )

    store.store(entry=expired_entry)
    store.store(entry=valid_entry)
    store.store(entry=no_expiry_entry)

    removed = store.cleanup_expired(reference_time=now)

    assert removed == 1, \
        "Should have removed 1 expired entry, got {}".format(removed)
    assert store.count == 2, \
        "Store should have 2 remaining entries, got {}".format(store.count)
    assert store.retrieve(identifier="expired-1") is None, \
        "Expired entry should have been removed"
    assert store.retrieve(identifier="valid-1") is not None, \
        "Valid entry should still exist"
    assert store.retrieve(identifier="no-expiry-1") is not None, \
        "Entry without expiration should still exist"
    return


def test_cleanup_expired_returns_zero_when_none_expired():
    """
        Verify that cleanup_expired returns 0 when no entries are expired.
    """
    store = StubMemoryStore(store_name="test-store")

    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    entry = _create_entry(
        identifier="valid-1",
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )
    store.store(entry=entry)

    removed = store.cleanup_expired(reference_time=now)

    assert removed == 0, \
        "Should have removed 0 entries, got {}".format(removed)
    assert store.count == 1, \
        "Store should still have 1 entry"
    return


def test_cleanup_expired_empty_store_returns_zero():
    """
        Verify that cleanup_expired returns 0 on an empty store.
    """
    store = StubMemoryStore(store_name="test-store")

    removed = store.cleanup_expired()

    assert removed == 0, \
        "Should have removed 0 entries from empty store, got {}".format(removed)
    return


def test_cleanup_expired_removes_multiple_expired():
    """
        Verify that cleanup_expired removes all expired entries.
    """
    store = StubMemoryStore(store_name="test-store")

    now = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(3):
        expired = _create_entry(
            identifier="expired-{}".format(i),
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(minutes=i + 1),
        )
        store.store(entry=expired)

    valid = _create_entry(
        identifier="valid-1",
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )
    store.store(entry=valid)

    removed = store.cleanup_expired(reference_time=now)

    assert removed == 3, \
        "Should have removed 3 expired entries, got {}".format(removed)
    assert store.count == 1, \
        "Store should have 1 remaining entry, got {}".format(store.count)
    return


# ---- __repr__ and __str__ Tests ----


def test_memorystore_repr():
    """
        Verify that __repr__ includes the class name, store name, and count.
    """
    store = StubMemoryStore(store_name="my-store")
    entry = _create_entry(identifier="e1")
    store.store(entry=entry)

    repr_str = repr(store)
    assert "StubMemoryStore" in repr_str, \
        "repr should include the class name"
    assert "my-store" in repr_str, \
        "repr should include the store name"
    assert "1" in repr_str, \
        "repr should include the entry count"
    return


def test_memorystore_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    store = StubMemoryStore(store_name="my-store")
    entry = _create_entry(identifier="e1")
    store.store(entry=entry)

    str_val = str(store)
    assert "my-store" in str_val, \
        "str should include the store name"
    assert "1" in str_val, \
        "str should include the entry count"
    return


def test_memorystore_repr_empty_store():
    """
        Verify that __repr__ works correctly for an empty store.
    """
    store = StubMemoryStore(store_name="empty-store")

    repr_str = repr(store)
    assert "empty-store" in repr_str, \
        "repr should include the store name"
    assert "0" in repr_str, \
        "repr should show count of 0 for empty store"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
