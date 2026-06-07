"""
    Unit tests for WorkflowEdge, ParallelBranch, StepResult, and WorkflowResult
    immutable data types in the Workflow & Orchestration feature.

    Tests construction, property access, as_dict, __repr__, __str__,
    is_success, get_step_result, and JSON round-trip serialization.

    Requirements: 3.1-3.2, 6.1-6.15, 8.10-8.13
"""

import json

from ccai.agentkit.workflowedge import WorkflowEdge
from ccai.agentkit.parallelbranch import ParallelBranch
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.workflowresult import WorkflowResult
from ccai.agentkit.workflowexecutionstatus import WorkflowExecutionStatus


# =========================================================================
# WorkflowEdge tests (Requirements 3.1, 3.2, 3.13, 3.14, 3.15)
# =========================================================================

def test_workflow_edge_construction_and_properties():
    """
        Verify that WorkflowEdge stores all fields and exposes them
        as read-only properties.
    """
    edge = WorkflowEdge("step-a", "step-b", condition="steps.step-a.result == 'ok'", priority=5)

    assert edge.source_step_id == "step-a", "source_step_id should be 'step-a'"
    assert edge.target_step_id == "step-b", "target_step_id should be 'step-b'"
    assert edge.condition == "steps.step-a.result == 'ok'", "condition should match"
    assert edge.priority == 5, "priority should be 5"
    return


def test_workflow_edge_default_priority():
    """
        Verify that WorkflowEdge defaults priority to 0 when not provided.
    """
    edge = WorkflowEdge("src", "tgt")

    assert edge.priority == 0, "Default priority should be 0"
    assert edge.condition is None, "Default condition should be None"
    return


def test_workflow_edge_as_dict():
    """
        Verify that as_dict returns a dictionary with all edge fields.
    """
    edge = WorkflowEdge("s1", "s2", condition="x > 1", priority=3)
    d = edge.as_dict()

    assert d["source_step_id"] == "s1", "as_dict source_step_id should be 's1'"
    assert d["target_step_id"] == "s2", "as_dict target_step_id should be 's2'"
    assert d["condition"] == "x > 1", "as_dict condition should be 'x > 1'"
    assert d["priority"] == 3, "as_dict priority should be 3"
    return


def test_workflow_edge_as_dict_no_condition():
    """
        Verify that as_dict includes None for condition when not set.
    """
    edge = WorkflowEdge("a", "b")
    d = edge.as_dict()

    assert d["condition"] is None, "as_dict condition should be None when not set"
    return


def test_workflow_edge_repr_has_condition():
    """
        Verify that __repr__ includes class name, source, target,
        and has_condition=True when a condition is present.
    """
    edge = WorkflowEdge("src", "tgt", condition="x == 1")
    repr_str = repr(edge)

    assert "WorkflowEdge" in repr_str, "repr should contain class name"
    assert "src" in repr_str, "repr should contain source_step_id"
    assert "tgt" in repr_str, "repr should contain target_step_id"
    assert "True" in repr_str, "repr should indicate has_condition=True"
    return


def test_workflow_edge_repr_no_condition():
    """
        Verify that __repr__ shows has_condition=False when no condition.
    """
    edge = WorkflowEdge("a", "b")
    repr_str = repr(edge)

    assert "False" in repr_str, "repr should indicate has_condition=False"
    return


def test_workflow_edge_str_conditional():
    """
        Verify that __str__ includes condition and priority for conditional edges.
    """
    edge = WorkflowEdge("s1", "s2", condition="x > 0", priority=2)
    str_val = str(edge)

    assert "s1" in str_val, "str should contain source step id"
    assert "s2" in str_val, "str should contain target step id"
    assert "x > 0" in str_val, "str should contain condition expression"
    assert "2" in str_val, "str should contain priority"
    return


def test_workflow_edge_str_unconditional():
    """
        Verify that __str__ shows 'unconditional' when no condition is set.
    """
    edge = WorkflowEdge("a", "b")
    str_val = str(edge)

    assert "unconditional" in str_val, "str should contain 'unconditional'"
    assert "a" in str_val, "str should contain source step id"
    assert "b" in str_val, "str should contain target step id"
    return


# =========================================================================
# ParallelBranch tests (Requirements 8.10, 8.11, 8.12, 8.13)
# =========================================================================

def test_parallel_branch_construction_and_properties():
    """
        Verify that ParallelBranch stores fork and join step ids
        and exposes them as read-only properties.
    """
    branch = ParallelBranch("fork-1", "join-1")

    assert branch.fork_step_id == "fork-1", "fork_step_id should be 'fork-1'"
    assert branch.join_step_id == "join-1", "join_step_id should be 'join-1'"
    return


