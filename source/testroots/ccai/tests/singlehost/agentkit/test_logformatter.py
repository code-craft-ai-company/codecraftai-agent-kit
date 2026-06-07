"""
    Unit tests for the ccai.agentkit.logformatter module.

    Tests the LogFormatter abstract base class and concrete formatters:
    JsonLogFormatter, KeyValueLogFormatter, and HumanReadableLogFormatter.
    Covers format output correctness, format_name property, abstract
    enforcement, __repr__, and __str__.
"""

import json

from datetime import datetime

from ccai.agentkit.structuredlogentry import StructuredLogEntry
from ccai.agentkit.logformatter import (
    LogFormatter,
    JsonLogFormatter,
    KeyValueLogFormatter,
    HumanReadableLogFormatter,
)


def _create_test_entry():
    """
        Helper to create a standard StructuredLogEntry for testing formatters.
    """
    ts = datetime(2025, 3, 10, 8, 45, 30)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="Agent started",
        logger_name="ccai.agentkit.observability",
        correlation_id="corr-fmt-001",
        agent_id="agent-fmt-001",
        metadata={"env": "test"}
    )
    return entry


# --- Abstract enforcement ---

def test_logformatter_cannot_be_instantiated_directly():
    """
        Verify that LogFormatter cannot be instantiated because it has
        an abstract format method.
    """
    raised = False
    try:
        LogFormatter("test_format")
    except TypeError:
        raised = True

    assert raised is True, "LogFormatter should not be directly instantiable"
    return


def test_subclass_without_format_cannot_be_instantiated():
    """
        Verify that a subclass that does not implement format raises TypeError.
    """

    class IncompleteFormatter(LogFormatter):
        pass

    raised = False
    try:
        IncompleteFormatter("incomplete")
    except TypeError:
        raised = True

    assert raised is True, "Subclass without format implementation should not be instantiable"
    return


# --- JsonLogFormatter tests ---

def test_json_formatter_format_name():
    """
        Verify that JsonLogFormatter has format_name 'json'.
    """
    formatter = JsonLogFormatter()
    name = formatter.format_name
    assert name == "json", "JsonLogFormatter format_name should be 'json'"
    return


def test_json_formatter_output_is_valid_json():
    """
        Verify that JsonLogFormatter produces a valid JSON string.
    """
    formatter = JsonLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)
    parsed = json.loads(result)

    is_dict = isinstance(parsed, dict)
    assert is_dict is True, "Parsed JSON output should be a dictionary"
    return


def test_json_formatter_output_contains_all_fields():
    """
        Verify that JsonLogFormatter output contains all entry fields.
    """
    formatter = JsonLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)
    parsed = json.loads(result)

    assert "timestamp" in parsed, "JSON output should contain timestamp"
    assert "level" in parsed, "JSON output should contain level"
    assert "message" in parsed, "JSON output should contain message"
    assert "logger_name" in parsed, "JSON output should contain logger_name"
    assert "correlation_id" in parsed, "JSON output should contain correlation_id"
    assert "agent_id" in parsed, "JSON output should contain agent_id"
    assert "metadata" in parsed, "JSON output should contain metadata"
    return


def test_json_formatter_output_field_values():
    """
        Verify that JsonLogFormatter output field values match the entry.
    """
    formatter = JsonLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)
    parsed = json.loads(result)

    assert parsed["level"] == "info", "level should match entry"
    assert parsed["message"] == "Agent started", "message should match entry"
    assert parsed["correlation_id"] == "corr-fmt-001", "correlation_id should match entry"
    assert parsed["agent_id"] == "agent-fmt-001", "agent_id should match entry"
    assert parsed["metadata"] == {"env": "test"}, "metadata should match entry"
    return


def test_json_formatter_output_is_single_line():
    """
        Verify that JsonLogFormatter produces a single-line JSON string
        (no embedded newlines).
    """
    formatter = JsonLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)
    line_count = result.count("\n")
    assert line_count == 0, "JSON output should be a single line"
    return


# --- KeyValueLogFormatter tests ---

def test_key_value_formatter_format_name():
    """
        Verify that KeyValueLogFormatter has format_name 'key_value'.
    """
    formatter = KeyValueLogFormatter()
    name = formatter.format_name
    assert name == "key_value", "KeyValueLogFormatter format_name should be 'key_value'"
    return


def test_key_value_formatter_output_contains_key_value_pairs():
    """
        Verify that KeyValueLogFormatter output contains key=value pairs.
    """
    formatter = KeyValueLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    has_level = "level=info" in result
    assert has_level is True, "Output should contain level=info"

    has_message = "message=Agent started" in result
    assert has_message is True, "Output should contain message=Agent started"

    has_corr_id = "correlation_id=corr-fmt-001" in result
    assert has_corr_id is True, "Output should contain correlation_id=corr-fmt-001"
    return


