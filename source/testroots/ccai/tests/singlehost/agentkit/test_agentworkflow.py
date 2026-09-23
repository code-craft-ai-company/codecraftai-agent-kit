"""
    Unit tests for Agent workflow integration.

    Tests cover the workflow properties, register_workflow,
    execute_workflow, resume_workflow methods, and the lifecycle
    integration methods _initialize_workflows and _stop_workflows.

    Requirements: 18.1-18.11, 19.1-19.4

    .. module:: ccai.tests.singlehost.agentkit.test_agentworkflow
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for Agent workflow integration.
"""

import ccai.testbase as testbase

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.approvalgate import ApprovalGate
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.workflowdefinition import WorkflowDefinition
from ccai.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from ccai.agentkit.workflowregistry import WorkflowRegistry
from ccai.agentkit.workflowresult import WorkflowResult
from ccai.agentkit.workflowstep import WorkflowStep


# ===================================================================
# Helpers
# ===================================================================

def _reset_registry():
    """Resets the AgentRegistry singleton."""
    registry = AgentRegistry.instance()
    registry._reset()
    return


class _SimpleStep(WorkflowStep):
    """A minimal concrete WorkflowStep for testing."""

    def __init__(self, step_id, name):
        super().__init__(step_id=step_id, name=name, step_type="simple")
        return

    def execute(self, context):
        output = dict(context.inputs)
        result = StepResult(
            step_id=self.step_id,
            step_name=self.name,
            status=StepExecutionStatus.COMPLETED,
            output=output,
            duration=0.001
        )
        return result


