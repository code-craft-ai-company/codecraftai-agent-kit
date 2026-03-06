"""
    Property-based tests for the automojo.agentkit.featureflag module.

    Uses the hypothesis library to verify that FeatureFlag instances
    survive a JSON round-trip (to_json followed by from_json) with all
    fields preserved.

    **Validates: Requirement 11 AC 7**
"""

from hypothesis import given, settings
from hypothesis.strategies import (
    booleans,
    dictionaries,
    none,
    one_of,
    text,
)

from automojo.agentkit.featureflag import FeatureFlag


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_description_strategy = one_of(
    none(),
    text(min_size=0, max_size=100),
)

_metadata_value_strategy = one_of(
    text(min_size=0, max_size=50),
    booleans(),
)

_metadata_strategy = one_of(
    none(),
    dictionaries(
        keys=text(min_size=1, max_size=30),
        values=_metadata_value_strategy,
        max_size=5,
    ),
)


# ---------------------------------------------------------------------------
# Property 6: FeatureFlag JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    name=text(min_size=1, max_size=50),
    default_value=booleans(),
    description=_description_strategy,
    metadata=_metadata_strategy,
)
@settings(max_examples=200)
def test_featureflag_json_round_trip(name, default_value, description, metadata):
    """
        **Validates: Requirement 11 AC 7**

        FOR ALL valid FeatureFlag instances, calling to_json and then from_json
        SHALL produce an equivalent FeatureFlag object with the same name,
        default_value, description, and metadata.
    """
    original = FeatureFlag(
        name=name,
        default_value=default_value,
        description=description,
        metadata=metadata,
    )

    json_str = original.to_json()
    reconstructed = FeatureFlag.from_json(json_str)

    reconstructed_name = reconstructed.name
    assert reconstructed_name == name, (
        "Round-trip name mismatch: expected {!r}, got {!r}".format(
            name, reconstructed_name)
    )

    reconstructed_default_value = reconstructed.default_value
    assert reconstructed_default_value == default_value, (
        "Round-trip default_value mismatch: expected {!r}, got {!r}".format(
            default_value, reconstructed_default_value)
    )

    reconstructed_description = reconstructed.description
    assert reconstructed_description == description, (
        "Round-trip description mismatch: expected {!r}, got {!r}".format(
            description, reconstructed_description)
    )

    expected_metadata = metadata if metadata is not None else {}
    reconstructed_metadata = reconstructed.metadata
    assert reconstructed_metadata == expected_metadata, (
        "Round-trip metadata mismatch: expected {!r}, got {!r}".format(
            expected_metadata, reconstructed_metadata)
    )

    return
