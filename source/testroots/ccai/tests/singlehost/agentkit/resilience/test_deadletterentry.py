"""
    Unit tests for the ccai.agentkit.deadletterentry module.
"""

from ccai.agentkit.deadletterentry import DeadLetterEntry


def test_entry_construction():
    """
        Verify that DeadLetterEntry stores all fields correctly.
    """
    entry = DeadLetterEntry(
        operation_type="send_message",
        payload={"to": "agent-2", "body": "hello"},
        exception_info="ConnectionError(timeout)",
        retry_attempts=3,
        source_component="transport",
        agent_identifier="agent-1"
    )
    assert entry.operation_type == "send_message", "operation_type should match"
    assert entry.payload == {"to": "agent-2", "body": "hello"}, "payload should match"
    assert entry.exception_info == "ConnectionError(timeout)", "exception_info should match"
    assert entry.retry_attempts == 3, "retry_attempts should match"
    assert entry.source_component == "transport", "source_component should match"
    assert entry.agent_identifier == "agent-1", "agent_identifier should match"
    return


def test_entry_auto_generates_identifier():
    """
        Verify that identifier is auto-generated when not provided.
    """
    entry = DeadLetterEntry("op", {}, "err", 0, "src", "agent")
    assert entry.identifier is not None, "identifier should be auto-generated"
    assert len(entry.identifier) > 0, "identifier should not be empty"
    return


def test_entry_auto_generates_timestamp():
    """
        Verify that timestamp is auto-generated when not provided.
    """
    entry = DeadLetterEntry("op", {}, "err", 0, "src", "agent")
    assert entry.timestamp is not None, "timestamp should be auto-generated"
    return


def test_entry_json_round_trip():
    """
        Verify that to_json followed by from_json produces equivalent values.
    """
    original = DeadLetterEntry(
        operation_type="tool_exec",
        payload={"tool": "search", "args": [1, 2]},
        exception_info="ToolError(not found)",
        retry_attempts=2,
        source_component="tool_executor",
        agent_identifier="agent-1",
        metadata={"priority": "high"}
    )
    json_str = original.to_json()
    restored = DeadLetterEntry.from_json(json_str)

    assert restored.identifier == original.identifier, "identifier should match"
    assert restored.operation_type == original.operation_type, "operation_type should match"
    assert restored.payload == original.payload, "payload should match"
    assert restored.retry_attempts == original.retry_attempts, "retry_attempts should match"
    return
