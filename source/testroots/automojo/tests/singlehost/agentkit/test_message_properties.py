"""
    Property-based tests for the automojo.agentkit.message module.

    Uses the automojo.testbase.properties engine to verify:
    - Message JSON round-trip consistency

    **Validates: Requirements 4.9, 24.9**
"""

import automojo.testbase as testbase

from datetime import datetime
from datetime import timezone

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.agentaddress import AgentAddress
from automojo.agentkit.message import Message
from automojo.agentkit.messagepattern import MessagePattern


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_identifier_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
)

_transport_name_strategy = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
)

_endpoint_key_strategy = st.sampled_from(["host", "port", "path", "queue_name", "topic"])

_endpoint_value_strategy = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789.:/",
)

_endpoint_strategy = st.dictionaries(
    keys=_endpoint_key_strategy,
    values=_endpoint_value_strategy,
    min_size=0,
    max_size=3,
)

_agent_address_strategy = st.builds(
    AgentAddress,
    agent_identifier=_identifier_strategy,
    transport_name=_transport_name_strategy,
    endpoint=_endpoint_strategy,
)

_pattern_strategy = st.sampled_from([
    MessagePattern.REQUEST,
    MessagePattern.RESPONSE,
    MessagePattern.FIRE_AND_FORGET,
    MessagePattern.EVENT,
])

_string_key = st.text(
    min_size=1,
    max_size=10,
    alphabet="abcdefghijklmnopqrstuvwxyz",
)

_json_value = st.one_of(
    st.integers(-1000, 1000),
    st.text(min_size=0, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 "),
)

_payload_strategy = st.one_of(
    st.dictionaries(
        keys=_string_key,
        values=_json_value,
        min_size=0,
        max_size=3,
    ),
    st.lists(
        st.integers(-100, 100),
        min_size=0,
        max_size=5,
    ),
    st.text(min_size=0, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 "),
)

_headers_strategy = st.dictionaries(
    keys=_string_key,
    values=st.text(min_size=1, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    min_size=0,
    max_size=3,
)

_correlation_id_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"),
)

_message_id_strategy = st.text(
    min_size=1,
    max_size=36,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
)


# ---------------------------------------------------------------------------
# Property: Message JSON round-trip consistency
# ---------------------------------------------------------------------------

@given(
    sender=_agent_address_strategy,
    recipient=_agent_address_strategy,
    payload=_payload_strategy,
    pattern=_pattern_strategy,
    headers=_headers_strategy,
    correlation_id=_correlation_id_strategy,
    message_id=_message_id_strategy,
    constraints={"max_examples": 50},
)
def test_message_json_roundtrip(
    sender: AgentAddress,
    recipient: AgentAddress,
    payload: object,
    pattern: MessagePattern,
    headers: dict,
    correlation_id: str,
    message_id: str,
) -> None:
    """
        **Validates: Requirements 4.9, 24.9**

        For all valid Message instances with JSON-serializable payloads,
        serializing to JSON via to_json and then deserializing via from_json
        produces an equivalent Message object with identical identifier,
        sender, recipient, payload, pattern, headers, correlation_id, and
        timestamp values.
    """
    fixed_timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    original = Message(
        sender=sender,
        recipient=recipient,
        payload=payload,
        pattern=pattern,
        headers=headers,
        correlation_id=correlation_id,
        identifier=message_id,
        timestamp=fixed_timestamp,
    )

    json_str = original.to_json()
    restored = Message.from_json(json_str)

    testbase.assert_equal(
        restored.identifier, original.identifier,
        "identifier mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.identifier, original.identifier),
    )

    testbase.assert_equal(
        restored.sender.agent_identifier, original.sender.agent_identifier,
        "sender.agent_identifier mismatch after JSON round-trip: "
        "{!r} != {!r}".format(
            restored.sender.agent_identifier, original.sender.agent_identifier),
    )

    testbase.assert_equal(
        restored.sender.transport_name, original.sender.transport_name,
        "sender.transport_name mismatch after JSON round-trip: "
        "{!r} != {!r}".format(
            restored.sender.transport_name, original.sender.transport_name),
    )

    testbase.assert_equal(
        restored.sender.endpoint, original.sender.endpoint,
        "sender.endpoint mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.sender.endpoint, original.sender.endpoint),
    )

    testbase.assert_equal(
        restored.recipient.agent_identifier, original.recipient.agent_identifier,
        "recipient.agent_identifier mismatch after JSON round-trip: "
        "{!r} != {!r}".format(
            restored.recipient.agent_identifier, original.recipient.agent_identifier),
    )

    testbase.assert_equal(
        restored.recipient.transport_name, original.recipient.transport_name,
        "recipient.transport_name mismatch after JSON round-trip: "
        "{!r} != {!r}".format(
            restored.recipient.transport_name, original.recipient.transport_name),
    )

    testbase.assert_equal(
        restored.recipient.endpoint, original.recipient.endpoint,
        "recipient.endpoint mismatch after JSON round-trip: "
        "{!r} != {!r}".format(
            restored.recipient.endpoint, original.recipient.endpoint),
    )

    testbase.assert_equal(
        restored.payload, original.payload,
        "payload mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.payload, original.payload),
    )

    testbase.assert_equal(
        restored.pattern, original.pattern,
        "pattern mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.pattern, original.pattern),
    )

    testbase.assert_equal(
        restored.headers, original.headers,
        "headers mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.headers, original.headers),
    )

    testbase.assert_equal(
        restored.correlation_id, original.correlation_id,
        "correlation_id mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.correlation_id, original.correlation_id),
    )

    testbase.assert_equal(
        restored.timestamp.isoformat(), original.timestamp.isoformat(),
        "timestamp mismatch after JSON round-trip: "
        "{!r} != {!r}".format(
            restored.timestamp.isoformat(), original.timestamp.isoformat()),
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
