"""
    Unit tests for the automojo.agentkit.structuredlogger module.

    Tests the StructuredLogger class: log methods produce correct
    StructuredLogEntry objects, set_correlation_context updates the
    active context, delegation to standard Python logging, and
    string representations.

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
"""

import logging

from datetime import datetime

from automojo.agentkit.correlationcontext import CorrelationContext
from automojo.agentkit.structuredlogger import StructuredLogger
from automojo.agentkit.structuredlogentry import StructuredLogEntry
from automojo.testbase.mocking import Mock, create_instance_patch


# ---- Helper Functions ----


def _create_logger(agent_id="agent-test-001", correlation_id="corr-test-001"):
    """
        Creates a StructuredLogger with a known CorrelationContext for testing.
    """
    context = CorrelationContext(correlation_id=correlation_id)
    logger = StructuredLogger(agent_id=agent_id, correlation_context=context)
    return logger


# ---- Constructor Tests ----


def test_constructor_stores_agent_id():
    """
        Verify that the constructor stores the agent_id and it is
        accessible via the repr output.
    """
    logger = _create_logger(agent_id="agent-abc")
    repr_str = repr(logger)

    assert "agent-abc" in repr_str, "repr should contain the agent_id"
    return


def test_constructor_stores_correlation_context():
    """
        Verify that the constructor stores the CorrelationContext and
        it is accessible via the correlation_context property.
    """
    context = CorrelationContext(correlation_id="corr-ctor-001")
    logger = StructuredLogger(agent_id="agent-001", correlation_context=context)

    stored_context = logger.correlation_context
    assert stored_context is context, "correlation_context property should return the provided context"
    return


# ---- correlation_context property ----


def test_correlation_context_property_returns_current_context():
    """
        Verify that the correlation_context property returns the current
        CorrelationContext instance.
    """
    logger = _create_logger(correlation_id="corr-prop-001")
    context = logger.correlation_context

    assert context.correlation_id == "corr-prop-001", "correlation_context should have the expected correlation_id"
    return


# ---- set_correlation_context ----


def test_set_correlation_context_updates_context():
    """
        Verify that set_correlation_context replaces the active
        CorrelationContext for subsequent log entries.
    """
    logger = _create_logger(correlation_id="corr-old")
    new_context = CorrelationContext(correlation_id="corr-new")

    logger.set_correlation_context(new_context)
    stored_context = logger.correlation_context

    assert stored_context is new_context, "set_correlation_context should update the active context"
    return


def test_set_correlation_context_affects_subsequent_entries():
    """
        Verify that after set_correlation_context, log entries use the
        new correlation_id.
    """
    logger = _create_logger(correlation_id="corr-old")
    new_context = CorrelationContext(correlation_id="corr-new")
    logger.set_correlation_context(new_context)

    entry = logger.info("test message")

    assert entry.correlation_id == "corr-new", "entry should use the new correlation_id"
    return


# ---- Log method tests ----


def test_debug_returns_structured_log_entry():
    """
        Verify that the debug method returns a StructuredLogEntry instance.
    """
    logger = _create_logger()
    entry = logger.debug("debug message")

    assert isinstance(entry, StructuredLogEntry), "debug should return a StructuredLogEntry"
    return


def test_debug_entry_has_correct_level():
    """
        Verify that the debug method produces an entry with level 'debug'.
    """
    logger = _create_logger()
    entry = logger.debug("debug message")

    assert entry.level == "debug", "debug entry should have level 'debug'"
    return


def test_info_returns_entry_with_correct_level():
    """
        Verify that the info method produces an entry with level 'info'.
    """
    logger = _create_logger()
    entry = logger.info("info message")

    assert entry.level == "info", "info entry should have level 'info'"
    return


def test_warning_returns_entry_with_correct_level():
    """
        Verify that the warning method produces an entry with level 'warning'.
    """
    logger = _create_logger()
    entry = logger.warning("warning message")

    assert entry.level == "warning", "warning entry should have level 'warning'"
    return


def test_error_returns_entry_with_correct_level():
    """
        Verify that the error method produces an entry with level 'error'.
    """
    logger = _create_logger()
    entry = logger.error("error message")

    assert entry.level == "error", "error entry should have level 'error'"
    return


def test_critical_returns_entry_with_correct_level():
    """
        Verify that the critical method produces an entry with level 'critical'.
    """
    logger = _create_logger()
    entry = logger.critical("critical message")

    assert entry.level == "critical", "critical entry should have level 'critical'"
    return


def test_log_entry_contains_message():
    """
        Verify that the log entry contains the provided message.
    """
    logger = _create_logger()
    entry = logger.info("Agent started successfully")

    assert entry.message == "Agent started successfully", "entry message should match"
    return


def test_log_entry_contains_logger_name():
    """
        Verify that the log entry contains the expected logger name.
    """
    logger = _create_logger()
    entry = logger.info("test")

    assert entry.logger_name == "automojo.agentkit.observability", "logger_name should be 'automojo.agentkit.observability'"
    return


