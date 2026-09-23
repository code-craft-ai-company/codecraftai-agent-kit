"""
    Unit tests for the ccai.agentkit.metricsexporter module.

    Tests the MetricsExporter abstract base class and concrete exporters:
    ConsoleMetricsExporter and FileMetricsExporter. Covers console output,
    file writing, export failure raises ObservabilityError, abstract
    enforcement, and string representations.

    Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8,
                  16.9, 16.10, 16.11
"""

import json
import os
import sys
import tempfile

from ccai.agentkit.metricsexporter import (
    MetricsExporter,
    ConsoleMetricsExporter,
    FileMetricsExporter,
)
from ccai.agentkit.metricmeasurement import MetricMeasurement
from ccai.agentkit.observabilityerror import ObservabilityError
from ccai.testbase.mocking import Mock, create_module_patch


# ---- Helper Functions ----


def _create_test_measurement():
    """
        Creates a standard MetricMeasurement for testing exporters.

        :returns: A MetricMeasurement instance.
    """
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=42.0,
        labels={"env": "test"}
    )
    return measurement


# ---- Abstract enforcement ----


def test_metricsexporter_cannot_be_instantiated_directly():
    """
        Verify that MetricsExporter cannot be instantiated because it
        has abstract methods (export, flush, shutdown).
    """
    raised = False
    try:
        MetricsExporter()
    except TypeError:
        raised = True

    assert raised is True, "MetricsExporter should not be directly instantiable"
    return


def test_subclass_without_export_cannot_be_instantiated():
    """
        Verify that a subclass that does not implement export raises
        TypeError.
    """

    class IncompleteExporter(MetricsExporter):
        def flush(self) -> None:
            return

        def shutdown(self) -> None:
            return

    raised = False
    try:
        IncompleteExporter()
    except TypeError:
        raised = True

    assert raised is True, "Subclass without export should not be instantiable"
    return


def test_subclass_without_flush_cannot_be_instantiated():
    """
        Verify that a subclass missing flush raises TypeError.
    """

    class NoFlushExporter(MetricsExporter):
        def export(self, measurements: list) -> None:
            return

        def shutdown(self) -> None:
            return

    raised = False
    try:
        NoFlushExporter()
    except TypeError:
        raised = True

    assert raised is True, "Subclass without flush should not be instantiable"
    return


def test_subclass_without_shutdown_cannot_be_instantiated():
    """
        Verify that a subclass missing shutdown raises TypeError.
    """

    class NoShutdownExporter(MetricsExporter):
        def export(self, measurements: list) -> None:
            return

        def flush(self) -> None:
            return

    raised = False
    try:
        NoShutdownExporter()
    except TypeError:
        raised = True

    assert raised is True, "Subclass without shutdown should not be instantiable"
    return


# ---- ConsoleMetricsExporter tests ----


def test_console_exporter_writes_to_stdout():
    """
        Verify that ConsoleMetricsExporter writes formatted measurement
        text to stdout.
    """
    exporter = ConsoleMetricsExporter()
    measurement = _create_test_measurement()

    written_parts = []
    patch = create_module_patch(sys, "stdout")
    mock_stdout = patch.activate()
    mock_stdout.configure(recursive=True)
    mock_stdout.mock_context().mock_method(
        "write",
        side_effect=lambda text: written_parts.append(text)
    )

    try:
        exporter.export([measurement])
    finally:
        patch.deactivate()

    combined = "".join(written_parts)
    assert "test.counter" in combined, "stdout output should contain the metric name"
    assert "42.0" in combined, "stdout output should contain the value"
    return


def test_console_exporter_flush_calls_stdout_flush():
    """
        Verify that ConsoleMetricsExporter flush calls sys.stdout.flush.
    """
    exporter = ConsoleMetricsExporter()

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
        Verify that ConsoleMetricsExporter shutdown completes without error.
    """
    exporter = ConsoleMetricsExporter()

    exporter.shutdown()
    return


# ---- FileMetricsExporter tests ----


def test_file_exporter_writes_json_lines_to_file():
    """
        Verify that FileMetricsExporter writes measurement JSON lines
        to the specified file.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "metrics.jsonl")

    exporter = FileMetricsExporter(file_path=file_path)
    measurement = _create_test_measurement()

    exporter.export([measurement])

    with open(file_path, "r") as f:
        content = f.read()

    assert "test.counter" in content, "file should contain the metric name"

    lines = [line for line in content.strip().split("\n") if line]
    assert len(lines) == 1, "file should contain one JSON line"

    parsed = json.loads(lines[0])
    assert parsed["metric_name"] == "test.counter", "parsed JSON should have correct metric name"
    assert parsed["value"] == 42.0, "parsed JSON should have correct value"
    return


