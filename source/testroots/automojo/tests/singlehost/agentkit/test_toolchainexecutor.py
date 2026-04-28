"""
    Property-based tests for the automojo.agentkit.toolchainexecutor module.

    Contains property-based tests (using automojo.testbase.properties) for the ToolChainExecutor
    class, validating sequential execution with mappings and correct result
    construction based on step outcomes.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite
from automojo.agentkit.tool import Tool
from automojo.agentkit.toolchain import ToolChain
from automojo.agentkit.toolchainexecutor import ToolChainExecutor
from automojo.agentkit.toolchainresult import ToolChainResult
from automojo.agentkit.toolexecutor import ToolExecutor
from automojo.agentkit.toolregistry import ToolRegistry
from automojo.agentkit.toolresult import ToolResult
from automojo.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# testbase property strategies
# ---------------------------------------------------------------------------

# Strategy for generating valid tool names (non-empty alphanumeric strings)
tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)


# ---------------------------------------------------------------------------
# Helper: dynamic Tool subclass factory with execute tracking
# ---------------------------------------------------------------------------

def _make_tracking_tool_class(name, input_schema_dict=None, output_schema_dict=None,
                               execute_fn=None):
    """
        Creates a concrete Tool subclass that delegates execute to a callable.

        :param name: The TOOL_NAME value.
        :param input_schema_dict: The INPUT_SCHEMA dictionary or None.
        :param output_schema_dict: The OUTPUT_SCHEMA dictionary or None.
        :param execute_fn: A callable for the execute method.

        :returns: A concrete Tool subclass type.
    """

    class TrackingTool(Tool):
        """
            A concrete Tool subclass that tracks execution for testing.
        """

        TOOL_NAME = name
        TOOL_DESCRIPTION = "Tracking test tool: {}".format(name)
        TOOL_VERSION = "1.0.0"
        INPUT_SCHEMA = input_schema_dict
        OUTPUT_SCHEMA = output_schema_dict

        def execute(self, inputs: dict, credentials: dict = None) -> dict:
            """
                Delegates to the provided execute_fn.

                :param inputs: Validated input dictionary.
                :param credentials: Optional dictionary of resolved credentials.

                :returns: Output dictionary from execute_fn.
            """
            if execute_fn is not None:
                rtnval = execute_fn(inputs, credentials)
            else:
                rtnval = {}
            return rtnval

    return TrackingTool


# ---------------------------------------------------------------------------
# Property 19: ToolChainExecutor executes steps in sequence with mappings
# Feature: tool-capability-system, Property 19: ToolChainExecutor executes steps in sequence with mappings
# **Validates: Requirements 7.6, 7.7**
# ---------------------------------------------------------------------------

@given(
    step_count=st.integers(min_value=2, max_value=3),
    initial_value=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=20
    ),
    constraints={"max_examples": 100}
)
def test_property_19_toolchainexecutor_executes_steps_in_sequence_with_mappings(step_count, initial_value):
    """
        Property 19: ToolChainExecutor executes steps in sequence with mappings.

        For any valid ToolChain with N steps and input-output mappings, the
        ToolChainExecutor shall execute each step in order, applying the
        mappings to pass output fields from the previous step as input fields
        to the next step.

        **Validates: Requirements 7.6, 7.7**
    """
    # Generate a chain of 2 or 3 steps

    # Use a simple pipeline: each tool takes a "value" string input and
    # outputs a "result" string. Mappings map "result" -> "value" between steps.
    execution_order = []
    received_inputs_by_step = {}

    input_schema_dict = {
        "parameters": [
            {"name": "value", "type": "string", "required": True}
        ]
    }
    output_schema_dict = {
        "parameters": [
            {"name": "result", "type": "string", "required": True}
        ]
    }

    registry = ToolRegistry()
    tool_names = []

    for step_idx in range(step_count):
        tool_name = "step_tool_{}".format(step_idx)
        tool_names.append(tool_name)

        # Capture step_idx in closure
        def make_execute(idx):
            """
                Creates an execute function that records execution order
                and transforms the input value.

                :param idx: The step index for tracking.

                :returns: An execute callable.
            """
            def execute_fn(inputs, credentials):
                """
                    Records execution and transforms the value.

                    :param inputs: The input dictionary.
                    :param credentials: The credentials dictionary.

                    :returns: A dictionary with a 'result' key.
                """
                execution_order.append(idx)
                received_inputs_by_step[idx] = dict(inputs)
                input_value = inputs.get("value", "")
                rtnval = {"result": "{}_processed_{}".format(input_value, idx)}
                return rtnval

            return execute_fn

        tool_cls = _make_tracking_tool_class(
            name=tool_name,
            input_schema_dict=input_schema_dict,
            output_schema_dict=output_schema_dict,
            execute_fn=make_execute(step_idx),
        )
        registry.register(tool=tool_cls())

    # Build steps with mappings: result -> value for steps after the first
    steps = [{"tool_name": tool_names[0]}]
    for idx in range(1, step_count):
        steps.append({
            "tool_name": tool_names[idx],
            "mappings": {"result": "value"},
        })

    chain = ToolChain(name="sequence_chain", steps=steps, registry=registry)

    initial_inputs = {"value": initial_value}

    executor = ToolExecutor()
    chain_executor = ToolChainExecutor(tool_executor=executor)
    result = chain_executor.execute(chain=chain, initial_inputs=initial_inputs)

    # Verify all steps executed in order
    expected_order = list(range(step_count))
    assert execution_order == expected_order, (
        "Steps should execute in order {}, got: {}".format(
            expected_order, execution_order
        )
    )

    # Verify the first step received the initial inputs
    assert received_inputs_by_step[0]["value"] == initial_value, (
        "Step 0 should receive initial value '{}', got: {!r}".format(
            initial_value, received_inputs_by_step[0].get("value")
        )
    )

    # Verify subsequent steps received mapped outputs from previous steps
    for idx in range(1, step_count):
        prev_output_value = "{}_processed_{}".format(
            received_inputs_by_step[idx - 1]["value"], idx - 1
        )
        actual_input_value = received_inputs_by_step[idx].get("value")
        assert actual_input_value == prev_output_value, (
            "Step {} should receive mapped value '{}', got: {!r}".format(
                idx, prev_output_value, actual_input_value
            )
        )

    # Verify the result is a success
    assert result.is_success is True, (
        "ToolChainResult should be success when all steps succeed"
    )

    return


# ---------------------------------------------------------------------------
# Property 20: ToolChainExecutor returns correct result based on outcome
# Feature: tool-capability-system, Property 20: ToolChainExecutor returns correct result based on outcome
# **Validates: Requirements 7.8, 7.9**
# ---------------------------------------------------------------------------

@given(
    step_count=st.integers(min_value=1, max_value=4),
    constraints={"max_examples": 100}
)
def test_property_20_toolchainexecutor_returns_correct_result_all_succeed(step_count):
    """
        Property 20 (success case): ToolChainExecutor returns correct result
        based on outcome.

        When all steps succeed, the ToolChainResult has success status, the
        final step output, N ToolResult objects, and a non-negative total
        duration.

        **Validates: Requirements 7.8**
    """

    registry = ToolRegistry()
    tool_names = []

    for step_idx in range(step_count):
        tool_name = "success_tool_{}".format(step_idx)
        tool_names.append(tool_name)

        def make_execute(idx):
            """
                Creates an execute function that returns a success output.

                :param idx: The step index.

                :returns: An execute callable.
            """
            def execute_fn(inputs, credentials):
                """
                    Returns a simple output dictionary.

                    :param inputs: The input dictionary.
                    :param credentials: The credentials dictionary.

                    :returns: A dictionary with an 'output_value' key.
                """
                rtnval = {"output_value": "result_from_step_{}".format(idx)}
                return rtnval

            return execute_fn

        tool_cls = _make_tracking_tool_class(
            name=tool_name,
            execute_fn=make_execute(step_idx),
        )
        registry.register(tool=tool_cls())

    steps = [{"tool_name": name} for name in tool_names]
    chain = ToolChain(name="all_success_chain", steps=steps, registry=registry)

    executor = ToolExecutor()
    chain_executor = ToolChainExecutor(tool_executor=executor)
    result = chain_executor.execute(chain=chain, initial_inputs={})

    # Verify success status
    assert result.is_success is True, (
        "ToolChainResult should be success when all steps succeed"
    )
    assert result.status == ToolChainResult.STATUS_SUCCESS, (
        "ToolChainResult status should be '{}', got: {!r}".format(
            ToolChainResult.STATUS_SUCCESS, result.status
        )
    )

    # Verify final step output
    expected_final_output = {"output_value": "result_from_step_{}".format(step_count - 1)}
    assert result.output == expected_final_output, (
        "ToolChainResult output should be {!r}, got: {!r}".format(
            expected_final_output, result.output
        )
    )

    # Verify N ToolResult objects
    assert len(result.step_results) == step_count, (
        "ToolChainResult should have {} step_results, got: {}".format(
            step_count, len(result.step_results)
        )
    )

    for step_result in result.step_results:
        assert isinstance(step_result, ToolResult), (
            "Each step_result should be a ToolResult, got: {}".format(
                type(step_result).__name__
            )
        )
        assert step_result.is_success is True, (
            "Each step_result should be success"
        )

    # Verify non-negative total duration
    assert result.duration >= 0.0, (
        "ToolChainResult duration should be non-negative, got: {}".format(
            result.duration
        )
    )

    # Verify no error
    assert result.error is None, (
        "ToolChainResult error should be None on success, got: {!r}".format(
            result.error
        )
    )

    return


@composite
def _fail_at_step_data(draw):
    """
        Generates a total_steps count and a fail_at_step index within range.

        :returns: A tuple of (total_steps, fail_at_step).
    """
    total_steps = draw(st.integers(min_value=2, max_value=4))
    fail_at_step = draw(st.integers(min_value=0, max_value=total_steps - 1))
    return (total_steps, fail_at_step)


@given(
    test_data=_fail_at_step_data(),
    constraints={"max_examples": 100}
)
def test_property_20_toolchainexecutor_returns_correct_result_step_fails(test_data):
    """
        Property 20 (failure case): ToolChainExecutor returns correct result
        based on outcome.

        When step K fails, execution stops and the ToolChainResult has failure
        status with results for steps 0..K.

        **Validates: Requirements 7.9**
    """
    # Create a chain of 2-4 steps where one step fails
    total_steps, fail_at_step = test_data

    execution_tracker = []

    registry = ToolRegistry()
    tool_names = []

    for step_idx in range(total_steps):
        tool_name = "fail_chain_tool_{}".format(step_idx)
        tool_names.append(tool_name)

        def make_execute(idx, should_fail):
            """
                Creates an execute function that either succeeds or fails.

                :param idx: The step index.
                :param should_fail: Whether this step should raise an exception.

                :returns: An execute callable.
            """
            def execute_fn(inputs, credentials):
                """
                    Records execution and optionally raises an error.

                    :param inputs: The input dictionary.
                    :param credentials: The credentials dictionary.

                    :returns: A dictionary with an 'out' key, or raises RuntimeError.
                """
                execution_tracker.append(idx)
                if should_fail is True:
                    raise RuntimeError("Step {} failed".format(idx))
                rtnval = {"out": "ok_{}".format(idx)}
                return rtnval

            return execute_fn

        should_fail = (step_idx == fail_at_step)
        tool_cls = _make_tracking_tool_class(
            name=tool_name,
            execute_fn=make_execute(step_idx, should_fail),
        )
        registry.register(tool=tool_cls())

    steps = [{"tool_name": name} for name in tool_names]
    chain = ToolChain(name="fail_chain", steps=steps, registry=registry)

    executor = ToolExecutor()
    chain_executor = ToolChainExecutor(tool_executor=executor)
    result = chain_executor.execute(chain=chain, initial_inputs={})

    # Verify failure status
    assert result.is_success is False, (
        "ToolChainResult should be failure when step {} fails".format(fail_at_step)
    )
    assert result.status == ToolChainResult.STATUS_FAILURE, (
        "ToolChainResult status should be '{}', got: {!r}".format(
            ToolChainResult.STATUS_FAILURE, result.status
        )
    )

    # Verify execution stopped at the failing step
    expected_executed = list(range(fail_at_step + 1))
    assert execution_tracker == expected_executed, (
        "Only steps 0..{} should have executed, got: {}".format(
            fail_at_step, execution_tracker
        )
    )

    # Verify step_results contains results for steps 0..K
    expected_result_count = fail_at_step + 1
    assert len(result.step_results) == expected_result_count, (
        "ToolChainResult should have {} step_results (0..{}), got: {}".format(
            expected_result_count, fail_at_step, len(result.step_results)
        )
    )

    # Verify the last step_result is a failure
    last_result = result.step_results[-1]
    assert last_result.is_success is False, (
        "The failing step's result should have failure status"
    )

    # Verify all preceding step_results are successes
    for idx in range(fail_at_step):
        assert result.step_results[idx].is_success is True, (
            "Step {} result should be success, got failure".format(idx)
        )

    # Verify non-negative total duration
    assert result.duration >= 0.0, (
        "ToolChainResult duration should be non-negative, got: {}".format(
            result.duration
        )
    )

    # Verify error is present
    assert result.error is not None, (
        "ToolChainResult error should not be None on failure"
    )

    return


# ---------------------------------------------------------------------------
# Unit tests for ToolChainExecutor
# ---------------------------------------------------------------------------

def test_single_step_chain_execution():
    """
        Verifies that executing a single-step chain through ToolChainExecutor
        produces a success ToolChainResult with the correct output and one
        step result.

        **Validates: Requirements 7.6, 7.8**
    """
    def execute_fn(inputs, credentials):
        """
            Returns a simple output dictionary.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :returns: A dictionary with a 'greeting' key.
        """
        rtnval = {"greeting": "hello {}".format(inputs.get("name", "world"))}
        return rtnval

    input_schema_dict = {
        "parameters": [
            {"name": "name", "type": "string", "required": True}
        ]
    }
    output_schema_dict = {
        "parameters": [
            {"name": "greeting", "type": "string", "required": True}
        ]
    }

    tool_cls = _make_tracking_tool_class(
        name="greeter",
        input_schema_dict=input_schema_dict,
        output_schema_dict=output_schema_dict,
        execute_fn=execute_fn,
    )

    registry = ToolRegistry()
    registry.register(tool=tool_cls())

    steps = [{"tool_name": "greeter"}]
    chain = ToolChain(name="single_chain", steps=steps, registry=registry)

    executor = ToolExecutor()
    chain_executor = ToolChainExecutor(tool_executor=executor)
    result = chain_executor.execute(chain=chain, initial_inputs={"name": "AutomationX"})

    assert result.is_success is True, (
        "ToolChainResult should be success for a single-step chain"
    )

    expected_output = {"greeting": "hello AutomationX"}
    assert result.output == expected_output, (
        "Output should be {!r}, got: {!r}".format(expected_output, result.output)
    )

    assert len(result.step_results) == 1, (
        "Should have 1 step result, got: {}".format(len(result.step_results))
    )

    assert result.step_results[0].is_success is True, (
        "The single step result should be success"
    )

    assert result.duration >= 0.0, (
        "Duration should be non-negative, got: {}".format(result.duration)
    )

    return


def test_chain_passthrough_without_mappings():
    """
        Verifies that executing a multi-step chain with no mappings passes
        the previous step's output directly as the next step's input.

        **Validates: Requirements 7.6, 7.7, 7.8**
    """
    received_inputs = {}

    def make_execute(step_name):
        """
            Creates an execute function that records received inputs and
            returns a known output.

            :param step_name: The name of the step for tracking.

            :returns: An execute callable.
        """
        def execute_fn(inputs, credentials):
            """
                Records inputs and returns a passthrough output.

                :param inputs: The input dictionary.
                :param credentials: The credentials dictionary.

                :returns: A dictionary with a 'data' key.
            """
            received_inputs[step_name] = dict(inputs)
            rtnval = {"data": "{}_done".format(step_name)}
            return rtnval

        return execute_fn

    registry = ToolRegistry()

    tool_a_cls = _make_tracking_tool_class(
        name="step_a",
        execute_fn=make_execute("step_a"),
    )
    tool_b_cls = _make_tracking_tool_class(
        name="step_b",
        execute_fn=make_execute("step_b"),
    )

    registry.register(tool=tool_a_cls())
    registry.register(tool=tool_b_cls())

    steps = [
        {"tool_name": "step_a"},
        {"tool_name": "step_b"},
    ]
    chain = ToolChain(name="passthrough_chain", steps=steps, registry=registry)

    executor = ToolExecutor()
    chain_executor = ToolChainExecutor(tool_executor=executor)
    result = chain_executor.execute(chain=chain, initial_inputs={"seed": "start"})

    assert result.is_success is True, (
        "ToolChainResult should be success when all steps succeed"
    )

    # Step A should receive the initial inputs
    assert received_inputs["step_a"] == {"seed": "start"}, (
        "Step A should receive initial inputs, got: {!r}".format(
            received_inputs.get("step_a")
        )
    )

    # Step B should receive step A's output directly (no mappings = pass-through)
    assert received_inputs["step_b"] == {"data": "step_a_done"}, (
        "Step B should receive step A's output as pass-through, got: {!r}".format(
            received_inputs.get("step_b")
        )
    )

    assert len(result.step_results) == 2, (
        "Should have 2 step results, got: {}".format(len(result.step_results))
    )

    expected_output = {"data": "step_b_done"}
    assert result.output == expected_output, (
        "Final output should be {!r}, got: {!r}".format(expected_output, result.output)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