def test_parallel_branch_as_dict():
    """
        Verify that as_dict returns a dictionary with fork and join step ids.
    """
    branch = ParallelBranch("f", "j")
    d = branch.as_dict()

    assert d["fork_step_id"] == "f", "as_dict fork_step_id should be 'f'"
    assert d["join_step_id"] == "j", "as_dict join_step_id should be 'j'"
    assert len(d) == 2, "as_dict should have exactly 2 keys"
    return


def test_parallel_branch_repr():
    """
        Verify that __repr__ includes class name, fork step id, and join step id.
    """
    branch = ParallelBranch("fork-x", "join-y")
    repr_str = repr(branch)

    assert "ParallelBranch" in repr_str, "repr should contain class name"
    assert "fork-x" in repr_str, "repr should contain fork_step_id"
    assert "join-y" in repr_str, "repr should contain join_step_id"
    return


def test_parallel_branch_str():
    """
        Verify that __str__ returns a human-readable summary with fork and join ids.
    """
    branch = ParallelBranch("start-fork", "end-join")
    str_val = str(branch)

    assert "start-fork" in str_val, "str should contain fork step id"
    assert "end-join" in str_val, "str should contain join step id"
    return


# =========================================================================
# StepResult tests (Requirements 6.9-6.15)
# =========================================================================

def test_step_result_construction_and_properties():
    """
        Verify that StepResult stores all fields and exposes them
        as read-only properties.
    """
    sr = StepResult(
        step_id="step-1",
        step_name="Extract Data",
        status=StepExecutionStatus.COMPLETED,
        output={"rows": 100},
        duration=1.5,
        error=None
    )

    assert sr.step_id == "step-1", "step_id should be 'step-1'"
    assert sr.step_name == "Extract Data", "step_name should be 'Extract Data'"
    assert sr.status is StepExecutionStatus.COMPLETED, "status should be COMPLETED"
    assert sr.output == {"rows": 100}, "output should match"
    assert sr.duration == 1.5, "duration should be 1.5"
    assert sr.error is None, "error should be None"
    return


def test_step_result_defaults():
    """
        Verify that StepResult defaults output to empty dict, duration to 0.0,
        and error to None.
    """
    sr = StepResult("s1", "Step One", StepExecutionStatus.PENDING)

    assert sr.output == {}, "Default output should be empty dict"
    assert sr.duration == 0.0, "Default duration should be 0.0"
    assert sr.error is None, "Default error should be None"
    return


def test_step_result_is_success_true_for_completed():
    """
        Verify that is_success returns True when status is COMPLETED.
    """
    sr = StepResult("s1", "Step", StepExecutionStatus.COMPLETED)

    assert sr.is_success is True, "is_success should be True for COMPLETED"
    return


def test_step_result_is_success_false_for_failed():
    """
        Verify that is_success returns False when status is FAILED.
    """
    sr = StepResult("s1", "Step", StepExecutionStatus.FAILED, error="timeout")

    assert sr.is_success is False, "is_success should be False for FAILED"
    return


def test_step_result_is_success_false_for_other_statuses():
    """
        Verify that is_success returns False for non-COMPLETED statuses.
    """
    non_completed = [
        StepExecutionStatus.PENDING,
        StepExecutionStatus.RUNNING,
        StepExecutionStatus.SKIPPED,
        StepExecutionStatus.PENDING_APPROVAL,
        StepExecutionStatus.CANCELLED,
    ]

    for status in non_completed:
        sr = StepResult("s1", "Step", status)
        assert sr.is_success is False, "is_success should be False for {}".format(status.value)

    return


def test_step_result_as_dict():
    """
        Verify that as_dict returns a dictionary with status as string value.
    """
    sr = StepResult("s1", "Step One", StepExecutionStatus.COMPLETED,
                     output={"key": "val"}, duration=2.0, error=None)
    d = sr.as_dict()

    assert d["step_id"] == "s1", "as_dict step_id should be 's1'"
    assert d["step_name"] == "Step One", "as_dict step_name should be 'Step One'"
    assert d["status"] == "COMPLETED", "as_dict status should be string 'COMPLETED'"
    assert d["output"] == {"key": "val"}, "as_dict output should match"
    assert d["duration"] == 2.0, "as_dict duration should be 2.0"
    assert d["error"] is None, "as_dict error should be None"
    return


