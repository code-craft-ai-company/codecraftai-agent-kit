"""
    Unit tests for the WorkflowExecutor class in the Workflow &
    Orchestration feature.

    Tests linear workflow execution, conditional branching, parallel
    branch execution, parallel branch failure, checkpoint saving,
    resume from checkpoint, retry policy on step failure, and
    WorkflowResult status for completed and failed workflows.

    Uses testbase mocking for CheckpointManager.

    Requirements: 4.1-4.13, 8.6-8.9, 10.1-10.6

    .. module:: ccai.tests.singlehost.agentkit.test_workflowexecutor
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for WorkflowExecutor.
"""

import time

from ccai.agentkit.parallelbranch import ParallelBranch
from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.workflowcheckpoint import WorkflowCheckpoint
from ccai.agentkit.workflowconfiguration import WorkflowConfiguration
from ccai.agentkit.workflowdefinition import WorkflowDefinition
from ccai.agentkit.workflowedge import WorkflowEdge
from ccai.agentkit.workflowerrors import WorkflowCheckpointError
from ccai.agentkit.workflowerrors import WorkflowDefinitionError
from ccai.agentkit.workflowerrors import WorkflowExecutionError
from ccai.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from ccai.agentkit.workflowexecutor import WorkflowExecutor
from ccai.agentkit.workflowstep import WorkflowStep
from ccai.testbase.mocking import Mock


# =========================================================================
# Helper: concrete WorkflowStep that records execution order
# =========================================================================

class _RecordingStep(WorkflowStep):
    """
        Records execution order for testing. Appends step_id to a
        shared execution log list when executed.
    """

    def __init__(self, step_id, name, execution_log=None, output=None,
                 should_fail=False, delay=0.0, **kwargs):
        super().__init__(step_id=step_id, name=name, step_type="test",
                         **kwargs)
        self._execution_log = execution_log if execution_log is not None else []
        self._output = output or {}
        self._should_fail = should_fail
        self._delay = delay
        return

    def execute(self, context):
        self._execution_log.append(self.step_id)
        if self._delay > 0.0:
            time.sleep(self._delay)
        if self._should_fail:
            rtnval = StepResult(
                step_id=self.step_id,
                step_name=self.name,
                status=StepExecutionStatus.FAILED,
                error="Intentional failure"
            )
            return rtnval
        rtnval = StepResult(
            step_id=self.step_id,
            step_name=self.name,
            status=StepExecutionStatus.COMPLETED,
            output=self._output
        )
        return rtnval


# =========================================================================
# Helper: simple retry policy
# =========================================================================

class _SimpleRetryPolicy:
    """
        Simple retry policy for testing. Retries up to max_retries
        times with zero delay.
    """

    def __init__(self, max_retries=2, delay=0.0):
        self.max_retries = max_retries
        self._delay = delay
        return

    def should_retry(self, error, attempt):
        rtnval = attempt < self.max_retries
        return rtnval

    def get_delay(self, attempt):
        return self._delay


# =========================================================================
# Helper: build a simple linear workflow A -> B -> C
# =========================================================================

def _build_linear_workflow(execution_log, outputs=None, delay=0.0):
    """
        Builds a linear workflow: step_a -> step_b -> step_c.

        :param execution_log: Shared list for recording execution order.
        :param outputs: Optional dict mapping step_id to output dict.
        :param delay: Optional number of seconds step_a sleeps while executing.

        :returns: A WorkflowDefinition.
    """
    if outputs is None:
        outputs = {}

    step_a = _RecordingStep(
        step_id="step_a", name="Step A",
        execution_log=execution_log,
        output=outputs.get("step_a", {"a_result": "done"}),
        delay=delay
    )
    step_b = _RecordingStep(
        step_id="step_b", name="Step B",
        execution_log=execution_log,
        output=outputs.get("step_b", {"b_result": "done"})
    )
    step_c = _RecordingStep(
        step_id="step_c", name="Step C",
        execution_log=execution_log,
        output=outputs.get("step_c", {"c_result": "done"})
    )

    steps = {
        "step_a": step_a,
        "step_b": step_b,
        "step_c": step_c,
    }

    edges = [
        WorkflowEdge(source_step_id="step_a", target_step_id="step_b"),
        WorkflowEdge(source_step_id="step_b", target_step_id="step_c"),
    ]

    workflow = WorkflowDefinition(
        name="linear-workflow",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id="step_a"
    )
    return workflow


# =========================================================================
# Test: Linear workflow execution (A -> B -> C)
# Requirements: 4.1, 4.2, 4.3, 4.6
# =========================================================================

