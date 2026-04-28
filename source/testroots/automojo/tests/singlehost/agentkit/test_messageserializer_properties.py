"""
    Property-based tests for the automojo.agentkit message serializer
    modules.

    Uses the automojo.testbase.properties engine to verify:
    - JSON serializer round-trip consistency
    - MsgPack serializer round-trip consistency

    .. module:: automojo.tests.singlehost.agentkit.test_messageserializer_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for message serializer round-trip invariants.
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.jsonmessageserializer import JsonMessageSerializer


# ---------------------------------------------------------------------------
# Strategies for JSON-serializable Python objects
# ---------------------------------------------------------------------------

_string_key = st.text(
    min_size=1,
    max_size=10,
    alphabet="abcdefghijklmnopqrstuvwxyz",
)

_json_primitive = st.one_of(
    st.integers(-10000, 10000),
    st.text(min_size=0, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 "),
    st.booleans(),
    st.none(),
)

_json_value = st.one_of(
    _json_primitive,
    st.lists(_json_primitive, min_size=0, max_size=5),
)

_json_object_strategy = st.one_of(
    st.dictionaries(
        keys=_string_key,
        values=_json_value,
        min_size=0,
        max_size=5,
    ),
    st.lists(_json_primitive, min_size=0, max_size=5),
    st.text(min_size=0, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 "),
    st.integers(-10000, 10000),
    st.booleans(),
    st.none(),
)


# ---------------------------------------------------------------------------
# Property: JSON serializer round-trip consistency
# ---------------------------------------------------------------------------

@given(
    obj=_json_object_strategy,
    constraints={"max_examples": 50},
)
def test_json_serializer_roundtrip(obj: object) -> None:
    """
        **Validates: Requirements 9.12**

        For all valid JSON-serializable Python objects, serializing with
        JsonMessageSerializer and then deserializing produces an equivalent
        Python object.
    """
    serializer = JsonMessageSerializer()

    serialized = serializer.serialize(obj)

    testbase.assert_true(
        isinstance(serialized, bytes),
        "serialize should return bytes, got {!r}".format(type(serialized).__name__),
    )

    deserialized = serializer.deserialize(serialized)

    testbase.assert_equal(
        deserialized, obj,
        "JSON round-trip mismatch: deserialize(serialize({!r})) produced {!r}".format(
            obj, deserialized),
    )

    return


# ---------------------------------------------------------------------------
# Strategies for MsgPack-serializable Python objects
# ---------------------------------------------------------------------------

_msgpack_primitive = st.one_of(
    st.integers(-10000, 10000),
    st.text(min_size=0, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 "),
    st.booleans(),
    st.none(),
)

_msgpack_value = st.one_of(
    _msgpack_primitive,
    st.lists(_msgpack_primitive, min_size=0, max_size=5),
)

_msgpack_object_strategy = st.one_of(
    st.dictionaries(
        keys=_string_key,
        values=_msgpack_value,
        min_size=0,
        max_size=5,
    ),
    st.lists(_msgpack_primitive, min_size=0, max_size=5),
    st.text(min_size=0, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 "),
    st.integers(-10000, 10000),
    st.booleans(),
    st.none(),
)


# ---------------------------------------------------------------------------
# Property: MsgPack serializer round-trip consistency
# ---------------------------------------------------------------------------

# NOTE: The msgpack package may not be installed. If it is not available,
# the MsgpackMessageSerializer constructor raises ImportError. We guard
# the property test so it is only defined when msgpack is importable.

try:
    from automojo.agentkit.msgpackmessageserializer import MsgpackMessageSerializer
    MsgpackMessageSerializer()
    _MSGPACK_AVAILABLE = True
except ImportError:
    _MSGPACK_AVAILABLE = False


if _MSGPACK_AVAILABLE:

    @given(
        obj=_msgpack_object_strategy,
        constraints={"max_examples": 50},
    )
    def test_msgpack_serializer_roundtrip(obj: object) -> None:
        """
            **Validates: Requirements 9.13**

            For all valid MessagePack-serializable Python objects, serializing
            with MsgpackMessageSerializer and then deserializing produces an
            equivalent Python object.
        """
        serializer = MsgpackMessageSerializer()

        serialized = serializer.serialize(obj)

        testbase.assert_true(
            isinstance(serialized, bytes),
            "serialize should return bytes, got {!r}".format(type(serialized).__name__),
        )

        deserialized = serializer.deserialize(serialized)

        testbase.assert_equal(
            deserialized, obj,
            "MsgPack round-trip mismatch: deserialize(serialize({!r})) produced {!r}".format(
                obj, deserialized),
        )

        return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
