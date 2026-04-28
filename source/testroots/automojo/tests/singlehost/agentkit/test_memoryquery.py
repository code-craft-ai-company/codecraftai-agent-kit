"""
    .. module:: automojo.tests.singlehost.agentkit.test_memoryquery
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryQuery value object.
"""

import json
from datetime import datetime, timezone, timedelta

from automojo.agentkit.memoryquery import MemoryQuery
from automojo.agentkit.memoryscope import MemoryScope


# ---- Construction Tests ----


def test_memoryquery_construction_with_no_filters():
    """
        Verify that a MemoryQuery can be constructed with no filter criteria.
    """
    query = MemoryQuery()
    assert query.tags is None, "tags should be None when not provided"
    assert query.metadata is None, "metadata should be None when not provided"
    assert query.scope is None, "scope should be None when not provided"
    assert query.start_time is None, "start_time should be None when not provided"
    assert query.end_time is None, "end_time should be None when not provided"
    assert query.semantic_text is None, "semantic_text should be None when not provided"
    assert query.max_results is None, "max_results should be None when not provided"
    assert query.min_relevance is None, "min_relevance should be None when not provided"
    return


def test_memoryquery_construction_with_tags():
    """
        Verify that a MemoryQuery stores the provided tags.
    """
    query = MemoryQuery(tags=["important", "recent"])
    tags = query.tags
    assert tags == ["important", "recent"], "tags should match the provided list"
    return


def test_memoryquery_construction_with_metadata():
    """
        Verify that a MemoryQuery stores the provided metadata.
    """
    query = MemoryQuery(metadata={"source": "user", "priority": "high"})
    metadata = query.metadata
    assert metadata == {"source": "user", "priority": "high"}, "metadata should match"
    return


def test_memoryquery_construction_with_scope():
    """
        Verify that a MemoryQuery stores the provided scope.
    """
    query = MemoryQuery(scope=MemoryScope.SHARED)
    assert query.scope is MemoryScope.SHARED, "scope should be SHARED"
    return


def test_memoryquery_construction_with_time_range():
    """
        Verify that a MemoryQuery stores the provided time range.
    """
    start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    query = MemoryQuery(start_time=start, end_time=end)
    assert query.start_time == start, "start_time should match"
    assert query.end_time == end, "end_time should match"
    return


def test_memoryquery_construction_with_semantic_text():
    """
        Verify that a MemoryQuery stores the provided semantic text.
    """
    query = MemoryQuery(semantic_text="find related documents")
    assert query.semantic_text == "find related documents", "semantic_text should match"
    return


def test_memoryquery_construction_with_max_results():
    """
        Verify that a MemoryQuery stores the provided max_results.
    """
    query = MemoryQuery(max_results=10)
    assert query.max_results == 10, "max_results should be 10"
    return


def test_memoryquery_construction_with_min_relevance():
    """
        Verify that a MemoryQuery stores the provided min_relevance.
    """
    query = MemoryQuery(min_relevance=0.75)
    assert query.min_relevance == 0.75, "min_relevance should be 0.75"
    return


def test_memoryquery_construction_with_all_filters():
    """
        Verify that a MemoryQuery stores all filter criteria together.
    """
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 12, 31, tzinfo=timezone.utc)
    query = MemoryQuery(
        tags=["t1", "t2"],
        metadata={"k": "v"},
        scope=MemoryScope.GLOBAL,
        start_time=start,
        end_time=end,
        semantic_text="search text",
        max_results=5,
        min_relevance=0.5,
    )
    assert query.tags == ["t1", "t2"], "tags should match"
    assert query.metadata == {"k": "v"}, "metadata should match"
    assert query.scope is MemoryScope.GLOBAL, "scope should be GLOBAL"
    assert query.start_time == start, "start_time should match"
    assert query.end_time == end, "end_time should match"
    assert query.semantic_text == "search text", "semantic_text should match"
    assert query.max_results == 5, "max_results should be 5"
    assert query.min_relevance == 0.5, "min_relevance should be 0.5"
    return


# ---- Defensive Copy Tests ----


def test_memoryquery_tags_returns_defensive_copy():
    """
        Verify that modifying the returned tags does not affect the query.
    """
    query = MemoryQuery(tags=["a", "b"])
    returned = query.tags
    returned.append("c")
    internal = query.tags
    assert len(internal) == 2, "Modifying returned tags should not affect the query"
    return


def test_memoryquery_metadata_returns_defensive_copy():
    """
        Verify that modifying the returned metadata does not affect the query.
    """
    query = MemoryQuery(metadata={"key": "value"})
    returned = query.metadata
    returned["new_key"] = "new_value"
    internal = query.metadata
    has_new_key = "new_key" in internal
    assert has_new_key is False, "Modifying returned metadata should not affect the query"
    return


