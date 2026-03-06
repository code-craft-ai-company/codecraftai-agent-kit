"""
    Defines the LogExporter abstract base class and concrete exporter
    implementations for exporting StructuredLogEntry objects to external
    systems.

    Provides two concrete exporters:
    - ConsoleLogExporter: writes formatted log entries to standard output
    - FileLogExporter: writes formatted log entries to a specified file
      path, resolved relative to the AppContext directory provided by
      automojo-this-app

    All exporters accept a LogFormatter at construction time for
    formatting entries before export. Export failures raise
    ObservabilityError with the exporter class name and underlying
    error detail.
"""

import abc
import os
import sys

from typing import Optional

from automojo.agentkit.logformatter import LogFormatter
from automojo.agentkit.observabilityerror import ObservabilityError
from automojo.agentkit.structuredlogentry import StructuredLogEntry


class LogExporter(abc.ABC):
    """
        Abstract base class for exporting StructuredLogEntry objects to
        external systems.

        Subclasses must implement the export, flush, and shutdown methods
        to handle specific export destinations. Each exporter accepts a
        LogFormatter for formatting entries before export and an optional
        list of credential reference names declaring which credentials
        the exporter requires.

        :param formatter: The LogFormatter used to format entries before
            export.
        :param credential_references: Optional list of credential
            reference name strings declaring which credentials the
            exporter requires.
    """

    def __init__(self, formatter: LogFormatter, credential_references: list = None) -> None:

        self._formatter = formatter

        if credential_references is not None:
            self._credential_references = list(credential_references)
        else:
            self._credential_references = []

        return

    @property
    def formatter(self) -> LogFormatter:
        """
            The LogFormatter used to format entries before export.

            :returns: The LogFormatter instance.
        """
        return self._formatter

    @property
    def credential_references(self) -> list:
        """
            The list of credential reference name strings declaring
            which credentials the exporter requires.

            :returns: A list of credential reference name strings.
        """
        return list(self._credential_references)

    @abc.abstractmethod
    def export(self, entry: StructuredLogEntry) -> None:
        """
            Exports a StructuredLogEntry to the configured destination.

            :param entry: The structured log entry to export.

            :raises: ObservabilityError
        """

    @abc.abstractmethod
    def flush(self) -> None:
        """
            Ensures all buffered entries are delivered to the
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
            class name and the LogFormatter format name.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(format_name={!r})".format(
            self.__class__.__name__,
            self._formatter.format_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the exporter
            class name and format name.

            :returns: A human-readable string.
        """
        str_val = "{}: format_name={}".format(
            self.__class__.__name__,
            self._formatter.format_name
        )
        return str_val



class ConsoleLogExporter(LogExporter):
    """
        Writes formatted log entries to standard output.

        Uses the provided LogFormatter to format each StructuredLogEntry
        and writes the formatted string followed by a newline to
        sys.stdout.

        :param formatter: The LogFormatter used to format entries before
            writing to standard output.
    """

    def __init__(self, formatter: LogFormatter) -> None:

        super().__init__(formatter=formatter)

        return

    def export(self, entry: StructuredLogEntry) -> None:
        """
            Writes a formatted log entry to standard output.

            Formats the entry using the configured LogFormatter and
            writes the result followed by a newline to sys.stdout.

            :param entry: The structured log entry to export.

            :raises: ObservabilityError
        """
        try:
            formatted = self._formatter.format(entry)
            sys.stdout.write(formatted + "\n")
        except Exception as exc:
            raise ObservabilityError(
                component_name=self.__class__.__name__,
                operation_name="export",
                message="Failed to export log entry to console: {}".format(str(exc)),
                cause=exc
            ) from exc

        return

    def flush(self) -> None:
        """
            Flushes standard output to ensure all buffered entries
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

            The ConsoleLogExporter does not hold resources that
            require explicit release, so this method performs no
            action.
        """
        return


class FileLogExporter(LogExporter):
    """
        Writes formatted log entries to a specified file path, resolved
        relative to the AppContext directory provided by automojo-this-app.

        Uses the provided LogFormatter to format each StructuredLogEntry
        and appends the formatted string followed by a newline to the
        target file. If an app_context is provided, the file_path is
        resolved relative to the app_context directory. Otherwise, the
        file_path is used as-is.

        :param formatter: The LogFormatter used to format entries before
            writing to the file.
        :param file_path: The file path string where log entries are
            written.
        :param app_context: Optional AppContext instance providing the
            directory for resolving relative file paths.
    """

    def __init__(self, formatter: LogFormatter, file_path: str, app_context=None) -> None:

        super().__init__(formatter=formatter)

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

    def export(self, entry: StructuredLogEntry) -> None:
        """
            Writes a formatted log entry to the configured file path.

            Formats the entry using the configured LogFormatter and
            appends the result followed by a newline to the target file.

            :param entry: The structured log entry to export.

            :raises: ObservabilityError
        """
        try:
            formatted = self._formatter.format(entry)
            with open(self._resolved_path, "a") as file_handle:
                file_handle.write(formatted + "\n")
        except Exception as exc:
            raise ObservabilityError(
                component_name=self.__class__.__name__,
                operation_name="export",
                message="Failed to export log entry to file {!r}: {}".format(
                    self._resolved_path, str(exc)
                ),
                cause=exc
            ) from exc

        return

    def flush(self) -> None:
        """
            Flushes the file to ensure all buffered entries are
            delivered. Since each export call opens and closes the
            file, this method performs no additional action.
        """
        return

    def shutdown(self) -> None:
        """
            Releases resources held by the file exporter.

            The FileLogExporter opens and closes the file on each
            export call, so this method performs no additional action.
        """
        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, format name, and file path.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(format_name={!r}, file_path={!r})".format(
            self.__class__.__name__,
            self._formatter.format_name,
            self._resolved_path
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the exporter
            class name, format name, and file path.

            :returns: A human-readable string.
        """
        str_val = "{}: format_name={}, file_path={}".format(
            self.__class__.__name__,
            self._formatter.format_name,
            self._resolved_path
        )
        return str_val
