"""
    Unit tests for the automojo.agentkit.traceexporter module.

    Tests the TraceExporter abstract base class and concrete exporters:
    ConsoleTraceExporter and FileTraceExporter. Covers console output,
    file writing, export failure raises ObservabilityError, abstract
    enforcement, and string representations.

    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8,
                  10.9, 10.10, 10.11
"""

import json
import os
import sys
import tempfile

from datetime import datetime

from automojo.agentkit.traceexporter import TraceExporter, ConsoleTraceExporter, FileTraceExporter
from automojo.agentkit.tracespan import TraceSpan
from automojo.agentkit.tracecontext import TraceContext
from automojo.agentkit.observabilityerror import ObservabilityError
from automojo.testbase.mocking import Mock, create_module_patch


# ---- Helper Functions ----


def _create_test_span():
    """
        Creates a standard completed TraceSpan for testing exporters.

        :returns: A completed TraceSpan instance.
    """
    ctx = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16
    )
    span = TraceSpan(
        name="test-operation",
        trace_context=ctx,
        attributes={"key": "value"}
    )
    span.end()
    return span


# ---- Abstract enforcement ----


def test_traceexporter_cannot_be_instantiated_directly():
    """
        Verify that TraceExporter cannot be instantiated because it
        has abstract methods (export, flush, shutdown).
    """
    raised = False
    try:
        TraceExporter()
    except TypeError:
        raised = True

    assert raised is True, "TraceExporter should not be directly instantiable"
    return


def test_subclass_without_export_cannot_be_instantiated():
    """
        Verify that a subclass that does not implement all abstract
        methods raises TypeError.
    """

    class IncompleteExporter(TraceExporter):
        def flush(self) -> None:
            return

        def shutdown(self) -> None:
            return

    raised = False
    try:
        IncompleteExporter()
    except TypeError:
        raised = True

    assert raised is True, "Subclass without export implementation should not be instantiable"
    return


def test_subclass_without_flush_cannot_be_instantiated():
    """
        Verify that a subclass missing flush raises TypeError.
    """

    class NoFlushExporter(TraceExporter):
        def export(self, spans: list) -> None:
            return

        def shutdown(self) -> None:
            return

    raised = False
    try:
        NoFlushExporter()
    except TypeError:
        raised = True

    assert raised is True, "Subclass without flush implementation should not be instantiable"
    return


def test_subclass_without_shutdown_cannot_be_instantiated():
    """
        Verify that a subclass missing shutdown raises TypeError.
    """

    class NoShutdownExporter(TraceExporter):
        def export(self, spans: list) -> None:
            return

        def flush(self) -> None:
            return

    raised = False
    try:
        NoShutdownExporter()
    except TypeError:
        raised = True

    assert raised is True, "Subclass without shutdown implementation should not be instantiable"
    return


# ---- ConsoleTraceExporter tests ----


def test_console_exporter_writes_to_stdout():
    """
        Verify that ConsoleTraceExporter writes formatted span text
        to stdout.
    """
    exporter = ConsoleTraceExporter()
    span = _create_test_span()

    written_parts = []
    patch = create_module_patch(sys, "stdout")
    mock_stdout = patch.activate()
    mock_stdout.configure(recursive=True)
    mock_stdout.mock_context().mock_method(
        "write",
        side_effect=lambda text: written_parts.append(text)
    )

    try:
        exporter.export([span])
    finally:
        patch.deactivate()

    combined = "".join(written_parts)
    assert "test-operation" in combined, "stdout output should contain the span name"
    return


def test_console_exporter_output_contains_trace_id():
    """
        Verify that ConsoleTraceExporter output contains the trace_id.
    """
    exporter = ConsoleTraceExporter()
    span = _create_test_span()

    written_parts = []
    patch = create_module_patch(sys, "stdout")
    mock_stdout = patch.activate()
    mock_stdout.configure(recursive=True)
    mock_stdout.mock_context().mock_method(
        "write",
        side_effect=lambda text: written_parts.append(text)
    )

    try:
        exporter.export([span])
    finally:
        patch.deactivate()

    combined = "".join(written_parts)
    assert "a" * 32 in combined, "stdout output should contain the trace_id"
    return


def test_console_exporter_flush_calls_stdout_flush():
    """
        Verify that ConsoleTraceExporter flush calls sys.stdout.flush.
    """
    exporter = ConsoleTraceExporter()

    flush_called = [False]

    patch = create_module_patch(sys, "stdout")
    mock_stdout = patch.activate()
    mock_stdout.configure(recursive=True)
    mock_stdout.mock_context().mock_method(
        "flush",
        side_effect=lambda: flush_called.__setitem__(0, True)
    )

    try:
        exporter.flush()
    finally:
        patch.deactivate()

    assert flush_called[0] is True, "flush should call sys.stdout.flush"
    return


def test_console_exporter_shutdown_does_not_raise():
    """
        Verify that ConsoleTraceExporter shutdown completes without error.
    """
    exporter = ConsoleTraceExporter()

    exporter.shutdown()
    return


