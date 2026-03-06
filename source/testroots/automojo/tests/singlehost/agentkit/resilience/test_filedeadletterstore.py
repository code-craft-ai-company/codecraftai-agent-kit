"""
    Unit tests for the automojo.agentkit.filedeadletterstore module.

    Tests file persistence, directory creation, I/O error handling,
    and round-trip serialization for the FileDeadLetterStore.

    Requirements: 13.5-13.11
"""

import os
import tempfile
import shutil

from automojo.agentkit.deadletterentry import DeadLetterEntry
from automojo.agentkit.deadletterquery import DeadLetterQuery
from automojo.agentkit.filedeadletterstore import FileDeadLetterStore
from automojo.agentkit.resilienceerrors import ResilienceError


def _make_entry(op_type="op", source="src", agent="agent-1", identifier=None):
    """
        Helper to create a DeadLetterEntry for testing.
    """
    return DeadLetterEntry(
        operation_type=op_type, payload={"key": "value"},
        exception_info="err", retry_attempts=2,
        source_component=source, agent_identifier=agent,
        identifier=identifier
    )


def test_creates_directory_at_construction():
    """
        Verify that FileDeadLetterStore creates the directory if it does
        not exist at construction time.
        Validates: Requirement 13.8
    """
    base = tempfile.mkdtemp()
    try:
        target = os.path.join(base, "new_subdir")
        assert not os.path.exists(target), "directory should not exist yet"

        FileDeadLetterStore(target)
        assert os.path.isdir(target), "directory should be created"
    finally:
        shutil.rmtree(base)
    return


def test_store_and_retrieve_round_trip():
    """
        Verify that storing an entry and retrieving it produces an
        equivalent DeadLetterEntry with matching fields.
        Validates: Requirements 13.5, 13.7, 13.11
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        entry = _make_entry()
        store.store(entry)

        retrieved = store.retrieve(entry.identifier)
        assert retrieved is not None, "should retrieve the stored entry"
        assert retrieved.identifier == entry.identifier, "identifier should match"
        assert retrieved.operation_type == entry.operation_type, "operation_type should match"
        assert retrieved.payload == entry.payload, "payload should match"
        assert retrieved.exception_info == entry.exception_info, "exception_info should match"
        assert retrieved.source_component == entry.source_component, "source_component should match"
        assert retrieved.agent_identifier == entry.agent_identifier, "agent_identifier should match"
    finally:
        shutil.rmtree(base)
    return


def test_store_creates_json_file():
    """
        Verify that storing an entry creates a JSON file named after the
        entry identifier.
        Validates: Requirement 13.7
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        entry = _make_entry(identifier="test-entry-001")
        store.store(entry)

        expected_path = os.path.join(base, "test-entry-001.json")
        assert os.path.isfile(expected_path), "JSON file should exist"
    finally:
        shutil.rmtree(base)
    return


def test_retrieve_returns_none_for_unknown():
    """
        Verify that retrieve returns None for an identifier that has not
        been stored.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        result = store.retrieve("nonexistent")
        assert result is None, "should return None for unknown identifier"
    finally:
        shutil.rmtree(base)
    return



def test_search_with_operation_type_filter():
    """
        Verify that search filters entries by operation_type.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        store.store(_make_entry(op_type="send"))
        store.store(_make_entry(op_type="exec"))
        store.store(_make_entry(op_type="send"))

        query = DeadLetterQuery(operation_type="send")
        result = store.search(query)
        assert result.total_count == 2, "should find 2 matching entries"
    finally:
        shutil.rmtree(base)
    return


def test_search_with_source_component_filter():
    """
        Verify that search filters entries by source_component.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        store.store(_make_entry(source="transport"))
        store.store(_make_entry(source="memory"))
        store.store(_make_entry(source="transport"))

        query = DeadLetterQuery(source_component="transport")
        result = store.search(query)
        assert result.total_count == 2, "should find 2 matching entries"
    finally:
        shutil.rmtree(base)
    return


def test_delete_removes_file():
    """
        Verify that delete removes the entry file from disk.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        entry = _make_entry(identifier="to-delete")
        store.store(entry)

        store.delete("to-delete")
        assert store.retrieve("to-delete") is None, "entry should be deleted"

        filepath = os.path.join(base, "to-delete.json")
        assert not os.path.exists(filepath), "file should be removed"
    finally:
        shutil.rmtree(base)
    return


def test_delete_nonexistent_does_not_raise():
    """
        Verify that deleting a nonexistent entry does not raise.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        store.delete("nonexistent")
    finally:
        shutil.rmtree(base)
    return


def test_purge_removes_all_entries():
    """
        Verify that purge removes all entry files.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        store.store(_make_entry())
        store.store(_make_entry())
        store.store(_make_entry())

        store.purge()
        assert store.count() == 0, "count should be 0 after purge"
    finally:
        shutil.rmtree(base)
    return


def test_count_returns_number_of_entries():
    """
        Verify that count returns the correct number of stored entries.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        assert store.count() == 0, "initial count should be 0"

        store.store(_make_entry())
        assert store.count() == 1, "count should be 1"

        store.store(_make_entry())
        assert store.count() == 2, "count should be 2"
    finally:
        shutil.rmtree(base)
    return


def test_store_raises_resilience_error_on_io_failure():
    """
        Verify that store raises ResilienceError when the directory is
        not writable.
        Validates: Requirement 13.10
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        os.chmod(base, 0o444)

        entry = _make_entry()
        raised = False
        try:
            store.store(entry)
        except ResilienceError:
            raised = True
        finally:
            os.chmod(base, 0o755)

        assert raised, "should raise ResilienceError on write failure"
    finally:
        shutil.rmtree(base)
    return


def test_retrieve_raises_resilience_error_on_io_failure():
    """
        Verify that retrieve raises ResilienceError when a file cannot
        be read.
        Validates: Requirement 13.10
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        entry = _make_entry(identifier="bad-read")
        store.store(entry)

        filepath = os.path.join(base, "bad-read.json")
        os.chmod(filepath, 0o000)

        raised = False
        try:
            store.retrieve("bad-read")
        except ResilienceError:
            raised = True
        finally:
            os.chmod(filepath, 0o644)

        assert raised, "should raise ResilienceError on read failure"
    finally:
        shutil.rmtree(base)
    return


def test_count_raises_resilience_error_on_io_failure():
    """
        Verify that count raises ResilienceError when the directory
        cannot be listed.
        Validates: Requirement 13.10
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        shutil.rmtree(base)

        raised = False
        try:
            store.count()
        except ResilienceError:
            raised = True

        assert raised, "should raise ResilienceError on listing failure"
    finally:
        if os.path.exists(base):
            shutil.rmtree(base)
    return


def test_existing_directory_accepted():
    """
        Verify that FileDeadLetterStore works with an already existing
        directory.
        Validates: Requirement 13.6
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        entry = _make_entry()
        store.store(entry)
        assert store.count() == 1, "should store entry in existing directory"
    finally:
        shutil.rmtree(base)
    return


def test_store_name_is_file():
    """
        Verify that the store_name property returns 'file'.
        Validates: Requirement 13.5
    """
    base = tempfile.mkdtemp()
    try:
        store = FileDeadLetterStore(base)
        assert store.store_name == "file", "store_name should be 'file'"
    finally:
        shutil.rmtree(base)
    return
