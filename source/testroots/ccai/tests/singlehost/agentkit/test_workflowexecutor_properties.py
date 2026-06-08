"""
    Property-based tests for the ccai.agentkit.workflowexecutor module.

    Uses ccai.testbase.properties to verify:
    - Property 12: Topological Execution Order

    **Validates: Requirement 4 AC 2**

    .. module:: ccai.tests.singlehost.agentkit.test_workflowexecutor_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for WorkflowExecutor topological execution order.
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.workflowcontext import WorkflowContext
from ccai.agentkit.workflowdefinition import WorkflowDefinition
from ccai.agentkit.workflowedge import WorkflowEdge
from ccai.agentkit.workflowexecutor import WorkflowExecutor
from ccai.agentkit.workflowstep import WorkflowStep


# ---------------------------------------------------------------------------
# Minimal concrete WorkflowStep that records execution order
# ---------------------------------------------------------------------------

_global_execution_log = []


class _OrderRecordingStep(WorkflowStep):
    """
        Concrete WorkflowStep that appends its step_id to a shared
        execution log list when executed, allowing verification of
        execution order.
    """

    def __init__(self, step_id: str, name: str, execution_log: list,
                 **kwargs) -> None:
        super().__init__(step_id=step_id, name=name, step_type="test",
                         **kwargs)
        self._execution_log = execution_log
        return

    def execute(self, context) -> StepResult:
        self._execution_log.append(self.step_id)
        rtnval = StepResult(
            step_id=self.step_id,
            step_name=self.name,
            status=StepExecutionStatus.COMPLETED,
            output={}
        )
        return rtnval


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@composite
def valid_dag_for_execution(draw, min_steps=2, max_steps=6):
    """
        Generates a valid DAG suitable for execution testing: a list
        of unique step IDs and edges forming an acyclic, fully-reachable
        graph from step 0.

        Steps are assigned indices 0..n-1. Edges only go from lower
        index to higher index, guaranteeing acyclicity. Every step
        (except the start) has at least one incoming edge from a
        lower-indexed step, guaranteeing reachability.

        Returns (step_ids, edge_tuples) where edge_tuples is a list
        of (source_id, target_id) pairs.
    """
    num_steps = draw(st.integers(min_steps, max_steps))

    step_ids = []
    for i in range(num_steps):
        sid = "s{}".format(i)
        step_ids.append(sid)

    edges = []

    # Ensure every step (except start) is reachable from a
    # lower-indexed step.
    for i in range(1, num_steps):
        source_idx = draw(st.integers(0, i - 1))
        edges.append((step_ids[source_idx], step_ids[i]))

    # Add some extra forward edges for variety.
    extra_count = draw(st.integers(0, min(num_steps, 4)))
    for _ in range(extra_count):
        src_idx = draw(st.integers(0, num_steps - 2))
        tgt_idx = draw(st.integers(src_idx + 1, num_steps - 1))
        pair = (step_ids[src_idx], step_ids[tgt_idx])
        if pair not in edges:
            edges.append(pair)

    return step_ids, edges


# ---------------------------------------------------------------------------
# Property 12: Topological Execution Order
# ---------------------------------------------------------------------------

@given(
    dag_data=valid_dag_for_execution(min_steps=2, max_steps=6),
    constraints={"max_examples": 80},
)
def test_topological_execution_order(dag_data) -> None:
    """
        **Validates: Requirement 4 AC 2**

        For all valid WorkflowDefinition instances, the WorkflowExecutor
        shall execute steps in an order such that for every edge (A -> B),
        step A completes before step B begins. No step shall execute
        before all its incoming edge sources have completed.
    """
    step_ids, edge_tuples = dag_data

    execution_log = []

    steps = {}
    for sid in step_ids:
        steps[sid] = _OrderRecordingStep(
            step_id=sid,
            name="Step {}".format(sid),
            execution_log=execution_log
        )

    edges = []
    for src, tgt in edge_tuples:
        edges.append(WorkflowEdge(source_step_id=src, target_step_id=tgt))

    start_step_id = step_ids[0]

    workflow = WorkflowDefinition(
        name="topo-test",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id=start_step_id
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    # Verify the workflow completed successfully.
    testbase.assert_true(result.is_success,
        "Workflow should complete successfully, got status={}, "
        "error={}".format(result.status, result.error))

    # Verify all steps were executed.
    testbase.assert_equal(len(execution_log), len(step_ids),
        "All {} steps should have been executed, but only {} were: "
        "log={}, steps={}".format(
            len(step_ids), len(execution_log),
            execution_log, step_ids))

    # Build a position map: step_id -> index in execution_log.
    position = {}
    for idx, sid in enumerate(execution_log):
        position[sid] = idx

    # For every edge (A -> B), verify A was executed before B.
    for src, tgt in edge_tuples:
        src_pos = position.get(src)
        tgt_pos = position.get(tgt)

        testbase.assert_true(src_pos is not None,
            "Source step '{}' should appear in execution log: "
            "log={}".format(src, execution_log))

        testbase.assert_true(tgt_pos is not None,
            "Target step '{}' should appear in execution log: "
            "log={}".format(tgt, execution_log))

        testbase.assert_true(src_pos < tgt_pos,
            "For edge ({} -> {}), source should execute before "
            "target. Source position={}, target position={}. "
            "Execution log={}, edges={}".format(
                src, tgt, src_pos, tgt_pos,
                execution_log, edge_tuples))

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
