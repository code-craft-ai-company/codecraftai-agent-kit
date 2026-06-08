"""
    .. module:: ccai.tests.singlehost.agentkit.test_memoryqueryresult
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryQueryResult value object.
"""

from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryscope import MemoryScope
from ccai.agentkit.memoryqueryresult import MemoryQueryResult


# ---- Construction Tests ----


def test_memoryqueryresult_construction_with_entries():
    """
        Verify that a MemoryQueryResult stores the provided entries.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="e1")
    result = MemoryQueryResult(entries=[entry])
    entries = result.entries
    assert len(entries) == 1, "entries should contain one entry"
    assert entries[0].identifier == "e1", "entry identifier should match"
    return


def test_memoryqueryresult_construction_with_scores():
    """
        Verify that a MemoryQueryResult stores the provided scores.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="e1")
    result = MemoryQueryResult(entries=[entry], scores=[0.95])
    scores = result.scores
    assert scores == [0.95], "scores should match the provided list"
    return


def test_memoryqueryresult_construction_without_scores():
    """
        Verify that scores is None when not provided.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    result = MemoryQueryResult(entries=[entry])
    assert result.scores is None, "scores should be None when not provided"
    return


def test_memoryqueryresult_default_total_count_equals_len_entries():
    """
        Verify that total_count defaults to len(entries) when not provided.
    """
    entries = [
        MemoryEntry(content="a", scope=MemoryScope.AGENT, identifier="e1"),
        MemoryEntry(content="b", scope=MemoryScope.AGENT, identifier="e2"),
        MemoryEntry(content="c", scope=MemoryScope.AGENT, identifier="e3"),
    ]
    result = MemoryQueryResult(entries=entries)
    assert result.total_count == 3, "total_count should default to len(entries)"
    return


def test_memoryqueryresult_explicit_total_count():
    """
        Verify that an explicit total_count overrides the default.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    result = MemoryQueryResult(entries=[entry], total_count=100)
    assert result.total_count == 100, "total_count should use the provided value"
    return


def test_memoryqueryresult_empty_entries():
    """
        Verify that an empty entries list is handled correctly.
    """
    result = MemoryQueryResult(entries=[])
    assert result.total_count == 0, "total_count should be 0 for empty entries"
    entries = result.entries
    assert entries == [], "entries should be an empty list"
    return


# ---- Defensive Copy Tests ----


def test_memoryqueryresult_entries_returns_defensive_copy():
    """
        Verify that modifying the returned entries does not affect the result.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT, identifier="e1")
    result = MemoryQueryResult(entries=[entry])
    returned = result.entries
    returned.append(MemoryEntry(content="extra", scope=MemoryScope.AGENT))
    internal = result.entries
    assert len(internal) == 1, "Modifying returned entries should not affect the result"
    return


def test_memoryqueryresult_scores_returns_defensive_copy():
    """
        Verify that modifying the returned scores does not affect the result.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    result = MemoryQueryResult(entries=[entry], scores=[0.9])
    returned = result.scores
    returned.append(0.5)
    internal = result.scores
    assert len(internal) == 1, "Modifying returned scores should not affect the result"
    return


# ---- as_dict Tests ----


def test_memoryqueryresult_as_dict_contains_entries():
    """
        Verify that as_dict serializes entries via their as_dict method.
    """
    entry = MemoryEntry(
        content="hello",
        scope=MemoryScope.SHARED,
        identifier="d1",
    )
    result = MemoryQueryResult(entries=[entry], scores=[0.85])
    d = result.as_dict()
    assert len(d["entries"]) == 1, "as_dict should contain one entry"
    assert d["entries"][0]["identifier"] == "d1", "entry identifier should match"
    assert d["entries"][0]["content"] == "hello", "entry content should match"
    assert d["scores"] == [0.85], "scores should match"
    assert d["total_count"] == 1, "total_count should match"
    return


def test_memoryqueryresult_as_dict_with_no_scores():
    """
        Verify that as_dict returns None for scores when not provided.
    """
    entry = MemoryEntry(content="test", scope=MemoryScope.AGENT)
    result = MemoryQueryResult(entries=[entry])
    d = result.as_dict()
    assert d["scores"] is None, "scores should be None in as_dict"
    return


# ---- __repr__ Tests ----


def test_memoryqueryresult_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    result = MemoryQueryResult(entries=[])
    repr_str = repr(result)
    has_class_name = "MemoryQueryResult" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_memoryqueryresult_repr_contains_count():
    """
        Verify that __repr__ contains the total count.
    """
    entries = [
        MemoryEntry(content="a", scope=MemoryScope.AGENT),
        MemoryEntry(content="b", scope=MemoryScope.AGENT),
    ]
    result = MemoryQueryResult(entries=entries)
    repr_str = repr(result)
    has_count = "count=2" in repr_str
    assert has_count is True, "repr should contain the count"
    return


# ---- __str__ Tests ----


def test_memoryqueryresult_str_contains_match_count():
    """
        Verify that __str__ contains the match count.
    """
    entries = [
        MemoryEntry(content="a", scope=MemoryScope.AGENT, identifier="id-1"),
    ]
    result = MemoryQueryResult(entries=entries)
    str_val = str(result)
    has_count = "1 matches" in str_val
    assert has_count is True, "__str__ should contain the match count"
    return


def test_memoryqueryresult_str_contains_top_identifiers():
    """
        Verify that __str__ contains the top entry identifiers.
    """
    entries = [
        MemoryEntry(content="a", scope=MemoryScope.AGENT, identifier="alpha"),
        MemoryEntry(content="b", scope=MemoryScope.AGENT, identifier="beta"),
    ]
    result = MemoryQueryResult(entries=entries)
    str_val = str(result)
    has_alpha = "alpha" in str_val
    has_beta = "beta" in str_val
    assert has_alpha is True, "__str__ should contain identifier 'alpha'"
    assert has_beta is True, "__str__ should contain identifier 'beta'"
    return


def test_memoryqueryresult_str_limits_top_identifiers_to_five():
    """
        Verify that __str__ shows at most 5 top entry identifiers.
    """
    entries = [
        MemoryEntry(content="e{}".format(i), scope=MemoryScope.AGENT, identifier="id-{}".format(i))
        for i in range(10)
    ]
    result = MemoryQueryResult(entries=entries)
    str_val = str(result)
    has_id_4 = "id-4" in str_val
    has_id_5 = "id-5" in str_val
    assert has_id_4 is True, "__str__ should contain id-4 (within top 5)"
    assert has_id_5 is False, "__str__ should not contain id-5 (beyond top 5)"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
