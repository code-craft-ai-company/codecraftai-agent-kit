"""
    Property-based tests for the ccai.agentkit.structuredlogentry and
    ccai.agentkit.logformatter modules.

    Uses the ccai.testbase.properties engine to verify:
    - Property 4: StructuredLogEntry JSON round-trip preserves all fields
    - Property 6: JsonLogFormatter produces valid JSON containing all entry fields

    **Validates: Requirements 2.4, 2.6, 2.7, 4.3**
"""

import json

from datetime import datetime

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.structuredlogentry import StructuredLogEntry
from ccai.agentkit.logformatter import JsonLogFormatter


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_timestamp_strategy = _datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 1, 1),
)

_level_strategy = st.sampled_from(["debug", "info", "warning", "error", "critical"])

_short_text = st.text(min_size=1, max_size=100)

_metadata_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.text(min_size=0, max_size=50),
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 4: StructuredLogEntry JSON round-trip
# ---------------------------------------------------------------------------

@given(
    timestamp=_timestamp_strategy,
    level=_level_strategy,
    message=_short_text,
    logger_name=_short_text,
    correlation_id=_short_text,
    agent_id=_short_text,
    metadata=_metadata_strategy,
    constraints={"max_examples": 50},
)
def test_structuredlogentry_json_round_trip(timestamp, level, message, logger_name, correlation_id, agent_id, metadata):
    """
        **Validates: Requirements 2.4, 2.6, 2.7**

        FOR ALL valid StructuredLogEntry instances with any combination of
        timestamp, level, message, logger_name, correlation_id, agent_id,
        and metadata, calling to_json and then from_json SHALL produce a
        StructuredLogEntry whose fields are equal to the original.
    """
    original = StructuredLogEntry(
        timestamp=timestamp,
        level=level,
        message=message,
        logger_name=logger_name,
        correlation_id=correlation_id,
        agent_id=agent_id,
        metadata=metadata,
    )

    json_str = original.to_json()
    reconstructed = StructuredLogEntry.from_json(json_str)

    reconstructed_timestamp = reconstructed.timestamp
    assert reconstructed_timestamp == timestamp, (
        "Round-trip timestamp mismatch: expected {!r}, got {!r}".format(
            timestamp, reconstructed_timestamp)
    )

    reconstructed_level = reconstructed.level
    assert reconstructed_level == level, (
        "Round-trip level mismatch: expected {!r}, got {!r}".format(
            level, reconstructed_level)
    )

    reconstructed_message = reconstructed.message
    assert reconstructed_message == message, (
        "Round-trip message mismatch: expected {!r}, got {!r}".format(
            message, reconstructed_message)
    )

    reconstructed_logger_name = reconstructed.logger_name
    assert reconstructed_logger_name == logger_name, (
        "Round-trip logger_name mismatch: expected {!r}, got {!r}".format(
            logger_name, reconstructed_logger_name)
    )

    reconstructed_correlation_id = reconstructed.correlation_id
    assert reconstructed_correlation_id == correlation_id, (
        "Round-trip correlation_id mismatch: expected {!r}, got {!r}".format(
            correlation_id, reconstructed_correlation_id)
    )

    reconstructed_agent_id = reconstructed.agent_id
    assert reconstructed_agent_id == agent_id, (
        "Round-trip agent_id mismatch: expected {!r}, got {!r}".format(
            agent_id, reconstructed_agent_id)
    )

    reconstructed_metadata = reconstructed.metadata
    assert reconstructed_metadata == metadata, (
        "Round-trip metadata mismatch: expected {!r}, got {!r}".format(
            metadata, reconstructed_metadata)
    )

    return


# ---------------------------------------------------------------------------
# Property 6: JsonLogFormatter produces valid JSON with all fields
# ---------------------------------------------------------------------------

@given(
    timestamp=_timestamp_strategy,
    level=_level_strategy,
    message=_short_text,
    logger_name=_short_text,
    correlation_id=_short_text,
    agent_id=_short_text,
    metadata=_metadata_strategy,
    constraints={"max_examples": 50},
)
def test_jsonlogformatter_produces_valid_json_with_all_fields(timestamp, level, message, logger_name, correlation_id, agent_id, metadata):
    """
        **Validates: Requirements 4.3**

        FOR ALL valid StructuredLogEntry instances, calling
        JsonLogFormatter.format() SHALL produce a string that is valid JSON
        and when parsed contains keys for timestamp, level, message,
        logger_name, correlation_id, and agent_id with values matching
        the entry.
    """
    entry = StructuredLogEntry(
        timestamp=timestamp,
        level=level,
        message=message,
        logger_name=logger_name,
        correlation_id=correlation_id,
        agent_id=agent_id,
        metadata=metadata,
    )

    formatter = JsonLogFormatter()
    formatted_str = formatter.format(entry)

    parsed = json.loads(formatted_str)

    parsed_timestamp = parsed["timestamp"]
    expected_timestamp = timestamp.isoformat()
    assert parsed_timestamp == expected_timestamp, (
        "Formatted timestamp mismatch: expected {!r}, got {!r}".format(
            expected_timestamp, parsed_timestamp)
    )

    parsed_level = parsed["level"]
    assert parsed_level == level, (
        "Formatted level mismatch: expected {!r}, got {!r}".format(
            level, parsed_level)
    )

    parsed_message = parsed["message"]
    assert parsed_message == message, (
        "Formatted message mismatch: expected {!r}, got {!r}".format(
            message, parsed_message)
    )

    parsed_logger_name = parsed["logger_name"]
    assert parsed_logger_name == logger_name, (
        "Formatted logger_name mismatch: expected {!r}, got {!r}".format(
            logger_name, parsed_logger_name)
    )

    parsed_correlation_id = parsed["correlation_id"]
    assert parsed_correlation_id == correlation_id, (
        "Formatted correlation_id mismatch: expected {!r}, got {!r}".format(
            correlation_id, parsed_correlation_id)
    )

    parsed_agent_id = parsed["agent_id"]
    assert parsed_agent_id == agent_id, (
        "Formatted agent_id mismatch: expected {!r}, got {!r}".format(
            agent_id, parsed_agent_id)
    )

    parsed_metadata = parsed["metadata"]
    assert parsed_metadata == metadata, (
        "Formatted metadata mismatch: expected {!r}, got {!r}".format(
            metadata, parsed_metadata)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
