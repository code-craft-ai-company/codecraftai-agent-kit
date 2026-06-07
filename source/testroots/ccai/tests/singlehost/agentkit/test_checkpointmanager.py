"""
    Unit tests for the WorkflowCheckpoint and CheckpointManager
    classes in the Workflow & Orchestration feature.

    Tests WorkflowCheckpoint construction, properties, as_dict,
    to_json, from_json, __repr__, and __str__.

    Tests CheckpointManager save, load, list, delete operations,
    and WorkflowCheckpointError for save/load failures.

    Uses testbase mocking for MemoryStore.

    Requirements: 9.1-9.15
"""

import json

from datetime import datetime, timezone

from ccai.agentkit.checkpointmanager import CheckpointManager
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryqueryresult import MemoryQueryResult
from ccai.agentkit.memoryscope import MemoryScope
from ccai.agentkit.workflowcheckpoint import WorkflowCheckpoint
from ccai.agentkit.workflowcontext import WorkflowContext
from ccai.agentkit.workflowerrors import WorkflowCheckpointError
from ccai.testbase.mocking import Mock


# =========================================================================
# WorkflowCheckpoint construction tests (Requirements 9.10, 9.11)
# =========================================================================

def test_checkpoint_construction_with_all_fields():
    """
        Verify that WorkflowCheckpoint stores all fields provided
        at construction time.
    """
    ts = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    cp = WorkflowCheckpoint(
        workflow_name="data-pipeline",
        execution_id="exec-001",
        completed_step_ids={"step-a", "step-b"},
        context_state={"inputs": {"x": 1}, "step_outputs": {}, "metadata": {}},
        current_step_id="step-c",
        timestamp=ts
    )

    assert cp.workflow_name == "data-pipeline", \
        "workflow_name should match"
    assert cp.execution_id == "exec-001", \
        "execution_id should match"
    assert cp.completed_step_ids == {"step-a", "step-b"}, \
        "completed_step_ids should match"
    assert cp.context_state == {"inputs": {"x": 1}, "step_outputs": {}, "metadata": {}}, \
        "context_state should match"
    assert cp.current_step_id == "step-c", \
        "current_step_id should match"
    assert cp.timestamp == ts, \
        "timestamp should match the provided value"
    return


def test_checkpoint_default_timestamp_is_utc():
    """
        Verify that the timestamp defaults to a UTC datetime when
        not provided.
    """
    cp = WorkflowCheckpoint(
        workflow_name="wf",
        execution_id="exec-002",
        completed_step_ids=set(),
        context_state={},
        current_step_id="step-1"
    )

    assert cp.timestamp is not None, \
        "timestamp should not be None"
    assert cp.timestamp.tzinfo is not None, \
        "timestamp should have timezone info"
    return


# =========================================================================
# WorkflowCheckpoint property immutability tests (Requirement 9.11)
# =========================================================================

def test_checkpoint_completed_step_ids_returns_defensive_copy():
    """
        Verify that completed_step_ids returns a defensive copy
        so the internal set cannot be mutated externally.
    """
    cp = WorkflowCheckpoint(
        workflow_name="wf",
        execution_id="exec-003",
        completed_step_ids={"step-a"},
        context_state={},
        current_step_id="step-b"
    )

    ids = cp.completed_step_ids
    ids.add("step-injected")

    assert "step-injected" not in cp.completed_step_ids, \
        "Modifying the returned set should not affect the checkpoint"
    return


def test_checkpoint_context_state_returns_defensive_copy():
    """
        Verify that context_state returns a defensive copy so the
        internal dict cannot be mutated externally.
    """
    cp = WorkflowCheckpoint(
        workflow_name="wf",
        execution_id="exec-004",
        completed_step_ids=set(),
        context_state={"inputs": {"a": 1}},
        current_step_id="step-1"
    )

    state = cp.context_state
    state["injected"] = "bad"

    assert "injected" not in cp.context_state, \
        "Modifying the returned dict should not affect the checkpoint"
    return


