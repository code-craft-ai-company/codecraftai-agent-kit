"""
    .. module:: ccai.tests.singlehost.agentkit.test_memoryentry_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for MemoryEntry and ExpirationPolicy round-trip serialization.

    Uses ccai.testbase.properties to verify:
    - Property 1: MemoryEntry JSON round-trip
    - Property 2: ExpirationPolicy round-trip

    **Validates: Requirements 1.7, 1.8, 1.9, 1.10, 13.7, 13.8, 13.9, 17.1, 17.2, 17.7**
"""

import json

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryscope import MemoryScope
from ccai.agentkit.expirationpolicy import ExpirationPolicy


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_scope = st.sampled_from([MemoryScope.AGENT, MemoryScope.SHARED, MemoryScope.GLOBAL])

_content = st.text(min_size=0, max_size=200)

_identifier = st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")

_tag = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")

_tags = st.lists(element=_tag, min_size=0, max_size=5)

_metadata_value = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
)

_metadata = st.dictionaries(
    keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
    values=_metadata_value,
    max_size=5,
)

_embedding_float = st.floats(min_value=-10.0, max_value=10.0)

_embedding = st.one_of(
    st.none(),
    st.lists(element=_embedding_float, min_size=1, max_size=8),
)


# ---------------------------------------------------------------------------
# Property 1: MemoryEntry JSON round-trip
# ---------------------------------------------------------------------------

@given(
    content=_content,
    scope=_scope,
    identifier=_identifier,
    embedding=_embedding,
    metadata=_metadata,
    tags=_tags,
    constraints={"max_examples": 50},
)
def test_memoryentry_json_roundtrip(
    content: str,
    scope: MemoryScope,
    identifier: str,
    embedding: list,
    metadata: dict,
    tags: list,
) -> None:
    """
        **Validates: Requirements 1.7, 1.8, 1.9, 1.10, 17.1, 17.2, 17.7**

        For all valid MemoryEntry instances, calling to_json() and then
        from_json() on the resulting string shall produce an equivalent
        MemoryEntry whose fields are equal to the original.
    """
    original = MemoryEntry(
        content=content,
        scope=scope,
        identifier=identifier,
        embedding=embedding,
        metadata=metadata,
        tags=tags,
    )

    json_str = original.to_json()
    restored = MemoryEntry.from_json(json_str)

    assert original == restored, (
        "MemoryEntry JSON round-trip failed. "
        "Original identifier={!r}, scope={!r}, content={!r}. "
        "Restored identifier={!r}, scope={!r}, content={!r}.".format(
            original.identifier, original.scope, original.content,
            restored.identifier, restored.scope, restored.content,
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 2: ExpirationPolicy round-trip
# ---------------------------------------------------------------------------

@given(
    default_ttl=st.one_of(st.none(), st.floats(min_value=0.1, max_value=86400.0)),
    cleanup_interval=st.floats(min_value=1.0, max_value=86400.0),
    constraints={"max_examples": 50},
)
def test_expirationpolicy_roundtrip(
    default_ttl: float,
    cleanup_interval: float,
) -> None:
    """
        **Validates: Requirements 13.7, 13.8, 13.9**

        For all valid ExpirationPolicy instances, calling to_json() and then
        from_dict(json.loads(...)) shall produce an equivalent ExpirationPolicy.
    """
    original = ExpirationPolicy(
        default_ttl=default_ttl,
        cleanup_interval=cleanup_interval,
    )

    json_str = original.to_json()
    data = json.loads(json_str)
    restored = ExpirationPolicy.from_dict(data)

    assert original == restored, (
        "ExpirationPolicy round-trip failed. "
        "Original ttl={}, interval={}. "
        "Restored ttl={}, interval={}.".format(
            original.default_ttl, original.cleanup_interval,
            restored.default_ttl, restored.cleanup_interval,
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
