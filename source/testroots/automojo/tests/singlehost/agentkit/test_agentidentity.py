"""
    Tests for the automojo.agentkit.agentidentity module.

    Contains property-based tests (using automojo.testbase.properties) and unit tests
    for the AgentIdentity class.

    Feature: core-agent-framework
"""

import json
import uuid


from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.agentidentity import AgentIdentity


# ---------------------------------------------------------------------------
# testbase property strategies for generating AgentIdentity inputs
# ---------------------------------------------------------------------------

# Strategy for generating non-empty printable text suitable for name/version
name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=50
).filter(lambda s: len(s.strip()) > 0)

version_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating tag dictionaries with string keys and values
tags_strategy = st.dictionaries(
    keys=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=20
    ),
    values=st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z")),
        min_size=0,
        max_size=50
    ),
    max_size=10
)

# Strategy for generating optional explicit identifiers
@composite
def _uuid_string(draw):
    """
        Generates a valid UUID v4 string.

        :returns: A UUID v4 formatted string.
    """
    segments = [
        draw(st.integers(min_value=0, max_value=0xFFFFFFFF)),
        draw(st.integers(min_value=0, max_value=0xFFFF)),
        draw(st.integers(min_value=0x4000, max_value=0x4FFF)),
        draw(st.integers(min_value=0x8000, max_value=0xBFFF)),
        draw(st.integers(min_value=0, max_value=0xFFFFFFFFFFFF)),
    ]
    return f"{segments[0]:08x}-{segments[1]:04x}-{segments[2]:04x}-{segments[3]:04x}-{segments[4]:012x}"


optional_identifier_strategy = st.one_of(
    st.none(),
    _uuid_string()
)


# ---------------------------------------------------------------------------
# Property 1: AgentIdentity JSON round-trip
# **Validates: Requirements 2.6, 12.7**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    tags=tags_strategy,
    identifier=optional_identifier_strategy,
    constraints={"max_examples": 100})
def test_property_1_json_round_trip(name, version, tags, identifier):
    """
        Property 1: AgentIdentity JSON round-trip.

        For any valid AgentIdentity instance, calling to_json() and then
        from_json() on the resulting string produces an AgentIdentity whose
        identifier, name, version, and tags are equal to the original.

        **Validates: Requirements 2.6, 12.7**
    """
    identity = AgentIdentity(
        name=name,
        version=version,
        tags=tags,
        identifier=identifier
    )

    json_str = identity.to_json()
    restored = AgentIdentity.from_json(json_str)

    assert restored.identifier == identity.identifier, (
        "Round-trip identifier mismatch: {!r} != {!r}".format(
            restored.identifier, identity.identifier
        )
    )
    assert restored.name == identity.name, (
        "Round-trip name mismatch: {!r} != {!r}".format(
            restored.name, identity.name
        )
    )
    assert restored.version == identity.version, (
        "Round-trip version mismatch: {!r} != {!r}".format(
            restored.version, identity.version
        )
    )
    assert restored.tags == identity.tags, (
        "Round-trip tags mismatch: {!r} != {!r}".format(
            restored.tags, identity.tags
        )
    )
    return


# ---------------------------------------------------------------------------
# Property 2: AgentIdentity serialization completeness
# **Validates: Requirements 2.1, 2.4, 2.5, 12.1**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    tags=tags_strategy,
    identifier=optional_identifier_strategy,
    constraints={"max_examples": 100})
def test_property_2_serialization_completeness(name, version, tags, identifier):
    """
        Property 2: AgentIdentity serialization completeness.

        For any valid AgentIdentity instance, as_dict() contains keys
        identifier, name, version, and tags with values matching the
        properties. to_json() produces valid JSON with the same keys
        and values.

        **Validates: Requirements 2.1, 2.4, 2.5, 12.1**
    """
    identity = AgentIdentity(
        name=name,
        version=version,
        tags=tags,
        identifier=identifier
    )

    # Verify as_dict completeness
    d = identity.as_dict()

    has_identifier = "identifier" in d
    has_name = "name" in d
    has_version = "version" in d
    has_tags = "tags" in d

    assert has_identifier is True, "as_dict should contain 'identifier' key"
    assert has_name is True, "as_dict should contain 'name' key"
    assert has_version is True, "as_dict should contain 'version' key"
    assert has_tags is True, "as_dict should contain 'tags' key"

    assert d["identifier"] == identity.identifier, (
        "as_dict identifier mismatch: {!r} != {!r}".format(
            d["identifier"], identity.identifier
        )
    )
    assert d["name"] == identity.name, (
        "as_dict name mismatch: {!r} != {!r}".format(
            d["name"], identity.name
        )
    )
    assert d["version"] == identity.version, (
        "as_dict version mismatch: {!r} != {!r}".format(
            d["version"], identity.version
        )
    )
    assert d["tags"] == identity.tags, (
        "as_dict tags mismatch: {!r} != {!r}".format(
            d["tags"], identity.tags
        )
    )

    # Verify to_json produces valid JSON with same keys and values
    json_str = identity.to_json()
    parsed = json.loads(json_str)

    has_identifier_json = "identifier" in parsed
    has_name_json = "name" in parsed
    has_version_json = "version" in parsed
    has_tags_json = "tags" in parsed

    assert has_identifier_json is True, "JSON should contain 'identifier' key"
    assert has_name_json is True, "JSON should contain 'name' key"
    assert has_version_json is True, "JSON should contain 'version' key"
    assert has_tags_json is True, "JSON should contain 'tags' key"

    assert parsed["identifier"] == identity.identifier, (
        "JSON identifier mismatch: {!r} != {!r}".format(
            parsed["identifier"], identity.identifier
        )
    )
    assert parsed["name"] == identity.name, (
        "JSON name mismatch: {!r} != {!r}".format(
            parsed["name"], identity.name
        )
    )
    assert parsed["version"] == identity.version, (
        "JSON version mismatch: {!r} != {!r}".format(
            parsed["version"], identity.version
        )
    )
    assert parsed["tags"] == identity.tags, (
        "JSON tags mismatch: {!r} != {!r}".format(
            parsed["tags"], identity.tags
        )
    )
    return


