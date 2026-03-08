"""
    Property-based tests for the File I/O round-trip property.

    Contains a property-based test (using automojo.testbase.properties) that validates
    writing content with FileWriteTool and reading it back with
    FileReadTool produces the original content string.

    Feature: tool-capability-system
"""

import os
import shutil
import tempfile

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.builtins.filereadtool import FileReadTool
from automojo.agentkit.builtins.filewritetool import FileWriteTool


# ---------------------------------------------------------------------------
# Property 24: File I/O round-trip
# Feature: tool-capability-system, Property 24: File I/O round-trip
# **Validates: Requirements 9.2, 9.6**
# ---------------------------------------------------------------------------

@given(
    content=st.text(
        alphabet=st.characters(
            categories=("L", "N", "P", "Z"),
        ).filter(lambda c: c != "\x00"),
        min_size=0,
        max_size=500,
    ),
    settings=settings(max_examples=100),
)
def test_property_24_file_io_round_trip(content):
    """
        Property 24: File I/O round-trip.

        For any string content and valid file path, executing FileWriteTool
        to write the content and then FileReadTool to read it back shall
        produce the original content string.

        **Validates: Requirements 9.2, 9.6**
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "roundtrip_test.txt")

        write_tool = FileWriteTool()
        read_tool = FileReadTool()

        write_inputs = {
            "file_path": file_path,
            "content": content,
            "encoding": "utf-8",
        }
        write_result = write_tool.execute(inputs=write_inputs)

        bytes_written = write_result["bytes_written"]
        expected_bytes = len(content.encode("utf-8"))

        assert bytes_written == expected_bytes, (
            "bytes_written mismatch: {} != {}".format(
                bytes_written, expected_bytes
            )
        )

        read_inputs = {
            "file_path": file_path,
            "encoding": "utf-8",
        }
        read_result = read_tool.execute(inputs=read_inputs)

        read_content = read_result["content"]

        assert read_content == content, (
            "Round-trip content mismatch: {!r} != {!r}".format(
                read_content, content
            )
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


from automojo.agentkit.toolerrors import ToolExecutionError


# ---------------------------------------------------------------------------
# Unit tests for FileReadTool
# Feature: tool-capability-system, Task 10.7
# **Validates: Requirements 9.1, 9.2, 9.3, 9.4**
# ---------------------------------------------------------------------------


def test_filereadtool_reads_known_content_from_temp_file():
    """
        FileReadTool reads a real temporary file with known content and
        returns the expected content string.

        **Validates: Requirements 9.2**
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "read_test.txt")
        expected_content = "Hello from AutomationX!"

        with open(file_path, mode="w", encoding="utf-8") as fh:
            fh.write(expected_content)

        tool = FileReadTool()

        inputs = {
            "file_path": file_path,
            "encoding": "utf-8",
        }

        result = tool.execute(inputs=inputs)

        actual_content = result["content"]
        assert actual_content == expected_content, (
            "Content mismatch: {!r} != {!r}".format(actual_content, expected_content)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_filereadtool_file_not_found_raises_tool_execution_error():
    """
        FileReadTool raises ToolExecutionError when the specified file
        does not exist.

        **Validates: Requirements 9.3**
    """
    tool = FileReadTool()

    inputs = {
        "file_path": "/tmp/nonexistent_file_automationx_test_12345.txt",
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
        "Expected ToolExecutionError for file not found"
    )

    assert caught_error.tool_name == "file_read", (
        "tool_name mismatch: {!r}".format(caught_error.tool_name)
    )

    return


def test_filereadtool_permission_error_raises_tool_execution_error():
    """
        FileReadTool raises ToolExecutionError when the file cannot be
        read due to a permission error.

        **Validates: Requirements 9.4**
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "noperm_test.txt")

        with open(file_path, mode="w", encoding="utf-8") as fh:
            fh.write("secret content")

        os.chmod(file_path, 0o000)

        tool = FileReadTool()

        inputs = {
            "file_path": file_path,
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
            "Expected ToolExecutionError for permission denied"
        )

        assert caught_error.tool_name == "file_read", (
            "tool_name mismatch: {!r}".format(caught_error.tool_name)
        )
    finally:
        # Restore permissions for cleanup
        os.chmod(os.path.join(temp_dir, "noperm_test.txt"), 0o644)
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
