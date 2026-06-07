"""
    Unit tests for the workflow enumeration and error classes.

    Tests WorkflowExecutionStatus and StepExecutionStatus enums including
    all values and from_string behavior, and WorkflowDefinitionError,
    WorkflowExecutionError, WorkflowCheckpointError, and ApprovalTimeoutError
    including construction, property access, repr, and error messages.

    Requirements: 7.1-7.6, 20.1-20.9
"""

import enum

from ccai.agentkit.errors import AgentKitError
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.workflowerrors import ApprovalTimeoutError
from ccai.agentkit.workflowerrors import WorkflowCheckpointError
from ccai.agentkit.workflowerrors import WorkflowDefinitionError
from ccai.agentkit.workflowerrors import WorkflowExecutionError


# =========================================================================
# WorkflowExecutionStatus enum tests (Requirements 7.1, 7.2, 7.3)
# =========================================================================

def test_workflow_execution_status_is_enum():
    """
        Verify that WorkflowExecutionStatus is an Enum class.
    """
    is_enum = issubclass(WorkflowExecutionStatus, enum.Enum)
    assert is_enum is True, "WorkflowExecutionStatus should be an Enum"
    return


def test_workflow_execution_status_has_running():
    """
        Verify that the RUNNING value exists with value 'RUNNING'.
    """
    status = WorkflowExecutionStatus.RUNNING
    assert status.value == "RUNNING", "RUNNING should have value 'RUNNING'"
    return


def test_workflow_execution_status_has_completed():
    """
        Verify that the COMPLETED value exists with value 'COMPLETED'.
    """
    status = WorkflowExecutionStatus.COMPLETED
    assert status.value == "COMPLETED", "COMPLETED should have value 'COMPLETED'"
    return


def test_workflow_execution_status_has_failed():
    """
        Verify that the FAILED value exists with value 'FAILED'.
    """
    status = WorkflowExecutionStatus.FAILED
    assert status.value == "FAILED", "FAILED should have value 'FAILED'"
    return


def test_workflow_execution_status_has_paused():
    """
        Verify that the PAUSED value exists with value 'PAUSED'.
    """
    status = WorkflowExecutionStatus.PAUSED
    assert status.value == "PAUSED", "PAUSED should have value 'PAUSED'"
    return


def test_workflow_execution_status_has_cancelled():
    """
        Verify that the CANCELLED value exists with value 'CANCELLED'.
    """
    status = WorkflowExecutionStatus.CANCELLED
    assert status.value == "CANCELLED", "CANCELLED should have value 'CANCELLED'"
    return


def test_workflow_execution_status_has_exactly_five_members():
    """
        Verify that WorkflowExecutionStatus has exactly 5 members.
    """
    member_count = len(WorkflowExecutionStatus)
    assert member_count == 5, "WorkflowExecutionStatus should have 5 members, got {}".format(member_count)
    return


def test_workflow_execution_status_from_string_valid():
    """
        Verify that from_string returns the correct member for each valid value.
    """
    expected_pairs = [
        ("RUNNING", WorkflowExecutionStatus.RUNNING),
        ("COMPLETED", WorkflowExecutionStatus.COMPLETED),
        ("FAILED", WorkflowExecutionStatus.FAILED),
        ("PAUSED", WorkflowExecutionStatus.PAUSED),
        ("CANCELLED", WorkflowExecutionStatus.CANCELLED),
    ]

    for string_val, expected_member in expected_pairs:
        result = WorkflowExecutionStatus.from_string(string_val)
        assert result is expected_member, "from_string('{}') should return {}".format(string_val, expected_member)

    return


def test_workflow_execution_status_from_string_case_insensitive():
    """
        Verify that from_string handles lowercase input.
    """
    result = WorkflowExecutionStatus.from_string("running")
    assert result is WorkflowExecutionStatus.RUNNING, "from_string('running') should return RUNNING"
    return


