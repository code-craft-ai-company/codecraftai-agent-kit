"""
    .. module:: automojo.tests.singlehost.agentkit.test_memoryindex
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryIndex internal indexing component.
"""

import math
from datetime import datetime, timezone, timedelta

from automojo.agentkit.memoryentry import MemoryEntry
from automojo.agentkit.memoryindex import MemoryIndex
from automojo.agentkit.memoryquery import MemoryQuery
from automojo.agentkit.memoryscope import MemoryScope


# ---- Helper Factories ----


def _create_entry(identifier="entry-1", content="test content", scope=MemoryScope.AGENT,
                  tags=None, metadata=None, embedding=None, created_at=None):
    """
        Creates a MemoryEntry with sensible defaults for testing.
    """
    entry = MemoryEntry(
        content=content,
        scope=scope,
        identifier=identifier,
        tags=tags,
        metadata=metadata,
        embedding=embedding,
        created_at=created_at,
    )
    return entry


# ---- add / get / contains / count Tests ----


def test_memoryindex_add_and_get():
    """
        Verify that adding an entry makes it retrievable by identifier.
    """
    index = MemoryIndex()
    entry = _create_entry(identifier="e1")
    index.add(entry=entry)

    result = index.get(identifier="e1")
    assert result is not None, "get should return the added entry"
    assert result.identifier == "e1", "returned entry should have the correct identifier"
    return


def test_memoryindex_contains_returns_true_for_existing():
    """
        Verify that contains returns True for an added entry.
    """
    index = MemoryIndex()
    entry = _create_entry(identifier="e1")
    index.add(entry=entry)

    result = index.contains(identifier="e1")
    assert result is True, "contains should return True for an existing entry"
    return


def test_memoryindex_contains_returns_false_for_missing():
    """
        Verify that contains returns False for a non-existent identifier.
    """
    index = MemoryIndex()

    result = index.contains(identifier="nonexistent")
    assert result is False, "contains should return False for a missing identifier"
    return


def test_memoryindex_get_returns_none_for_missing():
    """
        Verify that get returns None for a non-existent identifier.
    """
    index = MemoryIndex()

    result = index.get(identifier="nonexistent")
    assert result is None, "get should return None for a missing identifier"
    return


def test_memoryindex_count_empty():
    """
        Verify that count is 0 for an empty index.
    """
    index = MemoryIndex()

    assert index.count == 0, "count should be 0 for an empty index"
    return


def test_memoryindex_count_after_adds():
    """
        Verify that count reflects the number of added entries.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1"))
    index.add(entry=_create_entry(identifier="e2"))
    index.add(entry=_create_entry(identifier="e3"))

    assert index.count == 3, "count should be 3 after adding 3 entries"
    return


# ---- remove Tests ----


def test_memoryindex_remove_existing():
    """
        Verify that remove deletes an entry from the index.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1"))
    index.remove(identifier="e1")

    assert index.contains(identifier="e1") is False, "entry should be removed"
    assert index.count == 0, "count should be 0 after removing the only entry"
    return


def test_memoryindex_remove_nonexistent_does_not_raise():
    """
        Verify that removing a non-existent identifier does not raise.
    """
    index = MemoryIndex()

    # Should not raise
    index.remove(identifier="nonexistent")
    assert index.count == 0, "count should remain 0"
    return


def test_memoryindex_remove_cleans_tag_index():
    """
        Verify that remove cleans up tag index references.
    """
    index = MemoryIndex()
    entry = _create_entry(identifier="e1", tags=["alpha", "beta"])
    index.add(entry=entry)
    index.remove(identifier="e1")

    # After removal, searching by those tags should return no results
    query = MemoryQuery(tags=["alpha"])
    result = index.search(query=query)
    assert result.total_count == 0, "tag index should be cleaned after removal"
    return


def test_memoryindex_remove_cleans_metadata_index():
    """
        Verify that remove cleans up metadata index references.
    """
    index = MemoryIndex()
    entry = _create_entry(identifier="e1", metadata={"source": "test"})
    index.add(entry=entry)
    index.remove(identifier="e1")

    query = MemoryQuery(metadata={"source": "test"})
    result = index.search(query=query)
    assert result.total_count == 0, "metadata index should be cleaned after removal"
    return


# ---- clear Tests ----