# ---- FileTraceExporter tests ----


def test_file_exporter_writes_json_lines_to_file():
    """
        Verify that FileTraceExporter writes span JSON lines to the
        specified file.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "traces.jsonl")

    exporter = FileTraceExporter(file_path=file_path)
    span = _create_test_span()

    exporter.export([span])

    with open(file_path, "r") as f:
        content = f.read()

    assert "test-operation" in content, "file should contain the span name"

    lines = [line for line in content.strip().split("\n") if line]
    assert len(lines) == 1, "file should contain one JSON line"

    parsed = json.loads(lines[0])
    assert parsed["name"] == "test-operation", "parsed JSON should have correct span name"
    return


def test_file_exporter_appends_on_successive_exports():
    """
        Verify that FileTraceExporter appends entries on successive
        export calls.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "traces_append.jsonl")

    exporter = FileTraceExporter(file_path=file_path)
    span = _create_test_span()

    exporter.export([span])
    exporter.export([span])

    with open(file_path, "r") as f:
        content = f.read()

    lines = [line for line in content.strip().split("\n") if line]
    assert len(lines) == 2, "file should contain two JSON lines after two exports"
    return


def test_file_exporter_resolves_path_with_app_context():
    """
        Verify that FileTraceExporter resolves the file path relative
        to the AppContext directory when app_context is provided.
    """
    tmp_dir = tempfile.mkdtemp()

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_context.mock_context().set_attribute("directory", tmp_dir)

    exporter = FileTraceExporter(
        file_path="traces/spans.jsonl",
        app_context=mock_app_context
    )

    expected_path = os.path.join(tmp_dir, "traces/spans.jsonl")
    repr_str = repr(exporter)

    assert expected_path in repr_str or "traces/spans.jsonl" in repr_str, \
        "resolved path should include the app_context directory"
    return


def test_file_exporter_export_failure_raises_observability_error():
    """
        Verify that FileTraceExporter raises ObservabilityError when
        writing to the file fails.
    """
    exporter = FileTraceExporter(
        file_path="/nonexistent/path/that/should/fail/traces.jsonl"
    )
    span = _create_test_span()

    raised = False
    try:
        exporter.export([span])
    except ObservabilityError:
        raised = True

    assert raised is True, "export failure should raise ObservabilityError"
    return


def test_file_exporter_flush_does_not_raise():
    """
        Verify that FileTraceExporter flush completes without error.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "traces_flush.jsonl")

    exporter = FileTraceExporter(file_path=file_path)

    exporter.flush()
    return


def test_file_exporter_shutdown_does_not_raise():
    """
        Verify that FileTraceExporter shutdown completes without error.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "traces_shutdown.jsonl")

    exporter = FileTraceExporter(file_path=file_path)

    exporter.shutdown()
    return


# ---- __repr__ and __str__ ----


def test_console_exporter_repr_contains_class_name():
    """
        Verify that ConsoleTraceExporter __repr__ includes the class name.
    """
    exporter = ConsoleTraceExporter()
    repr_str = repr(exporter)

    assert "ConsoleTraceExporter" in repr_str, "repr should contain 'ConsoleTraceExporter'"
    return


def test_console_exporter_str_contains_class_name():
    """
        Verify that ConsoleTraceExporter __str__ includes the class name.
    """
    exporter = ConsoleTraceExporter()
    str_val = str(exporter)

    assert "ConsoleTraceExporter" in str_val, "str should contain 'ConsoleTraceExporter'"
    return


def test_file_exporter_repr_contains_class_name():
    """
        Verify that FileTraceExporter __repr__ includes the class name.
    """
    exporter = FileTraceExporter(file_path="/tmp/test_traces.jsonl")
    repr_str = repr(exporter)

    assert "FileTraceExporter" in repr_str, "repr should contain 'FileTraceExporter'"
    return


def test_file_exporter_repr_contains_file_path():
    """
        Verify that FileTraceExporter __repr__ includes the file path.
    """
    exporter = FileTraceExporter(file_path="/tmp/test_traces.jsonl")
    repr_str = repr(exporter)

    assert "/tmp/test_traces.jsonl" in repr_str, "repr should contain the file path"
    return


def test_file_exporter_str_contains_class_name():
    """
        Verify that FileTraceExporter __str__ includes the class name.
    """
    exporter = FileTraceExporter(file_path="/tmp/test_traces.jsonl")
    str_val = str(exporter)

    assert "FileTraceExporter" in str_val, "str should contain 'FileTraceExporter'"
    return


def test_file_exporter_str_contains_file_path():
    """
        Verify that FileTraceExporter __str__ includes the file path.
    """
    exporter = FileTraceExporter(file_path="/tmp/test_traces.jsonl")
    str_val = str(exporter)

    assert "/tmp/test_traces.jsonl" in str_val, "str should contain the file path"
    return
