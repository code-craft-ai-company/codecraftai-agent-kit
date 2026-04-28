"""
    Unit tests for built-in workflow step implementations:
    ToolStep, LLMStep, AgentStep, ApprovalStep, SubWorkflowStep.

    Tests cover construction, property access, execute success/failure
    paths, input mapping resolution, __repr__, and __str__ for each
    built-in step type.

    Requirements: 11.1-11.7, 12.1-12.5, 13.1-13.6, 14.1-14.7, 15.1-15.5

    .. module:: automojo.tests.singlehost.agentkit.steps.test_workflowsteps
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for built-in workflow step implementations.
"""

import automojo.testbase as testbase

from automojo.testbase.mocking import Mock

from automojo.agentkit.stepexecutionstatus import StepExecutionStatus
from automojo.agentkit.workflowcontext import WorkflowContext
from automojo.agentkit.approvalgate import ApprovalGate
from automojo.agentkit.workflowerrors import ApprovalTimeoutError

from automojo.agentkit.steps.toolstep import ToolStep
from automojo.agentkit.steps.llmstep import LLMStep
from automojo.agentkit.steps.agentstep import AgentStep
from automojo.agentkit.steps.approvalstep import ApprovalStep
from automojo.agentkit.steps.subworkflowstep import SubWorkflowStep


# ===================================================================
# Helper: create a mock agent with tool registry
# ===================================================================

def _create_mock_agent_with_tools(tool_name, tool_mock, execute_result):
    """
        Creates a mock agent with a tool registry that returns
        the given tool_mock on lookup and execute_result on
        execute_tool.
    """
    agent = Mock()
    agent.configure(recursive=True)
    ctx = agent.mock_context()

    tool_registry = Mock()
    tool_registry.configure(recursive=True)
    tool_registry.mock_context().mock_method("lookup", return_value=tool_mock)

    ctx.set_attribute("tools", tool_registry)
    ctx.mock_method("execute_tool", return_value=execute_result)

    return agent


# ===================================================================
# ToolStep Tests
# ===================================================================

def test_toolstep_construction():
    """
        Verifies ToolStep properties: step_id, name, step_type,
        tool_name, input_mapping.
    """
    step = ToolStep(
        step_id="ts-001",
        name="Run Formatter",
        tool_name="formatter",
        input_mapping={"text": "inputs.raw_text"}
    )

    testbase.assert_equal(step.step_id, "ts-001",
        "step_id should be 'ts-001'.")
    testbase.assert_equal(step.name, "Run Formatter",
        "name should be 'Run Formatter'.")
    testbase.assert_equal(step.step_type, "tool",
        "step_type should be 'tool'.")
    testbase.assert_equal(step.tool_name, "formatter",
        "tool_name should be 'formatter'.")
    testbase.assert_equal(step.input_mapping, {"text": "inputs.raw_text"},
        "input_mapping should match provided value.")

    return


def test_toolstep_execute_success():
    """
        Verifies ToolStep returns COMPLETED StepResult when the
        tool executes successfully.
    """
    tool_result = Mock()
    tool_result.configure(recursive=True)
    tool_result_ctx = tool_result.mock_context()
    tool_result_ctx.set_attribute("is_success", True)
    tool_result_ctx.set_attribute("output", {"formatted": "hello world"})

    tool_mock = Mock()
    tool_mock.configure(recursive=True)

    agent = _create_mock_agent_with_tools("formatter", tool_mock, tool_result)

    step = ToolStep(
        step_id="ts-002",
        name="Format Text",
        tool_name="formatter",
        input_mapping={"text": "inputs.raw_text"}
    )

    context = WorkflowContext(inputs={"raw_text": "hello world"}, agent=agent)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    testbase.assert_equal(result.step_id, "ts-002",
        "Result step_id should be 'ts-002'.")
    testbase.assert_true(result.is_success,
        "Result should indicate success.")

    return


def test_toolstep_execute_no_agent():
    """
        Verifies ToolStep returns FAILED StepResult when
        context.agent is None.
    """
    step = ToolStep(
        step_id="ts-003",
        name="No Agent Tool",
        tool_name="formatter"
    )

    context = WorkflowContext(inputs={}, agent=None)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED when agent is None.")
    testbase.assert_true("no agent" in result.error.lower(),
        "Error should mention missing agent.")

    return