def test_linear_workflow_executes_in_order():
    """
        Verify that a linear workflow A -> B -> C executes steps
        in the correct order and returns a COMPLETED result.
    """
    execution_log = []
    workflow = _build_linear_workflow(execution_log)

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={"key": "value"})

    assert result.status == WorkflowExecutionStatus.COMPLETED, \
        "Workflow should complete successfully, got {}".format(result.status)
    assert result.is_success is True, \
        "is_success should be True for completed workflow"
    assert execution_log == ["step_a", "step_b", "step_c"], \
        "Steps should execute in order A, B, C, got {}".format(execution_log)
    assert len(result.step_results) == 3, \
        "Should have 3 step results, got {}".format(len(result.step_results))
    return


def test_linear_workflow_stores_step_outputs_in_context():
    """
        Verify that step outputs are stored in the WorkflowContext
        and available in the final result.
    """
    execution_log = []
    workflow = _build_linear_workflow(
        execution_log,
        outputs={
            "step_a": {"a_out": 1},
            "step_b": {"b_out": 2},
            "step_c": {"c_out": 3},
        }
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.is_success is True, \
        "Workflow should complete successfully"

    # The final output should contain the terminal step's output.
    assert "c_out" in result.final_output, \
        "Final output should contain terminal step output, got {}".format(
            result.final_output)
    assert result.final_output["c_out"] == 3, \
        "Terminal step output value should be 3"
    return


# =========================================================================
# Helper: build a workflow of recording steps from step ids and edges
# =========================================================================

def _build_recording_workflow(name, execution_log, step_ids, edges,
                              start_step_id, outputs=None,
                              parallel_branches=None):
    """
        Builds a WorkflowDefinition whose steps are _RecordingStep
        instances that append their step_id to the execution log.

        :param name: The workflow name.
        :param execution_log: Shared list for recording execution order.
        :param step_ids: The identifiers of the steps to create.
        :param edges: The list of WorkflowEdge objects.
        :param start_step_id: The identifier of the start step.
        :param outputs: Optional dict mapping step_id to output dict.
        :param parallel_branches: Optional list of ParallelBranch objects.

        :returns: A WorkflowDefinition.
    """
    if outputs is None:
        outputs = {}

    steps = {}
    for step_id in step_ids:
        default_output = {"{}_done".format(step_id): True}
        step_output = outputs.get(step_id, default_output)
        steps[step_id] = _RecordingStep(
            step_id=step_id, name=step_id,
            execution_log=execution_log,
            output=step_output
        )

    workflow = WorkflowDefinition(
        name=name,
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id=start_step_id,
        parallel_branches=parallel_branches
    )
    return workflow


def _get_step_status(result, step_id):
    """
        Returns the StepExecutionStatus recorded for a step in a
        WorkflowResult, or None when the result has no entry for it.

        :param result: The WorkflowResult to inspect.
        :param step_id: The step identifier to look up.

        :returns: The StepExecutionStatus or None.
    """
    step_result = result.get_step_result(step_id)

    if step_result is None:
        return None

    status = step_result.status
    return status


def _build_level_routing_workflow(execution_log, include_default=False,
                                  include_unconditional=False):
    """
        Builds a workflow whose start step routes on the 'level'
        workflow input:

        - start -> high_path when inputs.level == 'high' (priority 1)
        - start -> low_path when inputs.level == 'low' (priority 2)
        - start -> default_path with condition 'True' (priority 99),
          when include_default is True
        - start -> audit unconditionally, when include_unconditional
          is True

        :param execution_log: Shared list for recording execution order.
        :param include_default: Whether to add the default edge.
        :param include_unconditional: Whether to add the unconditional
            edge to the audit step.

        :returns: A WorkflowDefinition.
    """
    step_ids = ["start", "high_path", "low_path"]

    # The edges are declared in reverse priority order so the test also
    # verifies that the executor orders them by priority.
    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="low_path",
            condition="inputs.level == 'low'",
            priority=2
        ),
        WorkflowEdge(
            source_step_id="start",
            target_step_id="high_path",
            condition="inputs.level == 'high'",
            priority=1
        ),
    ]

    if include_default is True:
        step_ids.append("default_path")
        edges.insert(0, WorkflowEdge(
            source_step_id="start",
            target_step_id="default_path",
            condition="True",
            priority=99
        ))

    if include_unconditional is True:
        step_ids.append("audit")
        edges.append(WorkflowEdge(
            source_step_id="start",
            target_step_id="audit"
        ))

    workflow = _build_recording_workflow(
        name="level-routing-workflow",
        execution_log=execution_log,
        step_ids=step_ids,
        edges=edges,
        start_step_id="start"
    )
    return workflow


# =========================================================================
# Test: Conditional branching
# Requirements: 3.3, 3.4, 4.4, 4.5
# =========================================================================

