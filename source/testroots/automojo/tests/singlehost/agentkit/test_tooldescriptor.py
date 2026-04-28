"""
    Property-based tests for the automojo.agentkit.tooldescriptor module.

    Contains property-based tests (using automojo.testbase.properties) for the ToolDescriptor class,
    validating JSON round-trip serialization and deserialization.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.tooldescriptor import ToolDescriptor
from automojo.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# testbase property strategies for generating ToolDescriptor inputs
# ---------------------------------------------------------------------------

# Strategy for generating valid name strings
name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating description strings
description_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P", "Z")),
    min_size=0,
    max_size=80
)

# Strategy for generating version strings
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

# Strategy for generating tag dictionaries with string keys and string values
tags_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(
            alphabet=st.characters(categories=("L", "N")),
            min_size=1,
            max_size=15
        ),
        values=st.text(
            alphabet=st.characters(categories=("L", "N")),
            min_size=0,
            max_size=15
        ),
        max_size=5
    )
)


# Strategy for generating a single parameter definition dict
@composite
def param_def_strategy(draw):
    """
        Generates a single valid parameter definition dictionary with
        a name, type, required flag, and optional default and description.

        :returns: A dictionary representing a parameter definition.
    """
    supported_types = sorted(ToolSchema.SUPPORTED_TYPES)
    pname = draw(name_strategy)
    param_type = draw(st.sampled_from(supported_types))
    is_required = draw(st.booleans())

    param_def = {
        "name": pname,
        "type": param_type,
        "required": is_required,
    }

    include_description = draw(st.booleans())
    if include_description is True:
        desc = draw(description_strategy)
        param_def["description"] = desc

    if is_required is False:
        include_default = draw(st.booleans())
        if include_default is True:
            default_val = draw(_default_value_for_type(param_type))
            param_def["default"] = default_val

    return param_def


def _default_value_for_type(type_name):
    """
        Returns a testbase property strategy that generates a default value
        appropriate for the given type name.

        :param type_name: One of the ToolSchema SUPPORTED_TYPES.

        :returns: A testbase property strategy for generating values of that type.
    """
    if type_name == "string":
        rtnval = st.text(min_size=0, max_size=20)
    elif type_name == "integer":
        rtnval = st.integers(min_value=-1000, max_value=1000)
    elif type_name == "float":
        rtnval = st.floats(
            min_value=-1000.0,
            max_value=1000.0
        )
    elif type_name == "boolean":
        rtnval = st.booleans()
    elif type_name == "list":
        rtnval = st.lists(
            st.integers(min_value=-100, max_value=100),
            max_size=5
        )
    elif type_name == "dictionary":
        rtnval = st.dictionaries(
            keys=st.text(
                alphabet=st.characters(categories=("L", "N")),
                min_size=1,
                max_size=10
            ),
            values=st.integers(min_value=-100, max_value=100),
            max_size=5
        )
    else:
        rtnval = st.none()

    return rtnval


# Strategy for generating a list of parameter definitions with unique names
@composite
def param_list_strategy(draw, min_size=0, max_size=6):
    """
        Generates a list of parameter definition dictionaries with
        unique names.

        :param min_size: Minimum number of parameters.
        :param max_size: Maximum number of parameters.

        :returns: A list of parameter definition dictionaries.
    """
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    params = []
    used_names = set()

    for _ in range(count):
        param = draw(param_def_strategy())
        param_name = param["name"]

        while param_name in used_names:
            param_name = draw(name_strategy)

        param["name"] = param_name
        used_names.add(param_name)
        params.append(param)

    return params


# Strategy for generating a ToolSchema instance (or None)
@composite
def tool_schema_strategy(draw, allow_none=True):
    """
        Generates a valid ToolSchema instance, or optionally None.

        :param allow_none: Whether None is a valid return value.

        :returns: A ToolSchema instance or None.
    """
    if allow_none is True:
        is_none = draw(st.booleans())
        if is_none is True:
            return None

    params = draw(param_list_strategy())
    schema = ToolSchema(parameters=params)
    return schema


# Strategy for generating a complete ToolDescriptor instance
@composite
def tool_descriptor_strategy(draw):
    """
        Generates a valid ToolDescriptor instance with random name,
        description, version, input_schema, output_schema, and tags.

        :returns: A ToolDescriptor instance.
    """
    td_name = draw(name_strategy)
    td_description = draw(description_strategy)
    td_version = draw(version_strategy)
    td_input_schema = draw(tool_schema_strategy(allow_none=True))
    td_output_schema = draw(tool_schema_strategy(allow_none=True))
    td_tags = draw(tags_strategy)

    descriptor = ToolDescriptor(
        name=td_name,
        description=td_description,
        version=td_version,
        input_schema=td_input_schema,
        output_schema=td_output_schema,
        tags=td_tags,
    )
    return descriptor


# ---------------------------------------------------------------------------
# Property 5: ToolDescriptor JSON round-trip
# Feature: tool-capability-system, Property 5: ToolDescriptor JSON round-trip
# **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 16.1, 16.2, 16.5**
# ---------------------------------------------------------------------------

@given(
    original=tool_descriptor_strategy(),
    constraints={"max_examples": 100}
)
def test_property_5_tooldescriptor_json_round_trip(original):
    """
        Property 5: ToolDescriptor JSON round-trip.

        For any valid ToolDescriptor instance, calling to_json() and then
        from_json() on the resulting string produces a ToolDescriptor whose
        name, description, version, input_schema, output_schema, and tags
        are equal to the original.

        **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 16.1, 16.2, 16.5**
    """

    json_str = original.to_json()
    restored = ToolDescriptor.from_json(json_str=json_str)

    # Verify name round-trips
    assert restored.name == original.name, (
        "Name mismatch after round-trip: {!r} != {!r}".format(
            restored.name, original.name
        )
    )

    # Verify description round-trips
    assert restored.description == original.description, (
        "Description mismatch after round-trip: {!r} != {!r}".format(
            restored.description, original.description
        )
    )

    # Verify version round-trips
    assert restored.version == original.version, (
        "Version mismatch after round-trip: {!r} != {!r}".format(
            restored.version, original.version
        )
    )

    # Verify tags round-trip
    assert restored.tags == original.tags, (
        "Tags mismatch after round-trip: {!r} != {!r}".format(
            restored.tags, original.tags
        )
    )

    # Verify input_schema round-trips via as_dict comparison
    if original.input_schema is not None:
        assert restored.input_schema is not None, (
            "Restored input_schema should not be None when original is not None"
        )
        assert restored.input_schema.as_dict() == original.input_schema.as_dict(), (
            "Input schema as_dict mismatch after round-trip: {!r} != {!r}".format(
                restored.input_schema.as_dict(), original.input_schema.as_dict()
            )
        )
    else:
        assert restored.input_schema is None, (
            "Restored input_schema should be None when original is None"
        )

    # Verify output_schema round-trips via as_dict comparison
    if original.output_schema is not None:
        assert restored.output_schema is not None, (
            "Restored output_schema should not be None when original is not None"
        )
        assert restored.output_schema.as_dict() == original.output_schema.as_dict(), (
            "Output schema as_dict mismatch after round-trip: {!r} != {!r}".format(
                restored.output_schema.as_dict(), original.output_schema.as_dict()
            )
        )
    else:
        assert restored.output_schema is None, (
            "Restored output_schema should be None when original is None"
        )

    # Verify full as_dict round-trip equivalence
    assert restored.as_dict() == original.as_dict(), (
        "Full as_dict mismatch after round-trip: {!r} != {!r}".format(
            restored.as_dict(), original.as_dict()
        )
    )

    return


# ---------------------------------------------------------------------------
# Unit tests for ToolDescriptor
# ---------------------------------------------------------------------------


def test_tooldescriptor_readonly_properties():
    """
        ToolDescriptor exposes all fields as read-only properties that
        match the values provided at construction time.

        **Validates: Requirements 2.1, 2.2**
    """
    input_schema = ToolSchema(parameters=[
        {"name": "file_path", "type": "string", "required": True},
    ])
    output_schema = ToolSchema(parameters=[
        {"name": "content", "type": "string", "required": True},
    ])
    tags = {"category": "io", "level": "basic"}

    descriptor = ToolDescriptor(
        name="file_read",
        description="Reads a file from disk.",
        version="1.2.0",
        input_schema=input_schema,
        output_schema=output_schema,
        tags=tags,
    )

    assert descriptor.name == "file_read", (
        "name mismatch: {!r}".format(descriptor.name)
    )
    assert descriptor.description == "Reads a file from disk.", (
        "description mismatch: {!r}".format(descriptor.description)
    )
    assert descriptor.version == "1.2.0", (
        "version mismatch: {!r}".format(descriptor.version)
    )
    assert descriptor.input_schema is input_schema, (
        "input_schema should be the same object passed at construction"
    )
    assert descriptor.output_schema is output_schema, (
        "output_schema should be the same object passed at construction"
    )

    return


def test_tooldescriptor_tags_defensive_copy():
    """
        ToolDescriptor.tags returns a defensive copy of the tags dictionary.
        Modifying the returned dictionary does not affect the internal state.

        **Validates: Requirements 2.1, 2.2**
    """
    original_tags = {"env": "production"}

    descriptor = ToolDescriptor(
        name="test_tool",
        description="A test tool.",
        version="1.0.0",
        input_schema=None,
        output_schema=None,
        tags=original_tags,
    )

    returned_tags = descriptor.tags
    returned_tags["env"] = "staging"
    returned_tags["new_key"] = "new_value"

    assert descriptor.tags == {"env": "production"}, (
        "Internal tags should not be modified by external changes, got: {!r}".format(
            descriptor.tags
        )
    )

    return


def test_tooldescriptor_tags_default_empty():
    """
        When tags is not provided (None), ToolDescriptor.tags returns
        an empty dictionary.

        **Validates: Requirements 2.1, 2.2**
    """
    descriptor = ToolDescriptor(
        name="no_tags_tool",
        description="Tool without tags.",
        version="1.0.0",
        input_schema=None,
        output_schema=None,
    )

    assert descriptor.tags == {}, (
        "Default tags should be empty dict, got: {!r}".format(descriptor.tags)
    )

    return


def test_tooldescriptor_repr_output():
    """
        ToolDescriptor __repr__ returns a string in the format
        "ToolDescriptor(name='...', version='...')".

        **Validates: Requirements 18.3**
    """
    descriptor = ToolDescriptor(
        name="my_tool",
        description="Does something.",
        version="2.5.1",
        input_schema=None,
        output_schema=None,
    )

    repr_str = repr(descriptor)
    assert repr_str == "ToolDescriptor(name='my_tool', version='2.5.1')", (
        "repr mismatch: {!r}".format(repr_str)
    )

    return


def test_tooldescriptor_str_output():
    """
        ToolDescriptor __str__ returns a string in the format
        "ToolDescriptor: name - description".

        **Validates: Requirements 18.4**
    """
    descriptor = ToolDescriptor(
        name="my_tool",
        description="Does something useful.",
        version="1.0.0",
        input_schema=None,
        output_schema=None,
    )

    str_output = str(descriptor)
    assert str_output == "ToolDescriptor: my_tool - Does something useful.", (
        "str mismatch: {!r}".format(str_output)
    )

    return


def test_tooldescriptor_repr_and_str_with_empty_description():
    """
        ToolDescriptor __repr__ and __str__ work correctly when the
        description is an empty string.

        **Validates: Requirements 18.3, 18.4**
    """
    descriptor = ToolDescriptor(
        name="empty_desc",
        description="",
        version="0.1.0",
        input_schema=None,
        output_schema=None,
    )

    repr_str = repr(descriptor)
    assert repr_str == "ToolDescriptor(name='empty_desc', version='0.1.0')", (
        "repr with empty description mismatch: {!r}".format(repr_str)
    )

    str_output = str(descriptor)
    assert str_output == "ToolDescriptor: empty_desc - ", (
        "str with empty description mismatch: {!r}".format(str_output)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