def test_toolstep_execute_tool_not_found():
    """
        Verifies ToolStep returns FAILED StepResult when the tool
        is not found in the registry.
    """
    agent = Mock()
    agent.configure(recursive=True)

    tool_registry = Mock()
    tool_registry.configure(recursive=True)
    tool_registry.mock_context().mock_method("lookup", return_value=None)

    agent.mock_context().set_attribute("tools", tool_registry)

    step = ToolStep(
        step_id="ts-004",
        name="Missing Tool",
        tool_name="nonexistent_tool"
    )

    context = WorkflowContext(inputs={}, agent=agent)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED when tool not found.")
    testbase.assert_true("not found" in result.error.lower(),
        "Error should mention tool not found.")

    return


def test_toolstep_execute_tool_failure():
    """
        Verifies ToolStep returns FAILED StepResult when
        execute_tool raises an exception.
    """
    tool_mock = Mock()
    tool_mock.configure(recursive=True)

    agent = Mock()
    agent.configure(recursive=True)

    tool_registry = Mock()
    tool_registry.configure(recursive=True)
    tool_registry.mock_context().mock_method("lookup", return_value=tool_mock)

    agent.mock_context().set_attribute("tools", tool_registry)
    agent.mock_context().mock_method(
        "execute_tool",
        side_effect=lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("Tool crashed"))
    )

    step = ToolStep(
        step_id="ts-005",
        name="Crashing Tool",
        tool_name="crasher"
    )

    context = WorkflowContext(inputs={}, agent=agent)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED on tool exception.")
    testbase.assert_true("Tool crashed" in result.error,
        "Error should contain the exception message.")

    return


def test_toolstep_input_mapping_resolution():
    """
        Verifies that ToolStep resolves inputs.<field> and
        steps.<step_id>.<field> references from the context.
    """
    tool_result = Mock()
    tool_result.configure(recursive=True)
    tool_result_ctx = tool_result.mock_context()
    tool_result_ctx.set_attribute("is_success", True)
    tool_result_ctx.set_attribute("output", {"result": "ok"})

    tool_mock = Mock()
    tool_mock.configure(recursive=True)

    captured_args = {}

    def capture_execute_tool(tool_name, resolved_inputs):
        captured_args["tool_name"] = tool_name
        captured_args["inputs"] = resolved_inputs
        return tool_result

    agent = Mock()
    agent.configure(recursive=True)

    tool_registry = Mock()
    tool_registry.configure(recursive=True)
    tool_registry.mock_context().mock_method("lookup", return_value=tool_mock)

    agent.mock_context().set_attribute("tools", tool_registry)
    agent.mock_context().mock_method("execute_tool", side_effect=capture_execute_tool)

    step = ToolStep(
        step_id="ts-006",
        name="Mapped Tool",
        tool_name="mapper",
        input_mapping={
            "param_a": "inputs.field_a",
            "param_b": "steps.prev_step.output_field"
        }
    )

    context = WorkflowContext(
        inputs={"field_a": "value_a"},
        agent=agent
    )
    context.set_step_output("prev_step", {"output_field": "value_b"})

    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    testbase.assert_equal(captured_args["inputs"]["param_a"], "value_a",
        "param_a should resolve to 'value_a' from inputs.")
    testbase.assert_equal(captured_args["inputs"]["param_b"], "value_b",
        "param_b should resolve to 'value_b' from step output.")

    return


def test_toolstep_repr_and_str():
    """
        Verifies __repr__ and __str__ output for ToolStep.
    """
    step = ToolStep(
        step_id="ts-007",
        name="Repr Tool",
        tool_name="my_tool"
    )

    repr_str = repr(step)
    str_val = str(step)

    testbase.assert_true("ToolStep" in repr_str,
        "repr should contain 'ToolStep'.")
    testbase.assert_true("ts-007" in repr_str,
        "repr should contain the step_id.")
    testbase.assert_true("my_tool" in repr_str,
        "repr should contain the tool_name.")

    testbase.assert_true("ToolStep" in str_val,
        "str should contain 'ToolStep'.")
    testbase.assert_true("my_tool" in str_val,
        "str should contain the tool_name.")

    return


# ===================================================================
# LLMStep Tests
# ===================================================================