# =========================================================================
# WorkflowCheckpoint as_dict tests (Requirement 9.12)
# =========================================================================

def test_checkpoint_as_dict_contains_all_fields():
    """
        Verify that as_dict returns a dictionary with all checkpoint
        fields and completed_step_ids as a sorted list.
    """
    ts = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    cp = WorkflowCheckpoint(
        workflow_name="pipeline",
        execution_id="exec-100",
        completed_step_ids={"step-b", "step-a"},
        context_state={"inputs": {}, "step_outputs": {}, "metadata": {}},
        current_step_id="step-c",
        timestamp=ts
    )

    result = cp.as_dict()

    assert result["workflow_name"] == "pipeline", \
        "as_dict workflow_name should match"
    assert result["execution_id"] == "exec-100", \
        "as_dict execution_id should match"
    assert result["completed_step_ids"] == ["step-a", "step-b"], \
        "as_dict completed_step_ids should be a sorted list"
    assert result["current_step_id"] == "step-c", \
        "as_dict current_step_id should match"
    assert result["timestamp"] == ts.isoformat(), \
        "as_dict timestamp should be ISO format string"
    return


# =========================================================================
# WorkflowCheckpoint to_json / from_json tests (Requirements 9.13, 9.14)
# =========================================================================

def test_checkpoint_to_json_produces_valid_json():
    """
        Verify that to_json produces a valid JSON string whose
        parsed content matches as_dict.
    """
    ts = datetime(2025, 3, 15, 8, 30, 0, tzinfo=timezone.utc)

    cp = WorkflowCheckpoint(
        workflow_name="etl",
        execution_id="exec-200",
        completed_step_ids={"extract"},
        context_state={"inputs": {"source": "db"}, "step_outputs": {}, "metadata": {}},
        current_step_id="transform",
        timestamp=ts
    )

    json_str = cp.to_json()
    parsed = json.loads(json_str)

    assert parsed == cp.as_dict(), \
        "Parsed JSON should match as_dict output"
    return


def test_checkpoint_from_json_reconstructs_equivalent():
    """
        Verify that from_json reconstructs a WorkflowCheckpoint
        with equivalent fields.
    """
    ts = datetime(2025, 6, 1, 14, 0, 0, tzinfo=timezone.utc)

    original = WorkflowCheckpoint(
        workflow_name="deploy",
        execution_id="exec-300",
        completed_step_ids={"build", "test"},
        context_state={"inputs": {"env": "prod"}, "step_outputs": {}, "metadata": {}},
        current_step_id="release",
        timestamp=ts
    )

    json_str = original.to_json()
    restored = WorkflowCheckpoint.from_json(json_str)

    assert restored.workflow_name == original.workflow_name, \
        "Restored workflow_name should match"
    assert restored.execution_id == original.execution_id, \
        "Restored execution_id should match"
    assert restored.completed_step_ids == original.completed_step_ids, \
        "Restored completed_step_ids should match"
    assert restored.context_state == original.context_state, \
        "Restored context_state should match"
    assert restored.current_step_id == original.current_step_id, \
        "Restored current_step_id should match"
    assert restored.timestamp == original.timestamp, \
        "Restored timestamp should match"
    return


# =========================================================================
# WorkflowCheckpoint __repr__ / __str__ tests (Requirements 23.13, 23.14)
# =========================================================================

def test_checkpoint_repr_includes_key_fields():
    """
        Verify that __repr__ includes the class name, workflow name,
        execution identifier, and completed step count.
    """
    cp = WorkflowCheckpoint(
        workflow_name="my-workflow",
        execution_id="exec-repr",
        completed_step_ids={"a", "b", "c"},
        context_state={},
        current_step_id="d"
    )

    repr_str = repr(cp)

    assert "WorkflowCheckpoint" in repr_str, \
        "__repr__ should include the class name"
    assert "my-workflow" in repr_str, \
        "__repr__ should include the workflow name"
    assert "exec-repr" in repr_str, \
        "__repr__ should include the execution id"
    assert "3" in repr_str, \
        "__repr__ should include the completed step count"
    return