def test_log_entry_contains_correlation_id():
    """
        Verify that the log entry contains the correlation_id from the
        active CorrelationContext.
    """
    logger = _create_logger(correlation_id="corr-entry-001")
    entry = logger.info("test")

    assert entry.correlation_id == "corr-entry-001", "entry should contain the correlation_id"
    return


def test_log_entry_contains_agent_id():
    """
        Verify that the log entry contains the agent_id.
    """
    logger = _create_logger(agent_id="agent-entry-001")
    entry = logger.info("test")

    assert entry.agent_id == "agent-entry-001", "entry should contain the agent_id"
    return


def test_log_entry_contains_timestamp():
    """
        Verify that the log entry contains a timestamp as a datetime.
    """
    logger = _create_logger()
    before = datetime.utcnow()
    entry = logger.info("test")
    after = datetime.utcnow()

    assert isinstance(entry.timestamp, datetime), "timestamp should be a datetime"
    assert before <= entry.timestamp <= after, "timestamp should be between before and after"
    return


def test_log_entry_contains_metadata_kwargs():
    """
        Verify that additional keyword arguments are stored in the
        entry metadata dictionary.
    """
    logger = _create_logger()
    entry = logger.info("test", env="production", version="1.0")

    assert entry.metadata.get("env") == "production", "metadata should contain env"
    assert entry.metadata.get("version") == "1.0", "metadata should contain version"
    return


def test_log_entry_empty_metadata_when_no_kwargs():
    """
        Verify that metadata is empty when no keyword arguments are provided.
    """
    logger = _create_logger()
    entry = logger.info("test")

    assert entry.metadata == {}, "metadata should be empty when no kwargs provided"
    return


# ---- Delegation to standard logging ----


def test_debug_delegates_to_standard_logger():
    """
        Verify that the debug method delegates to the standard Python
        logger at the DEBUG level.
    """
    logger = _create_logger()
    patch = create_instance_patch(logger._logger, "debug")
    mock_debug = patch.activate()

    try:
        logger.debug("debug delegation test")
        mock_debug.mock_context().assert_called_once()
    finally:
        patch.deactivate()

    return


def test_info_delegates_to_standard_logger():
    """
        Verify that the info method delegates to the standard Python
        logger at the INFO level.
    """
    logger = _create_logger()
    patch = create_instance_patch(logger._logger, "info")
    mock_info = patch.activate()

    try:
        logger.info("info delegation test")
        mock_info.mock_context().assert_called_once()
    finally:
        patch.deactivate()

    return


def test_warning_delegates_to_standard_logger():
    """
        Verify that the warning method delegates to the standard Python
        logger at the WARNING level.
    """
    logger = _create_logger()
    patch = create_instance_patch(logger._logger, "warning")
    mock_warning = patch.activate()

    try:
        logger.warning("warning delegation test")
        mock_warning.mock_context().assert_called_once()
    finally:
        patch.deactivate()

    return


def test_error_delegates_to_standard_logger():
    """
        Verify that the error method delegates to the standard Python
        logger at the ERROR level.
    """
    logger = _create_logger()
    patch = create_instance_patch(logger._logger, "error")
    mock_error = patch.activate()

    try:
        logger.error("error delegation test")
        mock_error.mock_context().assert_called_once()
    finally:
        patch.deactivate()

    return


def test_critical_delegates_to_standard_logger():
    """
        Verify that the critical method delegates to the standard Python
        logger at the CRITICAL level.
    """
    logger = _create_logger()
    patch = create_instance_patch(logger._logger, "critical")
    mock_critical = patch.activate()

    try:
        logger.critical("critical delegation test")
        mock_critical.mock_context().assert_called_once()
    finally:
        patch.deactivate()

    return


# ---- __repr__ and __str__ ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name 'StructuredLogger'.
    """
    logger = _create_logger()
    repr_str = repr(logger)

    assert "StructuredLogger" in repr_str, "repr should contain 'StructuredLogger'"
    return


def test_repr_contains_agent_id():
    """
        Verify that __repr__ includes the agent identifier.
    """
    logger = _create_logger(agent_id="agent-repr-001")
    repr_str = repr(logger)

    assert "agent-repr-001" in repr_str, "repr should contain the agent_id"
    return


def test_repr_contains_logger_name():
    """
        Verify that __repr__ includes the logger name.
    """
    logger = _create_logger()
    repr_str = repr(logger)

    assert "automojo.agentkit.observability" in repr_str, "repr should contain the logger name"
    return


def test_str_contains_agent_id():
    """
        Verify that __str__ includes the agent identifier.
    """
    logger = _create_logger(agent_id="agent-str-001")
    str_val = str(logger)

    assert "agent-str-001" in str_val, "str should contain the agent_id"
    return


def test_str_contains_logger_name():
    """
        Verify that __str__ includes the logger name.
    """
    logger = _create_logger()
    str_val = str(logger)

    assert "automojo.agentkit.observability" in str_val, "str should contain the logger name"
    return