def test_llmstep_construction():
    """
        Verifies LLMStep properties: step_id, name, step_type,
        provider_name, model_name, prompt_template, prompt_string,
        output_parser.
    """
    step = LLMStep(
        step_id="llm-001",
        name="Summarize",
        provider_name="openai",
        model_name="gpt-4",
        prompt_string="Summarize this text."
    )

    testbase.assert_equal(step.step_id, "llm-001",
        "step_id should be 'llm-001'.")
    testbase.assert_equal(step.name, "Summarize",
        "name should be 'Summarize'.")
    testbase.assert_equal(step.step_type, "llm",
        "step_type should be 'llm'.")
    testbase.assert_equal(step.provider_name, "openai",
        "provider_name should be 'openai'.")
    testbase.assert_equal(step.model_name, "gpt-4",
        "model_name should be 'gpt-4'.")
    testbase.assert_equal(step.prompt_string, "Summarize this text.",
        "prompt_string should match.")
    testbase.assert_equal(step.prompt_template, None,
        "prompt_template should be None.")
    testbase.assert_equal(step.output_parser, None,
        "output_parser should be None.")

    return


def _create_mock_agent_for_llm(response_content):
    """
        Creates a mock agent whose complete method returns a mock
        LLMResponse with the given content.
    """
    message_mock = Mock()
    message_mock.configure(recursive=True)
    message_mock.mock_context().set_attribute("content", response_content)

    llm_response = Mock()
    llm_response.configure(recursive=True)
    llm_response.mock_context().set_attribute("message", message_mock)

    agent = Mock()
    agent.configure(recursive=True)
    agent.mock_context().mock_method("complete", return_value=llm_response)

    return agent


def test_llmstep_execute_with_prompt_string():
    """
        Verifies LLMStep with a static prompt_string returns
        COMPLETED StepResult with the LLM response content.
    """
    agent = _create_mock_agent_for_llm("This is a summary.")

    step = LLMStep(
        step_id="llm-002",
        name="Static Prompt",
        provider_name="openai",
        model_name="gpt-4",
        prompt_string="Summarize the document."
    )

    context = WorkflowContext(inputs={}, agent=agent)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    testbase.assert_equal(result.output.get("content"), "This is a summary.",
        "Output content should match the LLM response.")

    return


def test_llmstep_execute_with_prompt_template():
    """
        Verifies LLMStep with a prompt_template renders
        {inputs.field} references correctly.
    """
    agent = _create_mock_agent_for_llm("Translated text.")

    step = LLMStep(
        step_id="llm-003",
        name="Template Prompt",
        provider_name="openai",
        model_name="gpt-4",
        prompt_template="Translate: {inputs.text}"
    )

    context = WorkflowContext(
        inputs={"text": "Hello world"},
        agent=agent
    )
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    testbase.assert_equal(result.output.get("content"), "Translated text.",
        "Output content should match the LLM response.")

    return


def test_llmstep_execute_with_output_parser():
    """
        Verifies LLMStep applies the output_parser to the LLM
        response content and returns the parsed output.
    """
    agent = _create_mock_agent_for_llm('{"key": "value"}')

    def parser(content):
        return {"parsed_key": "parsed_value"}

    step = LLMStep(
        step_id="llm-004",
        name="Parsed LLM",
        provider_name="openai",
        model_name="gpt-4",
        prompt_string="Generate JSON.",
        output_parser=parser
    )

    context = WorkflowContext(inputs={}, agent=agent)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    testbase.assert_equal(result.output.get("parsed_key"), "parsed_value",
        "Output should contain parsed values.")

    return


def test_llmstep_execute_no_agent():
    """
        Verifies LLMStep returns FAILED StepResult when
        context.agent is None.
    """
    step = LLMStep(
        step_id="llm-005",
        name="No Agent LLM",
        provider_name="openai",
        model_name="gpt-4",
        prompt_string="Hello."
    )

    context = WorkflowContext(inputs={}, agent=None)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED when agent is None.")
    testbase.assert_true("no agent" in result.error.lower(),
        "Error should mention missing agent.")

    return


def test_llmstep_execute_completion_failure():
    """
        Verifies LLMStep returns FAILED StepResult when
        agent.complete raises an exception.
    """
    agent = Mock()
    agent.configure(recursive=True)
    agent.mock_context().mock_method(
        "complete",
        side_effect=lambda **kw: (_ for _ in ()).throw(RuntimeError("LLM unavailable"))
    )

    step = LLMStep(
        step_id="llm-006",
        name="Failing LLM",
        provider_name="openai",
        model_name="gpt-4",
        prompt_string="Hello."
    )

    context = WorkflowContext(inputs={}, agent=agent)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED on completion error.")
    testbase.assert_true("LLM unavailable" in result.error,
        "Error should contain the exception message.")

    return