def test_workflow_execution_status_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an invalid value.
    """
    caught = False
    try:
        WorkflowExecutionStatus.from_string("INVALID_STATUS")
    except SemanticError:
        caught = True

    assert caught is True, "from_string with invalid value should raise SemanticError"
    return


def test_workflow_execution_status_from_string_invalid_message_content():
    """
        Verify that the SemanticError message identifies the invalid value
        and lists valid values.
    """
    try:
        WorkflowExecutionStatus.from_string("BOGUS")
    except SemanticError as err:
        msg = err.message
        has_invalid = "BOGUS" in msg
        has_valid = "RUNNING" in msg and "COMPLETED" in msg
        assert has_invalid is True, "Error message should contain the invalid value"
        assert has_valid is True, "Error message should list valid values"
        return

    assert False, "SemanticError should have been raised"
    return


# =========================================================================
# StepExecutionStatus enum tests (Requirements 7.4, 7.5, 7.6)
# =========================================================================

def test_step_execution_status_is_enum():
    """
        Verify that StepExecutionStatus is an Enum class.
    """
    is_enum = issubclass(StepExecutionStatus, enum.Enum)
    assert is_enum is True, "StepExecutionStatus should be an Enum"
    return


def test_step_execution_status_has_pending():
    """
        Verify that the PENDING value exists with value 'PENDING'.
    """
    status = StepExecutionStatus.PENDING
    assert status.value == "PENDING", "PENDING should have value 'PENDING'"
    return


def test_step_execution_status_has_running():
    """
        Verify that the RUNNING value exists with value 'RUNNING'.
    """
    status = StepExecutionStatus.RUNNING
    assert status.value == "RUNNING", "RUNNING should have value 'RUNNING'"
    return


def test_step_execution_status_has_completed():
    """
        Verify that the COMPLETED value exists with value 'COMPLETED'.
    """
    status = StepExecutionStatus.COMPLETED
    assert status.value == "COMPLETED", "COMPLETED should have value 'COMPLETED'"
    return


def test_step_execution_status_has_failed():
    """
        Verify that the FAILED value exists with value 'FAILED'.
    """
    status = StepExecutionStatus.FAILED
    assert status.value == "FAILED", "FAILED should have value 'FAILED'"
    return


def test_step_execution_status_has_skipped():
    """
        Verify that the SKIPPED value exists with value 'SKIPPED'.
    """
    status = StepExecutionStatus.SKIPPED
    assert status.value == "SKIPPED", "SKIPPED should have value 'SKIPPED'"
    return


def test_step_execution_status_has_pending_approval():
    """
        Verify that the PENDING_APPROVAL value exists with value 'PENDING_APPROVAL'.
    """
    status = StepExecutionStatus.PENDING_APPROVAL
    assert status.value == "PENDING_APPROVAL", "PENDING_APPROVAL should have value 'PENDING_APPROVAL'"
    return


def test_step_execution_status_has_cancelled():
    """
        Verify that the CANCELLED value exists with value 'CANCELLED'.
    """
    status = StepExecutionStatus.CANCELLED
    assert status.value == "CANCELLED", "CANCELLED should have value 'CANCELLED'"
    return


def test_step_execution_status_has_exactly_seven_members():
    """
        Verify that StepExecutionStatus has exactly 7 members.
    """
    member_count = len(StepExecutionStatus)
    assert member_count == 7, "StepExecutionStatus should have 7 members, got {}".format(member_count)
    return


def test_step_execution_status_from_string_valid():
    """
        Verify that from_string returns the correct member for each valid value.
    """
    expected_pairs = [
        ("PENDING", StepExecutionStatus.PENDING),
        ("RUNNING", StepExecutionStatus.RUNNING),
        ("COMPLETED", StepExecutionStatus.COMPLETED),
        ("FAILED", StepExecutionStatus.FAILED),
        ("SKIPPED", StepExecutionStatus.SKIPPED),
        ("PENDING_APPROVAL", StepExecutionStatus.PENDING_APPROVAL),
        ("CANCELLED", StepExecutionStatus.CANCELLED),
    ]

    for string_val, expected_member in expected_pairs:
        result = StepExecutionStatus.from_string(string_val)
        assert result is expected_member, "from_string('{}') should return {}".format(string_val, expected_member)

    return


def test_step_execution_status_from_string_case_insensitive():
    """
        Verify that from_string handles lowercase input.
    """
    result = StepExecutionStatus.from_string("completed")
    assert result is StepExecutionStatus.COMPLETED, "from_string('completed') should return COMPLETED"
    return


def test_step_execution_status_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an invalid value.
    """
    caught = False
    try:
        StepExecutionStatus.from_string("NOT_A_STATUS")
    except SemanticError:
        caught = True

    assert caught is True, "from_string with invalid value should raise SemanticError"
    return