def test_conditional_branching_evaluates_priority_order():
    """
        Verify that when a step has multiple outgoing conditional
        edges, the executor evaluates them in ascending priority
        order and traverses only the first edge whose condition is
        True. The target of the edge that is not traversed is not
        executed and is reported as SKIPPED.
    """
    execution_log = []

    step_start = _RecordingStep(
        step_id="start", name="Start",
        execution_log=execution_log,
        output={"status": "high"}
    )
    step_high = _RecordingStep(
        step_id="high_path", name="High Path",
        execution_log=execution_log,
        output={"path": "high"}
    )
    step_low = _RecordingStep(
        step_id="low_path", name="Low Path",
        execution_log=execution_log,
        output={"path": "low"}
    )

    steps = {
        "start": step_start,
        "high_path": step_high,
        "low_path": step_low,
    }

    # Priority 1 (evaluated first): condition checks for "high"
    # Priority 2 (evaluated second): condition checks for "low"
    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="high_path",
            condition="steps.start.status == 'high'",
            priority=1
        ),
        WorkflowEdge(
            source_step_id="start",
            target_step_id="low_path",
            condition="steps.start.status == 'low'",
            priority=2
        ),
    ]

    workflow = WorkflowDefinition(
        name="conditional-workflow",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id="start"
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.is_success is True, \
        "Workflow should complete successfully, error={}".format(result.error)
    assert execution_log == ["start", "high_path"], \
        "Only start and high_path should execute, got {}".format(execution_log)

    high_status = _get_step_status(result, "high_path")
    assert high_status == StepExecutionStatus.COMPLETED, \
        "high_path should be COMPLETED, got {}".format(high_status)

    low_status = _get_step_status(result, "low_path")
    assert low_status == StepExecutionStatus.SKIPPED, \
        "low_path should be SKIPPED, got {}".format(low_status)

    assert result.final_output == {"path": "high"}, \
        "Final output should only hold the taken branch output, got {}".format(
            result.final_output)
    return


def test_conditional_branching_first_true_edge_by_priority_wins():
    """
        Verify that when more than one condition is True, only the
        edge with the lowest priority value is traversed, regardless
        of the order in which the edges are declared.
    """
    execution_log = []

    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="big_path",
            condition="steps.start.score > 10",
            priority=5
        ),
        WorkflowEdge(
            source_step_id="start",
            target_step_id="medium_path",
            condition="steps.start.score > 5",
            priority=1
        ),
    ]

    workflow = _build_recording_workflow(
        name="first-true-workflow",
        execution_log=execution_log,
        step_ids=["start", "big_path", "medium_path"],
        edges=edges,
        start_step_id="start",
        outputs={"start": {"score": 20}}
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.is_success is True, \
        "Workflow should complete successfully, error={}".format(result.error)
    assert execution_log == ["start", "medium_path"], \
        "Only the priority 1 edge should be traversed, got {}".format(
            execution_log)

    big_status = _get_step_status(result, "big_path")
    assert big_status == StepExecutionStatus.SKIPPED, \
        "big_path should be SKIPPED, got {}".format(big_status)
    return


def test_conditional_branching_no_match_skips_conditional_targets():
    """
        Verify that when no conditional edge matches, none of the
        conditional targets is executed, the steps after them are
        skipped as well, and the workflow still completes.
    """
    execution_log = []

    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="high_path",
            condition="inputs.level == 'high'",
            priority=1
        ),
        WorkflowEdge(
            source_step_id="start",
            target_step_id="low_path",
            condition="inputs.level == 'low'",
            priority=2
        ),
        WorkflowEdge(
            source_step_id="high_path",
            target_step_id="high_followup"
        ),
    ]

    workflow = _build_recording_workflow(
        name="no-match-workflow",
        execution_log=execution_log,
        step_ids=["start", "high_path", "low_path", "high_followup"],
        edges=edges,
        start_step_id="start"
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={"level": "medium"})

    assert result.status == WorkflowExecutionStatus.COMPLETED, \
        "Workflow should complete when no condition matches, got {} ({})".format(
            result.status, result.error)
    assert execution_log == ["start"], \
        "Only the start step should execute, got {}".format(execution_log)

    for skipped_id in ["high_path", "low_path", "high_followup"]:
        skipped_status = _get_step_status(result, skipped_id)
        assert skipped_status == StepExecutionStatus.SKIPPED, \
            "{} should be SKIPPED, got {}".format(skipped_id, skipped_status)

    assert len(result.step_results) == 4, \
        "Every step should have a result, got {}".format(
            len(result.step_results))
    assert result.final_output == {}, \
        "No terminal step ran, so the final output should be empty, got {}".format(
            result.final_output)
    return


