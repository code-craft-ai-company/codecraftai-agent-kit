"""
    .. module:: automojo.tests.singlehost.agentkit.test_memoryentry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryEntry value object.
"""

import json
from datetime import datetime, timezone, timedelta

from automojo.agentkit.memoryentry import MemoryEntry
from automojo.agentkit.memoryscope import MemoryScope


# ---- Auto-generated UUID Tests ----


def test_memoryentry_auto_generates_uuid_when_identifier_not_provided():
    """
        Verify that a UUID-based identifier is generated when none is provided.
    """
    entry = MemoryEntry(content="test content", scope=MemoryScope.AGENT)
    identifier = entry.identifier
    has_identifier = identifier is not None and len(identifier) > 0
    assert has_identifier is True, "MemoryEntry should auto-generate a UUID identifier"
    return


def test_memoryentry_auto_generated_uuids_are_unique():
    """
        Verify that two entries without explicit identifiers get different UUIDs.
    """
    entry_a = MemoryEntry(content="content a", scope=MemoryScope.AGENT)
    entry_b = MemoryEntry(content="content b", scope=MemoryScope.AGENT)
    are_different = entry_a.identifier != entry_b.identifier
    assert are_different is True, "Auto-generated identifiers should be unique"
    return


def test_memoryentry_uses_provided_identifier():
    """
        Verify that the provided identifier is used when given.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="my-id-123")
    identifier = entry.identifier
    assert identifier == "my-id-123", "MemoryEntry should use the provided identifier"
    return


# ---- Auto-generated created_at Tests ----


def test_memoryentry_auto_generates_created_at_when_not_provided():
    """
        Verify that created_at defaults to approximately current UTC time.
    """
    before = datetime.now(timezone.utc)
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    after = datetime.now(timezone.utc)
    created_at = entry.created_at
    is_in_range = before <= created_at <= after
    assert is_in_range is True, "Auto-generated created_at should be approximately current UTC time"
    return


def test_memoryentry_uses_provided_created_at():
    """
        Verify that the provided created_at timestamp is used.
    """
    ts = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, created_at=ts)
    created_at = entry.created_at
    assert created_at == ts, "MemoryEntry should use the provided created_at"
    return


# ---- Defensive Copy Tests ----


def test_memoryentry_embedding_returns_defensive_copy():
    """
        Verify that modifying the returned embedding does not affect the entry.
    """
    original_embedding = [1.0, 2.0, 3.0]
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, embedding=original_embedding)
    returned = entry.embedding
    returned.append(4.0)
    internal = entry.embedding
    assert len(internal) == 3, "Modifying returned embedding should not affect the entry"
    return


def test_memoryentry_metadata_returns_defensive_copy():
    """
        Verify that modifying the returned metadata does not affect the entry.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, metadata={"key": "value"})
    returned = entry.metadata
    returned["new_key"] = "new_value"
    internal = entry.metadata
    has_new_key = "new_key" in internal
    assert has_new_key is False, "Modifying returned metadata should not affect the entry"
    return


def test_memoryentry_tags_returns_defensive_copy():
    """
        Verify that modifying the returned tags does not affect the entry.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, tags=["tag1", "tag2"])
    returned = entry.tags
    returned.append("tag3")
    internal = entry.tags
    assert len(internal) == 2, "Modifying returned tags should not affect the entry"
    return


def test_memoryentry_embedding_none_when_not_provided():
    """
        Verify that embedding is None when not provided.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    embedding = entry.embedding
    assert embedding is None, "Embedding should be None when not provided"
    return


def test_memoryentry_metadata_defaults_to_empty_dict():
    """
        Verify that metadata defaults to an empty dictionary.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    metadata = entry.metadata
    assert metadata == {}, "Metadata should default to empty dict"
    return


def test_memoryentry_tags_defaults_to_empty_list():
    """
        Verify that tags defaults to an empty list.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    tags = entry.tags
    assert tags == [], "Tags should default to empty list"
    return


# ---- is_expired Tests ----