class _TestAgent(Agent):
    """Concrete Agent subclass for testing workflow integration."""

    def initialize(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        self._stop_workflows()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        self._perform_transition(LifecycleState.CREATED, "on_error")
        return


def _create_test_agent(name="test-workflow-agent"):
    """Creates a _TestAgent with a minimal configuration."""
    _reset_registry()
    config = AgentConfiguration(identity={"name": name, "version": "1.0.0"})
    agent = _TestAgent(configuration=config)
    return agent


def _create_simple_workflow(name="test-workflow", version="1.0.0"):
    """Creates a simple single-step workflow for testing."""
    step_a = _SimpleStep(step_id="step-a", name="Step A")
    workflow = WorkflowDefinition(
        name=name,
        version=version,
        steps={"step-a": step_a},
        edges=[],
        start_step_id="step-a"
    )
    return workflow


# ===================================================================
# Tests: Workflow properties
# ===================================================================

def test_agent_workflows_property_returns_workflow_registry():
    """Verifies the workflows property returns a WorkflowRegistry."""
    agent = _create_test_agent("wf-prop-agent")
    testbase.assert_true(
        isinstance(agent.workflows, WorkflowRegistry),
        "workflows property should return a WorkflowRegistry instance."
    )
    return


def test_agent_approval_gate_property_returns_approval_gate():
    """Verifies the approval_gate property returns an ApprovalGate."""
    agent = _create_test_agent("ag-prop-agent")
    testbase.assert_true(
        isinstance(agent.approval_gate, ApprovalGate),
        "approval_gate property should return an ApprovalGate instance."
    )
    return


# ===================================================================
# Tests: register_workflow
# ===================================================================

def test_agent_register_workflow_adds_to_registry():
    """Verifies register_workflow adds the workflow to the registry."""
    agent = _create_test_agent("reg-wf-agent")
    workflow = _create_simple_workflow("my-workflow", "1.0.0")

    agent.register_workflow(workflow)

    testbase.assert_true(
        agent.workflows.has_workflow("my-workflow", "1.0.0"),
        "Workflow should be registered in the agent's WorkflowRegistry."
    )
    return


def test_agent_register_workflow_duplicate_raises_error():
    """Verifies register_workflow raises SemanticError on duplicate."""
    agent = _create_test_agent("dup-wf-agent")
    workflow = _create_simple_workflow("dup-workflow", "1.0.0")

    agent.register_workflow(workflow)

    caught_error = None
    try:
        agent.register_workflow(workflow)
    except SemanticError as err:
        caught_error = err

    testbase.assert_true(
        caught_error is not None,
        "Registering a duplicate workflow should raise SemanticError."
    )
    return


# ===================================================================
# Tests: execute_workflow
# ===================================================================

def test_agent_execute_workflow_success():
    """Verifies execute_workflow runs the workflow and returns a result."""
    agent = _create_test_agent("exec-wf-agent")
    workflow = _create_simple_workflow("exec-workflow", "1.0.0")
    agent.register_workflow(workflow)

    result = agent.execute_workflow("exec-workflow", inputs={"key": "value"})

    testbase.assert_equal(
        result.status, WorkflowExecutionStatus.COMPLETED,
        "Workflow execution should complete successfully."
    )
    testbase.assert_true(
        isinstance(result, WorkflowResult),
        "Result should be a WorkflowResult instance."
    )
    return


def test_agent_execute_workflow_not_found_raises_error():
    """Verifies execute_workflow raises SemanticError for missing workflow."""
    agent = _create_test_agent("notfound-wf-agent")

    caught_error = None
    try:
        agent.execute_workflow("nonexistent", inputs={})
    except SemanticError as err:
        caught_error = err

    testbase.assert_true(
        caught_error is not None,
        "Executing a nonexistent workflow should raise SemanticError."
    )
    testbase.assert_true(
        "not found" in str(caught_error).lower(),
        "Error message should mention workflow not found."
    )
    return


def test_agent_execute_workflow_with_version():
    """Verifies execute_workflow can look up a specific version."""
    agent = _create_test_agent("ver-wf-agent")
    wf_v1 = _create_simple_workflow("versioned-wf", "1.0.0")
    wf_v2 = _create_simple_workflow("versioned-wf", "2.0.0")
    agent.register_workflow(wf_v1)
    agent.register_workflow(wf_v2)

    result = agent.execute_workflow("versioned-wf", inputs={}, version="1.0.0")

    testbase.assert_equal(
        result.status, WorkflowExecutionStatus.COMPLETED,
        "Workflow execution with specific version should complete."
    )
    return


# ===================================================================
# Tests: Lifecycle integration
# ===================================================================

def test_agent_initialize_workflows_creates_executor():
    """Verifies _initialize_workflows creates the WorkflowExecutor."""
    agent = _create_test_agent("init-wf-agent")

    agent._initialize_workflows()

    testbase.assert_true(
        agent._workflow_executor is not None,
        "WorkflowExecutor should be created after _initialize_workflows."
    )
    testbase.assert_true(
        agent._workflow_configuration is not None,
        "WorkflowConfiguration should be set after _initialize_workflows."
    )
    return


def test_agent_stop_workflows_clears_registry():
    """Verifies _stop_workflows clears the WorkflowRegistry."""
    agent = _create_test_agent("stop-wf-agent")
    workflow = _create_simple_workflow("stop-workflow", "1.0.0")
    agent.register_workflow(workflow)

    testbase.assert_equal(
        agent.workflows.count, 1,
        "Registry should have 1 workflow before stop."
    )

    agent._stop_workflows()

    testbase.assert_equal(
        agent.workflows.count, 0,
        "Registry should be empty after _stop_workflows."
    )
    testbase.assert_true(
        agent._workflow_executor is None,
        "WorkflowExecutor should be None after _stop_workflows."
    )
    return


def test_agent_stop_workflows_cancels_pending_approvals():
    """Verifies _stop_workflows rejects all pending approval requests."""
    agent = _create_test_agent("cancel-ap-agent")

    # Create a pending approval request
    agent.approval_gate.create_request(
        execution_id="exec-001",
        step_id="step-001",
        description="Test approval",
        requesting_agent_id="agent-001"
    )

    testbase.assert_equal(
        agent.approval_gate.pending_count, 1,
        "Should have 1 pending request before stop."
    )

    agent._stop_workflows()

    testbase.assert_equal(
        agent.approval_gate.pending_count, 0,
        "Should have 0 pending requests after _stop_workflows."
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