def test_step_execution_status_from_string_invalid_message_content():
    """
        Verify that the SemanticError message identifies the invalid value
        and lists valid values.
    """
    try:
        StepExecutionStatus.from_string("BOGUS")
    except SemanticError as err:
        msg = err.message
        has_invalid = "BOGUS" in msg
        has_valid = "PENDING" in msg and "COMPLETED" in msg
        assert has_invalid is True, "Error message should contain the invalid value"
        assert has_valid is True, "Error message should list valid values"
        return

    assert False, "SemanticError should have been raised"
    return


# =========================================================================
# WorkflowDefinitionError tests (Requirements 20.1, 20.2, 20.9)
# =========================================================================

def test_workflow_definition_error_inherits_from_agentkit_error():
    """
        Verify that WorkflowDefinitionError inherits from AgentKitError.
    """
    err = WorkflowDefinitionError("my-workflow", "cycle detected")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "WorkflowDefinitionError should inherit from AgentKitError"
    return


def test_workflow_definition_error_workflow_name_property():
    """
        Verify that the workflow_name property returns the provided name.
    """
    err = WorkflowDefinitionError("data-pipeline", "missing start step")
    name = err.workflow_name
    assert name == "data-pipeline", "workflow_name should be 'data-pipeline'"
    return


def test_workflow_definition_error_detail_property():
    """
        Verify that the detail property returns the provided detail string.
    """
    err = WorkflowDefinitionError("etl-flow", "unreachable steps: step-x")
    detail = err.detail
    assert detail == "unreachable steps: step-x", "detail should match the provided string"
    return


def test_workflow_definition_error_message_format():
    """
        Verify that the error message includes the workflow name and detail.
    """
    err = WorkflowDefinitionError("my-wf", "cycle detected at step-a")
    msg = err.message
    has_name = "my-wf" in msg
    has_detail = "cycle detected at step-a" in msg
    assert has_name is True, "Message should contain the workflow name"
    assert has_detail is True, "Message should contain the detail"
    return


def test_workflow_definition_error_repr():
    """
        Verify that __repr__ includes class name, workflow name, and detail.
    """
    err = WorkflowDefinitionError("wf-1", "invalid edge")
    repr_str = repr(err)
    has_class = "WorkflowDefinitionError" in repr_str
    has_name = "wf-1" in repr_str
    has_detail = "invalid edge" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_name is True, "repr should contain the workflow name"
    assert has_detail is True, "repr should contain the detail"
    return


def test_workflow_definition_error_str_contains_message():
    """
        Verify that str() produces a meaningful string with the error message.
    """
    err = WorkflowDefinitionError("wf-2", "disconnected nodes")
    str_val = str(err)
    has_name = "wf-2" in str_val
    has_detail = "disconnected nodes" in str_val
    assert has_name is True, "str should contain the workflow name"
    assert has_detail is True, "str should contain the detail"
    return


# =========================================================================
# WorkflowExecutionError tests (Requirements 20.3, 20.4, 20.9)
# =========================================================================

def test_workflow_execution_error_inherits_from_agentkit_error():
    """
        Verify that WorkflowExecutionError inherits from AgentKitError.
    """
    err = WorkflowExecutionError("my-workflow", "step-1")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "WorkflowExecutionError should inherit from AgentKitError"
    return


