"""
    .. module:: ccai.tests.singlehost.agentkit.test_memoryconfiguration_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for MemoryConfiguration round-trip serialization.

    Uses ccai.testbase.properties to verify:
    - Property 9: MemoryConfiguration JSON round-trip

    **Validates: Requirements 12.10, 12.11, 12.12, 12.13, 12.14, 17.5, 17.6, 17.9**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.memoryconfiguration import MemoryConfiguration
from ccai.agentkit.memoryscope import MemoryScope
from ccai.agentkit.expirationpolicy import ExpirationPolicy


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_backend_type = st.sampled_from(["inmemory", "file", "redis", "postgres"])

_scope = st.sampled_from([MemoryScope.AGENT, MemoryScope.SHARED, MemoryScope.GLOBAL])

_metadata_value = st.one_of(
    st.text(min_size=0, max_size=30),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
)

_connection_params = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz_"),
        values=_metadata_value,
        max_size=4,
    ),
)

_embedding_settings = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz_"),
        values=_metadata_value,
        max_size=4,
    ),
)

_credential_name = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")

_credential_names = st.one_of(
    st.none(),
    st.lists(element=_credential_name, min_size=0, max_size=3),
)

_expiration_policy = st.one_of(
    st.none(),
    st.builds(
        ExpirationPolicy,
        default_ttl=st.one_of(st.none(), st.floats(min_value=0.1, max_value=86400.0)),
        cleanup_interval=st.floats(min_value=1.0, max_value=86400.0),
    ),
)


# ---------------------------------------------------------------------------
# Property 9: MemoryConfiguration JSON round-trip
# ---------------------------------------------------------------------------

@given(
    backend_type=_backend_type,
    connection_params=_connection_params,
    default_scope=_scope,
    expiration_policy=_expiration_policy,
    embedding_settings=_embedding_settings,
    credential_names=_credential_names,
    constraints={"max_examples": 50},
)
def test_memoryconfiguration_json_roundtrip(
    backend_type: str,
    connection_params: dict,
    default_scope: MemoryScope,
    expiration_policy: ExpirationPolicy,
    embedding_settings: dict,
    credential_names: list,
) -> None:
    """
        **Validates: Requirements 12.10, 12.11, 12.12, 12.13, 12.14, 17.5, 17.6, 17.9**

        For all valid MemoryConfiguration instances, calling to_json() and then
        from_json() on the resulting string shall produce an equivalent
        MemoryConfiguration whose fields are equal to the original.
    """
    original = MemoryConfiguration(
        backend_type=backend_type,
        connection_params=connection_params,
        default_scope=default_scope,
        expiration_policy=expiration_policy,
        embedding_settings=embedding_settings,
        credential_names=credential_names,
    )

    json_str = original.to_json()
    restored = MemoryConfiguration.from_json(json_str)

    assert original == restored, (
        "MemoryConfiguration JSON round-trip failed. "
        "Original backend_type={!r}, scope={!r}. "
        "Restored backend_type={!r}, scope={!r}.".format(
            original.backend_type, original.default_scope,
            restored.backend_type, restored.default_scope,
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