def test_memoryindex_clear():
    """
        Verify that clear removes all entries and resets indexes.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", tags=["a"]))
    index.add(entry=_create_entry(identifier="e2", tags=["b"]))
    index.clear()

    assert index.count == 0, "count should be 0 after clear"
    assert index.contains(identifier="e1") is False, "e1 should not exist after clear"
    assert index.contains(identifier="e2") is False, "e2 should not exist after clear"
    return


# ---- search with tag filters Tests ----


def test_memoryindex_search_by_single_tag():
    """
        Verify that search filters by a single tag.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", tags=["alpha", "beta"]))
    index.add(entry=_create_entry(identifier="e2", tags=["beta", "gamma"]))
    index.add(entry=_create_entry(identifier="e3", tags=["gamma"]))

    query = MemoryQuery(tags=["alpha"])
    result = index.search(query=query)

    assert result.total_count == 1, "only one entry has the 'alpha' tag"
    assert result.entries[0].identifier == "e1", "the matching entry should be e1"
    return


def test_memoryindex_search_by_multiple_tags_and_logic():
    """
        Verify that search with multiple tags uses AND logic.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", tags=["alpha", "beta"]))
    index.add(entry=_create_entry(identifier="e2", tags=["beta", "gamma"]))
    index.add(entry=_create_entry(identifier="e3", tags=["alpha", "gamma"]))

    query = MemoryQuery(tags=["alpha", "beta"])
    result = index.search(query=query)

    assert result.total_count == 1, "only e1 has both 'alpha' and 'beta' tags"
    assert result.entries[0].identifier == "e1", "the matching entry should be e1"
    return


def test_memoryindex_search_by_nonexistent_tag():
    """
        Verify that search with a non-existent tag returns no results.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", tags=["alpha"]))

    query = MemoryQuery(tags=["nonexistent"])
    result = index.search(query=query)

    assert result.total_count == 0, "no entries should match a non-existent tag"
    return


# ---- search with metadata filters Tests ----


def test_memoryindex_search_by_metadata():
    """
        Verify that search filters by metadata key-value pairs.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", metadata={"source": "web", "priority": "high"}))
    index.add(entry=_create_entry(identifier="e2", metadata={"source": "file", "priority": "high"}))
    index.add(entry=_create_entry(identifier="e3", metadata={"source": "web", "priority": "low"}))

    query = MemoryQuery(metadata={"source": "web", "priority": "high"})
    result = index.search(query=query)

    assert result.total_count == 1, "only e1 matches both metadata criteria"
    assert result.entries[0].identifier == "e1", "the matching entry should be e1"
    return


def test_memoryindex_search_by_metadata_and_logic():
    """
        Verify that metadata search uses AND logic across key-value pairs.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", metadata={"a": "1", "b": "2"}))
    index.add(entry=_create_entry(identifier="e2", metadata={"a": "1", "b": "3"}))

    query = MemoryQuery(metadata={"a": "1", "b": "2"})
    result = index.search(query=query)

    assert result.total_count == 1, "only e1 matches both metadata pairs"
    assert result.entries[0].identifier == "e1", "the matching entry should be e1"
    return


def test_memoryindex_search_by_nonexistent_metadata():
    """
        Verify that search with non-matching metadata returns no results.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", metadata={"source": "web"}))

    query = MemoryQuery(metadata={"source": "database"})
    result = index.search(query=query)

    assert result.total_count == 0, "no entries should match non-existent metadata value"
    return


# ---- search with scope filter Tests ----


def test_memoryindex_search_by_scope():
    """
        Verify that search filters by MemoryScope.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", scope=MemoryScope.AGENT))
    index.add(entry=_create_entry(identifier="e2", scope=MemoryScope.SHARED))
    index.add(entry=_create_entry(identifier="e3", scope=MemoryScope.GLOBAL))

    query = MemoryQuery(scope=MemoryScope.SHARED)
    result = index.search(query=query)

    assert result.total_count == 1, "only one entry has SHARED scope"
    assert result.entries[0].identifier == "e2", "the matching entry should be e2"
    return


