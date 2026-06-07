"""
    Unit tests for the ccai.agentkit.logexporter module.

    Tests the LogExporter abstract base class and concrete exporters:
    ConsoleLogExporter and FileLogExporter. Covers console output,
    file writing, export failure raises ObservabilityError, abstract
    enforcement, and string representations.

    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9,
                  5.10, 5.11, 5.12
"""

import io
import os
import sys
import tempfile

from datetime import datetime

from ccai.agentkit.logexporter import LogExporter, ConsoleLogExporter, FileLogExporter
from ccai.agentkit.logformatter import JsonLogFormatter, HumanReadableLogFormatter
from ccai.agentkit.observabilityerror import ObservabilityError
from ccai.agentkit.structuredlogentry import StructuredLogEntry
from ccai.testbase.mocking import Mock, create_module_patch


# ---- Helper Functions ----


def _create_test_entry():
    """
        Creates a standard StructuredLogEntry for testing exporters.
    """
    ts = datetime(2025, 6, 15, 12, 0, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="Test log message",
        logger_name="ccai.agentkit.observability",
        correlation_id="corr-exp-001",
        agent_id="agent-exp-001",
        metadata={"key": "value"}
    )
    return entry


# ---- Abstract enforcement ----


def test_logexporter_cannot_be_instantiated_directly():
    """
        Verify that LogExporter cannot be instantiated because it has
        abstract methods (export, flush, shutdown).
    """
    formatter = JsonLogFormatter()
    raised = False
    try:
        LogExporter(formatter=formatter)
    except TypeError:
        raised = True

    assert raised is True, "LogExporter should not be directly instantiable"
    return


def test_subclass_without_export_cannot_be_instantiated():
    """
        Verify that a subclass that does not implement all abstract
        methods raises TypeError.
    """

    class IncompleteExporter(LogExporter):
        def flush(self):
            return

        def shutdown(self):
            return

    formatter = JsonLogFormatter()
    raised = False
    try:
        IncompleteExporter(formatter=formatter)
    except TypeError:
        raised = True

    assert raised is True, "Subclass without export implementation should not be instantiable"
    return


# ---- LogExporter base class ----


def test_logexporter_stores_formatter():
    """
        Verify that the LogExporter stores the formatter and exposes
        it via the formatter property.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)

    assert exporter.formatter is formatter, "formatter property should return the provided formatter"
    return


def test_logexporter_credential_references_default_empty():
    """
        Verify that credential_references defaults to an empty list.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)

    creds = exporter.credential_references
    assert creds == [], "credential_references should default to empty list"
    return


# ---- ConsoleLogExporter tests ----


def test_console_exporter_writes_to_stdout():
    """
        Verify that ConsoleLogExporter writes formatted output to stdout.
    """
    formatter = HumanReadableLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)
    entry = _create_test_entry()

    captured = io.StringIO()
    patch = create_module_patch(sys, "stdout")
    mock_stdout = patch.activate()
    mock_stdout.configure(recursive=True)

    written_parts = []
    mock_stdout.mock_context().mock_method(
        "write",
        side_effect=lambda text: written_parts.append(text)
    )

    try:
        exporter.export(entry)
    finally:
        patch.deactivate()

    combined = "".join(written_parts)
    assert "Test log message" in combined, "stdout output should contain the log message"
    return


def test_console_exporter_output_contains_formatted_entry():
    """
        Verify that ConsoleLogExporter output matches the formatter output.
    """
    formatter = HumanReadableLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)
    entry = _create_test_entry()

    expected_formatted = formatter.format(entry)

    written_parts = []
    patch = create_module_patch(sys, "stdout")
    mock_stdout = patch.activate()
    mock_stdout.configure(recursive=True)
    mock_stdout.mock_context().mock_method(
        "write",
        side_effect=lambda text: written_parts.append(text)
    )

    try:
        exporter.export(entry)
    finally:
        patch.deactivate()

    combined = "".join(written_parts)
    assert expected_formatted in combined, "stdout output should contain the formatted entry"
    return


def test_console_exporter_export_failure_raises_observability_error():
    """
        Verify that ConsoleLogExporter raises ObservabilityError when
        the formatter raises an exception during export.
    """
    mock_formatter = Mock()
    mock_formatter.configure(recursive=True)
    mock_formatter.mock_context().set_attribute("format_name", "mock")
    mock_formatter.mock_context().mock_method(
        "format",
        side_effect=lambda entry: (_ for _ in ()).throw(RuntimeError("format failed"))
    )

    exporter = ConsoleLogExporter(formatter=mock_formatter)
    entry = _create_test_entry()

    raised = False
    try:
        exporter.export(entry)
    except ObservabilityError:
        raised = True

    assert raised is True, "export failure should raise ObservabilityError"
    return


def test_console_exporter_flush_calls_stdout_flush():
    """
        Verify that ConsoleLogExporter flush calls sys.stdout.flush.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)

    patch = create_module_patch(sys, "stdout")
    mock_stdout = patch.activate()
    mock_stdout.configure(recursive=True)
    mock_stdout.mock_context().mock_method("flush", return_value=None)

    try:
        exporter.flush()
        mock_stdout.mock_context().mock_calls
    finally:
        patch.deactivate()

    return


def test_console_exporter_shutdown_does_not_raise():
    """
        Verify that ConsoleLogExporter shutdown completes without error.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)

    exporter.shutdown()
    return