def test_conditional_branching_default_edge_taken_when_no_condition_matches():
    """
        Verify that a conditional edge with the condition 'True' and
        the largest priority value acts as the default branch: it is
        traversed when no other condition matches and is not
        evaluated when an earlier condition matches.
    """
    execution_log = []
    workflow = _build_level_routing_workflow(
        execution_log, include_default=True
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={"level": "medium"})

    assert result.is_success is True, \
        "Workflow should complete successfully, error={}".format(result.error)
    assert execution_log == ["start", "default_path"], \
        "Only the default branch should run, got {}".format(execution_log)

    del execution_log[:]
    result = executor.execute(workflow=workflow, inputs={"level": "low"})

    assert result.is_success is True, \
        "Workflow should complete successfully, error={}".format(result.error)
    assert execution_log == ["start", "low_path"], \
        "The matching branch should run instead of the default, got {}".format(
            execution_log)

    default_status = _get_step_status(result, "default_path")
    assert default_status == StepExecutionStatus.SKIPPED, \
        "default_path should be SKIPPED, got {}".format(default_status)
    return


def test_unconditional_edge_traversed_alongside_conditional_edges():
    """
        Verify that an unconditional edge is always traversed, even
        when it leaves a step that also has conditional edges, while
        only the first matching conditional edge is traversed.
    """
    execution_log = []
    workflow = _build_level_routing_workflow(
        execution_log, include_unconditional=True
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={"level": "low"})

    assert result.is_success is True, \
        "Workflow should complete successfully, error={}".format(result.error)

    executed = sorted(execution_log)
    assert executed == ["audit", "low_path", "start"], \
        "start, audit and low_path should execute, got {}".format(execution_log)

    high_status = _get_step_status(result, "high_path")
    assert high_status == StepExecutionStatus.SKIPPED, \
        "high_path should be SKIPPED, got {}".format(high_status)

    del execution_log[:]
    result = executor.execute(workflow=workflow, inputs={"level": "none"})

    assert result.is_success is True, \
        "Workflow should complete when no condition matches, error={}".format(result.error)

    assert execution_log == ["start", "audit"], \
        "The unconditional edge should be traversed when no condition " \
        "matches, got {}".format(execution_log)
    return


def test_conditional_branches_rejoin_at_merge_step():
    """
        Verify that a merge step reached from two conditional
        branches runs when the branch that was taken completes, even
        though the other branch was skipped.
    """
    execution_log = []

    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="high_path",
            condition="inputs.level == 'high'",
            priority=1
        ),
        WorkflowEdge(
            source_step_id="start",
            target_step_id="low_path",
            condition="inputs.level == 'low'",
            priority=2
        ),
        WorkflowEdge(source_step_id="high_path", target_step_id="merge"),
        WorkflowEdge(source_step_id="low_path", target_step_id="merge"),
    ]

    workflow = _build_recording_workflow(
        name="rejoin-workflow",
        execution_log=execution_log,
        step_ids=["start", "high_path", "low_path", "merge"],
        edges=edges,
        start_step_id="start",
        outputs={"merge": {"merged": True}}
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={"level": "high"})

    assert result.is_success is True, \
        "Workflow should complete successfully, error={}".format(result.error)
    assert execution_log == ["start", "high_path", "merge"], \
        "start, high_path and merge should execute, got {}".format(
            execution_log)

    low_status = _get_step_status(result, "low_path")
    assert low_status == StepExecutionStatus.SKIPPED, \
        "low_path should be SKIPPED, got {}".format(low_status)
    assert result.final_output == {"merged": True}, \
        "Final output should come from the merge step, got {}".format(
            result.final_output)
    return


def test_parallel_branch_with_untraversed_conditional_start_is_skipped():
    """
        Verify that a parallel branch whose start edge from the fork
        has a condition that is not met is skipped, while the other
        branch and the join step still run.
    """
    execution_log = []

    edges = [
        WorkflowEdge(
            source_step_id="fork",
            target_step_id="branch1",
            condition="inputs.run_branch1 == True",
            priority=1
        ),
        WorkflowEdge(source_step_id="fork", target_step_id="branch2"),
        WorkflowEdge(source_step_id="branch1", target_step_id="branch1_tail"),
        WorkflowEdge(source_step_id="branch1_tail", target_step_id="join"),
        WorkflowEdge(source_step_id="branch2", target_step_id="join"),
    ]

    workflow = _build_recording_workflow(
        name="parallel-conditional-workflow",
        execution_log=execution_log,
        step_ids=["fork", "branch1", "branch1_tail", "branch2", "join"],
        edges=edges,
        start_step_id="fork",
        parallel_branches=[
            ParallelBranch(fork_step_id="fork", join_step_id="join")
        ]
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={"run_branch1": False})

    assert result.is_success is True, \
        "Workflow should complete successfully, error={}".format(result.error)
    assert execution_log == ["fork", "branch2", "join"], \
        "fork, branch2 and join should execute, got {}".format(execution_log)

    for skipped_id in ["branch1", "branch1_tail"]:
        skipped_status = _get_step_status(result, skipped_id)
        assert skipped_status == StepExecutionStatus.SKIPPED, \
            "{} should be SKIPPED, got {}".format(skipped_id, skipped_status)
    return