def test_llmstep_repr_and_str():
    """
        Verifies __repr__ and __str__ output for LLMStep.
    """
    step = LLMStep(
        step_id="llm-007",
        name="Repr LLM",
        provider_name="anthropic",
        model_name="claude-3"
    )

    repr_str = repr(step)
    str_val = str(step)

    testbase.assert_true("LLMStep" in repr_str,
        "repr should contain 'LLMStep'.")
    testbase.assert_true("llm-007" in repr_str,
        "repr should contain the step_id.")
    testbase.assert_true("anthropic" in repr_str,
        "repr should contain the provider_name.")

    testbase.assert_true("LLMStep" in str_val,
        "str should contain 'LLMStep'.")
    testbase.assert_true("claude-3" in str_val,
        "str should contain the model_name.")

    return


# ===================================================================
# AgentStep Tests
# ===================================================================

def test_agentstep_construction():
    """
        Verifies AgentStep properties: step_id, name, step_type,
        target_agent_id, transport_name, timeout.
    """
    step = AgentStep(
        step_id="as-001",
        name="Delegate Task",
        target_agent_id="agent-worker-01",
        transport_name="grpc",
        timeout=30.0
    )

    testbase.assert_equal(step.step_id, "as-001",
        "step_id should be 'as-001'.")
    testbase.assert_equal(step.name, "Delegate Task",
        "name should be 'Delegate Task'.")
    testbase.assert_equal(step.step_type, "agent",
        "step_type should be 'agent'.")
    testbase.assert_equal(step.target_agent_id, "agent-worker-01",
        "target_agent_id should be 'agent-worker-01'.")
    testbase.assert_equal(step.transport_name, "grpc",
        "transport_name should be 'grpc'.")
    testbase.assert_equal(step.timeout, 30.0,
        "timeout should be 30.0.")

    return


def test_agentstep_execute_success():
    """
        Verifies AgentStep returns COMPLETED StepResult when
        send_message returns a response dict.
    """
    agent = Mock()
    agent.configure(recursive=True)
    agent.mock_context().mock_method(
        "send_message",
        return_value={"status": "done", "data": "result_data"}
    )

    step = AgentStep(
        step_id="as-002",
        name="Send Task",
        target_agent_id="agent-worker-02"
    )

    context = WorkflowContext(
        inputs={"task": "process_data"},
        agent=agent
    )
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    testbase.assert_equal(result.output.get("status"), "done",
        "Output should contain the response data.")

    return


def test_agentstep_execute_no_agent():
    """
        Verifies AgentStep returns FAILED StepResult when
        context.agent is None.
    """
    step = AgentStep(
        step_id="as-003",
        name="No Agent",
        target_agent_id="agent-worker-03"
    )

    context = WorkflowContext(inputs={}, agent=None)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED when agent is None.")
    testbase.assert_true("no agent" in result.error.lower(),
        "Error should mention missing agent.")

    return


def test_agentstep_execute_transport_error():
    """
        Verifies AgentStep returns FAILED StepResult when
        send_message raises an exception.
    """
    agent = Mock()
    agent.configure(recursive=True)
    agent.mock_context().mock_method(
        "send_message",
        side_effect=lambda *a, **kw: (_ for _ in ()).throw(
            ConnectionError("Transport connection refused")
        )
    )

    step = AgentStep(
        step_id="as-004",
        name="Transport Fail",
        target_agent_id="agent-worker-04"
    )

    context = WorkflowContext(inputs={}, agent=agent)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED on transport error.")
    testbase.assert_true("Transport connection refused" in result.error,
        "Error should contain the exception message.")

    return


def test_agentstep_repr_and_str():
    """
        Verifies __repr__ and __str__ output for AgentStep.
    """
    step = AgentStep(
        step_id="as-005",
        name="Repr Agent",
        target_agent_id="agent-target"
    )

    repr_str = repr(step)
    str_val = str(step)

    testbase.assert_true("AgentStep" in repr_str,
        "repr should contain 'AgentStep'.")
    testbase.assert_true("as-005" in repr_str,
        "repr should contain the step_id.")
    testbase.assert_true("agent-target" in repr_str,
        "repr should contain the target_agent_id.")

    testbase.assert_true("AgentStep" in str_val,
        "str should contain 'AgentStep'.")
    testbase.assert_true("agent-target" in str_val,
        "str should contain the target_agent_id.")

    return


