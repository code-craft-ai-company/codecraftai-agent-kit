"""
    Property-based tests for the automojo.agentkit.tool and
    automojo.agentkit.toolfactory modules.

    Contains property-based tests (using automojo.testbase.properties) for the Tool abstract
    base class and the create_tool factory function, validating descriptor
    metadata reflection, tag and credential name preservation, class-level
    schema validation, and factory tool creation.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.tool import Tool
from automojo.agentkit.toolfactory import create_tool
from automojo.agentkit.toolschema import ToolSchema
from automojo.agentkit.errors import SemanticError


# ---------------------------------------------------------------------------
# testbase property strategies for generating Tool-related inputs
# ---------------------------------------------------------------------------

# Strategy for generating valid tool names (non-empty alphanumeric strings)
tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating tool descriptions
tool_description_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P", "Z")),
    min_size=0,
    max_size=80
)

# Strategy for generating version strings
@composite
def _version_string(draw):
    """
        Generates a version string in the format major.minor.patch.

        :returns: A version string.
    """
    major = draw(st.integers(min_value=0, max_value=999))
    minor = draw(st.integers(min_value=0, max_value=999))
    patch = draw(st.integers(min_value=0, max_value=999))
    return f"{major}.{minor}.{patch}"


version_strategy = _version_string()

# Strategy for generating tag dictionaries (string -> string)
tags_strategy = st.dictionaries(
    keys=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=15
    ),
    values=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=15
    ),
    max_size=5
)

# Strategy for generating credential name lists
credential_names_strategy = st.lists(
    st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=20
    ),
    max_size=5
)

# Strategy for generating a supported type string
supported_type_strategy = st.sampled_from(sorted(ToolSchema.SUPPORTED_TYPES))

# Strategy for generating a parameter name
param_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)


@composite
def param_def_strategy(draw):
    """
        Generates a single valid parameter definition dictionary.

        :returns: A dictionary representing a parameter definition.
    """
    name = draw(param_name_strategy)
    param_type = draw(supported_type_strategy)
    is_required = draw(st.booleans())

    param_def = {
        "name": name,
        "type": param_type,
        "required": is_required,
    }

    return param_def


@composite
def schema_dict_strategy(draw, min_params=0, max_params=5):
    """
        Generates a valid schema dictionary with unique parameter names,
        suitable for use as INPUT_SCHEMA or OUTPUT_SCHEMA on a Tool subclass.

        :param min_params: Minimum number of parameters.
        :param max_params: Maximum number of parameters.

        :returns: A dictionary with a 'parameters' key.
    """
    count = draw(st.integers(min_value=min_params, max_value=max_params))
    params = []
    used_names = set()

    for _ in range(count):
        param = draw(param_def_strategy())
        param_name = param["name"]

        while param_name in used_names:
            param_name = draw(param_name_strategy)

        param["name"] = param_name
        used_names.add(param_name)
        params.append(param)

    rtnval = {"parameters": params}
    return rtnval


def _schemas_equivalent(schema_a, schema_b):
    """
        Compares two ToolSchema instances (or None values) for equivalence
        by comparing their as_dict() output.

        :param schema_a: A ToolSchema instance or None.
        :param schema_b: A ToolSchema instance or None.

        :returns: True if both are equivalent, False otherwise.
    """
    if schema_a is None and schema_b is None:
        rtnval = True
    elif schema_a is None or schema_b is None:
        rtnval = False
    else:
        rtnval = schema_a.as_dict() == schema_b.as_dict()

    return rtnval


def _make_tool_class(name, description, version, input_schema_dict, output_schema_dict):
    """
        Creates a concrete Tool subclass with the given class-level constants.

        :param name: The TOOL_NAME value.
        :param description: The TOOL_DESCRIPTION value.
        :param version: The TOOL_VERSION value.
        :param input_schema_dict: The INPUT_SCHEMA dictionary or None.
        :param output_schema_dict: The OUTPUT_SCHEMA dictionary or None.

        :returns: A concrete Tool subclass type.
    """

    class ConcreteTool(Tool):
        """
            A concrete Tool subclass for testing purposes.
        """

        TOOL_NAME = name
        TOOL_DESCRIPTION = description
        TOOL_VERSION = version
        INPUT_SCHEMA = input_schema_dict
        OUTPUT_SCHEMA = output_schema_dict

        def execute(self, inputs: dict, credentials: dict = None) -> dict:
            """
                A no-op execute implementation for testing.

                :param inputs: Validated input dictionary.
                :param credentials: Optional dictionary of resolved credentials.

                :returns: An empty dictionary.
            """
            rtnval = {}
            return rtnval

    return ConcreteTool


# ---------------------------------------------------------------------------
# Property 6: Tool descriptor property reflects tool metadata
# Feature: tool-capability-system, Property 6: Tool descriptor property reflects tool metadata
# **Validates: Requirements 1.3, 12.2, 12.3**
# ---------------------------------------------------------------------------

@given(
    name=tool_name_strategy,
    description=tool_description_strategy,
    version=version_strategy,
    input_schema_dict=schema_dict_strategy(),
    output_schema_dict=schema_dict_strategy(),
    tags=tags_strategy,
    constraints={"max_examples": 100}
)
def test_property_6_descriptor_reflects_tool_metadata(name, description, version, input_schema_dict, output_schema_dict, tags):
    """
        Property 6: Tool descriptor property reflects tool metadata.

        For any Tool instance, the descriptor property returns a ToolDescriptor
        whose name, description, version, input_schema, output_schema, and tags
        match the Tool's own corresponding properties.

        **Validates: Requirements 1.3, 12.2, 12.3**
    """

    tool_cls = _make_tool_class(
        name=name,
        description=description,
        version=version,
        input_schema_dict=input_schema_dict,
        output_schema_dict=output_schema_dict,
    )
    tool = tool_cls(tags=tags)

    desc = tool.descriptor

    assert desc.name == tool.name, (
        "Descriptor name '{}' does not match tool name '{}'".format(
            desc.name, tool.name
        )
    )

    assert desc.description == tool.description, (
        "Descriptor description '{}' does not match tool description '{}'".format(
            desc.description, tool.description
        )
    )

    assert desc.version == tool.version, (
        "Descriptor version '{}' does not match tool version '{}'".format(
            desc.version, tool.version
        )
    )

    assert desc.tags == tool.tags, (
        "Descriptor tags {!r} do not match tool tags {!r}".format(
            desc.tags, tool.tags
        )
    )

    input_schemas_match = _schemas_equivalent(desc.input_schema, tool.input_schema)
    assert input_schemas_match is True, (
        "Descriptor input_schema does not match tool input_schema"
    )

    output_schemas_match = _schemas_equivalent(desc.output_schema, tool.output_schema)
    assert output_schemas_match is True, (
        "Descriptor output_schema does not match tool output_schema"
    )

    return


# ---------------------------------------------------------------------------
# Property 7: Tool construction preserves tags and credential names
# Feature: tool-capability-system, Property 7: Tool construction preserves tags and credential names
# **Validates: Requirements 1.4, 1.5**
# ---------------------------------------------------------------------------

@given(
    name=tool_name_strategy,
    tags=tags_strategy,
    cred_names=credential_names_strategy,
    constraints={"max_examples": 100}
)
def test_property_7_construction_preserves_tags_and_credential_names(name, tags, cred_names):
    """
        Property 7: Tool construction preserves tags and credential names.

        For any Tool instance constructed with a tags dictionary and a
        credential_names list, the tags property returns a dictionary equal
        to the provided tags, and the credential_names property returns a
        list equal to the provided credential names.

        **Validates: Requirements 1.4, 1.5**
    """

    tool_cls = _make_tool_class(
        name=name,
        description="test tool",
        version="1.0.0",
        input_schema_dict=None,
        output_schema_dict=None,
    )
    tool = tool_cls(tags=tags, credential_names=cred_names)

    assert tool.tags == tags, (
        "Tool tags {!r} do not match provided tags {!r}".format(
            tool.tags, tags
        )
    )

    assert tool.credential_names == cred_names, (
        "Tool credential_names {!r} do not match provided credential_names {!r}".format(
            tool.credential_names, cred_names
        )
    )

    # Verify defensive copies: mutating the returned values should not
    # affect the tool's internal state
    returned_tags = tool.tags
    returned_tags["mutated_key"] = "mutated_value"
    assert "mutated_key" not in tool.tags, (
        "Mutating returned tags should not affect tool internal tags"
    )

    returned_creds = tool.credential_names
    returned_creds.append("mutated_cred")
    assert "mutated_cred" not in tool.credential_names, (
        "Mutating returned credential_names should not affect tool internal list"
    )

    return


# ---------------------------------------------------------------------------
# Property 8: Tool class-level schema declarations validated and converted
# Feature: tool-capability-system, Property 8: Tool class-level schema declarations validated and converted
# **Validates: Requirements 12.1, 12.5**
# ---------------------------------------------------------------------------

@given(
    input_schema_dict=schema_dict_strategy(),
    output_schema_dict=schema_dict_strategy(),
    name=tool_name_strategy,
    constraints={"max_examples": 100}
)
def test_property_8_class_level_schema_declarations_validated_and_converted(input_schema_dict, output_schema_dict, name):
    """
        Property 8: Tool class-level schema declarations are validated and converted.

        For any Tool subclass with valid class-level INPUT_SCHEMA and OUTPUT_SCHEMA
        dictionaries, construction produces a Tool whose input_schema and output_schema
        are ToolSchema instances equivalent to ToolSchema.from_dict() of the declared
        dictionaries. For any subclass with an invalid schema dictionary, construction
        raises SemanticError.

        **Validates: Requirements 12.1, 12.5**
    """
    # Part A: Valid schemas produce ToolSchema instances

    tool_cls = _make_tool_class(
        name=name,
        description="test tool",
        version="1.0.0",
        input_schema_dict=input_schema_dict,
        output_schema_dict=output_schema_dict,
    )
    tool = tool_cls()

    # Verify input_schema is a ToolSchema instance
    assert isinstance(tool.input_schema, ToolSchema), (
        "input_schema should be a ToolSchema instance, got: {}".format(
            type(tool.input_schema).__name__
        )
    )

    # Verify output_schema is a ToolSchema instance
    assert isinstance(tool.output_schema, ToolSchema), (
        "output_schema should be a ToolSchema instance, got: {}".format(
            type(tool.output_schema).__name__
        )
    )

    # Verify equivalence with ToolSchema.from_dict()
    expected_input = ToolSchema.from_dict(schema_data=input_schema_dict)
    expected_output = ToolSchema.from_dict(schema_data=output_schema_dict)

    input_match = tool.input_schema.as_dict() == expected_input.as_dict()
    assert input_match is True, (
        "input_schema as_dict mismatch: {!r} != {!r}".format(
            tool.input_schema.as_dict(), expected_input.as_dict()
        )
    )

    output_match = tool.output_schema.as_dict() == expected_output.as_dict()
    assert output_match is True, (
        "output_schema as_dict mismatch: {!r} != {!r}".format(
            tool.output_schema.as_dict(), expected_output.as_dict()
        )
    )

    return


def test_property_8_invalid_schema_raises_semantic_error():
    """
        Property 8 (invalid case): Tool class-level schema declarations
        validated and converted.

        For any subclass with an invalid schema dictionary, construction
        raises SemanticError.

        **Validates: Requirements 12.5**
    """
    # Invalid INPUT_SCHEMA: not a dictionary at all (causes from_dict to fail)
    raised_input = False
    try:
        invalid_cls = _make_tool_class(
            name="invalid_input_tool",
            description="test",
            version="1.0.0",
            input_schema_dict=[1, 2, 3],
            output_schema_dict=None,
        )
        invalid_cls()
    except SemanticError:
        raised_input = True

    assert raised_input is True, (
        "Invalid INPUT_SCHEMA should raise SemanticError"
    )

    # Invalid OUTPUT_SCHEMA: not a dictionary at all
    raised_output = False
    try:
        invalid_cls = _make_tool_class(
            name="invalid_output_tool",
            description="test",
            version="1.0.0",
            input_schema_dict=None,
            output_schema_dict=42,
        )
        invalid_cls()
    except SemanticError:
        raised_output = True

    assert raised_output is True, (
        "Invalid OUTPUT_SCHEMA should raise SemanticError"
    )

    return


# ---------------------------------------------------------------------------
# Property 26: create_tool factory produces working Tool
# Feature: tool-capability-system, Property 26: create_tool factory produces working Tool
# **Validates: Requirements 12.6**
# ---------------------------------------------------------------------------

@given(
    name=tool_name_strategy,
    description=tool_description_strategy,
    version=version_strategy,
    input_schema_dict=schema_dict_strategy(),
    output_schema_dict=schema_dict_strategy(),
    tags=tags_strategy,
    constraints={"max_examples": 100}
)
def test_property_26_create_tool_factory_produces_working_tool(name, description, version, input_schema_dict, output_schema_dict, tags):
    """
        Property 26: create_tool factory produces working Tool.

        For any valid name, description, input schema dictionary, output schema
        dictionary, and execute callable, create_tool() returns a Tool instance
        whose name, description, input_schema, and output_schema match the
        provided arguments, and whose execute method delegates to the provided
        callable.

        **Validates: Requirements 12.6**
    """

    # Track whether the execute callable was invoked
    call_tracker = {"called": False, "received_inputs": None, "received_credentials": None}
    sentinel_output = {"result": "sentinel_value"}

    def execute_fn(inputs, credentials):
        """
            A test execute callable that records its invocation.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :returns: A sentinel output dictionary.
        """
        call_tracker["called"] = True
        call_tracker["received_inputs"] = inputs
        call_tracker["received_credentials"] = credentials
        rtnval = dict(sentinel_output)
        return rtnval

    tool = create_tool(
        name=name,
        description=description,
        input_schema=input_schema_dict,
        output_schema=output_schema_dict,
        execute_fn=execute_fn,
        version=version,
        tags=tags,
    )

    # Verify the returned object is a Tool instance
    assert isinstance(tool, Tool), (
        "create_tool should return a Tool instance, got: {}".format(
            type(tool).__name__
        )
    )

    # Verify name matches
    assert tool.name == name, (
        "Tool name '{}' does not match provided name '{}'".format(
            tool.name, name
        )
    )

    # Verify description matches
    assert tool.description == description, (
        "Tool description '{}' does not match provided description '{}'".format(
            tool.description, description
        )
    )

    # Verify version matches
    assert tool.version == version, (
        "Tool version '{}' does not match provided version '{}'".format(
            tool.version, version
        )
    )

    # Verify input_schema matches
    expected_input = ToolSchema.from_dict(schema_data=input_schema_dict)
    input_match = tool.input_schema.as_dict() == expected_input.as_dict()
    assert input_match is True, (
        "Tool input_schema does not match provided input_schema"
    )

    # Verify output_schema matches
    expected_output = ToolSchema.from_dict(schema_data=output_schema_dict)
    output_match = tool.output_schema.as_dict() == expected_output.as_dict()
    assert output_match is True, (
        "Tool output_schema does not match provided output_schema"
    )

    # Verify tags match
    assert tool.tags == tags, (
        "Tool tags {!r} do not match provided tags {!r}".format(
            tool.tags, tags
        )
    )

    # Verify execute delegates to the provided callable
    test_inputs = {"key": "value"}
    test_credentials = {"cred": "secret"}
    result = tool.execute(inputs=test_inputs, credentials=test_credentials)

    assert call_tracker["called"] is True, (
        "execute_fn should have been called"
    )

    assert call_tracker["received_inputs"] == test_inputs, (
        "execute_fn should have received the inputs dictionary"
    )

    assert call_tracker["received_credentials"] == test_credentials, (
        "execute_fn should have received the credentials dictionary"
    )

    assert result == sentinel_output, (
        "execute should return the output from execute_fn, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Unit tests for Tool base class
# Feature: tool-capability-system, Task 4.4
# **Validates: Requirements 1.1, 1.2, 1.6, 1.7, 1.8, 18.1, 18.2**
# ---------------------------------------------------------------------------


def test_tool_without_name_raises_semantic_error():
    """
        A Tool subclass that does not provide a TOOL_NAME raises SemanticError
        at construction time.

        **Validates: Requirements 1.6**
    """

    class NoNameTool(Tool):
        """
            A Tool subclass with no TOOL_NAME set.
        """

        TOOL_NAME = None

        def execute(self, inputs: dict, credentials: dict = None) -> dict:
            """
                No-op execute.

                :param inputs: Validated input dictionary.
                :param credentials: Optional credentials dictionary.

                :returns: An empty dictionary.
            """
            rtnval = {}
            return rtnval

    raised = False
    error_message = ""
    try:
        NoNameTool()
    except SemanticError as err:
        raised = True
        error_message = str(err)

    assert raised is True, (
        "Tool without TOOL_NAME should raise SemanticError"
    )

    assert "name" in error_message.lower(), (
        "SemanticError message should mention 'name', got: {!r}".format(error_message)
    )

    return


def test_tool_abstract_execute_method_enforcement():
    """
        A Tool subclass that does not implement the execute method cannot
        be instantiated.

        **Validates: Requirements 1.2**
    """

    class IncompleteToolSubclass(Tool):
        """
            A Tool subclass that does not implement execute.
        """

        TOOL_NAME = "incomplete_tool"

    raised = False
    try:
        IncompleteToolSubclass()
    except TypeError:
        raised = True

    assert raised is True, (
        "Tool subclass without execute implementation should raise TypeError"
    )

    return


def test_tool_repr_contains_class_name_and_version():
    """
        Tool __repr__ includes the concrete class name, tool name, and version.

        **Validates: Requirements 1.7, 18.1**
    """
    tool_cls = _make_tool_class(
        name="repr_tool",
        description="A tool for repr testing",
        version="2.3.1",
        input_schema_dict=None,
        output_schema_dict=None,
    )
    tool = tool_cls()

    repr_str = repr(tool)

    assert "ConcreteTool" in repr_str, (
        "repr should contain the class name 'ConcreteTool', got: {!r}".format(repr_str)
    )
    assert "repr_tool" in repr_str, (
        "repr should contain the tool name 'repr_tool', got: {!r}".format(repr_str)
    )
    assert "2.3.1" in repr_str, (
        "repr should contain the version '2.3.1', got: {!r}".format(repr_str)
    )

    expected = "ConcreteTool(name='repr_tool', version='2.3.1')"
    assert repr_str == expected, (
        "repr mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )

    return


def test_tool_str_contains_name_and_description():
    """
        Tool __str__ returns a human-readable summary with the tool name
        and description.

        **Validates: Requirements 1.8, 18.2**
    """
    tool_cls = _make_tool_class(
        name="str_tool",
        description="A tool for str testing",
        version="1.0.0",
        input_schema_dict=None,
        output_schema_dict=None,
    )
    tool = tool_cls()

    str_str = str(tool)

    assert "str_tool" in str_str, (
        "str should contain the tool name 'str_tool', got: {!r}".format(str_str)
    )
    assert "A tool for str testing" in str_str, (
        "str should contain the description, got: {!r}".format(str_str)
    )

    expected = "str_tool - A tool for str testing"
    assert str_str == expected, (
        "str mismatch: expected {!r}, got {!r}".format(expected, str_str)
    )

    return


def test_tool_properties_are_accessible():
    """
        Tool exposes name, description, version, input_schema, output_schema,
        tags, and credential_names as read-only properties.

        **Validates: Requirements 1.1**
    """
    input_schema_dict = {
        "parameters": [
            {"name": "query", "type": "string", "required": True}
        ]
    }
    output_schema_dict = {
        "parameters": [
            {"name": "result", "type": "string", "required": True}
        ]
    }
    tool_cls = _make_tool_class(
        name="props_tool",
        description="Properties test tool",
        version="3.0.0",
        input_schema_dict=input_schema_dict,
        output_schema_dict=output_schema_dict,
    )
    tags = {"category": "test"}
    cred_names = ["api_key"]
    tool = tool_cls(tags=tags, credential_names=cred_names)

    assert tool.name == "props_tool", (
        "name mismatch: {!r}".format(tool.name)
    )
    assert tool.description == "Properties test tool", (
        "description mismatch: {!r}".format(tool.description)
    )
    assert tool.version == "3.0.0", (
        "version mismatch: {!r}".format(tool.version)
    )
    assert tool.tags == {"category": "test"}, (
        "tags mismatch: {!r}".format(tool.tags)
    )
    assert tool.credential_names == ["api_key"], (
        "credential_names mismatch: {!r}".format(tool.credential_names)
    )
    assert tool.input_schema is not None, (
        "input_schema should not be None"
    )
    assert tool.output_schema is not None, (
        "output_schema should not be None"
    )

    return


def test_tool_none_schemas_produce_none_properties():
    """
        When INPUT_SCHEMA and OUTPUT_SCHEMA are None, the input_schema
        and output_schema properties return None.

        **Validates: Requirements 1.1**
    """
    tool_cls = _make_tool_class(
        name="none_schema_tool",
        description="No schemas",
        version="1.0.0",
        input_schema_dict=None,
        output_schema_dict=None,
    )
    tool = tool_cls()

    assert tool.input_schema is None, (
        "input_schema should be None when INPUT_SCHEMA is None"
    )
    assert tool.output_schema is None, (
        "output_schema should be None when OUTPUT_SCHEMA is None"
    )

    return


def test_tool_default_tags_and_credential_names():
    """
        When no tags or credential_names are provided, the Tool defaults
        to an empty dict and empty list respectively.

        **Validates: Requirements 1.1**
    """
    tool_cls = _make_tool_class(
        name="defaults_tool",
        description="Defaults test",
        version="1.0.0",
        input_schema_dict=None,
        output_schema_dict=None,
    )
    tool = tool_cls()

    assert tool.tags == {}, (
        "Default tags should be empty dict, got: {!r}".format(tool.tags)
    )
    assert tool.credential_names == [], (
        "Default credential_names should be empty list, got: {!r}".format(
            tool.credential_names
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