def test_checkpoint_str_includes_summary():
    """
        Verify that __str__ includes the workflow name, execution
        identifier, and timestamp.
    """
    ts = datetime(2025, 7, 4, 12, 0, 0, tzinfo=timezone.utc)

    cp = WorkflowCheckpoint(
        workflow_name="summary-wf",
        execution_id="exec-str",
        completed_step_ids=set(),
        context_state={},
        current_step_id="step-1",
        timestamp=ts
    )

    str_val = str(cp)

    assert "summary-wf" in str_val, \
        "__str__ should include the workflow name"
    assert "exec-str" in str_val, \
        "__str__ should include the execution id"
    assert "2025" in str_val, \
        "__str__ should include the timestamp year"
    return


# =========================================================================
# Helper: create a mock MemoryStore
# =========================================================================

def _create_mock_memory_store(store_name="test-store"):
    """
        Creates a Mock MemoryStore with recursive configuration
        and a store_name attribute.
    """
    mock_store = Mock()
    mock_store.configure(recursive=True)
    ctx = mock_store.mock_context()
    ctx.set_attribute("store_name", store_name)
    return mock_store


# =========================================================================
# CheckpointManager save_checkpoint tests (Requirements 9.1, 9.2, 9.8)
# =========================================================================

def test_save_checkpoint_stores_entry_in_memory_store():
    """
        Verify that save_checkpoint creates a MemoryEntry and
        stores it in the MemoryStore.
    """
    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("contains", return_value=False)

    stored_entries = []

    def capture_store(entry):
        stored_entries.append(entry)
        return entry

    mock_store.mock_context().mock_method("store", side_effect=capture_store)

    manager = CheckpointManager(memory_store=mock_store)

    context = WorkflowContext(
        inputs={"source": "api"},
        metadata={"workflow_name": "data-pipeline"}
    )
    context.set_step_output("step-1", {"result": "ok"})

    manager.save_checkpoint(
        execution_id="exec-save-001",
        context=context,
        completed_step_ids={"step-1"},
        current_step_id="step-2"
    )

    assert len(stored_entries) == 1, \
        "save_checkpoint should store exactly one entry"

    entry = stored_entries[0]
    assert entry.identifier == "exec-save-001", \
        "Entry identifier should be the execution_id"

    checkpoint = WorkflowCheckpoint.from_json(entry.content)
    assert checkpoint.workflow_name == "data-pipeline", \
        "Checkpoint workflow_name should come from context metadata"
    assert checkpoint.completed_step_ids == {"step-1"}, \
        "Checkpoint completed_step_ids should match"
    assert checkpoint.current_step_id == "step-2", \
        "Checkpoint current_step_id should match"
    return


def test_save_checkpoint_updates_existing_entry():
    """
        Verify that save_checkpoint updates an existing entry when
        a checkpoint already exists for the execution.
    """
    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("contains", return_value=True)

    updated_entries = []

    def capture_update(identifier, entry):
        updated_entries.append((identifier, entry))
        return entry

    mock_store.mock_context().mock_method("update", side_effect=capture_update)

    manager = CheckpointManager(memory_store=mock_store)

    context = WorkflowContext(
        inputs={},
        metadata={"workflow_name": "wf"}
    )

    manager.save_checkpoint(
        execution_id="exec-update-001",
        context=context,
        completed_step_ids={"a", "b"},
        current_step_id="c"
    )

    assert len(updated_entries) == 1, \
        "save_checkpoint should update exactly one entry"
    assert updated_entries[0][0] == "exec-update-001", \
        "Update should use the execution_id as identifier"
    return