# ===================================================================
# ApprovalStep Tests
# ===================================================================

def _create_mock_agent_with_approval_gate(gate):
    """
        Creates a mock agent with the given ApprovalGate and a
        mock identity.
    """
    identity = Mock()
    identity.configure(recursive=True)
    identity.mock_context().set_attribute("identifier", "agent-approver-01")

    agent = Mock()
    agent.configure(recursive=True)
    agent.mock_context().set_attribute("approval_gate", gate)
    agent.mock_context().set_attribute("identity", identity)

    return agent


def test_approvalstep_construction():
    """
        Verifies ApprovalStep properties: step_id, name, step_type,
        description, timeout.
    """
    step = ApprovalStep(
        step_id="ap-001",
        name="Deploy Approval",
        description="Approve deployment to production",
        timeout=60.0
    )

    testbase.assert_equal(step.step_id, "ap-001",
        "step_id should be 'ap-001'.")
    testbase.assert_equal(step.name, "Deploy Approval",
        "name should be 'Deploy Approval'.")
    testbase.assert_equal(step.step_type, "approval",
        "step_type should be 'approval'.")
    testbase.assert_equal(step.description, "Approve deployment to production",
        "description should match.")
    testbase.assert_equal(step.timeout, 60.0,
        "timeout should be 60.0.")

    return


def test_approvalstep_execute_approved():
    """
        Verifies ApprovalStep returns COMPLETED StepResult when
        the handler immediately approves the request.
    """
    gate = ApprovalGate()

    def auto_approve_handler(request):
        gate.approve(request.identifier, metadata={"approver": "test-admin"})

    gate.register_handler(auto_approve_handler)

    agent = _create_mock_agent_with_approval_gate(gate)

    step = ApprovalStep(
        step_id="ap-002",
        name="Auto Approve",
        description="Auto-approved step"
    )

    context = WorkflowContext(inputs={}, agent=agent)
    context.set_metadata("execution_id", "exec-ap-002")

    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED when approved.")
    testbase.assert_true(result.is_success,
        "Result should indicate success.")
    testbase.assert_equal(result.output.get("approver"), "test-admin",
        "Output should contain approval metadata.")

    return


def test_approvalstep_execute_rejected():
    """
        Verifies ApprovalStep returns FAILED StepResult when
        the handler immediately rejects the request.
    """
    gate = ApprovalGate()

    def auto_reject_handler(request):
        gate.reject(request.identifier, reason="Not ready for production")

    gate.register_handler(auto_reject_handler)

    agent = _create_mock_agent_with_approval_gate(gate)

    step = ApprovalStep(
        step_id="ap-003",
        name="Auto Reject",
        description="Auto-rejected step"
    )

    context = WorkflowContext(inputs={}, agent=agent)
    context.set_metadata("execution_id", "exec-ap-003")

    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED when rejected.")
    testbase.assert_true("Not ready for production" in result.error,
        "Error should contain the rejection reason.")

    return


def test_approvalstep_execute_pending_with_timeout():
    """
        Verifies ApprovalStep raises ApprovalTimeoutError when
        the request remains pending and a timeout is configured.
    """
    gate = ApprovalGate()
    # No handler registered, so request stays pending.

    agent = _create_mock_agent_with_approval_gate(gate)

    step = ApprovalStep(
        step_id="ap-004",
        name="Timeout Approval",
        description="Will timeout",
        timeout=10.0
    )

    context = WorkflowContext(inputs={}, agent=agent)
    context.set_metadata("execution_id", "exec-ap-004")

    caught_error = None
    try:
        step.execute(context)
    except ApprovalTimeoutError as err:
        caught_error = err

    testbase.assert_true(caught_error is not None,
        "ApprovalTimeoutError should be raised.")
    testbase.assert_equal(caught_error.step_id, "ap-004",
        "Error step_id should be 'ap-004'.")
    testbase.assert_equal(caught_error.timeout, 10.0,
        "Error timeout should be 10.0.")

    return