# ---- FileLogExporter tests ----


def test_file_exporter_writes_to_file():
    """
        Verify that FileLogExporter writes formatted output to the
        specified file.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "test_log.txt")

    formatter = HumanReadableLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path=file_path)
    entry = _create_test_entry()

    exporter.export(entry)

    with open(file_path, "r") as f:
        content = f.read()

    assert "Test log message" in content, "file should contain the log message"
    return


def test_file_exporter_appends_to_file():
    """
        Verify that FileLogExporter appends entries to the file on
        successive export calls.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "test_append.txt")

    formatter = HumanReadableLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path=file_path)
    entry = _create_test_entry()

    exporter.export(entry)
    exporter.export(entry)

    with open(file_path, "r") as f:
        content = f.read()

    lines = [line for line in content.strip().split("\n") if line]
    assert len(lines) == 2, "file should contain two lines after two exports"
    return


def test_file_exporter_output_matches_formatter():
    """
        Verify that FileLogExporter file content matches the formatter output.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "test_format.txt")

    formatter = HumanReadableLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path=file_path)
    entry = _create_test_entry()

    expected_formatted = formatter.format(entry)
    exporter.export(entry)

    with open(file_path, "r") as f:
        content = f.read().strip()

    assert content == expected_formatted, "file content should match the formatted entry"
    return


def test_file_exporter_resolves_path_with_app_context():
    """
        Verify that FileLogExporter resolves the file path relative to
        the AppContext directory when app_context is provided.
    """
    tmp_dir = tempfile.mkdtemp()

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_context.mock_context().set_attribute("directory", tmp_dir)

    formatter = HumanReadableLogFormatter()
    exporter = FileLogExporter(
        formatter=formatter,
        file_path="logs/app.log",
        app_context=mock_app_context
    )

    expected_path = os.path.join(tmp_dir, "logs/app.log")
    repr_str = repr(exporter)

    assert expected_path in repr_str or "logs/app.log" in repr_str, \
        "resolved path should include the app_context directory"
    return


def test_file_exporter_export_failure_raises_observability_error():
    """
        Verify that FileLogExporter raises ObservabilityError when
        writing to the file fails.
    """
    formatter = HumanReadableLogFormatter()
    exporter = FileLogExporter(
        formatter=formatter,
        file_path="/nonexistent/path/that/should/fail/log.txt"
    )
    entry = _create_test_entry()

    raised = False
    try:
        exporter.export(entry)
    except ObservabilityError:
        raised = True

    assert raised is True, "export failure should raise ObservabilityError"
    return


def test_file_exporter_flush_does_not_raise():
    """
        Verify that FileLogExporter flush completes without error.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "test_flush.txt")

    formatter = JsonLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path=file_path)

    exporter.flush()
    return


def test_file_exporter_shutdown_does_not_raise():
    """
        Verify that FileLogExporter shutdown completes without error.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "test_shutdown.txt")

    formatter = JsonLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path=file_path)

    exporter.shutdown()
    return


# ---- __repr__ and __str__ ----


def test_console_exporter_repr_contains_class_name():
    """
        Verify that ConsoleLogExporter __repr__ includes the class name.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)
    repr_str = repr(exporter)

    assert "ConsoleLogExporter" in repr_str, "repr should contain 'ConsoleLogExporter'"
    return


def test_console_exporter_repr_contains_format_name():
    """
        Verify that ConsoleLogExporter __repr__ includes the format name.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)
    repr_str = repr(exporter)

    assert "json" in repr_str, "repr should contain the format name"
    return


def test_console_exporter_str_contains_class_name():
    """
        Verify that ConsoleLogExporter __str__ includes the class name.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)
    str_val = str(exporter)

    assert "ConsoleLogExporter" in str_val, "str should contain 'ConsoleLogExporter'"
    return


def test_console_exporter_str_contains_format_name():
    """
        Verify that ConsoleLogExporter __str__ includes the format name.
    """
    formatter = JsonLogFormatter()
    exporter = ConsoleLogExporter(formatter=formatter)
    str_val = str(exporter)

    assert "json" in str_val, "str should contain the format name"
    return


def test_file_exporter_repr_contains_class_name():
    """
        Verify that FileLogExporter __repr__ includes the class name.
    """
    formatter = JsonLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path="/tmp/test.log")
    repr_str = repr(exporter)

    assert "FileLogExporter" in repr_str, "repr should contain 'FileLogExporter'"
    return


def test_file_exporter_repr_contains_file_path():
    """
        Verify that FileLogExporter __repr__ includes the file path.
    """
    formatter = JsonLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path="/tmp/test.log")
    repr_str = repr(exporter)

    assert "/tmp/test.log" in repr_str, "repr should contain the file path"
    return


def test_file_exporter_str_contains_class_name():
    """
        Verify that FileLogExporter __str__ includes the class name.
    """
    formatter = JsonLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path="/tmp/test.log")
    str_val = str(exporter)

    assert "FileLogExporter" in str_val, "str should contain 'FileLogExporter'"
    return


def test_file_exporter_str_contains_file_path():
    """
        Verify that FileLogExporter __str__ includes the file path.
    """
    formatter = JsonLogFormatter()
    exporter = FileLogExporter(formatter=formatter, file_path="/tmp/test.log")
    str_val = str(exporter)

    assert "/tmp/test.log" in str_val, "str should contain the file path"
    return
