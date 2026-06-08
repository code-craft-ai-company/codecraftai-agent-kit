"""
    Unit tests for the ccai.agentkit.inmemorydeadletterstore module.
"""

from ccai.agentkit.deadletterentry import DeadLetterEntry
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore


def _make_entry(op_type="op", source="src", agent="agent-1"):
    return DeadLetterEntry(
        operation_type=op_type, payload={}, exception_info="err",
        retry_attempts=0, source_component=source, agent_identifier=agent
    )


def test_store_and_retrieve():
    """
        Verify that stored entries can be retrieved.
    """
    store = InMemoryDeadLetterStore()
    entry = _make_entry()
    store.store(entry)

    retrieved = store.retrieve(entry.identifier)
    assert retrieved is entry, "should retrieve the stored entry"
    return


def test_retrieve_returns_none_for_unknown():
    """
        Verify that retrieve returns None for unknown identifiers.
    """
    store = InMemoryDeadLetterStore()
    assert store.retrieve("nonexistent") is None, "should return None"
    return


def test_search_with_filter():
    """
        Verify that search filters by operation_type.
    """
    store = InMemoryDeadLetterStore()
    store.store(_make_entry(op_type="send"))
    store.store(_make_entry(op_type="exec"))
    store.store(_make_entry(op_type="send"))

    query = DeadLetterQuery(operation_type="send")
    result = store.search(query)
    assert result.total_count == 2, "should find 2 matching entries"
    return


def test_delete():
    """
        Verify that delete removes an entry.
    """
    store = InMemoryDeadLetterStore()
    entry = _make_entry()
    store.store(entry)
    store.delete(entry.identifier)

    assert store.retrieve(entry.identifier) is None, "should be deleted"
    assert store.count() == 0, "count should be 0"
    return


def test_purge():
    """
        Verify that purge removes all entries.
    """
    store = InMemoryDeadLetterStore()
    store.store(_make_entry())
    store.store(_make_entry())
    store.purge()

    assert store.count() == 0, "count should be 0 after purge"
    return


def test_count():
    """
        Verify that count returns the number of stored entries.
    """
    store = InMemoryDeadLetterStore()
    assert store.count() == 0, "initial count should be 0"
    store.store(_make_entry())
    assert store.count() == 1, "count should be 1"
    return
