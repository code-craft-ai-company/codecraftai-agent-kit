"""
    Unit tests for the ccai.agentkit.deadletterqueue module.
"""

from ccai.agentkit.deadletterqueue import DeadLetterQueue
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore


def test_enqueue_creates_entry():
    """
        Verify that enqueue creates and stores a DeadLetterEntry.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)

    entry = queue.enqueue(
        operation_type="send_message",
        payload={"body": "hello"},
        exception_info="ConnectionError(timeout)",
        retry_attempts=3,
        source_component="transport",
        agent_identifier="agent-1"
    )

    assert entry is not None, "should return created entry"
    assert entry.operation_type == "send_message", "operation_type should match"
    assert queue.entry_count == 1, "entry_count should be 1"
    return


def test_get_entry():
    """
        Verify that get_entry retrieves a specific entry.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)

    entry = queue.enqueue("op", {}, "err", 0, "src", "agent")
    retrieved = queue.get_entry(entry.identifier)
    assert retrieved is not None, "should retrieve the entry"
    assert retrieved.identifier == entry.identifier, "identifiers should match"
    return


def test_query():
    """
        Verify that query searches the store.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)

    queue.enqueue("send", {}, "err", 0, "transport", "agent-1")
    queue.enqueue("exec", {}, "err", 0, "tool", "agent-1")

    result = queue.query(DeadLetterQuery(operation_type="send"))
    assert result.total_count == 1, "should find 1 matching entry"
    return


def test_replay_success():
    """
        Verify that replay removes the entry on success.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)

    entry = queue.enqueue("op", {"data": "test"}, "err", 0, "src", "agent")
    replayed_payloads = []

    success = queue.replay(entry.identifier, lambda p: replayed_payloads.append(p))
    assert success is True, "replay should succeed"
    assert len(replayed_payloads) == 1, "callable should be invoked"
    assert queue.entry_count == 0, "entry should be removed after successful replay"
    return


def test_replay_failure():
    """
        Verify that replay returns False on failure.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)

    entry = queue.enqueue("op", {}, "err", 0, "src", "agent")

    def fail_replay(payload):
        raise RuntimeError("replay failed")

    success = queue.replay(entry.identifier, fail_replay)
    assert success is False, "replay should return False on failure"
    assert queue.entry_count == 1, "entry should remain after failed replay"
    return


def test_replay_nonexistent():
    """
        Verify that replay returns False for nonexistent entries.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)

    success = queue.replay("nonexistent", lambda p: None)
    assert success is False, "replay should return False for nonexistent entry"
    return


def test_purge():
    """
        Verify that purge removes all entries.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)

    queue.enqueue("op1", {}, "err", 0, "src", "agent")
    queue.enqueue("op2", {}, "err", 0, "src", "agent")
    queue.purge()

    assert queue.entry_count == 0, "entry_count should be 0 after purge"
    return


def test_repr():
    """
        Verify that __repr__ includes class name and count.
    """
    store = InMemoryDeadLetterStore()
    queue = DeadLetterQueue(store)
    repr_str = repr(queue)
    assert "DeadLetterQueue" in repr_str, "repr should contain class name"
    return
