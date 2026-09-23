"""
    Unit tests for the ccai.agentkit.builtins.filewritetool module.

    Contains unit tests for FileWriteTool verifying file writing,
    bytes_written output, and permission error handling.

    Feature: tool-capability-system
"""

import os
import shutil
import tempfile

from ccai.agentkit.builtins.filewritetool import FileWriteTool
from ccai.agentkit.toolerrors import ToolExecutionError


# ---------------------------------------------------------------------------
# Unit tests for FileWriteTool
# Feature: tool-capability-system, Task 10.7
# **Validates: Requirements 9.5, 9.6, 9.7**
# ---------------------------------------------------------------------------


def test_filewritetool_writes_content_to_temp_file():
    """
        FileWriteTool writes content to a real temporary file and the
        file contains the expected content when read back.

        **Validates: Requirements 9.6**
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "write_test.txt")
        tool = FileWriteTool()

        inputs = {
            "file_path": file_path,
            "content": "Hello, CodeCraftX!",
            "encoding": "utf-8",
        }

        tool.execute(inputs=inputs)

        file_exists = os.path.isfile(file_path)
        assert file_exists is True, (
            "File should exist after writing: {}".format(file_path)
        )

        with open(file_path, mode="r", encoding="utf-8") as fh:
            actual_content = fh.read()

        assert actual_content == "Hello, CodeCraftX!", (
            "File content mismatch: {!r}".format(actual_content)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_filewritetool_bytes_written_matches_expected():
    """
        FileWriteTool returns a bytes_written value that matches the
        byte length of the content encoded in the specified encoding.

        **Validates: Requirements 9.6**
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "bytes_test.txt")
        tool = FileWriteTool()

        content = "café résumé"
        expected_bytes = len(content.encode("utf-8"))

        inputs = {
            "file_path": file_path,
            "content": content,
            "encoding": "utf-8",
        }

        result = tool.execute(inputs=inputs)

        bytes_written = result["bytes_written"]
        assert bytes_written == expected_bytes, (
            "bytes_written mismatch: {} != {}".format(bytes_written, expected_bytes)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_filewritetool_permission_error_raises_tool_execution_error():
    """
        FileWriteTool raises ToolExecutionError when the file cannot be
        written due to a permission error.

        **Validates: Requirements 9.7**
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "readonly_test.txt")

        # Create the file and make the directory read-only
        with open(file_path, mode="w", encoding="utf-8") as fh:
            fh.write("original")

        os.chmod(file_path, 0o444)
        os.chmod(temp_dir, 0o555)

        tool = FileWriteTool()

        inputs = {
            "file_path": file_path,
            "content": "new content",
            "encoding": "utf-8",
        }

        raised = False
        caught_error = None

        try:
            tool.execute(inputs=inputs)
        except ToolExecutionError as exec_err:
            raised = True
            caught_error = exec_err

        assert raised is True, (
            "Expected ToolExecutionError for permission denied write"
        )

        assert caught_error.tool_name == "file_write", (
            "tool_name mismatch: {!r}".format(caught_error.tool_name)
        )
    finally:
        # Restore permissions for cleanup
        os.chmod(temp_dir, 0o755)
        os.chmod(os.path.join(temp_dir, "readonly_test.txt"), 0o644)
        shutil.rmtree(temp_dir, ignore_errors=True)

    return