def test_approvalstep_execute_pending_no_timeout():
    """
        Verifies ApprovalStep returns PENDING_APPROVAL StepResult
        when the request remains pending and no timeout is set.
    """
    gate = ApprovalGate()
    # No handler registered, so request stays pending.

    agent = _create_mock_agent_with_approval_gate(gate)

    step = ApprovalStep(
        step_id="ap-005",
        name="Pending Approval",
        description="Will stay pending"
    )

    context = WorkflowContext(inputs={}, agent=agent)
    context.set_metadata("execution_id", "exec-ap-005")

    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.PENDING_APPROVAL,
        "Result status should be PENDING_APPROVAL.")
    testbase.assert_true("approval_request_id" in result.output,
        "Output should contain the approval_request_id.")

    return


def test_approvalstep_execute_no_agent():
    """
        Verifies ApprovalStep returns FAILED StepResult when
        context.agent is None.
    """
    step = ApprovalStep(
        step_id="ap-006",
        name="No Agent Approval",
        description="No agent available"
    )

    context = WorkflowContext(inputs={}, agent=None)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED when agent is None.")
    testbase.assert_true("no agent" in result.error.lower(),
        "Error should mention missing agent.")

    return


def test_approvalstep_repr_and_str():
    """
        Verifies __repr__ and __str__ output for ApprovalStep.
    """
    step = ApprovalStep(
        step_id="ap-007",
        name="Repr Approval",
        description="Approve this"
    )

    repr_str = repr(step)
    str_val = str(step)

    testbase.assert_true("ApprovalStep" in repr_str,
        "repr should contain 'ApprovalStep'.")
    testbase.assert_true("ap-007" in repr_str,
        "repr should contain the step_id.")
    testbase.assert_true("Approve this" in repr_str,
        "repr should contain the description.")

    testbase.assert_true("ApprovalStep" in str_val,
        "str should contain 'ApprovalStep'.")
    testbase.assert_true("Approve this" in str_val,
        "str should contain the description.")

    return


# ===================================================================
# SubWorkflowStep Tests
# ===================================================================

from automojo.agentkit.workflowdefinition import WorkflowDefinition
from automojo.agentkit.workflowedge import WorkflowEdge
from automojo.agentkit.workflowstep import WorkflowStep as WorkflowStepBase
from automojo.agentkit.stepresult import StepResult


class _PassthroughStep(WorkflowStepBase):
    """
        A minimal concrete WorkflowStep that returns COMPLETED
        with the context inputs as output.
    """

    def __init__(self, step_id, name):
        super().__init__(step_id=step_id, name=name, step_type="passthrough")
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


class _FailingStep(WorkflowStepBase):
    """
        A minimal concrete WorkflowStep that always returns FAILED.
    """

    def __init__(self, step_id, name):
        super().__init__(step_id=step_id, name=name, step_type="failing")
        return

    def execute(self, context):
        result = StepResult(
            step_id=self.step_id,
            step_name=self.name,
            status=StepExecutionStatus.FAILED,
            duration=0.001,
            error="Step intentionally failed."
        )
        return result


def _create_simple_sub_workflow():
    """
        Creates a simple single-step sub-workflow for testing.
    """
    step_a = _PassthroughStep(step_id="sub-a", name="Sub Step A")

    workflow = WorkflowDefinition(
        name="sub-workflow",
        version="1.0.0",
        steps={"sub-a": step_a},
        edges=[],
        start_step_id="sub-a"
    )
    return workflow


def _create_failing_sub_workflow():
    """
        Creates a single-step sub-workflow that always fails.
    """
    step_a = _FailingStep(step_id="sub-fail", name="Failing Sub Step")

    workflow = WorkflowDefinition(
        name="failing-sub-workflow",
        version="1.0.0",
        steps={"sub-fail": step_a},
        edges=[],
        start_step_id="sub-fail"
    )
    return workflow


def test_subworkflowstep_construction():
    """
        Verifies SubWorkflowStep properties: step_id, name,
        step_type, sub_workflow, input_mapping.
    """
    sub_wf = _create_simple_sub_workflow()

    step = SubWorkflowStep(
        step_id="sw-001",
        name="Run Sub Workflow",
        sub_workflow=sub_wf,
        input_mapping={"data": "inputs.source_data"}
    )

    testbase.assert_equal(step.step_id, "sw-001",
        "step_id should be 'sw-001'.")
    testbase.assert_equal(step.name, "Run Sub Workflow",
        "name should be 'Run Sub Workflow'.")
    testbase.assert_equal(step.step_type, "sub_workflow",
        "step_type should be 'sub_workflow'.")
    testbase.assert_equal(step.sub_workflow.name, "sub-workflow",
        "sub_workflow name should be 'sub-workflow'.")
    testbase.assert_equal(step.input_mapping, {"data": "inputs.source_data"},
        "input_mapping should match provided value.")

    return