def test_save_checkpoint_raises_checkpoint_error_on_failure():
    """
        Verify that save_checkpoint raises WorkflowCheckpointError
        when the MemoryStore operation fails.
    """
    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("contains", return_value=False)
    mock_store.mock_context().mock_method(
        "store", side_effect=lambda entry: (_ for _ in ()).throw(RuntimeError("disk full"))
    )

    manager = CheckpointManager(memory_store=mock_store)

    context = WorkflowContext(inputs={}, metadata={"workflow_name": "wf"})

    caught = False
    try:
        manager.save_checkpoint(
            execution_id="exec-fail-001",
            context=context,
            completed_step_ids=set(),
            current_step_id="step-1"
        )
    except WorkflowCheckpointError as err:
        caught = True
        assert err.execution_id == "exec-fail-001", \
            "Error execution_id should match"
        assert err.operation == "save", \
            "Error operation should be 'save'"
        assert err.cause is not None, \
            "Error cause should not be None"

    assert caught is True, \
        "save_checkpoint should raise WorkflowCheckpointError on failure"
    return


# =========================================================================
# CheckpointManager load_checkpoint tests (Requirements 9.3, 9.9)
# =========================================================================

def test_load_checkpoint_returns_checkpoint_from_store():
    """
        Verify that load_checkpoint retrieves and deserializes a
        checkpoint from the MemoryStore.
    """
    ts = datetime(2025, 5, 1, 10, 0, 0, tzinfo=timezone.utc)

    original = WorkflowCheckpoint(
        workflow_name="load-wf",
        execution_id="exec-load-001",
        completed_step_ids={"step-a"},
        context_state={"inputs": {}, "step_outputs": {}, "metadata": {}},
        current_step_id="step-b",
        timestamp=ts
    )

    entry = MemoryEntry(
        content=original.to_json(),
        scope=MemoryScope.AGENT,
        identifier="exec-load-001"
    )

    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("retrieve", return_value=entry)

    manager = CheckpointManager(memory_store=mock_store)

    result = manager.load_checkpoint("exec-load-001")

    assert result is not None, \
        "load_checkpoint should return a checkpoint"
    assert result.workflow_name == "load-wf", \
        "Loaded checkpoint workflow_name should match"
    assert result.execution_id == "exec-load-001", \
        "Loaded checkpoint execution_id should match"
    assert result.completed_step_ids == {"step-a"}, \
        "Loaded checkpoint completed_step_ids should match"
    return


def test_load_checkpoint_returns_none_when_not_found():
    """
        Verify that load_checkpoint returns None when no checkpoint
        exists for the execution.
    """
    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("retrieve", return_value=None)

    manager = CheckpointManager(memory_store=mock_store)

    result = manager.load_checkpoint("exec-missing")

    assert result is None, \
        "load_checkpoint should return None when no checkpoint exists"
    return


def test_load_checkpoint_raises_checkpoint_error_on_failure():
    """
        Verify that load_checkpoint raises WorkflowCheckpointError
        when the MemoryStore operation fails.
    """
    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method(
        "retrieve", side_effect=lambda identifier: (_ for _ in ()).throw(RuntimeError("connection lost"))
    )

    manager = CheckpointManager(memory_store=mock_store)

    caught = False
    try:
        manager.load_checkpoint("exec-fail-load")
    except WorkflowCheckpointError as err:
        caught = True
        assert err.execution_id == "exec-fail-load", \
            "Error execution_id should match"
        assert err.operation == "load", \
            "Error operation should be 'load'"

    assert caught is True, \
        "load_checkpoint should raise WorkflowCheckpointError on failure"
    return


# =========================================================================
# CheckpointManager list_checkpoints tests (Requirement 9.4)
# =========================================================================