def test_key_value_formatter_output_is_space_separated():
    """
        Verify that KeyValueLogFormatter output uses spaces to separate pairs.
    """
    formatter = KeyValueLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    has_space_between = "info " in result or " message=" in result
    assert has_space_between is True, "Output should have space-separated key=value pairs"
    return


# --- HumanReadableLogFormatter tests ---

def test_human_readable_formatter_format_name():
    """
        Verify that HumanReadableLogFormatter has format_name 'human_readable'.
    """
    formatter = HumanReadableLogFormatter()
    name = formatter.format_name
    assert name == "human_readable", "HumanReadableLogFormatter format_name should be 'human_readable'"
    return


def test_human_readable_formatter_output_contains_timestamp():
    """
        Verify that HumanReadableLogFormatter output contains the timestamp
        in ISO format within brackets.
    """
    formatter = HumanReadableLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    has_timestamp = "[2025-03-10T08:45:30]" in result
    assert has_timestamp is True, "Output should contain [timestamp] in ISO format"
    return


def test_human_readable_formatter_output_contains_uppercase_level():
    """
        Verify that HumanReadableLogFormatter output contains the level
        in uppercase.
    """
    formatter = HumanReadableLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    has_level = "INFO" in result
    assert has_level is True, "Output should contain the level in uppercase"
    return


def test_human_readable_formatter_output_contains_logger_name():
    """
        Verify that HumanReadableLogFormatter output contains the logger name.
    """
    formatter = HumanReadableLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    has_logger = "ccai.agentkit.observability" in result
    assert has_logger is True, "Output should contain the logger name"
    return


def test_human_readable_formatter_output_contains_message():
    """
        Verify that HumanReadableLogFormatter output contains the message.
    """
    formatter = HumanReadableLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    has_message = "Agent started" in result
    assert has_message is True, "Output should contain the message"
    return


def test_human_readable_formatter_output_contains_correlation_id():
    """
        Verify that HumanReadableLogFormatter output contains the
        correlation_id in parentheses.
    """
    formatter = HumanReadableLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    has_corr_id = "(correlation_id=corr-fmt-001)" in result
    assert has_corr_id is True, "Output should contain (correlation_id=...)"
    return


def test_human_readable_formatter_full_format():
    """
        Verify the complete format of HumanReadableLogFormatter output.
    """
    formatter = HumanReadableLogFormatter()
    entry = _create_test_entry()

    result = formatter.format(entry)

    expected = "[2025-03-10T08:45:30] INFO ccai.agentkit.observability - Agent started (correlation_id=corr-fmt-001)"
    assert result == expected, "Full format should match expected pattern"
    return


# --- __repr__ and __str__ tests ---

def test_json_formatter_repr_contains_class_name():
    """
        Verify that JsonLogFormatter __repr__ includes the class name.
    """
    formatter = JsonLogFormatter()
    repr_str = repr(formatter)

    has_class = "JsonLogFormatter" in repr_str
    assert has_class is True, "repr should contain the class name"
    return


def test_json_formatter_repr_contains_format_name():
    """
        Verify that JsonLogFormatter __repr__ includes the format name.
    """
    formatter = JsonLogFormatter()
    repr_str = repr(formatter)

    has_format = "json" in repr_str
    assert has_format is True, "repr should contain the format name"
    return


def test_key_value_formatter_repr_contains_class_name():
    """
        Verify that KeyValueLogFormatter __repr__ includes the class name.
    """
    formatter = KeyValueLogFormatter()
    repr_str = repr(formatter)

    has_class = "KeyValueLogFormatter" in repr_str
    assert has_class is True, "repr should contain the class name"
    return


def test_human_readable_formatter_repr_contains_class_name():
    """
        Verify that HumanReadableLogFormatter __repr__ includes the class name.
    """
    formatter = HumanReadableLogFormatter()
    repr_str = repr(formatter)

    has_class = "HumanReadableLogFormatter" in repr_str
    assert has_class is True, "repr should contain the class name"
    return


def test_json_formatter_str_contains_format_name():
    """
        Verify that JsonLogFormatter __str__ includes the format name.
    """
    formatter = JsonLogFormatter()
    str_val = str(formatter)

    has_format = "json" in str_val
    assert has_format is True, "str should contain the format name"
    return


def test_key_value_formatter_str_contains_format_name():
    """
        Verify that KeyValueLogFormatter __str__ includes the format name.
    """
    formatter = KeyValueLogFormatter()
    str_val = str(formatter)

    has_format = "key_value" in str_val
    assert has_format is True, "str should contain the format name"
    return


def test_human_readable_formatter_str_contains_format_name():
    """
        Verify that HumanReadableLogFormatter __str__ includes the format name.
    """
    formatter = HumanReadableLogFormatter()
    str_val = str(formatter)

    has_format = "human_readable" in str_val
    assert has_format is True, "str should contain the format name"
    return