def test_workflow_execution_error_workflow_name_property():
    """
        Verify that the workflow_name property returns the provided name.
    """
    err = WorkflowExecutionError("pipeline-a", "step-2")
    name = err.workflow_name
    assert name == "pipeline-a", "workflow_name should be 'pipeline-a'"
    return


def test_workflow_execution_error_step_id_property():
    """
        Verify that the step_id property returns the provided step identifier.
    """
    err = WorkflowExecutionError("pipeline-a", "step-2")
    step = err.step_id
    assert step == "step-2", "step_id should be 'step-2'"
    return


def test_workflow_execution_error_cause_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = WorkflowExecutionError("wf", "s1")
    cause = err.cause
    assert cause is None, "Cause should be None when not provided"
    return


def test_workflow_execution_error_cause_with_exception():
    """
        Verify that cause stores the provided exception.
    """
    original = RuntimeError("step failed")
    err = WorkflowExecutionError("wf", "s1", cause=original)
    cause = err.cause
    assert cause is original, "Cause should be the original exception"
    return


def test_workflow_execution_error_message_without_cause():
    """
        Verify that the message includes workflow name and step id.
    """
    err = WorkflowExecutionError("etl", "transform-step")
    msg = err.message
    has_name = "etl" in msg
    has_step = "transform-step" in msg
    assert has_name is True, "Message should contain the workflow name"
    assert has_step is True, "Message should contain the step id"
    return


def test_workflow_execution_error_message_with_cause():
    """
        Verify that the message includes the cause when provided.
    """
    original = ValueError("bad input")
    err = WorkflowExecutionError("etl", "validate-step", cause=original)
    msg = err.message
    has_cause = "bad input" in msg
    assert has_cause is True, "Message should contain the cause description"
    return


def test_workflow_execution_error_repr():
    """
        Verify that __repr__ includes class name, workflow name, step id, and cause.
    """
    err = WorkflowExecutionError("wf-x", "step-y", cause=RuntimeError("boom"))
    repr_str = repr(err)
    has_class = "WorkflowExecutionError" in repr_str
    has_name = "wf-x" in repr_str
    has_step = "step-y" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_name is True, "repr should contain the workflow name"
    assert has_step is True, "repr should contain the step id"
    return


# =========================================================================
# WorkflowCheckpointError tests (Requirements 20.5, 20.6, 20.9)
# =========================================================================

def test_workflow_checkpoint_error_inherits_from_agentkit_error():
    """
        Verify that WorkflowCheckpointError inherits from AgentKitError.
    """
    err = WorkflowCheckpointError("exec-123", "save")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "WorkflowCheckpointError should inherit from AgentKitError"
    return


def test_workflow_checkpoint_error_execution_id_property():
    """
        Verify that the execution_id property returns the provided identifier.
    """
    err = WorkflowCheckpointError("exec-abc", "load")
    exec_id = err.execution_id
    assert exec_id == "exec-abc", "execution_id should be 'exec-abc'"
    return


def test_workflow_checkpoint_error_operation_property():
    """
        Verify that the operation property returns the provided operation name.
    """
    err = WorkflowCheckpointError("exec-1", "save")
    op = err.operation
    assert op == "save", "operation should be 'save'"
    return


def test_workflow_checkpoint_error_cause_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = WorkflowCheckpointError("exec-1", "load")
    cause = err.cause
    assert cause is None, "Cause should be None when not provided"
    return


def test_workflow_checkpoint_error_cause_with_exception():
    """
        Verify that cause stores the provided exception.
    """
    original = IOError("disk full")
    err = WorkflowCheckpointError("exec-1", "save", cause=original)
    cause = err.cause
    assert cause is original, "Cause should be the original exception"
    return


def test_workflow_checkpoint_error_message_without_cause():
    """
        Verify that the message includes execution id and operation.
    """
    err = WorkflowCheckpointError("exec-42", "save")
    msg = err.message
    has_exec = "exec-42" in msg
    has_op = "save" in msg
    assert has_exec is True, "Message should contain the execution id"
    assert has_op is True, "Message should contain the operation"
    return