def test_memoryentry_is_expired_returns_true_when_expired():
    """
        Verify that is_expired returns True when the reference time exceeds expires_at.
    """
    expires_at = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, expires_at=expires_at)
    reference = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = entry.is_expired(reference_time=reference)
    assert result is True, "Entry should be expired when reference time exceeds expires_at"
    return


def test_memoryentry_is_expired_returns_false_when_not_expired():
    """
        Verify that is_expired returns False when the reference time is before expires_at.
    """
    expires_at = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, expires_at=expires_at)
    reference = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = entry.is_expired(reference_time=reference)
    assert result is False, "Entry should not be expired when reference time is before expires_at"
    return


def test_memoryentry_is_expired_returns_false_when_no_expiration():
    """
        Verify that is_expired returns False when expires_at is None.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    result = entry.is_expired()
    assert result is False, "Entry without expires_at should not be expired"
    return


def test_memoryentry_is_expired_defaults_to_current_utc_time():
    """
        Verify that is_expired uses current UTC time when no reference_time is given.
    """
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, expires_at=past)
    result = entry.is_expired()
    assert result is True, "Entry with past expires_at should be expired using default reference time"
    return


# ---- Serialization Tests ----


def test_memoryentry_as_dict_contains_all_fields():
    """
        Verify that as_dict returns a dictionary with all expected fields.
    """
    entry = MemoryEntry(
        content="hello world",
        scope=MemoryScope.SHARED,
        identifier="entry-1",
        embedding=[0.1, 0.2],
        metadata={"key": "val"},
        tags=["t1"],
    )
    d = entry.as_dict()
    assert d["identifier"] == "entry-1", "as_dict should contain identifier"
    assert d["content"] == "hello world", "as_dict should contain content"
    assert d["scope"] == "SHARED", "as_dict should contain scope value string"
    assert d["embedding"] == [0.1, 0.2], "as_dict should contain embedding"
    assert d["metadata"] == {"key": "val"}, "as_dict should contain metadata"
    assert d["tags"] == ["t1"], "as_dict should contain tags"
    has_created_at = "created_at" in d
    assert has_created_at is True, "as_dict should contain created_at"
    return


def test_memoryentry_as_dict_brief_excludes_embedding():
    """
        Verify that as_dict(brief=True) excludes the embedding field.
    """
    entry = MemoryEntry(
        content="test",
        scope=MemoryScope.AGENT,
        embedding=[1.0, 2.0, 3.0],
    )
    d = entry.as_dict(brief=True)
    has_embedding = "embedding" in d
    assert has_embedding is False, "as_dict(brief=True) should exclude embedding"
    return


def test_memoryentry_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="json-test")
    json_str = entry.to_json()
    data = json.loads(json_str)
    assert data["identifier"] == "json-test", "to_json should produce valid JSON with correct identifier"
    return


def test_memoryentry_from_dict_reconstructs_entry():
    """
        Verify that from_dict constructs an equivalent MemoryEntry.
    """
    original = MemoryEntry(
        content="from dict test",
        scope=MemoryScope.GLOBAL,
        identifier="fd-1",
        metadata={"a": "b"},
        tags=["x"],
    )
    d = original.as_dict()
    restored = MemoryEntry.from_dict(d)
    assert original == restored, "from_dict should reconstruct an equivalent MemoryEntry"
    return


def test_memoryentry_from_json_reconstructs_entry():
    """
        Verify that from_json constructs an equivalent MemoryEntry.
    """
    original = MemoryEntry(
        content="from json test",
        scope=MemoryScope.SHARED,
        identifier="fj-1",
        embedding=[0.5, 0.6],
        tags=["y", "z"],
    )
    json_str = original.to_json()
    restored = MemoryEntry.from_json(json_str)
    assert original == restored, "from_json should reconstruct an equivalent MemoryEntry"
    return


def test_memoryentry_from_dict_with_expires_at():
    """
        Verify that from_dict correctly parses the expires_at field.
    """
    expires_at = datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    original = MemoryEntry(
        content="expiring",
        scope=MemoryScope.AGENT,
        identifier="exp-1",
        expires_at=expires_at,
    )
    d = original.as_dict()
    restored = MemoryEntry.from_dict(d)
    assert restored.expires_at == expires_at, "from_dict should parse expires_at correctly"
    return


def test_memoryentry_from_dict_with_none_expires_at():
    """
        Verify that from_dict handles None expires_at.
    """
    d = {
        "content": "no expiry",
        "scope": "AGENT",
        "identifier": "ne-1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "metadata": {},
        "tags": [],
        "embedding": None,
    }
    entry = MemoryEntry.from_dict(d)
    assert entry.expires_at is None, "from_dict should handle None expires_at"
    return


# ---- __repr__, __str__, __eq__ Tests ----


def test_memoryentry_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="repr-1")
    repr_str = repr(entry)
    has_class_name = "MemoryEntry" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_memoryentry_repr_contains_identifier():
    """
        Verify that __repr__ contains the identifier.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="repr-id")
    repr_str = repr(entry)
    has_id = "repr-id" in repr_str
    assert has_id is True, "repr should contain the identifier"
    return


