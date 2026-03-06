"""
    Defines the LogFormatter abstract base class and concrete formatter
    implementations for formatting StructuredLogEntry objects into output
    strings.

    Provides three concrete formatters:
    - JsonLogFormatter: formats entries as single-line JSON strings
    - KeyValueLogFormatter: formats entries as space-separated key=value pairs
    - HumanReadableLogFormatter: formats entries as human-readable strings
      with timestamp, level, logger name, message, and correlation identifier
"""

import abc
import json

from automojo.agentkit.structuredlogentry import StructuredLogEntry


class LogFormatter(abc.ABC):
    """
        Abstract base class for formatting StructuredLogEntry objects into
        output strings.

        Subclasses must implement the format method to produce a specific
        output format. Each formatter exposes a format_name property
        identifying the output format it produces.

        :param format_name: A string identifying the output format produced
            by this formatter.
    """

    def __init__(self, format_name: str) -> None:
        self._format_name = format_name
        return

    @property
    def format_name(self) -> str:
        """
            The name identifying the output format produced by this
            formatter.

            :returns: The format name string.
        """
        return self._format_name

    @abc.abstractmethod
    def format(self, entry: StructuredLogEntry) -> str:
        """
            Formats a StructuredLogEntry into an output string.

            :param entry: The structured log entry to format.

            :returns: The formatted output string.
        """

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class
            name and format name.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(format_name={!r})".format(
            self.__class__.__name__,
            self._format_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the format name.

            :returns: A human-readable string.
        """
        str_val = "{}: format_name={}".format(
            self.__class__.__name__,
            self._format_name
        )
        return str_val


class JsonLogFormatter(LogFormatter):
    """
        Formats a StructuredLogEntry as a single-line JSON string.

        Uses the entry's as_dict method to obtain a dictionary
        representation and serializes it with json.dumps to produce
        a compact single-line JSON output.
    """

    def __init__(self) -> None:
        super().__init__(format_name="json")
        return

    def format(self, entry: StructuredLogEntry) -> str:
        """
            Formats a StructuredLogEntry as a single-line JSON string.

            :param entry: The structured log entry to format.

            :returns: A single-line JSON string containing all entry fields.
        """
        entry_dict = entry.as_dict()
        result = json.dumps(entry_dict, separators=(",", ":"))
        return result


class KeyValueLogFormatter(LogFormatter):
    """
        Formats a StructuredLogEntry as a space-separated key=value pair
        string.

        Each field from the entry's dictionary representation is formatted
        as key=value and joined with spaces.
    """

    def __init__(self) -> None:
        super().__init__(format_name="key_value")
        return

    def format(self, entry: StructuredLogEntry) -> str:
        """
            Formats a StructuredLogEntry as space-separated key=value pairs.

            :param entry: The structured log entry to format.

            :returns: A string of space-separated key=value pairs.
        """
        entry_dict = entry.as_dict()
        pairs = []
        for key, value in entry_dict.items():
            pair = "{}={}".format(key, value)
            pairs.append(pair)
        result = " ".join(pairs)
        return result


class HumanReadableLogFormatter(LogFormatter):
    """
        Formats a StructuredLogEntry as a human-readable string.

        Produces output in the format:
        [timestamp] LEVEL logger_name - message (correlation_id=...)
    """

    def __init__(self) -> None:
        super().__init__(format_name="human_readable")
        return

    def format(self, entry: StructuredLogEntry) -> str:
        """
            Formats a StructuredLogEntry as a human-readable string with
            timestamp, level, logger name, message, and correlation
            identifier.

            :param entry: The structured log entry to format.

            :returns: A human-readable formatted string.
        """
        timestamp_str = entry.timestamp.isoformat()
        level_str = entry.level.upper()
        result = "[{}] {} {} - {} (correlation_id={})".format(
            timestamp_str,
            level_str,
            entry.logger_name,
            entry.message,
            entry.correlation_id
        )
        return result