def test_list_checkpoints_returns_checkpoints_ordered_by_timestamp_desc():
    """
        Verify that list_checkpoints returns checkpoints ordered
        by timestamp descending.
    """
    ts1 = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    ts3 = datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

    cp1 = WorkflowCheckpoint(
        workflow_name="wf", execution_id="e1",
        completed_step_ids=set(), context_state={},
        current_step_id="s1", timestamp=ts1
    )
    cp2 = WorkflowCheckpoint(
        workflow_name="wf", execution_id="e2",
        completed_step_ids={"s1"}, context_state={},
        current_step_id="s2", timestamp=ts2
    )
    cp3 = WorkflowCheckpoint(
        workflow_name="wf", execution_id="e3",
        completed_step_ids={"s1"}, context_state={},
        current_step_id="s2", timestamp=ts3
    )

    entries = [
        MemoryEntry(content=cp1.to_json(), scope=MemoryScope.AGENT, identifier="e1"),
        MemoryEntry(content=cp2.to_json(), scope=MemoryScope.AGENT, identifier="e2"),
        MemoryEntry(content=cp3.to_json(), scope=MemoryScope.AGENT, identifier="e3"),
    ]

    query_result = MemoryQueryResult(entries=entries)

    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("search", return_value=query_result)

    manager = CheckpointManager(memory_store=mock_store)

    result = manager.list_checkpoints("wf")

    assert len(result) == 3, \
        "list_checkpoints should return 3 checkpoints"
    assert result[0].execution_id == "e2", \
        "First checkpoint should be the most recent (ts2)"
    assert result[1].execution_id == "e3", \
        "Second checkpoint should be ts3"
    assert result[2].execution_id == "e1", \
        "Third checkpoint should be the oldest (ts1)"
    return


def test_list_checkpoints_returns_empty_list_when_none_found():
    """
        Verify that list_checkpoints returns an empty list when
        no checkpoints exist for the workflow.
    """
    query_result = MemoryQueryResult(entries=[])

    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("search", return_value=query_result)

    manager = CheckpointManager(memory_store=mock_store)

    result = manager.list_checkpoints("nonexistent-wf")

    assert result == [], \
        "list_checkpoints should return an empty list"
    return


# =========================================================================
# CheckpointManager delete_checkpoint tests (Requirement 9.5)
# =========================================================================

def test_delete_checkpoint_removes_entry_from_store():
    """
        Verify that delete_checkpoint removes the checkpoint entry
        from the MemoryStore.
    """
    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("contains", return_value=True)

    deleted_ids = []

    def capture_delete(identifier):
        deleted_ids.append(identifier)
        return

    mock_store.mock_context().mock_method("delete", side_effect=capture_delete)

    manager = CheckpointManager(memory_store=mock_store)

    manager.delete_checkpoint("exec-del-001")

    assert deleted_ids == ["exec-del-001"], \
        "delete_checkpoint should delete the entry by execution_id"
    return


def test_delete_checkpoint_does_nothing_when_not_found():
    """
        Verify that delete_checkpoint does not raise when the
        checkpoint does not exist.
    """
    mock_store = _create_mock_memory_store()
    mock_store.mock_context().mock_method("contains", return_value=False)

    manager = CheckpointManager(memory_store=mock_store)

    manager.delete_checkpoint("exec-nonexistent")

    return


# =========================================================================
# CheckpointManager __repr__ / __str__ tests (Requirements 23.27, 23.28)
# =========================================================================

def test_checkpoint_manager_repr_includes_store_name():
    """
        Verify that __repr__ includes the class name and the
        MemoryStore name.
    """
    mock_store = _create_mock_memory_store("my-checkpoint-store")

    manager = CheckpointManager(memory_store=mock_store)

    repr_str = repr(manager)

    assert "CheckpointManager" in repr_str, \
        "__repr__ should include the class name"
    assert "my-checkpoint-store" in repr_str, \
        "__repr__ should include the store name"
    return


def test_checkpoint_manager_str_includes_store_name():
    """
        Verify that __str__ includes the MemoryStore name.
    """
    mock_store = _create_mock_memory_store("cp-store")

    manager = CheckpointManager(memory_store=mock_store)

    str_val = str(manager)

    assert "cp-store" in str_val, \
        "__str__ should include the store name"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