def test_resume_follows_conditional_branch_from_checkpoint():
    """
        Verify that resuming a workflow re-derives the conditional
        branch taken from a step completed before the checkpoint and
        only executes the steps on that branch.
    """
    execution_log = []

    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="high_path",
            condition="steps.start.status == 'high'",
            priority=1
        ),
        WorkflowEdge(
            source_step_id="start",
            target_step_id="low_path",
            condition="steps.start.status == 'low'",
            priority=2
        ),
    ]

    workflow = _build_recording_workflow(
        name="resume-conditional-workflow",
        execution_log=execution_log,
        step_ids=["start", "high_path", "low_path"],
        edges=edges,
        start_step_id="start"
    )

    checkpoint = WorkflowCheckpoint(
        workflow_name="resume-conditional-workflow",
        execution_id="exec-cond-1",
        completed_step_ids={"start"},
        context_state={
            "inputs": {},
            "step_outputs": {"start": {"status": "low"}},
            "metadata": {}
        },
        current_step_id="start"
    )

    mock_cm = Mock()
    mock_cm.configure(recursive=True)
    cm_ctx = mock_cm.mock_context()
    cm_ctx.mock_method("load_checkpoint", return_value=checkpoint)
    cm_ctx.mock_method("save_checkpoint", return_value=None)

    executor = WorkflowExecutor(checkpoint_manager=mock_cm)
    result = executor.resume(execution_id="exec-cond-1", workflow=workflow)

    assert result.is_success is True, \
        "Resumed workflow should complete successfully, error={}".format(
            result.error)
    assert execution_log == ["low_path"], \
        "Only low_path should execute on resume, got {}".format(execution_log)

    high_status = _get_step_status(result, "high_path")
    assert high_status == StepExecutionStatus.SKIPPED, \
        "high_path should be SKIPPED, got {}".format(high_status)
    return


def test_invalid_edge_condition_raises_definition_error():
    """
        Verify that an edge condition using a disallowed construct
        raises a WorkflowDefinitionError that names the workflow and
        the edge instead of silently traversing the edge.
    """
    execution_log = []

    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="next_step",
            condition="len(inputs.items) > 1",
            priority=1
        ),
    ]

    workflow = _build_recording_workflow(
        name="invalid-condition-workflow",
        execution_log=execution_log,
        step_ids=["start", "next_step"],
        edges=edges,
        start_step_id="start"
    )

    executor = WorkflowExecutor()

    caught = None
    try:
        executor.execute(workflow=workflow, inputs={"items": [1, 2]})
    except WorkflowDefinitionError as def_err:
        caught = def_err

    assert caught is not None, \
        "An invalid edge condition should raise WorkflowDefinitionError"
    assert caught.workflow_name == "invalid-condition-workflow", \
        "The error should name the workflow, got {}".format(
            caught.workflow_name)
    assert "'start' -> 'next_step'" in caught.detail, \
        "The error should name the edge, got {}".format(caught.detail)
    assert "next_step" not in execution_log, \
        "The edge target should not execute, got {}".format(execution_log)
    return


def test_edge_condition_referencing_unexecuted_step_raises_execution_error():
    """
        Verify that an edge condition referencing a step that has not
        been executed raises a WorkflowExecutionError that names the
        workflow and the step whose edge was being evaluated.
    """
    execution_log = []

    edges = [
        WorkflowEdge(
            source_step_id="start",
            target_step_id="next_step",
            condition="steps.next_step.ready == True",
            priority=1
        ),
    ]

    workflow = _build_recording_workflow(
        name="unresolved-condition-workflow",
        execution_log=execution_log,
        step_ids=["start", "next_step"],
        edges=edges,
        start_step_id="start"
    )

    executor = WorkflowExecutor()

    caught = None
    try:
        executor.execute(workflow=workflow, inputs={})
    except WorkflowExecutionError as exec_err:
        caught = exec_err

    assert caught is not None, \
        "An unresolved step reference should raise WorkflowExecutionError"
    assert caught.workflow_name == "unresolved-condition-workflow", \
        "The error should name the workflow, got {}".format(
            caught.workflow_name)
    assert caught.step_id == "start", \
        "The error should name the source step, got {}".format(caught.step_id)
    return


# =========================================================================
# Test: Parallel branch execution
# Requirements: 8.6, 8.7
# =========================================================================