def test_subworkflowstep_execute_success():
    """
        Verifies SubWorkflowStep returns COMPLETED StepResult
        when the sub-workflow completes successfully.
    """
    sub_wf = _create_simple_sub_workflow()

    step = SubWorkflowStep(
        step_id="sw-002",
        name="Success Sub",
        sub_workflow=sub_wf,
        input_mapping={"value": "inputs.source_value"}
    )

    context = WorkflowContext(
        inputs={"source_value": "test_data"},
        agent=None
    )

    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    testbase.assert_true(result.is_success,
        "Result should indicate success.")
    testbase.assert_equal(result.output.get("value"), "test_data",
        "Output should contain the sub-workflow's final output.")

    return


def test_subworkflowstep_execute_failure():
    """
        Verifies SubWorkflowStep returns FAILED StepResult when
        the sub-workflow fails.
    """
    sub_wf = _create_failing_sub_workflow()

    step = SubWorkflowStep(
        step_id="sw-003",
        name="Failing Sub",
        sub_workflow=sub_wf
    )

    context = WorkflowContext(inputs={}, agent=None)

    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED when sub-workflow fails.")
    testbase.assert_true(result.error is not None,
        "Error should be set when sub-workflow fails.")

    return


def test_subworkflowstep_execute_exception():
    """
        Verifies SubWorkflowStep returns FAILED StepResult when
        the sub-workflow executor raises an exception.
    """
    # Create a sub-workflow with a step that raises an exception
    class _ExceptionStep(WorkflowStepBase):
        def __init__(self):
            super().__init__(step_id="exc-step", name="Exception Step",
                             step_type="exception")
            return

        def execute(self, context):
            raise RuntimeError("Unexpected executor error")

    exc_step = _ExceptionStep()

    sub_wf = WorkflowDefinition(
        name="exception-sub-workflow",
        version="1.0.0",
        steps={"exc-step": exc_step},
        edges=[],
        start_step_id="exc-step"
    )

    step = SubWorkflowStep(
        step_id="sw-004",
        name="Exception Sub",
        sub_workflow=sub_wf
    )

    context = WorkflowContext(inputs={}, agent=None)
    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.FAILED,
        "Result status should be FAILED on executor exception.")
    testbase.assert_true(result.error is not None,
        "Error should be set on executor exception.")

    return


def test_subworkflowstep_input_mapping():
    """
        Verifies SubWorkflowStep resolves input mapping from
        both inputs.<field> and steps.<step_id>.<field>.
    """
    sub_wf = _create_simple_sub_workflow()

    step = SubWorkflowStep(
        step_id="sw-005",
        name="Mapped Sub",
        sub_workflow=sub_wf,
        input_mapping={
            "param_x": "inputs.x_value",
            "param_y": "steps.prior.y_value"
        }
    )

    context = WorkflowContext(
        inputs={"x_value": "from_input"},
        agent=None
    )
    context.set_step_output("prior", {"y_value": "from_step"})

    result = step.execute(context)

    testbase.assert_equal(result.status, StepExecutionStatus.COMPLETED,
        "Result status should be COMPLETED.")
    # The sub-workflow's passthrough step returns its inputs as output.
    testbase.assert_equal(result.output.get("param_x"), "from_input",
        "param_x should resolve from inputs.")
    testbase.assert_equal(result.output.get("param_y"), "from_step",
        "param_y should resolve from step output.")

    return


def test_subworkflowstep_repr_and_str():
    """
        Verifies __repr__ and __str__ output for SubWorkflowStep.
    """
    sub_wf = _create_simple_sub_workflow()

    step = SubWorkflowStep(
        step_id="sw-006",
        name="Repr Sub",
        sub_workflow=sub_wf
    )

    repr_str = repr(step)
    str_val = str(step)

    testbase.assert_true("SubWorkflowStep" in repr_str,
        "repr should contain 'SubWorkflowStep'.")
    testbase.assert_true("sw-006" in repr_str,
        "repr should contain the step_id.")
    testbase.assert_true("sub-workflow" in repr_str,
        "repr should contain the sub-workflow name.")

    testbase.assert_true("SubWorkflowStep" in str_val,
        "str should contain 'SubWorkflowStep'.")
    testbase.assert_true("sub-workflow" in str_val,
        "str should contain the sub-workflow name.")

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
