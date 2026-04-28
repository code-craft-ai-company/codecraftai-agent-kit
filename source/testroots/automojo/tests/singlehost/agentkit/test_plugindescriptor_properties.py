"""
    Property-based tests for the automojo.agentkit.plugindescriptor module.

    Uses the automojo.testbase.properties engine to verify that PluginDescriptor instances
    survive a JSON round-trip (to_json followed by from_json) with all
    fields preserved.

    **Validates: Requirement 15 AC 7**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.plugindependency import PluginDependency
from automojo.agentkit.plugindescriptor import PluginDescriptor
from automojo.agentkit.pluginstatus import PluginStatus


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_status_strategy = st.sampled_from([
    PluginStatus.DISCOVERED,
    PluginStatus.LOADING,
    PluginStatus.LOADED,
    PluginStatus.ACTIVE,
    PluginStatus.FAILED,
    PluginStatus.DISABLED,
])

_version_constraint_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=20),
)

_extension_points_strategy = st.lists(
    st.text(min_size=1, max_size=30),
    min_size=0,
    max_size=5,
)


# ---------------------------------------------------------------------------
# Helper to build PluginDependency objects from generated data
# ---------------------------------------------------------------------------

def _build_dependency(dep_name, dep_version_constraint):
    """
        Builds a PluginDependency from generated name and version constraint.

        :param dep_name: The dependency name string.
        :param dep_version_constraint: The optional version constraint string.

        :returns: A PluginDependency instance.
    """
    dep = PluginDependency(
        name=dep_name,
        version_constraint=dep_version_constraint,
    )
    return dep


# ---------------------------------------------------------------------------
# Property 7: PluginDescriptor JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    name=st.text(min_size=1, max_size=50),
    version=st.text(min_size=1, max_size=20),
    description=st.text(min_size=0, max_size=100),
    author=st.text(min_size=1, max_size=50),
    extension_points=_extension_points_strategy,
    dep_names=st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=3),
    dep_constraints=st.lists(_version_constraint_strategy, min_size=0, max_size=3),
    status=_status_strategy,
    constraints={"max_examples": 50},
)
def test_plugindescriptor_json_round_trip(name, version, description, author,
                                          extension_points, dep_names,
                                          dep_constraints, status):
    """
        **Validates: Requirement 15 AC 7**

        FOR ALL valid PluginDescriptor instances, calling to_json and then
        from_json SHALL produce an equivalent PluginDescriptor object with
        the same name, version, description, author, extension points,
        dependencies, and status.
    """
    # Build dependencies from the shorter of the two generated lists
    dep_count = min(len(dep_names), len(dep_constraints))
    dependencies = []
    for idx in range(dep_count):
        dep = _build_dependency(dep_names[idx], dep_constraints[idx])
        dependencies.append(dep)

    original = PluginDescriptor(
        name=name,
        version=version,
        description=description,
        author=author,
        extension_points=extension_points,
        dependencies=dependencies,
        status=status,
    )

    json_str = original.to_json()
    reconstructed = PluginDescriptor.from_json(json_str)

    assert reconstructed.name == name, (
        "Round-trip name mismatch: expected {!r}, got {!r}".format(
            name, reconstructed.name)
    )

    assert reconstructed.version == version, (
        "Round-trip version mismatch: expected {!r}, got {!r}".format(
            version, reconstructed.version)
    )

    assert reconstructed.description == description, (
        "Round-trip description mismatch: expected {!r}, got {!r}".format(
            description, reconstructed.description)
    )

    assert reconstructed.author == author, (
        "Round-trip author mismatch: expected {!r}, got {!r}".format(
            author, reconstructed.author)
    )

    assert reconstructed.extension_points == extension_points, (
        "Round-trip extension_points mismatch: expected {!r}, got {!r}".format(
            extension_points, reconstructed.extension_points)
    )

    assert reconstructed.status == status, (
        "Round-trip status mismatch: expected {!r}, got {!r}".format(
            status, reconstructed.status)
    )

    reconstructed_deps = reconstructed.dependencies
    assert len(reconstructed_deps) == dep_count, (
        "Round-trip dependencies count mismatch: expected {}, got {}".format(
            dep_count, len(reconstructed_deps))
    )

    for idx in range(dep_count):
        original_dep = dependencies[idx]
        reconstructed_dep = reconstructed_deps[idx]

        assert reconstructed_dep.name == original_dep.name, (
            "Round-trip dependency[{}] name mismatch: expected {!r}, got {!r}".format(
                idx, original_dep.name, reconstructed_dep.name)
        )

        assert reconstructed_dep.version_constraint == original_dep.version_constraint, (
            "Round-trip dependency[{}] version_constraint mismatch: expected {!r}, got {!r}".format(
                idx, original_dep.version_constraint, reconstructed_dep.version_constraint)
        )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