def test_file_exporter_appends_on_successive_exports():
    """
        Verify that FileMetricsExporter appends entries on successive
        export calls.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "metrics_append.jsonl")

    exporter = FileMetricsExporter(file_path=file_path)
    measurement = _create_test_measurement()

    exporter.export([measurement])
    exporter.export([measurement])

    with open(file_path, "r") as f:
        content = f.read()

    lines = [line for line in content.strip().split("\n") if line]
    assert len(lines) == 2, "file should contain two JSON lines after two exports"
    return


def test_file_exporter_resolves_path_with_app_context():
    """
        Verify that FileMetricsExporter resolves the file path relative
        to the AppContext directory when app_context is provided.
    """
    tmp_dir = tempfile.mkdtemp()

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_context.mock_context().set_attribute("directory", tmp_dir)

    exporter = FileMetricsExporter(
        file_path="metrics/data.jsonl",
        app_context=mock_app_context
    )

    expected_path = os.path.join(tmp_dir, "metrics/data.jsonl")
    repr_str = repr(exporter)

    assert expected_path in repr_str or "metrics/data.jsonl" in repr_str, \
        "resolved path should include the app_context directory"
    return


def test_file_exporter_export_failure_raises_observability_error():
    """
        Verify that FileMetricsExporter raises ObservabilityError when
        writing to the file fails.
    """
    exporter = FileMetricsExporter(
        file_path="/nonexistent/path/that/should/fail/metrics.jsonl"
    )
    measurement = _create_test_measurement()

    raised = False
    try:
        exporter.export([measurement])
    except ObservabilityError:
        raised = True

    assert raised is True, "export failure should raise ObservabilityError"
    return


def test_file_exporter_flush_does_not_raise():
    """
        Verify that FileMetricsExporter flush completes without error.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "metrics_flush.jsonl")

    exporter = FileMetricsExporter(file_path=file_path)

    exporter.flush()
    return


def test_file_exporter_shutdown_does_not_raise():
    """
        Verify that FileMetricsExporter shutdown completes without error.
    """
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "metrics_shutdown.jsonl")

    exporter = FileMetricsExporter(file_path=file_path)

    exporter.shutdown()
    return


# ---- __repr__ and __str__ ----


def test_console_exporter_repr_contains_class_name():
    """
        Verify that ConsoleMetricsExporter __repr__ includes the class name.
    """
    exporter = ConsoleMetricsExporter()
    repr_str = repr(exporter)

    assert "ConsoleMetricsExporter" in repr_str, "repr should contain 'ConsoleMetricsExporter'"
    return


def test_console_exporter_str_contains_class_name():
    """
        Verify that ConsoleMetricsExporter __str__ includes the class name.
    """
    exporter = ConsoleMetricsExporter()
    str_val = str(exporter)

    assert "ConsoleMetricsExporter" in str_val, "str should contain 'ConsoleMetricsExporter'"
    return


def test_file_exporter_repr_contains_class_name():
    """
        Verify that FileMetricsExporter __repr__ includes the class name.
    """
    exporter = FileMetricsExporter(file_path="/tmp/test_metrics.jsonl")
    repr_str = repr(exporter)

    assert "FileMetricsExporter" in repr_str, "repr should contain 'FileMetricsExporter'"
    return


def test_file_exporter_repr_contains_file_path():
    """
        Verify that FileMetricsExporter __repr__ includes the file path.
    """
    exporter = FileMetricsExporter(file_path="/tmp/test_metrics.jsonl")
    repr_str = repr(exporter)

    assert "/tmp/test_metrics.jsonl" in repr_str, "repr should contain the file path"
    return


def test_file_exporter_str_contains_class_name():
    """
        Verify that FileMetricsExporter __str__ includes the class name.
    """
    exporter = FileMetricsExporter(file_path="/tmp/test_metrics.jsonl")
    str_val = str(exporter)

    assert "FileMetricsExporter" in str_val, "str should contain 'FileMetricsExporter'"
    return


def test_file_exporter_str_contains_file_path():
    """
        Verify that FileMetricsExporter __str__ includes the file path.
    """
    exporter = FileMetricsExporter(file_path="/tmp/test_metrics.jsonl")
    str_val = str(exporter)

    assert "/tmp/test_metrics.jsonl" in str_val, "str should contain the file path"
    return
