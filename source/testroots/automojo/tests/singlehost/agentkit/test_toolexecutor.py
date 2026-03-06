"""
    Property-based tests for the automojo.agentkit.toolexecutor module.

    Contains property-based tests (using automojo.testbase.properties) for the ToolExecutor class,
    validating input validation rejection, output validation rejection, and
    correct ToolResult construction based on execution outcome.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite
from automojo.agentkit.tool import Tool
from automojo.agentkit.toolexecutor import ToolExecutor
from automojo.agentkit.toolerrors import ToolValidationError
from automojo.agentkit.toolresult import ToolResult
from automojo.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# testbase property strategies for generating ToolExecutor-related inputs
# ---------------------------------------------------------------------------

# Strategy for generating valid tool names (non-empty alphanumeric strings)
tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating a supported type string
supported_type_strategy = st.sampled_from(sorted(ToolSchema.SUPPORTED_TYPES))

# Strategy for generating a parameter name
param_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)


# Map from schema type names to testbase property strategies that produce values
# of the WRONG type for that parameter.
_WRONG_TYPE_STRATEGIES = {
    "string": st.integers(min_value=-1000, max_value=1000),
    "integer": st.text(min_size=1, max_size=10),
    "float": st.text(min_size=1, max_size=10),
    "boolean": st.integers(min_value=-1000, max_value=1000),
    "list": st.text(min_size=1, max_size=10),
    "dictionary": st.text(min_size=1, max_size=10),
}

# Map from schema type names to testbase property strategies that produce values
# of the CORRECT type for that parameter.
_CORRECT_TYPE_STRATEGIES = {
    "string": st.text(min_size=0, max_size=30),
    "integer": st.integers(min_value=-10000, max_value=10000),
    "float": st.floats(min_value=-10000.0, max_value=10000.0),
    "boolean": st.booleans(),
    "list": st.lists(st.integers(), max_size=5),
    "dictionary": st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.integers(),
        max_size=3
    ),
}


def _make_tool_class(name, input_schema_dict, output_schema_dict, execute_fn=None):
    """
        Creates a concrete Tool subclass with the given class-level constants
        and an optional custom execute function.

        :param name: The TOOL_NAME value.
        :param input_schema_dict: The INPUT_SCHEMA dictionary or None.
        :param output_schema_dict: The OUTPUT_SCHEMA dictionary or None.
        :param execute_fn: An optional callable for the execute method.

        :returns: A concrete Tool subclass type.
    """

    class DynamicTool(Tool):
        """
            A concrete Tool subclass for testing ToolExecutor.
        """

        TOOL_NAME = name
        TOOL_DESCRIPTION = "A dynamic test tool"
        TOOL_VERSION = "1.0.0"
        INPUT_SCHEMA = input_schema_dict
        OUTPUT_SCHEMA = output_schema_dict

        def execute(self, inputs: dict, credentials: dict = None) -> dict:
            """
                Executes the tool, delegating to execute_fn if provided.

                :param inputs: Validated input dictionary.
                :param credentials: Optional dictionary of resolved credentials.

                :returns: Output dictionary.
            """
            if execute_fn is not None:
                rtnval = execute_fn(inputs, credentials)
            else:
                rtnval = {}
            return rtnval

    return DynamicTool



@composite
def required_param_strategy(draw):
    """
        Generates a single required parameter definition dictionary with
        a unique name and a supported type.

        :returns: A dictionary representing a required parameter definition.
    """
    name = draw(param_name_strategy)
    param_type = draw(supported_type_strategy)

    rtnval = {
        "name": name,
        "type": param_type,
        "required": True,
    }
    return rtnval


@composite
def schema_with_required_params_strategy(draw, min_params=1, max_params=4):
    """
        Generates a valid schema dictionary containing at least one required
        parameter, with unique parameter names.

        :param min_params: Minimum number of parameters.
        :param max_params: Maximum number of parameters.

        :returns: A dictionary with a 'parameters' key.
    """
    count = draw(st.integers(min_value=min_params, max_value=max_params))
    params = []
    used_names = set()

    for _ in range(count):
        param = draw(required_param_strategy())
        param_name = param["name"]

        while param_name in used_names:
            param_name = draw(param_name_strategy)

        param["name"] = param_name
        used_names.add(param_name)
        params.append(param)

    rtnval = {"parameters": params}
    return rtnval


# ---------------------------------------------------------------------------
# Property 12: ToolExecutor validates input and rejects invalid inputs
# Feature: tool-capability-system, Property 12: ToolExecutor validates input and rejects invalid inputs
# **Validates: Requirements 5.1, 5.2**
# ---------------------------------------------------------------------------

@composite
def _invalid_input_data(draw):
    """
        Generates a tool name, input schema, invalidation mode, and a wrong
        value for testing input validation rejection.

        :returns: A tuple of (tool_name, input_schema_dict, invalidation_mode, wrong_value).
    """
    tool_name = draw(tool_name_strategy)
    input_schema_dict = draw(schema_with_required_params_strategy(min_params=1, max_params=4))
    invalidation_mode = draw(st.sampled_from(["missing", "wrong_type"]))

    # Pick a wrong value based on the first parameter's type
    first_param_type = input_schema_dict["parameters"][0]["type"]
    wrong_value = draw(_WRONG_TYPE_STRATEGIES[first_param_type])

    return (tool_name, input_schema_dict, invalidation_mode, wrong_value)


@given(
    test_data=_invalid_input_data(),
    settings=settings(max_examples=100)
)
def test_property_12_toolexecutor_validates_input_and_rejects_invalid_inputs(test_data):
    """
        Property 12: ToolExecutor validates input and rejects invalid inputs.

        For any Tool and any input dictionary that fails the Tool's input
        ToolSchema validation, the ToolExecutor shall raise ToolValidationError
        containing the validation error strings, without invoking the Tool's
        execute method.

        **Validates: Requirements 5.1, 5.2**
    """
    tool_name, input_schema_dict, invalidation_mode, wrong_value = test_data

    # Track whether execute was called
    execute_tracker = {"called": False}

    def tracking_execute(inputs, credentials):
        """
            An execute function that records whether it was invoked.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :returns: An empty dictionary.
        """
        execute_tracker["called"] = True
        rtnval = {}
        return rtnval

    tool_cls = _make_tool_class(
        name=tool_name,
        input_schema_dict=input_schema_dict,
        output_schema_dict=None,
        execute_fn=tracking_execute,
    )
    tool = tool_cls()

    # Choose an invalidation strategy: either missing required params or wrong types
    params = input_schema_dict["parameters"]

    if invalidation_mode == "missing":
        # Provide an empty dict so all required params are missing
        invalid_inputs = {}
    else:
        # Provide values with wrong types for each parameter
        invalid_inputs = {}
        for param_def in params:
            param_name = param_def["name"]
            param_type = param_def["type"]
            invalid_inputs[param_name] = wrong_value

    executor = ToolExecutor()

    raised = False
    caught_error = None
    try:
        executor.execute(tool=tool, inputs=invalid_inputs)
    except ToolValidationError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "ToolExecutor should raise ToolValidationError for invalid inputs, "
        "mode='{}', inputs={!r}".format(invalidation_mode, invalid_inputs)
    )

    # Verify the error contains validation error strings
    assert len(caught_error.errors) > 0, (
        "ToolValidationError should contain at least one error string"
    )

    # Verify direction is "input"
    assert caught_error.direction == "input", (
        "ToolValidationError direction should be 'input', got: {!r}".format(
            caught_error.direction
        )
    )

    # Verify tool name is set
    assert caught_error.tool_name == tool_name, (
        "ToolValidationError tool_name should be '{}', got: {!r}".format(
            tool_name, caught_error.tool_name
        )
    )

    # Verify execute was NOT called
    assert execute_tracker["called"] is False, (
        "Tool.execute should NOT have been called when input validation fails"
    )

    return


# ---------------------------------------------------------------------------
# Property 13: ToolExecutor validates output and rejects invalid outputs
# Feature: tool-capability-system, Property 13: ToolExecutor validates output and rejects invalid outputs
# **Validates: Requirements 5.4, 5.5**
# ---------------------------------------------------------------------------

@composite
def _invalid_output_data(draw):
    """
        Generates a tool name, output schema, invalidation mode, and a wrong
        value for testing output validation rejection.

        :returns: A tuple of (tool_name, output_schema_dict, invalidation_mode, wrong_value).
    """
    tool_name = draw(tool_name_strategy)
    output_schema_dict = draw(schema_with_required_params_strategy(min_params=1, max_params=4))
    invalidation_mode = draw(st.sampled_from(["missing", "wrong_type"]))

    # Pick a wrong value based on the first parameter's type
    first_param_type = output_schema_dict["parameters"][0]["type"]
    wrong_value = draw(_WRONG_TYPE_STRATEGIES[first_param_type])

    return (tool_name, output_schema_dict, invalidation_mode, wrong_value)


@given(
    test_data=_invalid_output_data(),
    settings=settings(max_examples=100)
)
def test_property_13_toolexecutor_validates_output_and_rejects_invalid_outputs(test_data):
    """
        Property 13: ToolExecutor validates output and rejects invalid outputs.

        For any Tool whose execute method returns output that fails the Tool's
        output ToolSchema validation, the ToolExecutor shall raise
        ToolValidationError containing the output validation error strings.

        **Validates: Requirements 5.4, 5.5**
    """
    tool_name, output_schema_dict, invalidation_mode, wrong_value = test_data

    output_params = output_schema_dict["parameters"]

    # Choose an invalidation strategy for the output

    if invalidation_mode == "missing":
        # Return an empty dict so all required output params are missing
        bad_output = {}
    else:
        # Return values with wrong types for each output parameter
        bad_output = {}
        for param_def in output_params:
            param_name = param_def["name"]
            param_type = param_def["type"]
            bad_output[param_name] = wrong_value

    def bad_execute(inputs, credentials):
        """
            An execute function that returns invalid output.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :returns: A dictionary with invalid output values.
        """
        rtnval = dict(bad_output)
        return rtnval

    tool_cls = _make_tool_class(
        name=tool_name,
        input_schema_dict=None,
        output_schema_dict=output_schema_dict,
        execute_fn=bad_execute,
    )
    tool = tool_cls()

    executor = ToolExecutor()

    raised = False
    caught_error = None
    try:
        executor.execute(tool=tool, inputs={})
    except ToolValidationError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "ToolExecutor should raise ToolValidationError for invalid output, "
        "mode='{}', output={!r}".format(invalidation_mode, bad_output)
    )

    # Verify the error contains validation error strings
    assert len(caught_error.errors) > 0, (
        "ToolValidationError should contain at least one error string"
    )

    # Verify direction is "output"
    assert caught_error.direction == "output", (
        "ToolValidationError direction should be 'output', got: {!r}".format(
            caught_error.direction
        )
    )

    # Verify tool name is set
    assert caught_error.tool_name == tool_name, (
        "ToolValidationError tool_name should be '{}', got: {!r}".format(
            tool_name, caught_error.tool_name
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 14: ToolExecutor returns correct ToolResult based on execution outcome
# Feature: tool-capability-system, Property 14: ToolExecutor returns correct ToolResult based on execution outcome
# **Validates: Requirements 5.6, 5.7**
# ---------------------------------------------------------------------------

@composite
def _valid_output_data(draw):
    """
        Generates a tool name, output schema, and a dictionary of valid values
        for testing successful execution result construction.

        :returns: A tuple of (tool_name, output_schema_dict, valid_output).
    """
    tool_name = draw(tool_name_strategy)
    output_schema_dict = draw(schema_with_required_params_strategy(min_params=1, max_params=3))

    # Build valid output that matches each parameter's type
    valid_output = {}
    for param_def in output_schema_dict["parameters"]:
        param_name = param_def["name"]
        param_type = param_def["type"]
        valid_output[param_name] = draw(_CORRECT_TYPE_STRATEGIES[param_type])

    return (tool_name, output_schema_dict, valid_output)


@given(
    test_data=_valid_output_data(),
    settings=settings(max_examples=100)
)
def test_property_14_toolexecutor_returns_correct_toolresult_on_success(test_data):
    """
        Property 14 (success case): ToolExecutor returns correct ToolResult
        based on execution outcome.

        For any Tool and valid input, when execute succeeds with valid output,
        the ToolExecutor returns a ToolResult with success status, the output
        value, and a non-negative duration.

        **Validates: Requirements 5.6**
    """
    tool_name, output_schema_dict, valid_output = test_data

    def success_execute(inputs, credentials):
        """
            An execute function that returns valid output.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :returns: A dictionary with valid output values.
        """
        rtnval = dict(valid_output)
        return rtnval

    tool_cls = _make_tool_class(
        name=tool_name,
        input_schema_dict=None,
        output_schema_dict=output_schema_dict,
        execute_fn=success_execute,
    )
    tool = tool_cls()

    executor = ToolExecutor()
    result = executor.execute(tool=tool, inputs={})

    # Verify result is a ToolResult
    assert isinstance(result, ToolResult), (
        "ToolExecutor.execute should return a ToolResult, got: {}".format(
            type(result).__name__
        )
    )

    # Verify success status
    assert result.status == ToolResult.STATUS_SUCCESS, (
        "ToolResult status should be '{}', got: {!r}".format(
            ToolResult.STATUS_SUCCESS, result.status
        )
    )

    assert result.is_success is True, (
        "ToolResult.is_success should be True for success status"
    )

    # Verify output matches
    assert result.output == valid_output, (
        "ToolResult output should match the tool's output, "
        "expected: {!r}, got: {!r}".format(valid_output, result.output)
    )

    # Verify non-negative duration
    assert result.duration >= 0.0, (
        "ToolResult duration should be non-negative, got: {}".format(result.duration)
    )

    # Verify tool name
    assert result.tool_name == tool_name, (
        "ToolResult tool_name should be '{}', got: {!r}".format(
            tool_name, result.tool_name
        )
    )

    # Verify no error
    assert result.error is None, (
        "ToolResult error should be None on success, got: {!r}".format(result.error)
    )

    return


@given(
    tool_name=tool_name_strategy,
    error_message=st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z")),
        min_size=1,
        max_size=50
    ),
    settings=settings(max_examples=100)
)
def test_property_14_toolexecutor_returns_correct_toolresult_on_failure(tool_name, error_message):
    """
        Property 14 (failure case): ToolExecutor returns correct ToolResult
        based on execution outcome.

        For any Tool and valid input, when execute raises an exception, the
        ToolExecutor returns a ToolResult with failure status, the exception
        information, and a non-negative duration.

        **Validates: Requirements 5.7**
    """

    def failing_execute(inputs, credentials):
        """
            An execute function that always raises a RuntimeError.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :raises RuntimeError: Always raised with the generated error message.
        """
        raise RuntimeError(error_message)

    tool_cls = _make_tool_class(
        name=tool_name,
        input_schema_dict=None,
        output_schema_dict=None,
        execute_fn=failing_execute,
    )
    tool = tool_cls()

    executor = ToolExecutor()
    result = executor.execute(tool=tool, inputs={})

    # Verify result is a ToolResult
    assert isinstance(result, ToolResult), (
        "ToolExecutor.execute should return a ToolResult, got: {}".format(
            type(result).__name__
        )
    )

    # Verify failure status
    assert result.status == ToolResult.STATUS_FAILURE, (
        "ToolResult status should be '{}', got: {!r}".format(
            ToolResult.STATUS_FAILURE, result.status
        )
    )

    assert result.is_success is False, (
        "ToolResult.is_success should be False for failure status"
    )

    # Verify non-negative duration
    assert result.duration >= 0.0, (
        "ToolResult duration should be non-negative, got: {}".format(result.duration)
    )

    # Verify tool name
    assert result.tool_name == tool_name, (
        "ToolResult tool_name should be '{}', got: {!r}".format(
            tool_name, result.tool_name
        )
    )

    # Verify error is present and is the expected exception
    assert result.error is not None, (
        "ToolResult error should not be None on failure"
    )

    assert isinstance(result.error, RuntimeError), (
        "ToolResult error should be a RuntimeError, got: {}".format(
            type(result.error).__name__
        )
    )

    assert str(result.error) == error_message, (
        "ToolResult error message should be '{}', got: {!r}".format(
            error_message, str(result.error)
        )
    )

    return


# ---------------------------------------------------------------------------
# Additional imports for unit tests
# ---------------------------------------------------------------------------

import logging

from automojo.agentkit.errors import ConfigurationError
from automojo.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Logging capture helper
# ---------------------------------------------------------------------------

class _LogCapture(logging.Handler):
    """
        A logging handler that captures log records for test assertions.
    """

    def __init__(self):
        super().__init__()
        self.records = []
        return

    def emit(self, record):
        """
            Stores the emitted log record.

            :param record: The log record to capture.
        """
        self.records.append(record)
        return


# ---------------------------------------------------------------------------
# Unit Tests for ToolExecutor
# ---------------------------------------------------------------------------


def test_credential_resolution_success():
    """
        Verifies that when a tool declares credential_names and the executor
        has a mock credential_resolver that returns values, execute succeeds
        and the resolved credentials are passed to tool.execute.

        **Validates: Requirements 5.9**
    """
    received_credentials = {}

    def capture_execute(inputs, credentials):
        """
            Captures the credentials dictionary passed to execute.

            :param inputs: The input dictionary.
            :param credentials: The resolved credentials dictionary.

            :returns: An empty dictionary.
        """
        received_credentials.update(credentials)
        rtnval = {}
        return rtnval

    tool_cls = _make_tool_class(
        name="cred_tool",
        input_schema_dict=None,
        output_schema_dict=None,
        execute_fn=capture_execute,
    )
    tool = tool_cls(credential_names=["api_key", "db_password"])

    mock_resolver = Mock()
    mock_resolver.configure(recursive=True)

    resolve_values = {
        "api_key": "secret_api_key_value",
        "db_password": "secret_db_password_value",
    }

    def resolve_side_effect(name):
        """
            Returns a credential value for the given name.

            :param name: The credential name to resolve.

            :returns: The resolved credential value.
        """
        rtnval = resolve_values[name]
        return rtnval

    mock_resolver.mock_context().mock_method("resolve", side_effect=resolve_side_effect)

    executor = ToolExecutor(credential_resolver=mock_resolver)
    result = executor.execute(tool=tool, inputs={})

    assert result.is_success is True, (
        "Execution should succeed when credentials are resolved"
    )
    assert received_credentials.get("api_key") == "secret_api_key_value", (
        "Credential 'api_key' should be passed to tool.execute"
    )
    assert received_credentials.get("db_password") == "secret_db_password_value", (
        "Credential 'db_password' should be passed to tool.execute"
    )

    return


def test_credential_resolution_failure_raises_configuration_error():
    """
        Verifies that when a tool declares credential_names and the mock
        credential_resolver raises an exception during resolve, the executor
        raises a ConfigurationError.

        **Validates: Requirements 5.10**
    """
    tool_cls = _make_tool_class(
        name="cred_fail_tool",
        input_schema_dict=None,
        output_schema_dict=None,
    )
    tool = tool_cls(credential_names=["missing_secret"])

    mock_resolver = Mock()
    mock_resolver.configure(recursive=True)

    def resolve_failure(name):
        """
            Raises a RuntimeError simulating credential resolution failure.

            :param name: The credential name to resolve.

            :raises RuntimeError: Always raised.
        """
        raise RuntimeError("Credential not found: {}".format(name))

    mock_resolver.mock_context().mock_method("resolve", side_effect=resolve_failure)

    executor = ToolExecutor(credential_resolver=mock_resolver)

    raised = False
    caught_error = None
    try:
        executor.execute(tool=tool, inputs={})
    except ConfigurationError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "ToolExecutor should raise ConfigurationError when credential resolution fails"
    )
    assert "missing_secret" in caught_error.message, (
        "ConfigurationError message should contain the credential name"
    )

    return


def test_no_credential_resolver_raises_configuration_error():
    """
        Verifies that when a tool declares credential_names but the executor
        has no credential_resolver configured, the executor raises a
        ConfigurationError.

        **Validates: Requirements 5.10**
    """
    tool_cls = _make_tool_class(
        name="no_resolver_tool",
        input_schema_dict=None,
        output_schema_dict=None,
    )
    tool = tool_cls(credential_names=["some_credential"])

    executor = ToolExecutor(credential_resolver=None)

    raised = False
    caught_error = None
    try:
        executor.execute(tool=tool, inputs={})
    except ConfigurationError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "ToolExecutor should raise ConfigurationError when no credential_resolver is configured"
    )
    assert "no_resolver_tool" in caught_error.message, (
        "ConfigurationError message should contain the tool name"
    )

    return


def test_logging_info_on_begin_and_success():
    """
        Verifies that the ToolExecutor logs at INFO level when execution
        begins and when execution completes successfully.

        **Validates: Requirements 17.1, 17.2, 17.3**
    """
    tool_cls = _make_tool_class(
        name="log_success_tool",
        input_schema_dict=None,
        output_schema_dict=None,
        execute_fn=lambda inputs, credentials: {},
    )
    tool = tool_cls()

    logger = logging.getLogger("automojo.agentkit.tools")
    handler = _LogCapture()
    logger.addHandler(handler)
    original_level = logger.level
    logger.setLevel(logging.DEBUG)

    try:
        executor = ToolExecutor()
        executor.execute(tool=tool, inputs={}, agent_identifier="test-agent")

        info_records = [r for r in handler.records if r.levelno == logging.INFO]

        assert len(info_records) >= 2, (
            "Expected at least 2 INFO log records (begin and success), got: {}".format(
                len(info_records)
            )
        )

        begin_found = False
        success_found = False
        for record in info_records:
            msg = record.getMessage()
            if "log_success_tool" in msg and "Executing" in msg:
                begin_found = True
            if "log_success_tool" in msg and "successfully" in msg:
                success_found = True

        assert begin_found is True, (
            "Expected an INFO log record for execution begin containing the tool name"
        )
        assert success_found is True, (
            "Expected an INFO log record for execution success containing the tool name"
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)

    return


def test_logging_warning_on_failure():
    """
        Verifies that the ToolExecutor logs at WARNING level when tool
        execution fails with an exception.

        **Validates: Requirements 17.4**
    """

    def failing_execute(inputs, credentials):
        """
            An execute function that always raises a ValueError.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :raises ValueError: Always raised.
        """
        raise ValueError("Something went wrong")

    tool_cls = _make_tool_class(
        name="log_fail_tool",
        input_schema_dict=None,
        output_schema_dict=None,
        execute_fn=failing_execute,
    )
    tool = tool_cls()

    logger = logging.getLogger("automojo.agentkit.tools")
    handler = _LogCapture()
    logger.addHandler(handler)
    original_level = logger.level
    logger.setLevel(logging.DEBUG)

    try:
        executor = ToolExecutor()
        executor.execute(tool=tool, inputs={})

        warning_records = [r for r in handler.records if r.levelno == logging.WARNING]

        assert len(warning_records) >= 1, (
            "Expected at least 1 WARNING log record on execution failure, got: {}".format(
                len(warning_records)
            )
        )

        failure_logged = False
        for record in warning_records:
            msg = record.getMessage()
            if "log_fail_tool" in msg and "failed" in msg:
                failure_logged = True

        assert failure_logged is True, (
            "Expected a WARNING log record for execution failure containing the tool name"
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)

    return


def test_execution_duration_is_recorded():
    """
        Verifies that the ToolResult returned by ToolExecutor has a
        non-negative float duration value.

        **Validates: Requirements 5.6**
    """
    tool_cls = _make_tool_class(
        name="duration_tool",
        input_schema_dict=None,
        output_schema_dict=None,
        execute_fn=lambda inputs, credentials: {},
    )
    tool = tool_cls()

    executor = ToolExecutor()
    result = executor.execute(tool=tool, inputs={})

    assert isinstance(result.duration, float), (
        "ToolResult.duration should be a float, got: {}".format(
            type(result.duration).__name__
        )
    )
    assert result.duration >= 0.0, (
        "ToolResult.duration should be non-negative, got: {}".format(result.duration)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