def test_parallel_branch_execution_fork_and_join():
    """
        Verify that parallel branches execute concurrently from a
        fork step and converge at a join step.
    """
    execution_log = []

    step_fork = _RecordingStep(
        step_id="fork", name="Fork",
        execution_log=execution_log,
        output={"forked": True}
    )
    step_b1 = _RecordingStep(
        step_id="branch1", name="Branch 1",
        execution_log=execution_log,
        output={"b1": "done"}
    )
    step_b2 = _RecordingStep(
        step_id="branch2", name="Branch 2",
        execution_log=execution_log,
        output={"b2": "done"}
    )
    step_join = _RecordingStep(
        step_id="join", name="Join",
        execution_log=execution_log,
        output={"joined": True}
    )

    steps = {
        "fork": step_fork,
        "branch1": step_b1,
        "branch2": step_b2,
        "join": step_join,
    }

    edges = [
        WorkflowEdge(source_step_id="fork", target_step_id="branch1"),
        WorkflowEdge(source_step_id="fork", target_step_id="branch2"),
        WorkflowEdge(source_step_id="branch1", target_step_id="join"),
        WorkflowEdge(source_step_id="branch2", target_step_id="join"),
    ]

    parallel_branches = [
        ParallelBranch(fork_step_id="fork", join_step_id="join")
    ]

    workflow = WorkflowDefinition(
        name="parallel-workflow",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id="fork",
        parallel_branches=parallel_branches
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.is_success is True, \
        "Parallel workflow should complete successfully, error={}".format(
            result.error)

    # Fork should execute first.
    assert execution_log[0] == "fork", \
        "Fork step should execute first, got {}".format(execution_log)

    # Both branches should have executed.
    assert "branch1" in execution_log, \
        "Branch 1 should have executed"
    assert "branch2" in execution_log, \
        "Branch 2 should have executed"

    # Join should execute after both branches.
    assert "join" in execution_log, \
        "Join step should have executed"

    fork_pos = execution_log.index("fork")
    join_pos = execution_log.index("join")
    assert fork_pos < join_pos, \
        "Fork should execute before join"
    return


# =========================================================================
# Test: Parallel branch failure cancels remaining branches
# Requirements: 8.8
# =========================================================================

def test_parallel_branch_failure_cancels_remaining():
    """
        Verify that if any branch of a ParallelBranch fails, the
        workflow returns a FAILED result.
    """
    execution_log = []

    step_fork = _RecordingStep(
        step_id="fork", name="Fork",
        execution_log=execution_log,
        output={}
    )
    step_b1 = _RecordingStep(
        step_id="branch1", name="Branch 1",
        execution_log=execution_log,
        should_fail=True
    )
    step_b2 = _RecordingStep(
        step_id="branch2", name="Branch 2",
        execution_log=execution_log,
        output={"b2": "done"}
    )
    step_join = _RecordingStep(
        step_id="join", name="Join",
        execution_log=execution_log,
        output={}
    )

    steps = {
        "fork": step_fork,
        "branch1": step_b1,
        "branch2": step_b2,
        "join": step_join,
    }

    edges = [
        WorkflowEdge(source_step_id="fork", target_step_id="branch1"),
        WorkflowEdge(source_step_id="fork", target_step_id="branch2"),
        WorkflowEdge(source_step_id="branch1", target_step_id="join"),
        WorkflowEdge(source_step_id="branch2", target_step_id="join"),
    ]

    parallel_branches = [
        ParallelBranch(fork_step_id="fork", join_step_id="join")
    ]

    workflow = WorkflowDefinition(
        name="parallel-fail-workflow",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id="fork",
        parallel_branches=parallel_branches
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.status == WorkflowExecutionStatus.FAILED, \
        "Workflow should fail when a parallel branch fails, got {}".format(
            result.status)
    assert result.is_success is False, \
        "is_success should be False for failed workflow"
    return


# =========================================================================
# Test: Checkpoint saving at configured interval
# Requirements: 9.6, 9.7
# =========================================================================

def test_checkpoint_saving_at_configured_interval():
    """
        Verify that the WorkflowExecutor saves checkpoints via the
        CheckpointManager at the configured checkpoint interval.
    """
    execution_log = []
    workflow = _build_linear_workflow(execution_log)

    # Configure checkpoint interval of 1 (save after every step).
    config = WorkflowConfiguration(checkpoint_interval=1)

    # Create a mock checkpoint manager.
    mock_cm = Mock()
    mock_cm.configure(recursive=True)
    ctx = mock_cm.mock_context()

    saved_checkpoints = []

    def save_side_effect(execution_id, context, completed_step_ids,
                         current_step_id):
        saved_checkpoints.append({
            "execution_id": execution_id,
            "completed_step_ids": set(completed_step_ids),
            "current_step_id": current_step_id
        })
        return

    ctx.mock_method("save_checkpoint", side_effect=save_side_effect)

    executor = WorkflowExecutor(
        configuration=config,
        checkpoint_manager=mock_cm
    )
    result = executor.execute(workflow=workflow, inputs={})

    assert result.is_success is True, \
        "Workflow should complete successfully"

    # With checkpoint_interval=1 and 3 steps, we expect checkpoints
    # to be saved after each step.
    assert len(saved_checkpoints) >= 1, \
        "At least one checkpoint should have been saved, got {}".format(
            len(saved_checkpoints))
    return


def test_checkpoint_not_saved_when_no_manager():
    """
        Verify that when no CheckpointManager is configured, the
        executor does not attempt to save checkpoints and completes
        normally.
    """
    execution_log = []
    workflow = _build_linear_workflow(execution_log)

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.is_success is True, \
        "Workflow should complete without checkpoint manager"
    assert execution_log == ["step_a", "step_b", "step_c"], \
        "All steps should execute"
    return


# =========================================================================
# Test: Resume from checkpoint
# Requirements: 10.1, 10.2, 10.3, 10.4
# =========================================================================

def test_resume_from_checkpoint_skips_completed_steps():
    """
        Verify that resuming a workflow from a checkpoint skips
        previously completed steps and continues from the next step.
    """
    execution_log = []

    step_a = _RecordingStep(
        step_id="step_a", name="Step A",
        execution_log=execution_log,
        output={"a_result": "done"}
    )
    step_b = _RecordingStep(
        step_id="step_b", name="Step B",
        execution_log=execution_log,
        output={"b_result": "done"}
    )
    step_c = _RecordingStep(
        step_id="step_c", name="Step C",
        execution_log=execution_log,
        output={"c_result": "done"}
    )

    steps = {
        "step_a": step_a,
        "step_b": step_b,
        "step_c": step_c,
    }

    edges = [
        WorkflowEdge(source_step_id="step_a", target_step_id="step_b"),
        WorkflowEdge(source_step_id="step_b", target_step_id="step_c"),
    ]

    workflow = WorkflowDefinition(
        name="resume-workflow",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id="step_a"
    )

    # Create a checkpoint indicating step_a is already completed.
    checkpoint = WorkflowCheckpoint(
        workflow_name="resume-workflow",
        execution_id="exec-123",
        completed_step_ids={"step_a"},
        context_state={
            "inputs": {"key": "value"},
            "step_outputs": {"step_a": {"a_result": "done"}},
            "metadata": {}
        },
        current_step_id="step_a"
    )

    mock_cm = Mock()
    mock_cm.configure(recursive=True)
    cm_ctx = mock_cm.mock_context()
    cm_ctx.mock_method("load_checkpoint", return_value=checkpoint)
    cm_ctx.mock_method("save_checkpoint", return_value=None)

    executor = WorkflowExecutor(checkpoint_manager=mock_cm)
    result = executor.resume(
        execution_id="exec-123",
        workflow=workflow
    )

    assert result.is_success is True, \
        "Resumed workflow should complete successfully, error={}".format(
            result.error)

    # step_a should NOT have been re-executed.
    assert "step_a" not in execution_log, \
        "step_a should be skipped on resume, got {}".format(execution_log)

    # step_b and step_c should have been executed.
    assert "step_b" in execution_log, \
        "step_b should execute on resume"
    assert "step_c" in execution_log, \
        "step_c should execute on resume"
    return


def test_resume_raises_error_when_no_checkpoint_found():
    """
        Verify that resuming a workflow raises WorkflowCheckpointError
        when no checkpoint exists for the execution identifier.
    """
    execution_log = []
    workflow = _build_linear_workflow(execution_log)

    mock_cm = Mock()
    mock_cm.configure(recursive=True)
    cm_ctx = mock_cm.mock_context()
    cm_ctx.mock_method("load_checkpoint", return_value=None)

    executor = WorkflowExecutor(checkpoint_manager=mock_cm)

    caught = False
    try:
        executor.resume(
            execution_id="nonexistent-exec",
            workflow=workflow
        )
    except WorkflowCheckpointError:
        caught = True

    assert caught is True, \
        "resume should raise WorkflowCheckpointError when no checkpoint found"
    return


def test_resume_raises_error_when_no_checkpoint_manager():
    """
        Verify that resuming a workflow raises WorkflowCheckpointError
        when no checkpoint manager is configured.
    """
    execution_log = []
    workflow = _build_linear_workflow(execution_log)

    executor = WorkflowExecutor()

    caught = False
    try:
        executor.resume(
            execution_id="some-exec",
            workflow=workflow
        )
    except WorkflowCheckpointError:
        caught = True

    assert caught is True, \
        "resume should raise WorkflowCheckpointError when no manager configured"
    return


# =========================================================================
# Test: Retry policy on step failure
# Requirements: 4.8
# =========================================================================

def test_retry_policy_retries_failed_step():
    """
        Verify that when a step has a retry policy and fails, the
        executor retries the step according to the policy.
    """
    execution_log = []
    attempt_count = [0]

    class _FailThenSucceedStep(WorkflowStep):
        """
            Fails on the first attempt, succeeds on the second.
        """

        def __init__(self, step_id, name, execution_log, retry_policy):
            super().__init__(
                step_id=step_id, name=name, step_type="test",
                retry_policy=retry_policy
            )
            self._execution_log = execution_log
            return

        def execute(self, context):
            self._execution_log.append(self.step_id)
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                rtnval = StepResult(
                    step_id=self.step_id,
                    step_name=self.name,
                    status=StepExecutionStatus.FAILED,
                    error="Transient failure"
                )
                return rtnval
            rtnval = StepResult(
                step_id=self.step_id,
                step_name=self.name,
                status=StepExecutionStatus.COMPLETED,
                output={"retried": True}
            )
            return rtnval

    retry_policy = _SimpleRetryPolicy(max_retries=2, delay=0.0)

    step_a = _FailThenSucceedStep(
        step_id="step_a", name="Step A",
        execution_log=execution_log,
        retry_policy=retry_policy
    )
    step_b = _RecordingStep(
        step_id="step_b", name="Step B",
        execution_log=execution_log,
        output={"b_result": "done"}
    )

    steps = {
        "step_a": step_a,
        "step_b": step_b,
    }

    edges = [
        WorkflowEdge(source_step_id="step_a", target_step_id="step_b"),
    ]

    workflow = WorkflowDefinition(
        name="retry-workflow",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id="step_a"
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.is_success is True, \
        "Workflow should succeed after retry, error={}".format(result.error)
    assert attempt_count[0] == 2, \
        "Step should have been attempted 2 times, got {}".format(
            attempt_count[0])
    return


# =========================================================================
# Test: WorkflowResult status for completed and failed workflows
# Requirements: 4.6, 4.7
# =========================================================================

def test_workflow_result_completed_status():
    """
        Verify that a successfully completed workflow returns a
        WorkflowResult with COMPLETED status and correct step results.

        One step sleeps for a short, deterministic delay so the executor's
        monotonic clock is guaranteed to advance even where its resolution
        is coarse (Windows reports roughly 16 ms ticks), which keeps the
        positive-duration check meaningful on every platform.
    """
    execution_log = []
    workflow = _build_linear_workflow(execution_log, delay=0.05)

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.status == WorkflowExecutionStatus.COMPLETED, \
        "Status should be COMPLETED"
    assert result.is_success is True, \
        "is_success should be True"
    assert result.error is None, \
        "error should be None for completed workflow"
    assert result.duration > 0.0, \
        "duration should be positive"
    assert result.workflow_name == "linear-workflow", \
        "workflow_name should match"
    return


def test_workflow_result_failed_status_on_step_failure():
    """
        Verify that when a step fails without a retry policy, the
        workflow returns a FAILED result with error information.
    """
    execution_log = []

    step_a = _RecordingStep(
        step_id="step_a", name="Step A",
        execution_log=execution_log,
        output={"a_result": "done"}
    )
    step_b = _RecordingStep(
        step_id="step_b", name="Step B",
        execution_log=execution_log,
        should_fail=True
    )
    step_c = _RecordingStep(
        step_id="step_c", name="Step C",
        execution_log=execution_log,
        output={}
    )

    steps = {
        "step_a": step_a,
        "step_b": step_b,
        "step_c": step_c,
    }

    edges = [
        WorkflowEdge(source_step_id="step_a", target_step_id="step_b"),
        WorkflowEdge(source_step_id="step_b", target_step_id="step_c"),
    ]

    workflow = WorkflowDefinition(
        name="fail-workflow",
        version="1.0",
        steps=steps,
        edges=edges,
        start_step_id="step_a"
    )

    executor = WorkflowExecutor()
    result = executor.execute(workflow=workflow, inputs={})

    assert result.status == WorkflowExecutionStatus.FAILED, \
        "Status should be FAILED, got {}".format(result.status)
    assert result.is_success is False, \
        "is_success should be False"
    assert result.error is not None, \
        "error should contain failure information"

    # step_c should NOT have executed since step_b failed.
    assert "step_c" not in execution_log, \
        "step_c should not execute after step_b failure"
    return


# =========================================================================
# Test: WorkflowExecutor __repr__ and __str__
# Requirements: 23.21, 23.22
# =========================================================================

def test_executor_repr_includes_class_name():
    """
        Verify that __repr__ includes the class name.
    """
    executor = WorkflowExecutor()
    repr_str = repr(executor)

    assert "WorkflowExecutor" in repr_str, \
        "__repr__ should include the class name"
    return


def test_executor_str_includes_configuration():
    """
        Verify that __str__ includes configuration information.
    """
    executor = WorkflowExecutor()
    str_val = str(executor)

    assert "WorkflowExecutor" in str_val, \
        "__str__ should include the class name"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