# ---- Serialization Tests ----


def test_memoryquery_as_dict_with_all_fields():
    """
        Verify that as_dict returns a dictionary with all expected fields.
    """
    start = datetime(2025, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    query = MemoryQuery(
        tags=["tag1"],
        metadata={"source": "test"},
        scope=MemoryScope.AGENT,
        start_time=start,
        end_time=end,
        semantic_text="hello",
        max_results=10,
        min_relevance=0.8,
    )
    d = query.as_dict()
    assert d["tags"] == ["tag1"], "as_dict should contain tags"
    assert d["metadata"] == {"source": "test"}, "as_dict should contain metadata"
    assert d["scope"] == "AGENT", "as_dict should contain scope value string"
    assert d["start_time"] == start.isoformat(), "as_dict should contain start_time"
    assert d["end_time"] == end.isoformat(), "as_dict should contain end_time"
    assert d["semantic_text"] == "hello", "as_dict should contain semantic_text"
    assert d["max_results"] == 10, "as_dict should contain max_results"
    assert d["min_relevance"] == 0.8, "as_dict should contain min_relevance"
    return


def test_memoryquery_as_dict_with_no_filters():
    """
        Verify that as_dict returns None for unset fields.
    """
    query = MemoryQuery()
    d = query.as_dict()
    assert d["tags"] is None, "tags should be None"
    assert d["metadata"] is None, "metadata should be None"
    assert d["scope"] is None, "scope should be None"
    assert d["start_time"] is None, "start_time should be None"
    assert d["end_time"] is None, "end_time should be None"
    assert d["semantic_text"] is None, "semantic_text should be None"
    assert d["max_results"] is None, "max_results should be None"
    assert d["min_relevance"] is None, "min_relevance should be None"
    return


def test_memoryquery_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    query = MemoryQuery(tags=["x"], max_results=5)
    json_str = query.to_json()
    data = json.loads(json_str)
    assert data["tags"] == ["x"], "to_json should produce valid JSON with correct tags"
    assert data["max_results"] == 5, "to_json should produce valid JSON with correct max_results"
    return


def test_memoryquery_from_dict_reconstructs_query():
    """
        Verify that from_dict constructs an equivalent MemoryQuery.
    """
    start = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
    original = MemoryQuery(
        tags=["a", "b"],
        metadata={"k": "v"},
        scope=MemoryScope.SHARED,
        start_time=start,
        semantic_text="test query",
        max_results=20,
        min_relevance=0.6,
    )
    d = original.as_dict()
    restored = MemoryQuery.from_dict(d)
    assert original == restored, "from_dict should reconstruct an equivalent MemoryQuery"
    return


def test_memoryquery_from_json_reconstructs_query():
    """
        Verify that from_json constructs an equivalent MemoryQuery.
    """
    original = MemoryQuery(
        tags=["tag1"],
        scope=MemoryScope.GLOBAL,
        max_results=3,
    )
    json_str = original.to_json()
    restored = MemoryQuery.from_json(json_str)
    assert original == restored, "from_json should reconstruct an equivalent MemoryQuery"
    return


def test_memoryquery_from_dict_with_none_values():
    """
        Verify that from_dict handles None values for all optional fields.
    """
    d = {
        "tags": None,
        "metadata": None,
        "scope": None,
        "start_time": None,
        "end_time": None,
        "semantic_text": None,
        "max_results": None,
        "min_relevance": None,
    }
    query = MemoryQuery.from_dict(d)
    assert query.tags is None, "tags should be None"
    assert query.metadata is None, "metadata should be None"
    assert query.scope is None, "scope should be None"
    assert query.start_time is None, "start_time should be None"
    assert query.end_time is None, "end_time should be None"
    return


# ---- __repr__ Tests ----


def test_memoryquery_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    query = MemoryQuery()
    repr_str = repr(query)
    has_class_name = "MemoryQuery" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_memoryquery_repr_shows_no_filters_when_empty():
    """
        Verify that __repr__ shows 'no filters' when no criteria are set.
    """
    query = MemoryQuery()
    repr_str = repr(query)
    has_no_filters = "no filters" in repr_str
    assert has_no_filters is True, "repr should show 'no filters' when empty"
    return


def test_memoryquery_repr_shows_tag_count():
    """
        Verify that __repr__ shows the tag count when tags are set.
    """
    query = MemoryQuery(tags=["a", "b", "c"])
    repr_str = repr(query)
    has_tags = "tags=3" in repr_str
    assert has_tags is True, "repr should show tag count"
    return


def test_memoryquery_repr_shows_scope():
    """
        Verify that __repr__ shows the scope when set.
    """
    query = MemoryQuery(scope=MemoryScope.AGENT)
    repr_str = repr(query)
    has_scope = "scope=AGENT" in repr_str
    assert has_scope is True, "repr should show scope"
    return


def test_memoryquery_repr_shows_semantic():
    """
        Verify that __repr__ shows semantic=True when semantic_text is set.
    """
    query = MemoryQuery(semantic_text="find something")
    repr_str = repr(query)
    has_semantic = "semantic=True" in repr_str
    assert has_semantic is True, "repr should show semantic=True"
    return


def test_memoryquery_repr_shows_max_results():
    """
        Verify that __repr__ shows max results when set.
    """
    query = MemoryQuery(max_results=25)
    repr_str = repr(query)
    has_max = "max=25" in repr_str
    assert has_max is True, "repr should show max results"
    return


# ---- __str__ Tests ----


def test_memoryquery_str_shows_no_filters_when_empty():
    """
        Verify that __str__ shows 'no filters' when no criteria are set.
    """
    query = MemoryQuery()
    str_val = str(query)
    has_no_filters = "no filters" in str_val
    assert has_no_filters is True, "__str__ should show 'no filters' when empty"
    return


def test_memoryquery_str_shows_tags():
    """
        Verify that __str__ shows tags when set.
    """
    query = MemoryQuery(tags=["important"])
    str_val = str(query)
    has_tags = "tags:" in str_val
    assert has_tags is True, "__str__ should show tags"
    return


def test_memoryquery_str_shows_scope():
    """
        Verify that __str__ shows scope when set.
    """
    query = MemoryQuery(scope=MemoryScope.GLOBAL)
    str_val = str(query)
    has_scope = "GLOBAL" in str_val
    assert has_scope is True, "__str__ should show scope"
    return


def test_memoryquery_str_shows_time_range():
    """
        Verify that __str__ shows time range when set.
    """
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    query = MemoryQuery(start_time=start)
    str_val = str(query)
    has_time = "time range:" in str_val
    assert has_time is True, "__str__ should show time range"
    return


def test_memoryquery_str_shows_semantic_text():
    """
        Verify that __str__ shows semantic text when set.
    """
    query = MemoryQuery(semantic_text="find related")
    str_val = str(query)
    has_semantic = "semantic:" in str_val
    assert has_semantic is True, "__str__ should show semantic text"
    return


def test_memoryquery_str_truncates_long_semantic_text():
    """
        Verify that __str__ truncates semantic text longer than 50 characters.
    """
    long_text = "a" * 100
    query = MemoryQuery(semantic_text=long_text)
    str_val = str(query)
    has_ellipsis = "..." in str_val
    assert has_ellipsis is True, "__str__ should truncate long semantic text"
    return


# ---- __eq__ Tests ----


def test_memoryquery_eq_returns_true_for_equivalent_queries():
    """
        Verify that __eq__ returns True for queries with identical fields.
    """
    query_a = MemoryQuery(tags=["t1"], scope=MemoryScope.AGENT, max_results=10)
    query_b = MemoryQuery(tags=["t1"], scope=MemoryScope.AGENT, max_results=10)
    assert query_a == query_b, "Equivalent queries should be equal"
    return


def test_memoryquery_eq_returns_false_for_different_tags():
    """
        Verify that __eq__ returns False when tags differ.
    """
    query_a = MemoryQuery(tags=["a"])
    query_b = MemoryQuery(tags=["b"])
    result = query_a == query_b
    assert result is False, "Queries with different tags should not be equal"
    return


def test_memoryquery_eq_returns_false_for_non_memoryquery():
    """
        Verify that __eq__ returns False when compared to a non-MemoryQuery.
    """
    query = MemoryQuery(tags=["t1"])
    result = query == "not a query"
    assert result is False, "__eq__ should return False for non-MemoryQuery objects"
    return


def test_memoryquery_eq_returns_false_for_different_scope():
    """
        Verify that __eq__ returns False when scope differs.
    """
    query_a = MemoryQuery(scope=MemoryScope.AGENT)
    query_b = MemoryQuery(scope=MemoryScope.GLOBAL)
    result = query_a == query_b
    assert result is False, "Queries with different scope should not be equal"
    return


def test_memoryquery_eq_none_vs_set_tags():
    """
        Verify that __eq__ returns False when one has tags and the other does not.
    """
    query_a = MemoryQuery(tags=None)
    query_b = MemoryQuery(tags=["t1"])
    result = query_a == query_b
    assert result is False, "Query with None tags should not equal query with tags"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
