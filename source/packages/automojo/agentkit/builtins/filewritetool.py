"""
    Built-in tool for writing content to a file.

    Provides the FileWriteTool class which writes string content to a file
    at a specified path and returns the number of bytes written.
"""

import os

from automojo.agentkit.tool import Tool
from automojo.agentkit.toolerrors import ToolExecutionError


class FileWriteTool(Tool):
    """
        Writes content to a file at the specified path.

        Accepts required file_path and content parameters, and an optional
        encoding parameter (defaulting to utf-8). Returns the number of
        bytes written. Raises ToolExecutionError for permission errors.
    """

    TOOL_NAME = "file_write"
    TOOL_DESCRIPTION = "Writes content to a file at the specified path."
    TOOL_VERSION = "1.0.0"

    INPUT_SCHEMA = {
        "parameters": [
            {
                "name": "file_path",
                "type": "string",
                "required": True,
                "description": "Path to the file to write.",
            },
            {
                "name": "content",
                "type": "string",
                "required": True,
                "description": "Content to write.",
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
                "name": "bytes_written",
                "type": "integer",
                "required": True,
                "description": "Number of bytes written.",
            },
        ]
    }

    def execute(self, inputs: dict, credentials: dict = None) -> dict:
        """
            Writes content to the file specified by the inputs.

            :param inputs: Dictionary containing 'file_path', 'content', and optional 'encoding'.
            :param credentials: Optional dictionary of resolved credentials (unused).

            :returns: A dictionary with a 'bytes_written' key containing the byte count.

            :raises: ToolExecutionError
        """
        file_path = inputs["file_path"]
        content = inputs["content"]
        encoding = inputs.get("encoding", "utf-8")

        try:
            content_bytes = content.encode(encoding)
            with open(file_path, mode="wb") as file_handle:
                file_handle.write(content_bytes)
        except PermissionError as perm_err:
            err_msg_lines = [
                "Permission denied writing file: '{}'.".format(file_path),
                "DETAIL: {}".format(str(perm_err)),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ToolExecutionError(tool_name=self.TOOL_NAME, cause=PermissionError(err_msg)) from perm_err

        bytes_written = len(content_bytes)

        rtnval = {"bytes_written": bytes_written}

        return rtnval
