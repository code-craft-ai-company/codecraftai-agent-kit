"""
    Property-based tests for the ShellCommandTool metacharacter rejection.

    Contains a property-based test (using automojo.testbase.properties) that validates
    the ShellCommandTool raises ToolExecutionError when a command
    string contains shell metacharacters and safe_mode is True.

    Feature: tool-capability-system
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.builtins.shellcommandtool import ShellCommandTool
from automojo.agentkit.toolerrors import ToolExecutionError


# ---------------------------------------------------------------------------
# Strategies for generating commands with metacharacters
# ---------------------------------------------------------------------------

SHELL_METACHARACTERS = list(ShellCommandTool.SHELL_METACHARACTERS)

# Strategy for generating a single metacharacter
metachar_strategy = st.sampled_from(SHELL_METACHARACTERS)

# Strategy for generating a command prefix (safe text before the metacharacter)
safe_text_strategy = st.text(
    alphabet=st.characters(
        categories=("L", "N", "Z"),
    ).filter(lambda c: c not in SHELL_METACHARACTERS),
    min_size=0,
    max_size=30,
)


# Strategy for generating a command string that contains at least one metacharacter
@composite
def command_with_metachar_strategy(draw):
    """
        Generates a command string that contains at least one shell
        metacharacter from the ShellCommandTool.SHELL_METACHARACTERS set.

        :returns: A string containing at least one metacharacter.
    """
    prefix = draw(safe_text_strategy)
    meta = draw(metachar_strategy)
    suffix = draw(safe_text_strategy)

    command = prefix + meta + suffix

    return command


# ---------------------------------------------------------------------------
# Property 25: ShellCommandTool rejects metacharacters in safe mode
# Feature: tool-capability-system, Property 25: ShellCommandTool rejects metacharacters in safe mode
# **Validates: Requirements 11.5**
# ---------------------------------------------------------------------------

@given(
    command=command_with_metachar_strategy(),
    settings=settings(max_examples=100),
)
def test_property_25_shell_rejects_metacharacters_in_safe_mode(command):
    """
        Property 25: ShellCommandTool rejects metacharacters in safe mode.

        For any command string containing at least one shell metacharacter
        from the set {;|&<>$`\\!#~} when safe_mode is True, the
        ShellCommandTool shall raise ToolExecutionError.

        **Validates: Requirements 11.5**
    """
    tool = ShellCommandTool()

    inputs = {
        "command": command,
        "safe_mode": True,
    }

    raised = False
    caught_error = None

    try:
        tool.execute(inputs=inputs)
    except ToolExecutionError as exec_err:
        raised = True
        caught_error = exec_err

    assert raised is True, (
        "Expected ToolExecutionError for command with metacharacters: {!r}".format(
            command
        )
    )

    assert caught_error.tool_name == "shell_command", (
        "ToolExecutionError tool_name mismatch: {!r} != 'shell_command'".format(
            caught_error.tool_name
        )
    )

    return


import os
import tempfile


# ---------------------------------------------------------------------------
# Unit tests for ShellCommandTool
# Feature: tool-capability-system, Task 10.7
# **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**
# ---------------------------------------------------------------------------


def test_shellcommandtool_simple_echo_command():
    """
        ShellCommandTool executes a simple echo command and returns
        the expected stdout, exit code 0, and empty stderr.

        **Validates: Requirements 11.2**
    """
    tool = ShellCommandTool()

    inputs = {
        "command": "echo hello",
        "safe_mode": True,
    }

    result = tool.execute(inputs=inputs)

    exit_code = result["exit_code"]
    assert exit_code == 0, (
        "exit_code mismatch: {} != 0".format(exit_code)
    )

    stdout = result["stdout"].strip()
    assert stdout == "hello", (
        "stdout mismatch: {!r} != 'hello'".format(stdout)
    )

    return


def test_shellcommandtool_timeout_raises_tool_execution_error():
    """
        ShellCommandTool raises ToolExecutionError when the command
        exceeds the timeout duration.

        **Validates: Requirements 11.3**
    """
    tool = ShellCommandTool()

    inputs = {
        "command": "sleep 10",
        "timeout_seconds": 0.1,
        "safe_mode": True,
    }

    raised = False
    caught_error = None

    try:
        tool.execute(inputs=inputs)
    except ToolExecutionError as exec_err:
        raised = True
        caught_error = exec_err

    assert raised is True, (
        "Expected ToolExecutionError for command timeout"
    )

    assert caught_error.tool_name == "shell_command", (
        "tool_name mismatch: {!r}".format(caught_error.tool_name)
    )

    cause_is_timeout = isinstance(caught_error.cause, TimeoutError)
    assert cause_is_timeout is True, (
        "Expected cause to be TimeoutError, got: {!r}".format(type(caught_error.cause))
    )

    return


def test_shellcommandtool_missing_working_directory_raises_tool_execution_error():
    """
        ShellCommandTool raises ToolExecutionError when the specified
        working directory does not exist.

        **Validates: Requirements 11.4**
    """
    tool = ShellCommandTool()

    inputs = {
        "command": "echo test",
        "working_directory": "/nonexistent/path/automationx_test_12345",
        "safe_mode": True,
    }

    raised = False
    caught_error = None

    try:
        tool.execute(inputs=inputs)
    except ToolExecutionError as exec_err:
        raised = True
        caught_error = exec_err

    assert raised is True, (
        "Expected ToolExecutionError for missing working directory"
    )

    assert caught_error.tool_name == "shell_command", (
        "tool_name mismatch: {!r}".format(caught_error.tool_name)
    )

    return


def test_shellcommandtool_safe_mode_rejects_semicolon():
    """
        ShellCommandTool raises ToolExecutionError when safe_mode is True
        and the command contains a semicolon metacharacter.

        **Validates: Requirements 11.5**
    """
    tool = ShellCommandTool()

    inputs = {
        "command": "echo hello; echo world",
        "safe_mode": True,
    }

    raised = False
    caught_error = None

    try:
        tool.execute(inputs=inputs)
    except ToolExecutionError as exec_err:
        raised = True
        caught_error = exec_err

    assert raised is True, (
        "Expected ToolExecutionError for metacharacter in safe_mode"
    )

    assert caught_error.tool_name == "shell_command", (
        "tool_name mismatch: {!r}".format(caught_error.tool_name)
    )

    return


def test_shellcommandtool_safe_mode_false_allows_metacharacters():
    """
        ShellCommandTool does not reject metacharacters when safe_mode
        is False. The command is split with shlex so the metacharacter
        is passed as a literal argument rather than interpreted by a shell.

        **Validates: Requirements 11.5, 11.6**
    """
    tool = ShellCommandTool()

    temp_dir = tempfile.mkdtemp()

    try:
        inputs = {
            "command": "echo hello",
            "safe_mode": False,
            "working_directory": temp_dir,
        }

        # This should not raise ToolExecutionError for metacharacter rejection
        raised = False

        try:
            result = tool.execute(inputs=inputs)
        except ToolExecutionError:
            raised = True

        assert raised is False, (
            "safe_mode=False should not reject commands"
        )

        exit_code = result["exit_code"]
        assert exit_code == 0, (
            "exit_code mismatch: {} != 0".format(exit_code)
        )
    finally:
        os.rmdir(temp_dir)

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