# ---------------------------------------------------------------------------
# Property 3: AgentIdentity auto-generates UUID
# **Validates: Requirements 2.2**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    tags=tags_strategy,
    constraints={"max_examples": 100})
def test_property_3_auto_generates_uuid(name, version, tags):
    """
        Property 3: AgentIdentity auto-generates UUID.

        For any AgentIdentity created without an explicit identifier,
        the resulting identifier property is a valid UUID string
        parseable by uuid.UUID.

        **Validates: Requirements 2.2**
    """
    identity = AgentIdentity(
        name=name,
        version=version,
        tags=tags
    )

    identifier_str = identity.identifier

    is_not_none = identifier_str is not None
    assert is_not_none is True, "Auto-generated identifier should not be None"

    is_not_empty = len(identifier_str) > 0
    assert is_not_empty is True, "Auto-generated identifier should not be empty"

    # Verify it is a valid UUID
    parsed_uuid = uuid.UUID(identifier_str)
    round_trip_str = str(parsed_uuid)

    assert round_trip_str == identifier_str, (
        "Identifier should be a valid UUID string, got: {!r}".format(identifier_str)
    )
    return


# ---------------------------------------------------------------------------
# Unit tests for AgentIdentity edge cases (Task 4.5)
# **Validates: Requirements 2.3, 16.3, 16.4**
# ---------------------------------------------------------------------------

def test_repr_contains_class_name_identifier_name_version():
    """
        Verify that __repr__ includes the class name, identifier, name, and version.
    """
    identity = AgentIdentity(
        name="test-agent",
        version="1.0.0",
        identifier="abc-123"
    )

    repr_str = repr(identity)

    has_class_name = "AgentIdentity" in repr_str
    has_identifier = "abc-123" in repr_str
    has_name = "test-agent" in repr_str
    has_version = "1.0.0" in repr_str

    assert has_class_name is True, "repr should contain 'AgentIdentity'"
    assert has_identifier is True, "repr should contain the identifier"
    assert has_name is True, "repr should contain the name"
    assert has_version is True, "repr should contain the version"
    return


def test_str_contains_name_and_version():
    """
        Verify that __str__ returns a human-readable summary with name and version.
    """
    identity = AgentIdentity(
        name="my-agent",
        version="2.5.1"
    )

    str_val = str(identity)

    has_name = "my-agent" in str_val
    has_version = "2.5.1" in str_val

    assert has_name is True, "str should contain the name"
    assert has_version is True, "str should contain the version"
    return


def test_empty_tags_dictionary():
    """
        Verify that an AgentIdentity with empty tags returns an empty dict.
    """
    identity = AgentIdentity(
        name="agent",
        version="1.0",
        tags={}
    )

    tags = identity.tags
    tag_count = len(tags)

    assert tag_count == 0, "Empty tags should produce an empty dictionary"
    assert tags == {}, "Tags should be an empty dict"
    return


def test_explicit_identifier_is_preserved():
    """
        Verify that an explicit identifier is preserved and not overwritten.
    """
    explicit_id = "my-custom-identifier-12345"

    identity = AgentIdentity(
        name="agent",
        version="1.0",
        identifier=explicit_id
    )

    actual_id = identity.identifier
    assert actual_id == explicit_id, (
        "Explicit identifier should be preserved, got: {!r}".format(actual_id)
    )
    return


def test_tags_returns_defensive_copy():
    """
        Verify that modifying the returned tags dict does not affect the identity.
    """
    identity = AgentIdentity(
        name="agent",
        version="1.0",
        tags={"env": "prod"}
    )

    tags_copy = identity.tags
    tags_copy["injected"] = "value"

    original_tags = identity.tags
    has_injected = "injected" in original_tags

    assert has_injected is False, (
        "Modifying returned tags should not affect the identity's internal tags"
    )
    return


def test_constructor_tags_defensive_copy():
    """
        Verify that modifying the original tags dict after construction
        does not affect the identity.
    """
    original_tags = {"env": "dev"}

    identity = AgentIdentity(
        name="agent",
        version="1.0",
        tags=original_tags
    )

    original_tags["injected"] = "value"

    identity_tags = identity.tags
    has_injected = "injected" in identity_tags

    assert has_injected is False, (
        "Modifying original tags dict should not affect the identity"
    )
    return


def test_none_tags_defaults_to_empty_dict():
    """
        Verify that passing None for tags results in an empty dictionary.
    """
    identity = AgentIdentity(
        name="agent",
        version="1.0",
        tags=None
    )

    tags = identity.tags
    assert tags == {}, "None tags should default to empty dict"
    return


def test_as_dict_returns_independent_copy():
    """
        Verify that modifying the as_dict result does not affect the identity.
    """
    identity = AgentIdentity(
        name="agent",
        version="1.0",
        tags={"key": "value"}
    )

    d = identity.as_dict()
    d["name"] = "modified"
    d["tags"]["injected"] = "bad"

    assert identity.name == "agent", "Modifying as_dict result should not affect name"

    identity_tags = identity.tags
    has_injected = "injected" in identity_tags
    assert has_injected is False, "Modifying as_dict tags should not affect identity tags"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
