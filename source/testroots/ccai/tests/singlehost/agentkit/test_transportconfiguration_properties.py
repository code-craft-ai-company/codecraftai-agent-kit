"""
    Property-based tests for the ccai.agentkit.transportconfiguration module.

    Uses the ccai.testbase.properties engine to verify:
    - TransportConfiguration JSON round-trip consistency
    - TransportConfiguration YAML round-trip consistency

    **Validates: Requirements 2.16, 2.17, 24.11**
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.transportconfiguration import TransportConfiguration


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_protocol_type_strategy = st.sampled_from(["http", "websocket", "grpc", "message_queue"])

_host_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789.",
)

_port_strategy = st.integers(1, 65535)

_path_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789/.-_"),
)

_header_key_strategy = st.text(
    min_size=1,
    max_size=15,
    alphabet="abcdefghijklmnopqrstuvwxyz-",
)

_header_value_strategy = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789 ",
)

_headers_strategy = st.dictionaries(
    keys=_header_key_strategy,
    values=_header_value_strategy,
    min_size=0,
    max_size=3,
)

_timeout_strategy = st.floats(0.1, 300.0)

_option_key_strategy = st.text(
    min_size=1,
    max_size=10,
    alphabet="abcdefghijklmnopqrstuvwxyz_",
)

_option_value_strategy = st.one_of(
    st.integers(-100, 100),
    st.text(min_size=0, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
)

_options_strategy = st.dictionaries(
    keys=_option_key_strategy,
    values=_option_value_strategy,
    min_size=0,
    max_size=3,
)


# ---------------------------------------------------------------------------
# Property: TransportConfiguration JSON round-trip consistency
# ---------------------------------------------------------------------------

@given(
    protocol_type=_protocol_type_strategy,
    host=_host_strategy,
    port=_port_strategy,
    path=_path_strategy,
    headers=_headers_strategy,
    timeout=_timeout_strategy,
    options=_options_strategy,
    constraints={"max_examples": 50},
)
def test_transportconfiguration_json_roundtrip(
    protocol_type: str,
    host: str,
    port: int,
    path: str,
    headers: dict,
    timeout: float,
    options: dict,
) -> None:
    """
        **Validates: Requirements 2.16, 24.11**

        For all valid TransportConfiguration instances, serializing to JSON
        via to_json and then deserializing via from_json produces an
        equivalent TransportConfiguration object with identical protocol_type,
        host, port, path, headers, timeout, and options values.
    """
    original = TransportConfiguration(
        protocol_type=protocol_type,
        host=host,
        port=port,
        path=path,
        headers=headers,
        timeout=timeout,
        options=options,
    )

    json_str = original.to_json()
    restored = TransportConfiguration.from_json(json_str)

    testbase.assert_equal(
        restored.protocol_type, original.protocol_type,
        "protocol_type mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.protocol_type, original.protocol_type),
    )

    testbase.assert_equal(
        restored.host, original.host,
        "host mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.host, original.host),
    )

    testbase.assert_equal(
        restored.port, original.port,
        "port mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.port, original.port),
    )

    testbase.assert_equal(
        restored.path, original.path,
        "path mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.path, original.path),
    )

    testbase.assert_equal(
        restored.headers, original.headers,
        "headers mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.headers, original.headers),
    )

    testbase.assert_equal(
        restored.timeout, original.timeout,
        "timeout mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.timeout, original.timeout),
    )

    testbase.assert_equal(
        restored.options, original.options,
        "options mismatch after JSON round-trip: "
        "{!r} != {!r}".format(restored.options, original.options),
    )

    return


# ---------------------------------------------------------------------------
# Property: TransportConfiguration YAML round-trip consistency
# ---------------------------------------------------------------------------

@given(
    protocol_type=_protocol_type_strategy,
    host=_host_strategy,
    port=_port_strategy,
    path=_path_strategy,
    headers=_headers_strategy,
    timeout=_timeout_strategy,
    options=_options_strategy,
    constraints={"max_examples": 50},
)
def test_transportconfiguration_yaml_roundtrip(
    protocol_type: str,
    host: str,
    port: int,
    path: str,
    headers: dict,
    timeout: float,
    options: dict,
) -> None:
    """
        **Validates: Requirements 2.17**

        For all valid TransportConfiguration instances, serializing to YAML
        via to_yaml and then deserializing via from_yaml produces an
        equivalent TransportConfiguration object with identical protocol_type,
        host, port, path, headers, timeout, and options values.
    """
    original = TransportConfiguration(
        protocol_type=protocol_type,
        host=host,
        port=port,
        path=path,
        headers=headers,
        timeout=timeout,
        options=options,
    )

    yaml_str = original.to_yaml()
    restored = TransportConfiguration.from_yaml(yaml_str)

    testbase.assert_equal(
        restored.protocol_type, original.protocol_type,
        "protocol_type mismatch after YAML round-trip: "
        "{!r} != {!r}".format(restored.protocol_type, original.protocol_type),
    )

    testbase.assert_equal(
        restored.host, original.host,
        "host mismatch after YAML round-trip: "
        "{!r} != {!r}".format(restored.host, original.host),
    )

    testbase.assert_equal(
        restored.port, original.port,
        "port mismatch after YAML round-trip: "
        "{!r} != {!r}".format(restored.port, original.port),
    )

    testbase.assert_equal(
        restored.path, original.path,
        "path mismatch after YAML round-trip: "
        "{!r} != {!r}".format(restored.path, original.path),
    )

    testbase.assert_equal(
        restored.headers, original.headers,
        "headers mismatch after YAML round-trip: "
        "{!r} != {!r}".format(restored.headers, original.headers),
    )

    testbase.assert_equal(
        restored.timeout, original.timeout,
        "timeout mismatch after YAML round-trip: "
        "{!r} != {!r}".format(restored.timeout, original.timeout),
    )

    testbase.assert_equal(
        restored.options, original.options,
        "options mismatch after YAML round-trip: "
        "{!r} != {!r}".format(restored.options, original.options),
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