def test_workflow_checkpoint_error_message_with_cause():
    """
        Verify that the message includes the cause when provided.
    """
    original = IOError("connection lost")
    err = WorkflowCheckpointError("exec-42", "load", cause=original)
    msg = err.message
    has_cause = "connection lost" in msg
    assert has_cause is True, "Message should contain the cause description"
    return


def test_workflow_checkpoint_error_repr():
    """
        Verify that __repr__ includes class name, execution id, and operation.
    """
    err = WorkflowCheckpointError("exec-99", "save", cause=IOError("fail"))
    repr_str = repr(err)
    has_class = "WorkflowCheckpointError" in repr_str
    has_exec = "exec-99" in repr_str
    has_op = "save" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_exec is True, "repr should contain the execution id"
    assert has_op is True, "repr should contain the operation"
    return


# =========================================================================
# ApprovalTimeoutError tests (Requirements 20.7, 20.8, 20.9)
# =========================================================================

def test_approval_timeout_error_inherits_from_agentkit_error():
    """
        Verify that ApprovalTimeoutError inherits from AgentKitError.
    """
    err = ApprovalTimeoutError("req-1", "step-a", 60.0)
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "ApprovalTimeoutError should inherit from AgentKitError"
    return


def test_approval_timeout_error_request_id_property():
    """
        Verify that the request_id property returns the provided identifier.
    """
    err = ApprovalTimeoutError("req-abc", "step-x", 120.0)
    req_id = err.request_id
    assert req_id == "req-abc", "request_id should be 'req-abc'"
    return


def test_approval_timeout_error_step_id_property():
    """
        Verify that the step_id property returns the provided step identifier.
    """
    err = ApprovalTimeoutError("req-1", "approval-step", 300.0)
    step = err.step_id
    assert step == "approval-step", "step_id should be 'approval-step'"
    return


def test_approval_timeout_error_timeout_property():
    """
        Verify that the timeout property returns the provided duration.
    """
    err = ApprovalTimeoutError("req-1", "step-a", 3600.0)
    timeout = err.timeout
    assert timeout == 3600.0, "timeout should be 3600.0"
    return


def test_approval_timeout_error_message_format():
    """
        Verify that the message includes request id, step id, and timeout.
    """
    err = ApprovalTimeoutError("req-7", "step-b", 45.5)
    msg = err.message
    has_req = "req-7" in msg
    has_step = "step-b" in msg
    has_timeout = "45.5" in msg
    assert has_req is True, "Message should contain the request id"
    assert has_step is True, "Message should contain the step id"
    assert has_timeout is True, "Message should contain the timeout value"
    return


def test_approval_timeout_error_repr():
    """
        Verify that __repr__ includes class name, request id, step id, and timeout.
    """
    err = ApprovalTimeoutError("req-10", "step-c", 90.0)
    repr_str = repr(err)
    has_class = "ApprovalTimeoutError" in repr_str
    has_req = "req-10" in repr_str
    has_step = "step-c" in repr_str
    has_timeout = "90.0" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_req is True, "repr should contain the request id"
    assert has_step is True, "repr should contain the step id"
    assert has_timeout is True, "repr should contain the timeout"
    return


# =========================================================================
# Cross-cutting: all errors catchable as AgentKitError (Requirement 20.9)
# =========================================================================

def test_all_workflow_errors_catchable_as_agentkit_error():
    """
        Verify that all workflow exceptions can be caught as AgentKitError.
    """
    exceptions = [
        WorkflowDefinitionError("wf", "detail"),
        WorkflowExecutionError("wf", "step"),
        WorkflowCheckpointError("exec", "save"),
        ApprovalTimeoutError("req", "step", 60.0),
    ]

    for exc in exceptions:
        caught = False
        try:
            raise exc
        except AgentKitError:
            caught = True

        assert caught is True, "{} should be catchable as AgentKitError".format(type(exc).__name__)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
