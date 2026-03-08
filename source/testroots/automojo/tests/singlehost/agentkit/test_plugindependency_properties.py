"""
    Property-based tests for the automojo.agentkit.plugindependency module.

    Uses the automojo.testbase.properties engine to verify that PluginDependency instances
    survive a JSON round-trip (to_json followed by from_dict on the parsed
    JSON) with all fields preserved.

    **Validates: Requirement 17 AC 8**
"""

import json

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.plugindependency import PluginDependency


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_version_constraint_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=30),
)


# ---------------------------------------------------------------------------
# Property 8: PluginDependency JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    name=st.text(min_size=1, max_size=50),
    version_constraint=_version_constraint_strategy,
    settings=settings(max_examples=50),
)
def test_plugindependency_json_round_trip(name, version_constraint):
    """
        **Validates: Requirement 17 AC 8**

        FOR ALL valid PluginDependency instances, calling to_json and then
        from_dict on the parsed JSON SHALL produce a PluginDependency with
        equivalent dependency name and version constraint values.
    """
    original = PluginDependency(
        name=name,
        version_constraint=version_constraint,
    )

    json_str = original.to_json()
    parsed_data = json.loads(json_str)
    reconstructed = PluginDependency.from_dict(parsed_data)

    reconstructed_name = reconstructed.name
    assert reconstructed_name == name, (
        "Round-trip name mismatch: expected {!r}, got {!r}".format(
            name, reconstructed_name)
    )

    reconstructed_version_constraint = reconstructed.version_constraint
    assert reconstructed_version_constraint == version_constraint, (
        "Round-trip version_constraint mismatch: expected {!r}, got {!r}".format(
            version_constraint, reconstructed_version_constraint)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