def test_step_result_to_json_from_json_roundtrip():
    """
        Verify that to_json and from_json produce an equivalent StepResult.
    """
    original = StepResult(
        step_id="transform",
        step_name="Transform Data",
        status=StepExecutionStatus.FAILED,
        output={"partial": True},
        duration=3.14,
        error="connection lost"
    )

    json_str = original.to_json()
    restored = StepResult.from_json(json_str)

    assert restored.step_id == original.step_id, "step_id should match after roundtrip"
    assert restored.step_name == original.step_name, "step_name should match after roundtrip"
    assert restored.status is original.status, "status should match after roundtrip"
    assert restored.output == original.output, "output should match after roundtrip"
    assert restored.duration == original.duration, "duration should match after roundtrip"
    assert restored.error == original.error, "error should match after roundtrip"
    return


def test_step_result_repr():
    """
        Verify that __repr__ includes class name, step_id, and status.
    """
    sr = StepResult("s1", "Step", StepExecutionStatus.COMPLETED)
    repr_str = repr(sr)

    assert "StepResult" in repr_str, "repr should contain class name"
    assert "s1" in repr_str, "repr should contain step_id"
    assert "COMPLETED" in repr_str, "repr should contain status value"
    return


def test_step_result_str():
    """
        Verify that __str__ includes step name, status, and duration.
    """
    sr = StepResult("s1", "My Step", StepExecutionStatus.RUNNING, duration=0.5)
    str_val = str(sr)

    assert "My Step" in str_val, "str should contain step name"
    assert "RUNNING" in str_val, "str should contain status"
    assert "0.500" in str_val, "str should contain formatted duration"
    return


# =========================================================================
# WorkflowResult tests (Requirements 6.1-6.8)
# =========================================================================

def test_workflow_result_construction_and_properties():
    """
        Verify that WorkflowResult stores all fields and exposes them
        as read-only properties.
    """
    sr1 = StepResult("s1", "Step 1", StepExecutionStatus.COMPLETED, output={"a": 1})
    sr2 = StepResult("s2", "Step 2", StepExecutionStatus.COMPLETED, output={"b": 2})

    wr = WorkflowResult(
        workflow_name="my-workflow",
        status=WorkflowExecutionStatus.COMPLETED,
        step_results=[sr1, sr2],
        final_output={"result": "done"},
        duration=5.0,
        error=None
    )

    assert wr.workflow_name == "my-workflow", "workflow_name should be 'my-workflow'"
    assert wr.status is WorkflowExecutionStatus.COMPLETED, "status should be COMPLETED"
    assert len(wr.step_results) == 2, "step_results should have 2 entries"
    assert wr.final_output == {"result": "done"}, "final_output should match"
    assert wr.duration == 5.0, "duration should be 5.0"
    assert wr.error is None, "error should be None"
    return


def test_workflow_result_defaults():
    """
        Verify that WorkflowResult defaults step_results to empty list,
        final_output to empty dict, duration to 0.0, and error to None.
    """
    wr = WorkflowResult("wf", WorkflowExecutionStatus.RUNNING)

    assert wr.step_results == [], "Default step_results should be empty list"
    assert wr.final_output == {}, "Default final_output should be empty dict"
    assert wr.duration == 0.0, "Default duration should be 0.0"
    assert wr.error is None, "Default error should be None"
    return


def test_workflow_result_is_success_true_for_completed():
    """
        Verify that is_success returns True when status is COMPLETED.
    """
    wr = WorkflowResult("wf", WorkflowExecutionStatus.COMPLETED)

    assert wr.is_success is True, "is_success should be True for COMPLETED"
    return


def test_workflow_result_is_success_false_for_failed():
    """
        Verify that is_success returns False when status is FAILED.
    """
    wr = WorkflowResult("wf", WorkflowExecutionStatus.FAILED, error="step failed")

    assert wr.is_success is False, "is_success should be False for FAILED"
    return


def test_workflow_result_is_success_false_for_other_statuses():
    """
        Verify that is_success returns False for non-COMPLETED statuses.
    """
    non_completed = [
        WorkflowExecutionStatus.RUNNING,
        WorkflowExecutionStatus.PAUSED,
        WorkflowExecutionStatus.CANCELLED,
    ]

    for status in non_completed:
        wr = WorkflowResult("wf", status)
        assert wr.is_success is False, "is_success should be False for {}".format(status.value)

    return


def test_workflow_result_get_step_result_found():
    """
        Verify that get_step_result returns the matching StepResult.
    """
    sr1 = StepResult("s1", "Step 1", StepExecutionStatus.COMPLETED)
    sr2 = StepResult("s2", "Step 2", StepExecutionStatus.FAILED, error="err")

    wr = WorkflowResult("wf", WorkflowExecutionStatus.FAILED, step_results=[sr1, sr2])
    found = wr.get_step_result("s2")

    assert found is not None, "get_step_result should find 's2'"
    assert found.step_id == "s2", "Found step_id should be 's2'"
    assert found.step_name == "Step 2", "Found step_name should be 'Step 2'"
    return


