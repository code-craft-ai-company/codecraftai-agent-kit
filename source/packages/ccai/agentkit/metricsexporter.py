"""
    Defines the MetricsExporter abstract base class and concrete exporter
    implementations for exporting MetricMeasurement objects to external
    metrics backends.

    Provides two concrete exporters:
    - ConsoleMetricsExporter: writes MetricMeasurement objects as
      formatted text to standard output
    - FileMetricsExporter: writes MetricMeasurement objects as JSON
      lines to a specified file path, resolved relative to the
      AppContext directory provided by codecraftai-this-app

    All exporters accept an optional list of credential reference names
    at construction time. Export failures raise ObservabilityError with
    the exporter class name and underlying error detail.
"""

import abc
import json
import os
import sys

from typing import Optional

from ccai.agentkit.observabilityerror import ObservabilityError
from ccai.agentkit.metricmeasurement import MetricMeasurement


class MetricsExporter(abc.ABC):
    """
        Abstract base class for exporting MetricMeasurement objects
        to external metrics backends.

        Subclasses must implement the export, flush, and shutdown methods
        to handle specific export destinations. Each exporter accepts an
        optional list of credential reference names declaring which
        credentials the exporter requires.

        :param credential_references: Optional list of credential
            reference name strings declaring which credentials the
            exporter requires.
    """

    def __init__(self, credential_references: list = None) -> None:

        if credential_references is not None:
            self._credential_references = list(credential_references)
        else:
            self._credential_references = []

        return

    @property
    def credential_references(self) -> list:
        """
            The list of credential reference name strings declaring
            which credentials the exporter requires.

            :returns: A list of credential reference name strings.
        """
        return list(self._credential_references)

    @abc.abstractmethod
    def export(self, measurements: list) -> None:
        """
            Exports a list of MetricMeasurement objects to the
            configured destination.

            :param measurements: A list of MetricMeasurement objects
                to export.

            :raises: ObservabilityError
        """

    @abc.abstractmethod
    def flush(self) -> None:
        """
            Ensures all buffered measurements are delivered to the
            configured destination.

            :raises: ObservabilityError
        """

    @abc.abstractmethod
    def shutdown(self) -> None:
        """
            Releases resources held by the exporter.

            :raises: ObservabilityError
        """

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name.

            :returns: A repr string for debugging.
        """
        repr_str = "{}()".format(self.__class__.__name__)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the exporter
            class name.

            :returns: A human-readable string.
        """
        str_val = "{}".format(self.__class__.__name__)
        return str_val


class ConsoleMetricsExporter(MetricsExporter):
    """
        Writes MetricMeasurement objects as formatted text to standard
        output.

        Each measurement is formatted as a human-readable text line
        containing the metric name, value, timestamp, and labels.
        The formatted text is written to sys.stdout followed by a
        newline.
    """

    def __init__(self) -> None:

        super().__init__()

        return

    def export(self, measurements: list) -> None:
        """
            Writes a list of MetricMeasurement objects as formatted
            text to standard output.

            :param measurements: A list of MetricMeasurement objects
                to export.

            :raises: ObservabilityError
        """
        try:
            for measurement in measurements:
                formatted = (
                    "MetricMeasurement: metric_name={}, value={}, "
                    "timestamp={}, labels={}"
                ).format(
                    measurement.metric_name,
                    measurement.value,
                    measurement.timestamp.isoformat(),
                    measurement.labels
                )
                sys.stdout.write(formatted + "\n")
        except Exception as exc:
            raise ObservabilityError(
                component_name=self.__class__.__name__,
                operation_name="export",
                message="Failed to export measurements to console: {}".format(
                    str(exc)
                ),
                cause=exc
            ) from exc

        return

    def flush(self) -> None:
        """
            Flushes standard output to ensure all buffered measurements
            are delivered.

            :raises: ObservabilityError
        """
        try:
            sys.stdout.flush()
        except Exception as exc:
            raise ObservabilityError(
                component_name=self.__class__.__name__,
                operation_name="flush",
                message="Failed to flush console output: {}".format(str(exc)),
                cause=exc
            ) from exc

        return

    def shutdown(self) -> None:
        """
            Releases resources held by the console exporter.

            The ConsoleMetricsExporter does not hold resources that
            require explicit release, so this method performs no
            action.
        """
        return


class FileMetricsExporter(MetricsExporter):
    """
        Writes MetricMeasurement objects as JSON lines to a specified
        file path, resolved relative to the AppContext directory provided
        by codecraftai-this-app.

        Each measurement is serialized as a single-line JSON object and
        appended to the target file. If an app_context is provided, the
        file_path is resolved relative to the app_context directory.
        Otherwise, the file_path is used as-is.

        :param file_path: The file path string where measurement JSON
            lines are written.
        :param app_context: Optional AppContext instance providing the
            directory for resolving relative file paths.
    """

    def __init__(self, file_path: str, app_context=None) -> None:

        super().__init__()

        self._file_path = file_path
        self._app_context = app_context
        self._resolved_path = self._resolve_path()

        return

    def _resolve_path(self) -> str:
        """
            Resolves the file path relative to the AppContext directory
            if an app_context is provided, otherwise returns the
            file_path as-is.

            :returns: The resolved file path string.
        """
        if self._app_context is not None:
            resolved = os.path.join(self._app_context.directory, self._file_path)
        else:
            resolved = self._file_path

        return resolved

    def export(self, measurements: list) -> None:
        """
            Writes a list of MetricMeasurement objects as JSON lines
            to the configured file path.

            Each measurement is serialized using its to_json method and
            appended as a single line to the target file.

            :param measurements: A list of MetricMeasurement objects
                to export.

            :raises: ObservabilityError
        """
        try:
            with open(self._resolved_path, "a") as file_handle:
                for measurement in measurements:
                    json_line = measurement.to_json()
                    file_handle.write(json_line + "\n")
        except Exception as exc:
            raise ObservabilityError(
                component_name=self.__class__.__name__,
                operation_name="export",
                message="Failed to export measurements to file {!r}: {}".format(
                    self._resolved_path, str(exc)
                ),
                cause=exc
            ) from exc

        return

    def flush(self) -> None:
        """
            Flushes the file to ensure all buffered measurements are
            delivered. Since each export call opens and closes the
            file, this method performs no additional action.
        """
        return

    def shutdown(self) -> None:
        """
            Releases resources held by the file exporter.

            The FileMetricsExporter opens and closes the file on each
            export call, so this method performs no additional action.
        """
        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and file path.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(file_path={!r})".format(
            self.__class__.__name__,
            self._resolved_path
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the exporter
            class name and file path.

            :returns: A human-readable string.
        """
        str_val = "{}: file_path={}".format(
            self.__class__.__name__,
            self._resolved_path
        )
        return str_val
