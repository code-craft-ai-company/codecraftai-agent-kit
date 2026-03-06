"""
    Built-in tool for reading file contents.

    Provides the FileReadTool class which reads the contents of a file
    at a specified path and returns the content as a string.
"""

import os

from automojo.agentkit.tool import Tool
from automojo.agentkit.toolerrors import ToolExecutionError


class FileReadTool(Tool):
    """
        Reads the contents of a file at the specified path.

        Accepts a required file_path parameter and an optional encoding
        parameter (defaulting to utf-8). Returns the file contents as
        a string. Raises ToolExecutionError for file-not-found and
        permission errors.
    """

    TOOL_NAME = "file_read"
    TOOL_DESCRIPTION = "Reads the contents of a file at the specified path."
    TOOL_VERSION = "1.0.0"

    INPUT_SCHEMA = {
        "parameters": [
            {
                "name": "file_path",
                "type": "string",
                "required": True,
                "description": "Path to the file to read.",
            },
            {
                "name": "encoding",
                "type": "string",
                "required": False,
                "default": "utf-8",
                "description": "File encoding.",
            },
        ]
    }

    OUTPUT_SCHEMA = {
        "parameters": [
            {
                "name": "content",
                "type": "string",
                "required": True,
                "description": "File contents.",
            },
        ]
    }

    def execute(self, inputs: dict, credentials: dict = None) -> dict:
        """
            Reads the contents of the file specified by the inputs.

            :param inputs: Dictionary containing 'file_path' and optional 'encoding'.
            :param credentials: Optional dictionary of resolved credentials (unused).

            :returns: A dictionary with a 'content' key containing the file contents.

            :raises: ToolExecutionError
        """
        file_path = inputs["file_path"]
        encoding = inputs.get("encoding", "utf-8")

        try:
            with open(file_path, mode="r", encoding=encoding) as file_handle:
                content = file_handle.read()
        except FileNotFoundError as fnf_err:
            err_msg_lines = [
                "File not found: '{}'.".format(file_path),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ToolExecutionError(tool_name=self.TOOL_NAME, cause=FileNotFoundError(err_msg)) from fnf_err
        except PermissionError as perm_err:
            err_msg_lines = [
                "Permission denied reading file: '{}'.".format(file_path),
                "DETAIL: {}".format(str(perm_err)),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ToolExecutionError(tool_name=self.TOOL_NAME, cause=PermissionError(err_msg)) from perm_err

        rtnval = {"content": content}

        return rtnval
