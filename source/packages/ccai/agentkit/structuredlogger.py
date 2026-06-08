"""
    Defines the StructuredLogger class that wraps the Python standard
    logging module and enriches log records with correlation identifiers,
    agent identity, and structured metadata fields.

    The StructuredLogger produces StructuredLogEntry objects for each
    log call and delegates to a standard Python logger under the
    ``ccai.agentkit.observability`` hierarchy. It accepts an
    agent identifier and a CorrelationContext at construction time,
    and provides methods for each standard log level: debug, info,
    warning, error, and critical.
"""

import logging

from datetime import datetime

from ccai.agentkit.correlationcontext import CorrelationContext
from ccai.agentkit.structuredlogentry import StructuredLogEntry


class StructuredLogger:
    """
        A logger wrapper that enriches standard Python log records with
        correlation identifiers, agent identity, and structured metadata
        fields.

        The StructuredLogger produces StructuredLogEntry objects and
        delegates to the Python standard logging module under the
        ``ccai.agentkit.observability`` logger hierarchy.

        :param agent_id: The agent identifier string for the agent
            that owns this logger.
        :param correlation_context: The CorrelationContext providing
            the correlation identifier for log entries.
    """

    def __init__(self, agent_id: str, correlation_context: CorrelationContext) -> None:

        self._agent_id = agent_id
        self._correlation_context = correlation_context
        self._logger_name = "ccai.agentkit.observability"
        self._logger = logging.getLogger(self._logger_name)

        return

    @property
    def correlation_context(self) -> CorrelationContext:
        """
            The current CorrelationContext used for enriching log entries.

            :returns: The active CorrelationContext instance.
        """
        return self._correlation_context

    def set_correlation_context(self, context: CorrelationContext) -> None:
        """
            Updates the active correlation context for subsequent log entries.

            :param context: The new CorrelationContext to use for
                enriching log entries.
        """
        self._correlation_context = context
        return

    def debug(self, message: str, **metadata) -> StructuredLogEntry:
        """
            Creates a structured log entry at the DEBUG level and delegates
            to the standard Python logger.

            :param message: The log message string.
            :param metadata: Additional key-value pairs to include in the
                log entry metadata.

            :returns: The StructuredLogEntry created for this log call.
        """
        entry = self._create_entry(level="debug", message=message, metadata=metadata)
        self._logger.debug(message)
        return entry

    def info(self, message: str, **metadata) -> StructuredLogEntry:
        """
            Creates a structured log entry at the INFO level and delegates
            to the standard Python logger.

            :param message: The log message string.
            :param metadata: Additional key-value pairs to include in the
                log entry metadata.

            :returns: The StructuredLogEntry created for this log call.
        """
        entry = self._create_entry(level="info", message=message, metadata=metadata)
        self._logger.info(message)
        return entry

    def warning(self, message: str, **metadata) -> StructuredLogEntry:
        """
            Creates a structured log entry at the WARNING level and delegates
            to the standard Python logger.

            :param message: The log message string.
            :param metadata: Additional key-value pairs to include in the
                log entry metadata.

            :returns: The StructuredLogEntry created for this log call.
        """
        entry = self._create_entry(level="warning", message=message, metadata=metadata)
        self._logger.warning(message)
        return entry

    def error(self, message: str, **metadata) -> StructuredLogEntry:
        """
            Creates a structured log entry at the ERROR level and delegates
            to the standard Python logger.

            :param message: The log message string.
            :param metadata: Additional key-value pairs to include in the
                log entry metadata.

            :returns: The StructuredLogEntry created for this log call.
        """
        entry = self._create_entry(level="error", message=message, metadata=metadata)
        self._logger.error(message)
        return entry

    def critical(self, message: str, **metadata) -> StructuredLogEntry:
        """
            Creates a structured log entry at the CRITICAL level and delegates
            to the standard Python logger.

            :param message: The log message string.
            :param metadata: Additional key-value pairs to include in the
                log entry metadata.

            :returns: The StructuredLogEntry created for this log call.
        """
        entry = self._create_entry(level="critical", message=message, metadata=metadata)
        self._logger.critical(message)
        return entry

    def _create_entry(self, level: str, message: str, metadata: dict) -> StructuredLogEntry:
        """
            Creates a StructuredLogEntry with the current timestamp,
            correlation identifier, agent identifier, and provided
            metadata.

            :param level: The log level string.
            :param message: The log message string.
            :param metadata: Dictionary of additional key-value fields.

            :returns: A new StructuredLogEntry instance.
        """
        timestamp = datetime.utcnow()
        correlation_id = self._correlation_context.correlation_id

        entry = StructuredLogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            logger_name=self._logger_name,
            correlation_id=correlation_id,
            agent_id=self._agent_id,
            metadata=metadata
        )
        return entry

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            agent identifier, and logger name.

            :returns: A repr string for debugging.
        """
        repr_str = "StructuredLogger(agent_id={!r}, logger_name={!r})".format(
            self._agent_id, self._logger_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent identifier
            and logger name.

            :returns: A human-readable string.
        """
        str_val = "StructuredLogger: agent_id={}, logger_name={}".format(
            self._agent_id, self._logger_name
        )
        return str_val
