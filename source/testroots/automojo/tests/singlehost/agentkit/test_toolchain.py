"""
    Property-based tests for the automojo.agentkit.toolchain module.

    Contains property-based tests (using automojo.testbase.properties) for the ToolChain class,
    validating tool existence checking at construction, schema compatibility
    validation, and correct exposure of tool names and step count.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.tool import Tool
from automojo.agentkit.toolchain import ToolChain
from automojo.agentkit.toolerrors import ToolValidationError
from automojo.agentkit.toolregistry import ToolRegistry
from automojo.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# Helper: dynamic Tool subclass factory
# ---------------------------------------------------------------------------

def _make_tool_class(name, input_schema_dict=None, output_schema_dict=None):
    """
        Creates a concrete Tool subclass with the given class-level constants.

        :param name: The TOOL_NAME value.
        :param input_schema_dict: The INPUT_SCHEMA dictionary or None.
        :param output_schema_dict: The OUTPUT_SCHEMA dictionary or None.

        :returns: A concrete Tool subclass type.
    """

    class DynamicTool(Tool):
        """
            A concrete Tool subclass for testing ToolChain.
        """

        TOOL_NAME = name
        TOOL_DESCRIPTION = "Dynamic test tool: {}".format(name)
        TOOL_VERSION = "1.0.0"
        INPUT_SCHEMA = input_schema_dict
        OUTPUT_SCHEMA = output_schema_dict

        def execute(self, inputs: dict, credentials: dict = None) -> dict:
            """
                No-op execute for testing.

                :param inputs: Validated input dictionary.
                :param credentials: Optional dictionary of resolved credentials.

                :returns: An empty dictionary.
            """
            rtnval = {}
            return rtnval

    return DynamicTool


# ---------------------------------------------------------------------------
# testbase property strategies
# ---------------------------------------------------------------------------

# Strategy for generating valid tool names (non-empty alphanumeric strings)
tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating a supported type string
supported_type_strategy = st.sampled_from(sorted(ToolSchema.SUPPORTED_TYPES))


@composite
def unique_tool_names_strategy(draw, min_count=2, max_count=5):
    """
        Generates a list of unique tool name strings.

        :param min_count: Minimum number of names.
        :param max_count: Maximum number of names.

        :returns: A list of unique tool name strings.
    """
    count = draw(st.integers(min_value=min_count, max_value=max_count))
    names = []
    used = set()

    for _ in range(count):
        name = draw(tool_name_strategy)
        while name in used:
            name = draw(tool_name_strategy)
        used.add(name)
        names.append(name)

    rtnval = names
    return rtnval


@composite
def missing_tool_name_strategy(draw, existing_names):
    """
        Generates a tool name that is NOT in the existing_names set.

        :param existing_names: A set of existing tool names to avoid.

        :returns: A tool name string not in existing_names.
    """
    name = draw(tool_name_strategy)
    while name in existing_names:
        name = draw(tool_name_strategy)

    rtnval = name
    return rtnval


# ---------------------------------------------------------------------------
# Property 17: ToolChain validates tool existence at construction
# Feature: tool-capability-system, Property 17: ToolChain validates tool existence at construction
# **Validates: Requirements 7.2, 7.3**
# ---------------------------------------------------------------------------

@composite
def _property_17_data(draw):
    """
        Generates test data for property 17: registered names, a missing name,
        an insert position, and a chain name.

        :returns: A tuple of (registered_names, missing_name, insert_pos, chain_name).
    """
    registered_names = draw(unique_tool_names_strategy(min_count=1, max_count=3))
    existing_set = set(registered_names)
    name = draw(tool_name_strategy)
    while name in existing_set:
        name = draw(tool_name_strategy)
    missing_name = name
    insert_pos = draw(st.integers(min_value=0, max_value=len(registered_names)))
    chain_name = draw(tool_name_strategy)
    return (registered_names, missing_name, insert_pos, chain_name)


@given(
    test_data=_property_17_data(),
    constraints={"max_examples": 100}
)
def test_property_17_toolchain_validates_tool_existence_at_construction(test_data):
    """
        Property 17: ToolChain validates tool existence at construction.

        For any list of step definitions referencing a tool name not present
        in the provided ToolRegistry, ToolChain construction shall raise
        SemanticError identifying the missing tool name.

        **Validates: Requirements 7.2, 7.3**
    """
    registered_names, missing_name, insert_pos, chain_name = test_data

    # Create a registry with those tools
    registry = ToolRegistry()
    for name in registered_names:
        tool_cls = _make_tool_class(name=name)
        tool = tool_cls()
        registry.register(tool=tool)

    # Build steps that include the missing tool name
    # Place the missing name at a random position among valid names
    valid_steps = [{"tool_name": n} for n in registered_names]
    steps = list(valid_steps)
    steps.insert(insert_pos, {"tool_name": missing_name})


    raised = False
    caught_error = None
    try:
        ToolChain(name=chain_name, steps=steps, registry=registry)
    except SemanticError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "ToolChain should raise SemanticError for missing tool '{}', "
        "registered: {}".format(missing_name, registered_names)
    )

    assert missing_name in caught_error.message, (
        "SemanticError message should contain the missing tool name '{}', "
        "got: {!r}".format(missing_name, caught_error.message)
    )

    return


# ---------------------------------------------------------------------------
# Property 18: ToolChain validates schema compatibility at construction
# Feature: tool-capability-system, Property 18: ToolChain validates schema compatibility at construction
# **Validates: Requirements 7.4, 7.5**
# ---------------------------------------------------------------------------

_all_schema_types = sorted(ToolSchema.SUPPORTED_TYPES)


@composite
def _property_18_data(draw):
    """
        Generates test data for property 18: source type, target type (different),
        field name, tool A name, and tool B name.

        :returns: A tuple of (source_type, target_type, field_name, tool_a_name, tool_b_name).
    """
    source_type = draw(st.sampled_from(_all_schema_types))
    target_type = draw(st.sampled_from(_all_schema_types).filter(lambda t: t != source_type))
    field_name = draw(st.text(
        alphabet=st.characters(categories=("L",)),
        min_size=1,
        max_size=15
    ).filter(lambda s: len(s.strip()) > 0))
    tool_a_suffix = draw(st.text(
        alphabet=st.characters(categories=("L",)),
        min_size=1,
        max_size=8
    ).filter(lambda s: len(s.strip()) > 0))
    tool_b_suffix = draw(st.text(
        alphabet=st.characters(categories=("L",)),
        min_size=1,
        max_size=8
    ).filter(lambda s: len(s.strip()) > 0))
    tool_a_name = "tool_a_" + tool_a_suffix
    tool_b_name = "tool_b_" + tool_b_suffix
    while tool_b_name == tool_a_name:
        tool_b_name = tool_b_name + "x"
    return (source_type, target_type, field_name, tool_a_name, tool_b_name)


@given(
    test_data=_property_18_data(),
    constraints={"max_examples": 100}
)
def test_property_18_toolchain_validates_schema_compatibility_at_construction(test_data):
    """
        Property 18: ToolChain validates schema compatibility at construction.

        For any ToolChain where the output schema of step N is incompatible
        with the input schema of step N+1 according to the provided mappings,
        construction shall raise ToolValidationError identifying the
        incompatible step pair and the specific field mismatch.

        **Validates: Requirements 7.4, 7.5**
    """
    source_type, target_type, field_name, tool_a_name, tool_b_name = test_data

    tool_a_output_schema = {
        "parameters": [
            {"name": field_name, "type": source_type, "required": True}
        ]
    }

    tool_b_input_schema = {
        "parameters": [
            {"name": field_name, "type": target_type, "required": True}
        ]
    }

    # Create tools and registry
    tool_a_cls = _make_tool_class(
        name=tool_a_name,
        output_schema_dict=tool_a_output_schema,
    )
    tool_b_cls = _make_tool_class(
        name=tool_b_name,
        input_schema_dict=tool_b_input_schema,
    )

    registry = ToolRegistry()
    registry.register(tool=tool_a_cls())
    registry.register(tool=tool_b_cls())

    # Build steps with a mapping that creates the type mismatch
    steps = [
        {"tool_name": tool_a_name},
        {"tool_name": tool_b_name, "mappings": {field_name: field_name}},
    ]

    raised = False
    caught_error = None
    try:
        ToolChain(name="mismatch_chain", steps=steps, registry=registry)
    except ToolValidationError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "ToolChain should raise ToolValidationError for incompatible schemas: "
        "output type '{}' vs input type '{}'".format(source_type, target_type)
    )

    # Verify the error identifies the field mismatch
    has_field_reference = False
    for error_str in caught_error.errors:
        if field_name in error_str:
            has_field_reference = True
            break

    assert has_field_reference is True, (
        "ToolValidationError errors should reference the mismatched field '{}', "
        "got errors: {!r}".format(field_name, caught_error.errors)
    )

    return


# ---------------------------------------------------------------------------
# Property 21: ToolChain exposes correct tool names and step count
# Feature: tool-capability-system, Property 21: ToolChain exposes correct tool names and step count
# **Validates: Requirements 7.10, 7.11**
# ---------------------------------------------------------------------------

@given(
    tool_names_list=unique_tool_names_strategy(min_count=1, max_count=5),
    chain_name=tool_name_strategy,
    constraints={"max_examples": 100}
)
def test_property_21_toolchain_exposes_correct_tool_names_and_step_count(tool_names_list, chain_name):
    """
        Property 21: ToolChain exposes correct tool names and step count.

        For any valid ToolChain with N steps, tool_names shall return the
        ordered list of tool names and step_count shall equal N.

        **Validates: Requirements 7.10, 7.11**
    """
    # Generate unique tool names

    # Create a registry with those tools
    registry = ToolRegistry()
    for name in tool_names_list:
        tool_cls = _make_tool_class(name=name)
        tool = tool_cls()
        registry.register(tool=tool)

    # Build steps referencing the tools (no mappings needed for this property)
    steps = [{"tool_name": name} for name in tool_names_list]

    chain = ToolChain(name=chain_name, steps=steps, registry=registry)

    # Verify tool_names returns the ordered list
    actual_names = chain.tool_names
    assert actual_names == tool_names_list, (
        "tool_names should return {!r}, got: {!r}".format(
            tool_names_list, actual_names
        )
    )

    # Verify step_count equals N
    expected_count = len(tool_names_list)
    actual_count = chain.step_count
    assert actual_count == expected_count, (
        "step_count should be {}, got: {}".format(expected_count, actual_count)
    )

    return


# ---------------------------------------------------------------------------
# Unit tests for ToolChain
# ---------------------------------------------------------------------------

def test_single_step_chain():
    """
        Verifies that a ToolChain with a single step exposes the correct
        tool_names list and step_count of 1.

        **Validates: Requirements 7.1, 7.10, 7.11**
    """
    registry = ToolRegistry()
    tool_cls = _make_tool_class(name="only_tool")
    registry.register(tool=tool_cls())

    steps = [{"tool_name": "only_tool"}]
    chain = ToolChain(name="single_step_chain", steps=steps, registry=registry)

    actual_names = chain.tool_names
    assert actual_names == ["only_tool"], (
        "tool_names should be ['only_tool'], got: {!r}".format(actual_names)
    )

    actual_count = chain.step_count
    assert actual_count == 1, (
        "step_count should be 1, got: {}".format(actual_count)
    )

    return


def test_chain_without_mappings():
    """
        Verifies that a multi-step ToolChain with no mappings between steps
        constructs successfully and exposes the correct tool_names and step_count.

        **Validates: Requirements 7.1, 7.10, 7.11**
    """
    registry = ToolRegistry()

    tool_a_cls = _make_tool_class(name="tool_alpha")
    tool_b_cls = _make_tool_class(name="tool_beta")
    tool_c_cls = _make_tool_class(name="tool_gamma")

    registry.register(tool=tool_a_cls())
    registry.register(tool=tool_b_cls())
    registry.register(tool=tool_c_cls())

    steps = [
        {"tool_name": "tool_alpha"},
        {"tool_name": "tool_beta"},
        {"tool_name": "tool_gamma"},
    ]
    chain = ToolChain(name="no_mappings_chain", steps=steps, registry=registry)

    expected_names = ["tool_alpha", "tool_beta", "tool_gamma"]
    actual_names = chain.tool_names
    assert actual_names == expected_names, (
        "tool_names should be {!r}, got: {!r}".format(expected_names, actual_names)
    )

    actual_count = chain.step_count
    assert actual_count == 3, (
        "step_count should be 3, got: {}".format(actual_count)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
