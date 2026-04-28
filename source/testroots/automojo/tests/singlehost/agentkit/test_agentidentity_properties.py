"""
    Property-based tests for the automojo.agentkit.agentidentity module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 1: AgentIdentity JSON round-trip
    - Property 2: AgentIdentity auto-generates UUID
    - Property 11 (partial): Defensive copy for AgentIdentity tags

    **Validates: Requirements 2.2, 2.4, 2.5, 2.6, 2.7, 2.8**
"""

import uuid

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.agentidentity import AgentIdentity


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_name_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz",
)

_version_strategy = st.text(
    min_size=1,
    max_size=10,
    alphabet="0123456789.",
)

_tags_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
    values=st.text(min_size=0, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    min_size=0,
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 1: AgentIdentity JSON round-trip
# ---------------------------------------------------------------------------

@given(
    name=_name_strategy,
    version=_version_strategy,
    tags=_tags_strategy,
    constraints={"max_examples": 30},
)
def test_agentidentity_json_roundtrip(name: str, version: str, tags: dict) -> None:
    """
        **Validates: Requirements 2.5, 2.6, 2.7, 2.8**

        For any valid AgentIdentity, calling to_json() and then from_json()
        on the resulting string produces an AgentIdentity whose identifier,
        name, version, and tags are equal to the original.
    """
    identity = AgentIdentity(name=name, version=version, tags=tags)
    json_str = identity.to_json()
    restored = AgentIdentity.from_json(json_str)

    testbase.assert_equal(restored.identifier, identity.identifier,
        "Identifier mismatch after JSON roundtrip: "
        "expected {!r}, got {!r} (name={!r}, version={!r})".format(
            identity.identifier, restored.identifier, name, version))

    testbase.assert_equal(restored.name, identity.name,
        "Name mismatch after JSON roundtrip: "
        "expected {!r}, got {!r}".format(identity.name, restored.name))

    testbase.assert_equal(restored.version, identity.version,
        "Version mismatch after JSON roundtrip: "
        "expected {!r}, got {!r}".format(identity.version, restored.version))

    testbase.assert_equal(restored.tags, identity.tags,
        "Tags mismatch after JSON roundtrip: "
        "expected {!r}, got {!r}".format(identity.tags, restored.tags))

    return


# ---------------------------------------------------------------------------
# Property 2: AgentIdentity auto-generates UUID
# ---------------------------------------------------------------------------

@given(
    name=_name_strategy,
    version=_version_strategy,
    constraints={"max_examples": 30},
)
def test_agentidentity_auto_generates_uuid(name: str, version: str) -> None:
    """
        **Validates: Requirements 2.2**

        For any name and version without an explicit identifier, the
        identifier is a non-empty string that is a valid UUID format.
    """
    identity = AgentIdentity(name=name, version=version)

    testbase.assert_true(len(identity.identifier) > 0,
        "Identifier should be non-empty for name={!r}, version={!r}".format(
            name, version))

    try:
        parsed = uuid.UUID(identity.identifier)
    except ValueError:
        raise AssertionError(
            "Identifier {!r} is not a valid UUID for name={!r}, version={!r}".format(
                identity.identifier, name, version))

    testbase.assert_equal(str(parsed), identity.identifier,
        "UUID string representation mismatch: "
        "expected {!r}, got {!r}".format(str(parsed), identity.identifier))

    return


# ---------------------------------------------------------------------------
# Property 11 (partial): Defensive copy for AgentIdentity tags
# ---------------------------------------------------------------------------

@given(
    name=_name_strategy,
    version=_version_strategy,
    tags=_tags_strategy,
    constraints={"max_examples": 30},
)
def test_agentidentity_tags_defensive_copy(name: str, version: str, tags: dict) -> None:
    """
        **Validates: Requirements 2.4**

        Modifying the dictionary returned by the tags property does not
        affect the internal state of the AgentIdentity.
    """
    identity = AgentIdentity(name=name, version=version, tags=tags)

    original_tags = identity.tags

    returned_tags = identity.tags
    returned_tags["__injected_key__"] = "injected_value"

    after_mutation_tags = identity.tags

    testbase.assert_equal(after_mutation_tags, original_tags,
        "Tags should not be affected by mutation of returned copy: "
        "expected {!r}, got {!r} (name={!r}, version={!r})".format(
            original_tags, after_mutation_tags, name, version))

    testbase.assert_false("__injected_key__" in after_mutation_tags,
        "Injected key should not appear in tags after mutating returned copy "
        "(name={!r}, version={!r})".format(name, version))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