def test_memoryentry_repr_contains_scope():
    """
        Verify that __repr__ contains the scope value.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.SHARED, identifier="repr-scope")
    repr_str = repr(entry)
    has_scope = "SHARED" in repr_str
    assert has_scope is True, "repr should contain the scope value"
    return


def test_memoryentry_repr_truncates_long_content():
    """
        Verify that __repr__ truncates content longer than 50 characters.
    """
    long_content = "a" * 100
    entry = MemoryEntry(content=long_content, scope=MemoryScope.AGENT, identifier="trunc")
    repr_str = repr(entry)
    has_ellipsis = "..." in repr_str
    assert has_ellipsis is True, "repr should truncate long content with ellipsis"
    return


def test_memoryentry_str_contains_identifier():
    """
        Verify that __str__ contains the identifier.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="str-id")
    str_val = str(entry)
    has_id = "str-id" in str_val
    assert has_id is True, "__str__ should contain the identifier"
    return


def test_memoryentry_str_contains_scope():
    """
        Verify that __str__ contains the scope value.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.GLOBAL, identifier="str-scope")
    str_val = str(entry)
    has_scope = "GLOBAL" in str_val
    assert has_scope is True, "__str__ should contain the scope value"
    return


def test_memoryentry_str_contains_tag_count():
    """
        Verify that __str__ contains the tag count.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, tags=["a", "b", "c"])
    str_val = str(entry)
    has_count = "3" in str_val
    assert has_count is True, "__str__ should contain the tag count"
    return


def test_memoryentry_eq_returns_true_for_equivalent_entries():
    """
        Verify that __eq__ returns True for entries with identical fields.
    """
    ts = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    entry_a = MemoryEntry(
        content="same", scope=MemoryScope.AGENT, identifier="eq-1",
        metadata={"k": "v"}, tags=["t"], created_at=ts,
    )
    entry_b = MemoryEntry(
        content="same", scope=MemoryScope.AGENT, identifier="eq-1",
        metadata={"k": "v"}, tags=["t"], created_at=ts,
    )
    assert entry_a == entry_b, "Equivalent entries should be equal"
    return


def test_memoryentry_eq_returns_false_for_different_content():
    """
        Verify that __eq__ returns False when content differs.
    """
    ts = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    entry_a = MemoryEntry(content="alpha", scope=MemoryScope.AGENT, identifier="eq-2", created_at=ts)
    entry_b = MemoryEntry(content="beta", scope=MemoryScope.AGENT, identifier="eq-2", created_at=ts)
    result = entry_a == entry_b
    assert result is False, "Entries with different content should not be equal"
    return


def test_memoryentry_eq_returns_false_for_non_memoryentry():
    """
        Verify that __eq__ returns False when compared to a non-MemoryEntry.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    result = entry == "not a memory entry"
    assert result is False, "__eq__ should return False for non-MemoryEntry objects"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
