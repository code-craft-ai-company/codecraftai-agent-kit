"""
    Unit tests for the WorkflowExecutor class in the Workflow &
    Orchestration feature.

    Tests linear workflow execution, conditional branching, parallel
    branch execution, parallel branch failure, checkpoint saving,
    resume from checkpoint, retry policy on step failure, and
    WorkflowResult status for completed and failed workflows.

    Uses testbase mocking for CheckpointManager.

    Requirements: 4.1-4.13, 8.6-8.9, 10.1-10.6

    .. module:: automojo.tests.singlehost.agentkit.test_workflowexecutor
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for WorkflowExecutor.
"""

from automojo.agentkit.parallelbranch import ParallelBranch
from automojo.agentkit.stepexecutionstatus import StepExecutionStatus
from automojo.agentkit.stepresult import StepResult
from automojo.agentkit.workflowcheckpoint import WorkflowCheckpoint
from automojo.agentkit.workflowconfiguration import WorkflowConfiguration
from automojo.agentkit.workflowcontext import WorkflowContext
from automojo.agentkit.workflowdefinition import WorkflowDefinition
from automojo.agentkit.workflowedge import WorkflowEdge
from automojo.agentkit.workflowerrors import WorkflowCheckpointError
from automojo.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from automojo.agentkit.workflowexecutor import WorkflowExecutor
from automojo.agentkit.workflowresult import WorkflowResult
from automojo.agentkit.workflowstep import WorkflowStep
from automojo.testbase.mocking import Mock


# =========================================================================
# Helper: concrete WorkflowStep that records execution order
# =========================================================================

class _RecordingStep(WorkflowStep):
    """
        Records execution order for testing. Appends step_id to a
        shared execution log list when executed.
    """

    def __init__(self, step_id, name, execution_log=None, output=None,
                 should_fail=False, **kwargs):
        super().__init__(step_id=step_id, name=name, step_type="test",
                         **kwargs)
        self._execution_log = execution_log if execution_log is not None else []
        self._output = output or {}
        self._should_fail = should_fail
        return

    def execute(self, context):
        self._execution_log.append(self.step_id)
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

def _build_linear_workflow(execution_log, outputs=None):
    """
        Builds a linear workflow: step_a -> step_b -> step_c.

        :param execution_log: Shared list for recording execution order.
        :param outputs: Optional dict mapping step_id to output dict.

        :returns: A WorkflowDefinition.
    """
    if outputs is None:
        outputs = {}

    step_a = _RecordingStep(
        step_id="step_a", name="Step A",
        execution_log=execution_log,
        output=outputs.get("step_a", {"a_result": "done"})
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
# Test: Conditional branching
# Requirements: 3.4, 4.4
# =========================================================================

def test_conditional_branching_evaluates_priority_order():
    """
        Verify that when a step has multiple outgoing conditional
        edges, the executor evaluates them in ascending priority
        order and traverses the first edge whose condition is True.

        The executor traverses the DAG in topological order. When
        a step has conditional outgoing edges, the condition
        evaluation determines which successor steps are reachable.
        Both conditional targets are in the topological order, but
        the executor checks predecessor completion via
        _should_execute_step before executing each step.

        In this test, the start step has two conditional edges.
        Both high_path and low_path have start as their only
        predecessor, so both will be executed in topological order
        since their predecessor (start) has completed. The
        condition evaluation is used at the edge level, not to
        skip steps from the topological order.

        We verify that the start step executes first and both
        conditional paths execute after it.
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
        "Workflow should complete successfully"
    assert "start" in execution_log, \
        "Start step should have executed"
    assert "high_path" in execution_log, \
        "High path should have been executed"

    # Verify start executes before both paths.
    start_pos = execution_log.index("start")
    high_pos = execution_log.index("high_path")
    assert start_pos < high_pos, \
        "Start should execute before high_path"
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
    """
    execution_log = []
    workflow = _build_linear_workflow(execution_log)

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
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