def test_memoryindex_search_by_scope_returns_multiple():
    """
        Verify that scope filter returns all entries with matching scope.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", scope=MemoryScope.AGENT))
    index.add(entry=_create_entry(identifier="e2", scope=MemoryScope.AGENT))
    index.add(entry=_create_entry(identifier="e3", scope=MemoryScope.GLOBAL))

    query = MemoryQuery(scope=MemoryScope.AGENT)
    result = index.search(query=query)

    assert result.total_count == 2, "two entries have AGENT scope"
    return


# ---- search with time range filter Tests ----


def test_memoryindex_search_by_time_range():
    """
        Verify that search filters by time range.
    """
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", created_at=base_time - timedelta(hours=2)))
    index.add(entry=_create_entry(identifier="e2", created_at=base_time))
    index.add(entry=_create_entry(identifier="e3", created_at=base_time + timedelta(hours=2)))

    query = MemoryQuery(
        start_time=base_time - timedelta(hours=1),
        end_time=base_time + timedelta(hours=1),
    )
    result = index.search(query=query)

    assert result.total_count == 1, "only e2 falls within the time range"
    assert result.entries[0].identifier == "e2", "the matching entry should be e2"
    return


def test_memoryindex_search_by_start_time_only():
    """
        Verify that search with only start_time filters correctly.
    """
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", created_at=base_time - timedelta(hours=2)))
    index.add(entry=_create_entry(identifier="e2", created_at=base_time))
    index.add(entry=_create_entry(identifier="e3", created_at=base_time + timedelta(hours=2)))

    query = MemoryQuery(start_time=base_time)
    result = index.search(query=query)

    ids = [e.identifier for e in result.entries]
    assert result.total_count == 2, "e2 and e3 should match"
    assert "e2" in ids, "e2 should be in results"
    assert "e3" in ids, "e3 should be in results"
    return


def test_memoryindex_search_by_end_time_only():
    """
        Verify that search with only end_time filters correctly.
    """
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", created_at=base_time - timedelta(hours=2)))
    index.add(entry=_create_entry(identifier="e2", created_at=base_time))
    index.add(entry=_create_entry(identifier="e3", created_at=base_time + timedelta(hours=2)))

    query = MemoryQuery(end_time=base_time)
    result = index.search(query=query)

    ids = [e.identifier for e in result.entries]
    assert result.total_count == 2, "e1 and e2 should match"
    assert "e1" in ids, "e1 should be in results"
    assert "e2" in ids, "e2 should be in results"
    return


# ---- search with cosine similarity Tests ----


def test_memoryindex_search_with_cosine_similarity_ranking():
    """
        Verify that search ranks entries by cosine similarity when
        a query embedding is provided.
    """
    index = MemoryIndex()
    # Entry with embedding close to [1, 0, 0]
    index.add(entry=_create_entry(identifier="e1", embedding=[0.9, 0.1, 0.0]))
    # Entry with embedding close to [0, 1, 0]
    index.add(entry=_create_entry(identifier="e2", embedding=[0.1, 0.9, 0.0]))
    # Entry with embedding close to [1, 0, 0] but slightly less
    index.add(entry=_create_entry(identifier="e3", embedding=[0.8, 0.2, 0.0]))

    query = MemoryQuery()
    query_embedding = [1.0, 0.0, 0.0]
    result = index.search(query=query, query_embedding=query_embedding)

    assert result.total_count == 3, "all entries have embeddings and should match"
    assert result.scores is not None, "scores should be provided for semantic search"
    assert result.entries[0].identifier == "e1", "e1 should be ranked first (closest to query)"
    assert result.entries[1].identifier == "e3", "e3 should be ranked second"
    assert result.entries[2].identifier == "e2", "e2 should be ranked last"
    # Scores should be in descending order
    assert result.scores[0] >= result.scores[1], "scores should be in descending order"
    assert result.scores[1] >= result.scores[2], "scores should be in descending order"
    return


def test_memoryindex_search_with_min_relevance_threshold():
    """
        Verify that search excludes entries below the min_relevance threshold.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", embedding=[1.0, 0.0, 0.0]))
    index.add(entry=_create_entry(identifier="e2", embedding=[0.0, 1.0, 0.0]))

    query = MemoryQuery(min_relevance=0.5)
    query_embedding = [1.0, 0.0, 0.0]
    result = index.search(query=query, query_embedding=query_embedding)

    assert result.total_count == 1, "only e1 should exceed the min_relevance threshold"
    assert result.entries[0].identifier == "e1", "e1 should be the only result"
    return