def test_workflow_result_get_step_result_not_found():
    """
        Verify that get_step_result returns None when step id is not found.
    """
    sr1 = StepResult("s1", "Step 1", StepExecutionStatus.COMPLETED)
    wr = WorkflowResult("wf", WorkflowExecutionStatus.COMPLETED, step_results=[sr1])
    found = wr.get_step_result("nonexistent")

    assert found is None, "get_step_result should return None for unknown step id"
    return


def test_workflow_result_get_step_result_empty_list():
    """
        Verify that get_step_result returns None when step_results is empty.
    """
    wr = WorkflowResult("wf", WorkflowExecutionStatus.COMPLETED)
    found = wr.get_step_result("any")

    assert found is None, "get_step_result should return None when no step results"
    return


def test_workflow_result_as_dict():
    """
        Verify that as_dict returns status as string and step_results
        as list of dicts.
    """
    sr = StepResult("s1", "Step 1", StepExecutionStatus.COMPLETED,
                     output={"x": 1}, duration=1.0)
    wr = WorkflowResult("pipeline", WorkflowExecutionStatus.COMPLETED,
                         step_results=[sr], final_output={"done": True}, duration=2.5)
    d = wr.as_dict()

    assert d["workflow_name"] == "pipeline", "as_dict workflow_name should match"
    assert d["status"] == "COMPLETED", "as_dict status should be string 'COMPLETED'"
    assert len(d["step_results"]) == 1, "as_dict step_results should have 1 entry"
    assert d["step_results"][0]["step_id"] == "s1", "step_results dict should contain step_id"
    assert d["step_results"][0]["status"] == "COMPLETED", "step_results status should be string"
    assert d["final_output"] == {"done": True}, "as_dict final_output should match"
    assert d["duration"] == 2.5, "as_dict duration should be 2.5"
    assert d["error"] is None, "as_dict error should be None"
    return


def test_workflow_result_to_json_from_json_roundtrip():
    """
        Verify that to_json and from_json produce an equivalent WorkflowResult.
    """
    sr1 = StepResult("s1", "Extract", StepExecutionStatus.COMPLETED,
                      output={"rows": 50}, duration=1.0)
    sr2 = StepResult("s2", "Transform", StepExecutionStatus.FAILED,
                      duration=0.5, error="bad data")

    original = WorkflowResult(
        workflow_name="etl-pipeline",
        status=WorkflowExecutionStatus.FAILED,
        step_results=[sr1, sr2],
        final_output={"partial": True},
        duration=1.5,
        error="step s2 failed"
    )

    json_str = original.to_json()
    restored = WorkflowResult.from_json(json_str)

    assert restored.workflow_name == original.workflow_name, "workflow_name should match after roundtrip"
    assert restored.status is original.status, "status should match after roundtrip"
    assert len(restored.step_results) == 2, "step_results count should match after roundtrip"
    assert restored.step_results[0].step_id == "s1", "First step_result step_id should match"
    assert restored.step_results[1].step_id == "s2", "Second step_result step_id should match"
    assert restored.step_results[1].error == "bad data", "Second step_result error should match"
    assert restored.final_output == original.final_output, "final_output should match after roundtrip"
    assert restored.duration == original.duration, "duration should match after roundtrip"
    assert restored.error == original.error, "error should match after roundtrip"
    return


def test_workflow_result_repr():
    """
        Verify that __repr__ includes class name, workflow name, and status.
    """
    wr = WorkflowResult("my-wf", WorkflowExecutionStatus.COMPLETED)
    repr_str = repr(wr)

    assert "WorkflowResult" in repr_str, "repr should contain class name"
    assert "my-wf" in repr_str, "repr should contain workflow name"
    assert "COMPLETED" in repr_str, "repr should contain status value"
    return


def test_workflow_result_str():
    """
        Verify that __str__ includes workflow name, status, step count, and duration.
    """
    sr = StepResult("s1", "Step", StepExecutionStatus.COMPLETED)
    wr = WorkflowResult("pipeline", WorkflowExecutionStatus.COMPLETED,
                         step_results=[sr], duration=3.14)
    str_val = str(wr)

    assert "pipeline" in str_val, "str should contain workflow name"
    assert "COMPLETED" in str_val, "str should contain status"
    assert "1" in str_val, "str should contain step count"
    assert "3.140" in str_val, "str should contain formatted duration"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
