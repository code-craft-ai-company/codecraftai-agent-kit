"""
    Property-based tests for the ccai.agentkit.messagingconfiguration module.

    Uses the ccai.testbase.properties engine to verify:
    - MessagingConfiguration JSON round-trip consistency

    **Validates: Requirements 20.13, 24.12**
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.messagingconfiguration import MessagingConfiguration


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_transport_name_strategy = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
)

_serialization_format_strategy = st.sampled_from(["json", "msgpack", "protobuf"])

_timeout_strategy = st.floats(0.1, 300.0)

_dict_key_strategy = st.text(
    min_size=1,
    max_size=10,
    alphabet="abcdefghijklmnopqrstuvwxyz_",
)

_dict_value_strategy = st.one_of(
    st.integers(-100, 100),
    st.text(min_size=0, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
)

_optional_dict_strategy = st.one_of(
    st.just(None),
    st.dictionaries(
        keys=_dict_key_strategy,
        values=_dict_value_strategy,
        min_size=0,
        max_size=3,
    ),
)


# ---------------------------------------------------------------------------
# Property: MessagingConfiguration JSON round-trip consistency
# ---------------------------------------------------------------------------

@given(
    default_transport=_transport_name_strategy,
    default_serialization_format=_serialization_format_strategy,
    default_request_timeout=_timeout_strategy,
    transport_configurations=_optional_dict_strategy,
    pubsub_settings=_optional_dict_strategy,
    options=_optional_dict_strategy,
    constraints={"max_examples": 30},
)
def test_messagingconfiguration_json_roundtrip(
    default_transport: str,
    default_serialization_format: str,
    default_request_timeout: float,
    transport_configurations: dict,
    pubsub_settings: dict,
    options: dict,
) -> None:
    """
        **Validates: Requirements 20.13, 24.12**

        For all valid MessagingConfiguration instances, serializing to JSON
        via to_json and then deserializing via from_json produces an
        equivalent MessagingConfiguration object with identical
        default_transport, default_serialization_format,
        default_request_timeout, transport_configurations,
        pubsub_settings, and options values.
    """
    original = MessagingConfiguration(
        default_transport=default_transport,
        default_serialization_format=default_serialization_format,
        default_request_timeout=default_request_timeout,
        transport_configurations=transport_configurations,
        pubsub_settings=pubsub_settings,
        options=options,
    )

    json_str = original.to_json()
    restored = MessagingConfiguration.from_json(json_str)

    testbase.assert_equal(
        restored.default_transport, original.default_transport,
        "default_transport mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.default_transport, original.default_transport),
    )

    testbase.assert_equal(
        restored.default_serialization_format, original.default_serialization_format,
        "default_serialization_format mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.default_serialization_format, original.default_serialization_format),
    )

    testbase.assert_equal(
        restored.default_request_timeout, original.default_request_timeout,
        "default_request_timeout mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.default_request_timeout, original.default_request_timeout),
    )

    testbase.assert_equal(
        restored.transport_configurations, original.transport_configurations,
        "transport_configurations mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.transport_configurations, original.transport_configurations),
    )

    testbase.assert_equal(
        restored.pubsub_settings, original.pubsub_settings,
        "pubsub_settings mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.pubsub_settings, original.pubsub_settings),
    )

    testbase.assert_equal(
        restored.options, original.options,
        "options mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.options, original.options),
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