def test_memoryindex_search_skips_entries_without_embedding():
    """
        Verify that semantic search skips entries that have no embedding.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", embedding=[1.0, 0.0]))
    index.add(entry=_create_entry(identifier="e2", embedding=None))

    query = MemoryQuery()
    query_embedding = [1.0, 0.0]
    result = index.search(query=query, query_embedding=query_embedding)

    assert result.total_count == 1, "only e1 has an embedding"
    assert result.entries[0].identifier == "e1", "e1 should be the only result"
    return


# ---- search with max_results Tests ----


def test_memoryindex_search_with_max_results():
    """
        Verify that search limits results to max_results.
    """
    index = MemoryIndex()
    for i in range(10):
        index.add(entry=_create_entry(identifier="e{}".format(i)))

    query = MemoryQuery(max_results=3)
    result = index.search(query=query)

    assert result.total_count == 3, "results should be limited to 3"
    assert len(result.entries) == 3, "entries list should have 3 items"
    return


def test_memoryindex_search_with_max_results_and_similarity():
    """
        Verify that max_results limits results after similarity ranking.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", embedding=[1.0, 0.0]))
    index.add(entry=_create_entry(identifier="e2", embedding=[0.9, 0.1]))
    index.add(entry=_create_entry(identifier="e3", embedding=[0.5, 0.5]))

    query = MemoryQuery(max_results=2)
    query_embedding = [1.0, 0.0]
    result = index.search(query=query, query_embedding=query_embedding)

    assert result.total_count == 2, "results should be limited to 2"
    assert len(result.scores) == 2, "scores should also be limited to 2"
    return


# ---- search with no filters Tests ----


def test_memoryindex_search_no_filters_returns_all():
    """
        Verify that search with no filters returns all entries.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1"))
    index.add(entry=_create_entry(identifier="e2"))
    index.add(entry=_create_entry(identifier="e3"))

    query = MemoryQuery()
    result = index.search(query=query)

    assert result.total_count == 3, "all entries should be returned when no filters are set"
    assert result.scores is None, "scores should be None when no embedding search is performed"
    return


# ---- search with combined filters Tests ----


def test_memoryindex_search_combined_tag_and_scope():
    """
        Verify that search combines tag and scope filters.
    """
    index = MemoryIndex()
    index.add(entry=_create_entry(identifier="e1", tags=["alpha"], scope=MemoryScope.AGENT))
    index.add(entry=_create_entry(identifier="e2", tags=["alpha"], scope=MemoryScope.SHARED))
    index.add(entry=_create_entry(identifier="e3", tags=["beta"], scope=MemoryScope.AGENT))

    query = MemoryQuery(tags=["alpha"], scope=MemoryScope.AGENT)
    result = index.search(query=query)

    assert result.total_count == 1, "only e1 matches both tag and scope"
    assert result.entries[0].identifier == "e1", "the matching entry should be e1"
    return


# ---- _cosine_similarity Tests ----


def test_cosine_similarity_identical_vectors():
    """
        Verify that cosine similarity of identical vectors is 1.0.
    """
    vec = [1.0, 2.0, 3.0]
    similarity = MemoryIndex._cosine_similarity(vec, vec)

    assert abs(similarity - 1.0) < 1e-9, "cosine similarity of identical vectors should be 1.0"
    return


def test_cosine_similarity_orthogonal_vectors():
    """
        Verify that cosine similarity of orthogonal vectors is 0.0.
    """
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [0.0, 1.0, 0.0]
    similarity = MemoryIndex._cosine_similarity(vec_a, vec_b)

    assert abs(similarity - 0.0) < 1e-9, "cosine similarity of orthogonal vectors should be 0.0"
    return


def test_cosine_similarity_opposite_vectors():
    """
        Verify that cosine similarity of opposite vectors is -1.0.
    """
    vec_a = [1.0, 0.0]
    vec_b = [-1.0, 0.0]
    similarity = MemoryIndex._cosine_similarity(vec_a, vec_b)

    assert abs(similarity - (-1.0)) < 1e-9, "cosine similarity of opposite vectors should be -1.0"
    return


def test_cosine_similarity_zero_vector():
    """
        Verify that cosine similarity with a zero vector returns 0.0.
    """
    vec_a = [0.0, 0.0, 0.0]
    vec_b = [1.0, 2.0, 3.0]
    similarity = MemoryIndex._cosine_similarity(vec_a, vec_b)

    assert abs(similarity - 0.0) < 1e-9, "cosine similarity with a zero vector should be 0.0"
    return


def test_cosine_similarity_known_values():
    """
        Verify cosine similarity with known computed values.
    """
    vec_a = [1.0, 2.0, 3.0]
    vec_b = [4.0, 5.0, 6.0]
    # dot = 1*4 + 2*5 + 3*6 = 32
    # mag_a = sqrt(1+4+9) = sqrt(14)
    # mag_b = sqrt(16+25+36) = sqrt(77)
    expected = 32.0 / (math.sqrt(14.0) * math.sqrt(77.0))
    similarity = MemoryIndex._cosine_similarity(vec_a, vec_b)

    assert abs(similarity - expected) < 1e-9, "cosine similarity should match expected value"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
