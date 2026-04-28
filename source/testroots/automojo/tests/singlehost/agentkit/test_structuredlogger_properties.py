"""
    Property-based tests for the automojo.agentkit.structuredlogger module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 5: StructuredLogger produces entries with correct fields

    **Validates: Requirements 3.3, 3.4**
"""

from datetime import datetime

from automojo.testbase.properties import given, assume
from automojo.testbase.properties import strategies as st

from automojo.agentkit.correlationcontext import CorrelationContext
from automojo.agentkit.structuredlogger import StructuredLogger
from automojo.agentkit.structuredlogentry import StructuredLogEntry


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_short_text = st.text(min_size=1, max_size=100)

_level_strategy = st.sampled_from(["debug", "info", "warning", "error", "critical"])

_metadata_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.text(min_size=0, max_size=50),
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 5: StructuredLogger produces entries with correct fields
# ---------------------------------------------------------------------------

@given(
    agent_id=_short_text,
    correlation_id=_short_text,
    level=_level_strategy,
    message=_short_text,
    metadata=_metadata_strategy,
    constraints={"max_examples": 50},
)
def test_structuredlogger_produces_entries_with_correct_fields(agent_id, correlation_id, level, message, metadata):
    """
        **Validates: Requirements 3.3, 3.4**

        FOR ALL valid agent_id, correlation_id, level, message, and metadata
        combinations, calling the appropriate log method on a StructuredLogger
        SHALL return a StructuredLogEntry with matching level, message,
        logger_name equal to 'automojo.agentkit.observability',
        correlation_id from the CorrelationContext, agent_id from the logger,
        metadata matching the keyword arguments, and a timestamp that is a
        valid datetime.
    """
    context = CorrelationContext(correlation_id=correlation_id)
    logger = StructuredLogger(agent_id=agent_id, correlation_context=context)

    # Exclude metadata keys that would conflict with the log method's
    # positional 'message' parameter when unpacked as **kwargs.
    assume("message" not in metadata)

    before = datetime.utcnow()

    log_method = getattr(logger, level)
    entry = log_method(message, **metadata)

    after = datetime.utcnow()

    assert isinstance(entry, StructuredLogEntry), (
        "Expected StructuredLogEntry, got {!r}".format(type(entry))
    )

    entry_level = entry.level
    assert entry_level == level, (
        "Entry level mismatch: expected {!r}, got {!r}".format(level, entry_level)
    )

    entry_message = entry.message
    assert entry_message == message, (
        "Entry message mismatch: expected {!r}, got {!r}".format(message, entry_message)
    )

    entry_logger_name = entry.logger_name
    assert entry_logger_name == "automojo.agentkit.observability", (
        "Entry logger_name mismatch: expected 'automojo.agentkit.observability', got {!r}".format(
            entry_logger_name)
    )

    entry_correlation_id = entry.correlation_id
    assert entry_correlation_id == correlation_id, (
        "Entry correlation_id mismatch: expected {!r}, got {!r}".format(
            correlation_id, entry_correlation_id)
    )

    entry_agent_id = entry.agent_id
    assert entry_agent_id == agent_id, (
        "Entry agent_id mismatch: expected {!r}, got {!r}".format(
            agent_id, entry_agent_id)
    )

    entry_metadata = entry.metadata
    assert entry_metadata == metadata, (
        "Entry metadata mismatch: expected {!r}, got {!r}".format(
            metadata, entry_metadata)
    )

    entry_timestamp = entry.timestamp
    assert isinstance(entry_timestamp, datetime), (
        "Entry timestamp is not a datetime: got {!r}".format(type(entry_timestamp))
    )

    assert before <= entry_timestamp <= after, (
        "Entry timestamp {!r} not between {!r} and {!r}".format(
            entry_timestamp, before, after)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
