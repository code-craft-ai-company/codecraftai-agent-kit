"""
    Built-in tool for executing shell commands.

    Provides the ShellCommandTool class which executes a shell command
    using subprocess and returns the exit code, stdout, and stderr.
"""

import os
import shlex
import subprocess

from ccai.agentkit.tool import Tool
from ccai.agentkit.toolerrors import ToolExecutionError


class ShellCommandTool(Tool):
    """
        Executes a shell command and returns the output.

        Accepts a required command parameter, and optional working_directory,
        timeout_seconds, environment, and safe_mode parameters. Returns the
        exit code, stdout, and stderr. Raises ToolExecutionError for timeout,
        missing working directory, and shell metacharacter rejection in safe mode.
    """

    TOOL_NAME = "shell_command"
    TOOL_DESCRIPTION = "Executes a shell command and returns the output."
    TOOL_VERSION = "1.0.0"

    INPUT_SCHEMA = {
        "parameters": [
            {
                "name": "command",
                "type": "string",
                "required": True,
                "description": "Shell command to execute.",
            },
            {
                "name": "working_directory",
                "type": "string",
                "required": False,
                "description": "Working directory for command execution.",
            },
            {
                "name": "timeout_seconds",
                "type": "float",
                "required": False,
                "default": 60.0,
                "description": "Command timeout in seconds.",
            },
            {
                "name": "environment",
                "type": "dictionary",
                "required": False,
                "description": "Additional environment variables.",
            },
            {
                "name": "safe_mode",
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Reject commands with shell metacharacters.",
            },
        ]
    }

    OUTPUT_SCHEMA = {
        "parameters": [
            {
                "name": "exit_code",
                "type": "integer",
                "required": True,
                "description": "Process exit code.",
            },
            {
                "name": "stdout",
                "type": "string",
                "required": True,
                "description": "Standard output.",
            },
            {
                "name": "stderr",
                "type": "string",
                "required": True,
                "description": "Standard error.",
            },
        ]
    }

    SHELL_METACHARACTERS = set(";|&$`\\!#~")

    def execute(self, inputs: dict, credentials: dict = None) -> dict:
        """
            Executes the shell command specified by the inputs.

            :param inputs: Dictionary containing 'command' and optional
                'working_directory', 'timeout_seconds', 'environment', 'safe_mode'.
            :param credentials: Optional dictionary of resolved credentials (unused).

            :returns: A dictionary with 'exit_code', 'stdout', and 'stderr' keys.

            :raises: ToolExecutionError
        """
        command = inputs["command"]
        working_directory = inputs.get("working_directory", None)
        timeout_seconds = inputs.get("timeout_seconds", 60.0)
        environment = inputs.get("environment", None)
        safe_mode = inputs.get("safe_mode", True)

        if safe_mode is True:
            self._check_metacharacters(command=command)

        if working_directory is not None:
            if os.path.isdir(working_directory) is not True:
                err_msg_lines = [
                    "Working directory does not exist: '{}'.".format(working_directory),
                ]
                err_msg = os.linesep.join(err_msg_lines)
                raise ToolExecutionError(
                    tool_name=self.TOOL_NAME,
                    cause=FileNotFoundError(err_msg),
                )

        merged_env = None
        if environment is not None:
            merged_env = dict(os.environ)
            merged_env.update(environment)

        command_parts = shlex.split(command)

        try:
            completed = subprocess.run(
                command_parts,
                cwd=working_directory,
                env=merged_env,
                timeout=timeout_seconds,
                capture_output=True,
            )
        except subprocess.TimeoutExpired as timeout_err:
            err_msg_lines = [
                "Shell command timed out.",
                "COMMAND: {}".format(command),
                "TIMEOUT: {} seconds".format(timeout_seconds),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ToolExecutionError(
                tool_name=self.TOOL_NAME,
                cause=TimeoutError(err_msg),
            ) from timeout_err

        exit_code = completed.returncode
        stdout = completed.stdout.decode("utf-8")
        stderr = completed.stderr.decode("utf-8")

        rtnval = {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        }

        return rtnval

    def _check_metacharacters(self, command: str) -> None:
        """
            Checks the command string for shell metacharacters and raises
            ToolExecutionError if any are found.

            :param command: The command string to check.

            :raises: ToolExecutionError
        """
        found_chars = []

        for char in command:
            if char in self.SHELL_METACHARACTERS:
                found_chars.append(char)

        if len(found_chars) > 0:
            err_msg_lines = [
                "Command contains shell metacharacters and safe_mode is enabled.",
                "COMMAND: {}".format(command),
                "METACHARACTERS FOUND: {}".format(", ".join(found_chars)),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ToolExecutionError(
                tool_name=self.TOOL_NAME,
                cause=ValueError(err_msg),
            )

        return
