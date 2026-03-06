"""
    Property-based tests for the automojo.agentkit.toolregistry module.

    Contains property-based tests (using automojo.testbase.properties) for the ToolRegistry class,
    validating registration, lookup, enumeration, deregistration, and tag-based
    lookup correctness.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given, settings, assume
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite
from automojo.agentkit.tool import Tool
from automojo.agentkit.toolregistry import ToolRegistry
from automojo.agentkit.tooldescriptor import ToolDescriptor
from automojo.agentkit.errors import SemanticError


# ---------------------------------------------------------------------------
# testbase property strategies for generating ToolRegistry-related inputs
# ---------------------------------------------------------------------------

# Strategy for generating valid tool names (non-empty alphanumeric strings)
tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating tag keys
tag_key_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=15
)

# Strategy for generating tag values
tag_value_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=15
)

# Strategy for generating tag dictionaries (string -> string)
tags_strategy = st.dictionaries(
    keys=tag_key_strategy,
    values=tag_value_strategy,
    max_size=5
)


def _make_tool_class(name, tags=None):
    """
        Creates a concrete Tool subclass with the given name and optional tags.

        :param name: The TOOL_NAME value.
        :param tags: An optional dictionary of tags.

        :returns: A concrete Tool instance.
    """

    class DynamicTool(Tool):
        """
            A dynamically created Tool subclass for testing purposes.
        """

        TOOL_NAME = name
        TOOL_DESCRIPTION = "Test tool: {}".format(name)
        TOOL_VERSION = "1.0.0"

        def execute(self, inputs: dict, credentials: dict = None) -> dict:
            """
                A no-op execute implementation for testing.

                :param inputs: Validated input dictionary.
                :param credentials: Optional dictionary of resolved credentials.

                :returns: An empty dictionary.
            """
            rtnval = {}
            return rtnval

    tool = DynamicTool(tags=tags)
    return tool


@composite
def unique_tool_names_strategy(draw, min_size=1, max_size=10):
    """
        Generates a list of unique tool name strings.

        :param min_size: Minimum number of names.
        :param max_size: Maximum number of names.

        :returns: A list of unique non-empty strings.
    """
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    names = []
    used_names = set()

    for _ in range(count):
        name = draw(tool_name_strategy)

        while name in used_names:
            name = draw(tool_name_strategy)

        used_names.add(name)
        names.append(name)

    return names


# ---------------------------------------------------------------------------
# Property 9: ToolRegistry registration, lookup, and enumeration correctness
# Feature: tool-capability-system, Property 9: ToolRegistry registration, lookup, and enumeration correctness
# **Validates: Requirements 4.1, 4.2, 4.4, 4.6, 4.7, 4.8, 4.9**
# ---------------------------------------------------------------------------

@given(
    names=unique_tool_names_strategy(min_size=1, max_size=8),
    unregistered_name=tool_name_strategy,
    settings=settings(max_examples=100)
)
def test_property_9_registration_lookup_and_enumeration_correctness(names, unregistered_name):
    """
        Property 9: ToolRegistry registration, lookup, and enumeration correctness.

        For any set of N Tools with unique names: (a) after registration, count
        equals N, (b) lookup(name) returns the correct Tool or None for
        unregistered names, (c) has_tool(name) returns True for registered names
        and False otherwise, (d) list_all() returns all N Tools, (e)
        list_descriptors() returns N ToolDescriptors, (f) registering a duplicate
        name raises SemanticError.

        **Validates: Requirements 4.1, 4.2, 4.4, 4.6, 4.7, 4.8, 4.9**
    """
    n = len(names)

    # Ensure unregistered_name is not in the names list
    assume(unregistered_name not in names)

    # Create tools and register them
    registry = ToolRegistry()
    tools = []

    for name in names:
        tool = _make_tool_class(name=name)
        tools.append(tool)
        registry.register(tool=tool)

    # (a) count equals N
    assert registry.count == n, (
        "Expected count {}, got {}".format(n, registry.count)
    )

    # (b) lookup(name) returns the correct Tool for registered names
    for idx in range(n):
        expected_tool = tools[idx]
        looked_up = registry.lookup(tool_name=names[idx])
        assert looked_up is expected_tool, (
            "lookup('{}') should return the registered tool instance".format(names[idx])
        )

    # (b) lookup returns None for an unregistered name
    lookup_result = registry.lookup(tool_name=unregistered_name)
    assert lookup_result is None, (
        "lookup('{}') should return None for unregistered name, got {!r}".format(
            unregistered_name, lookup_result
        )
    )

    # (c) has_tool returns True for registered names
    for name in names:
        result = registry.has_tool(tool_name=name)
        assert result is True, (
            "has_tool('{}') should return True for registered name".format(name)
        )

    # (c) has_tool returns False for unregistered name
    has_unregistered = registry.has_tool(tool_name=unregistered_name)
    assert has_unregistered is False, (
        "has_tool('{}') should return False for unregistered name".format(
            unregistered_name
        )
    )

    # (d) list_all() returns all N Tools
    all_tools = registry.list_all()
    assert len(all_tools) == n, (
        "list_all() should return {} tools, got {}".format(n, len(all_tools))
    )
    for tool in tools:
        is_present = tool in all_tools
        assert is_present is True, (
            "list_all() should contain tool '{}'".format(tool.name)
        )

    # (e) list_descriptors() returns N ToolDescriptors
    descriptors = registry.list_descriptors()
    assert len(descriptors) == n, (
        "list_descriptors() should return {} descriptors, got {}".format(
            n, len(descriptors)
        )
    )
    for desc in descriptors:
        assert isinstance(desc, ToolDescriptor), (
            "Each item from list_descriptors() should be a ToolDescriptor, got {}".format(
                type(desc).__name__
            )
        )

    descriptor_names = [d.name for d in descriptors]
    for name in names:
        is_in_descriptors = name in descriptor_names
        assert is_in_descriptors is True, (
            "list_descriptors() should include a descriptor for tool '{}'".format(name)
        )

    # (f) registering a duplicate name raises SemanticError
    duplicate_tool = _make_tool_class(name=names[0])
    raised = False
    try:
        registry.register(tool=duplicate_tool)
    except SemanticError:
        raised = True

    assert raised is True, (
        "Registering a duplicate tool name '{}' should raise SemanticError".format(
            names[0]
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 10: ToolRegistry deregistration removes tool
# Feature: tool-capability-system, Property 10: ToolRegistry deregistration removes tool
# **Validates: Requirements 4.3**
# ---------------------------------------------------------------------------

@composite
def _deregister_data(draw):
    """
        Generates a list of unique tool names and a target index for deregistration.

        :returns: A tuple of (names, target_index).
    """
    names = draw(unique_tool_names_strategy(min_size=2, max_size=8))
    target_index = draw(st.integers(min_value=0, max_value=len(names) - 1))
    return (names, target_index)


@given(
    test_data=_deregister_data(),
    settings=settings(max_examples=100)
)
def test_property_10_deregistration_removes_tool(test_data):
    """
        Property 10: ToolRegistry deregistration removes tool.

        For any registered Tool, calling deregister(name) shall remove it so
        that lookup(name) returns None, has_tool(name) returns False, and count
        decreases by one.

        **Validates: Requirements 4.3**
    """
    names, target_index = test_data
    n = len(names)

    # Register all tools
    registry = ToolRegistry()
    tools = {}

    for name in names:
        tool = _make_tool_class(name=name)
        tools[name] = tool
        registry.register(tool=tool)

    # Pick a random tool to deregister
    target_name = names[target_index]

    count_before = registry.count
    registry.deregister(tool_name=target_name)

    # count decreases by one
    count_after = registry.count
    assert count_after == count_before - 1, (
        "Count should decrease by one after deregister: expected {}, got {}".format(
            count_before - 1, count_after
        )
    )

    # lookup returns None for deregistered tool
    lookup_result = registry.lookup(tool_name=target_name)
    assert lookup_result is None, (
        "lookup('{}') should return None after deregister, got {!r}".format(
            target_name, lookup_result
        )
    )

    # has_tool returns False for deregistered tool
    has_result = registry.has_tool(tool_name=target_name)
    assert has_result is False, (
        "has_tool('{}') should return False after deregister".format(target_name)
    )

    # Remaining tools are still accessible
    for name in names:
        if name == target_name:
            continue

        remaining_tool = registry.lookup(tool_name=name)
        assert remaining_tool is tools[name], (
            "Tool '{}' should still be accessible after deregistering '{}'".format(
                name, target_name
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 11: ToolRegistry lookup by tags returns matching tools
# Feature: tool-capability-system, Property 11: ToolRegistry lookup by tags returns matching tools
# **Validates: Requirements 4.5**
# ---------------------------------------------------------------------------

@composite
def _tag_lookup_data(draw):
    """
        Generates test data for tag-based lookup: a list of unique tool names,
        a tag dictionary, a source index, and a subset size for search criteria.

        :returns: A tuple of (names, tool_tags, source_index, subset_size).
    """
    names = draw(unique_tool_names_strategy(min_size=2, max_size=8))
    tool_tags = draw(tags_strategy)
    source_index = draw(st.integers(min_value=0, max_value=len(names) - 1))

    tag_keys = sorted(tool_tags.keys())
    if len(tag_keys) > 0:
        subset_size = draw(st.integers(min_value=1, max_value=len(tag_keys)))
    else:
        subset_size = 0

    return (names, tool_tags, source_index, subset_size)


@given(
    test_data=_tag_lookup_data(),
    settings=settings(max_examples=100)
)
def test_property_11_lookup_by_tags_returns_matching_tools(test_data):
    """
        Property 11: ToolRegistry lookup by tags returns matching tools.

        For any set of registered Tools with various tag dictionaries,
        lookup_by_tags(**criteria) shall return exactly those Tools whose
        tags contain all the specified key-value pairs.

        **Validates: Requirements 4.5**
    """
    names, tool_tags, source_index, subset_size = test_data
    n = len(names)

    # Generate a tag dictionary for each tool
    tag_dicts = []
    for _ in range(n):
        tag_dicts.append(tool_tags)

    # Register all tools with their tags
    registry = ToolRegistry()
    tools = []

    for idx in range(n):
        tool = _make_tool_class(name=names[idx], tags=tag_dicts[idx])
        tools.append(tool)
        registry.register(tool=tool)

    # Generate search criteria: pick a subset of tag key-value pairs
    # from one of the tools to use as search criteria
    source_tags = tag_dicts[source_index]

    if len(source_tags) > 0:
        # Pick a non-empty subset of the source tool's tags as criteria
        tag_keys = sorted(source_tags.keys())
        selected_keys = tag_keys[:subset_size]
        criteria = {}
        for key in selected_keys:
            criteria[key] = source_tags[key]
    else:
        # Empty criteria should match all tools
        criteria = {}

    # Perform the lookup
    results = registry.lookup_by_tags(**criteria)

    # Compute expected matches: tools whose tags contain ALL criteria key-value pairs
    expected_tools = []
    for idx in range(n):
        tool_tags = tag_dicts[idx]
        all_match = True

        for crit_key, crit_value in criteria.items():
            has_key = crit_key in tool_tags

            if has_key is not True:
                all_match = False
                break

            tag_value = tool_tags[crit_key]
            values_match = tag_value == crit_value

            if values_match is not True:
                all_match = False
                break

        if all_match is True:
            expected_tools.append(tools[idx])

    # Verify the result set matches the expected set
    assert len(results) == len(expected_tools), (
        "lookup_by_tags returned {} tools, expected {} for criteria {!r}".format(
            len(results), len(expected_tools), criteria
        )
    )

    result_names = sorted([t.name for t in results])
    expected_names = sorted([t.name for t in expected_tools])
    assert result_names == expected_names, (
        "lookup_by_tags returned tools {!r}, expected {!r} for criteria {!r}".format(
            result_names, expected_names, criteria
        )
    )

    # Verify each returned tool actually matches all criteria
    for tool in results:
        tool_tags = tool.tags
        for crit_key, crit_value in criteria.items():
            has_key = crit_key in tool_tags
            assert has_key is True, (
                "Returned tool '{}' missing tag key '{}'".format(tool.name, crit_key)
            )
            assert tool_tags[crit_key] == crit_value, (
                "Returned tool '{}' tag '{}' has value '{}', expected '{}'".format(
                    tool.name, crit_key, tool_tags[crit_key], crit_value
                )
            )

    return


# ---------------------------------------------------------------------------
# Unit tests for ToolRegistry
# Feature: tool-capability-system, Task 5.3
# **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 18.11, 18.12**
# ---------------------------------------------------------------------------


def test_empty_registry_count_is_zero():
    """
        Verifies that a newly created ToolRegistry has a count of zero.

        **Validates: Requirements 4.8**
    """
    registry = ToolRegistry()

    result = registry.count

    assert result == 0, (
        "Expected empty registry count to be 0, got {}".format(result)
    )

    return


def test_deregister_nonexistent_tool_is_noop():
    """
        Verifies that calling deregister with a name not present in the
        registry does not raise an exception and leaves the registry unchanged.

        **Validates: Requirements 4.3**
    """
    registry = ToolRegistry()
    tool = _make_tool_class(name="existing_tool")
    registry.register(tool=tool)

    count_before = registry.count

    registry.deregister(tool_name="nonexistent_tool")

    count_after = registry.count
    assert count_after == count_before, (
        "Deregistering a nonexistent tool should not change count: expected {}, got {}".format(
            count_before, count_after
        )
    )

    looked_up = registry.lookup(tool_name="existing_tool")
    assert looked_up is tool, (
        "Existing tool should still be accessible after deregistering a nonexistent name"
    )

    return


def test_lookup_by_tags_no_matches():
    """
        Verifies that lookup_by_tags returns an empty list when no registered
        tools match the provided tag criteria.

        **Validates: Requirements 4.5**
    """
    registry = ToolRegistry()
    tool_a = _make_tool_class(name="tool_a", tags={"env": "prod"})
    tool_b = _make_tool_class(name="tool_b", tags={"env": "staging"})
    registry.register(tool=tool_a)
    registry.register(tool=tool_b)

    results = registry.lookup_by_tags(env="dev")

    assert len(results) == 0, (
        "Expected no matches for tag criteria env=dev, got {} results".format(
            len(results)
        )
    )

    return


def test_repr_format():
    """
        Verifies that __repr__ contains 'ToolRegistry' and the current count.

        **Validates: Requirements 18.11**
    """
    registry = ToolRegistry()
    tool = _make_tool_class(name="alpha")
    registry.register(tool=tool)

    repr_str = repr(registry)

    has_class_name = "ToolRegistry" in repr_str
    assert has_class_name is True, (
        "repr should contain 'ToolRegistry', got: {}".format(repr_str)
    )

    has_count = "1" in repr_str
    assert has_count is True, (
        "repr should contain the count '1', got: {}".format(repr_str)
    )

    return


def test_str_format():
    """
        Verifies that __str__ contains 'ToolRegistry' and the registered tool names.

        **Validates: Requirements 18.12**
    """
    registry = ToolRegistry()
    tool_a = _make_tool_class(name="alpha")
    tool_b = _make_tool_class(name="beta")
    registry.register(tool=tool_a)
    registry.register(tool=tool_b)

    str_result = str(registry)

    has_class_name = "ToolRegistry" in str_result
    assert has_class_name is True, (
        "str should contain 'ToolRegistry', got: {}".format(str_result)
    )

    has_alpha = "alpha" in str_result
    assert has_alpha is True, (
        "str should contain tool name 'alpha', got: {}".format(str_result)
    )

    has_beta = "beta" in str_result
    assert has_beta is True, (
        "str should contain tool name 'beta', got: {}".format(str_result)
    )

    return


def test_clear_removes_all_tools():
    """
        Verifies that after calling clear(), the registry count is 0 and
        list_all() returns an empty list.

        **Validates: Requirements 4.1, 4.6, 4.8**
    """
    registry = ToolRegistry()
    tool_a = _make_tool_class(name="tool_x")
    tool_b = _make_tool_class(name="tool_y")
    registry.register(tool=tool_a)
    registry.register(tool=tool_b)

    registry.clear()

    count_result = registry.count
    assert count_result == 0, (
        "Expected count 0 after clear(), got {}".format(count_result)
    )

    all_tools = registry.list_all()
    assert len(all_tools) == 0, (
        "Expected list_all() to return empty list after clear(), got {} items".format(
            len(all_tools)
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
