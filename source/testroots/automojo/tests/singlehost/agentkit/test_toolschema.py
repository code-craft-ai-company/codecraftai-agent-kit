"""
    Property-based tests for the automojo.agentkit.toolschema module.

    Contains property-based tests (using automojo.testbase.properties) for the ToolSchema class,
    validating JSON round-trip, correct input validation, missing required
    parameter reporting, and type mismatch reporting.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite
from automojo.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# testbase property strategies for generating ToolSchema inputs
# ---------------------------------------------------------------------------

# Strategy for generating valid parameter names
param_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating a supported type string
supported_type_strategy = st.sampled_from(sorted(ToolSchema.SUPPORTED_TYPES))

# Strategy for generating a description string
description_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P", "Z")),
    min_size=0,
    max_size=80
)


# Strategy for generating a default value matching a given type
def _default_value_strategy_for_type(type_name):
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


def _value_strategy_for_type(type_name):
    """
        Returns a testbase property strategy that generates a valid value
        for the given type name.

        :param type_name: One of the ToolSchema SUPPORTED_TYPES.

        :returns: A testbase property strategy for generating values of that type.
    """
    rtnval = _default_value_strategy_for_type(type_name)
    return rtnval


# Strategy for generating a single parameter definition dict
@composite
def param_def_strategy(draw):
    """
        Generates a single valid parameter definition dictionary with
        a name, type, required flag, and optional default and description.

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

    include_description = draw(st.booleans())
    if include_description is True:
        desc = draw(description_strategy)
        param_def["description"] = desc

    if is_required is False:
        include_default = draw(st.booleans())
        if include_default is True:
            default_val = draw(_default_value_strategy_for_type(param_type))
            param_def["default"] = default_val

    return param_def


# Strategy for generating a list of parameter definitions with unique names
@composite
def param_list_strategy(draw, min_size=0, max_size=8):
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

        # Ensure unique names
        while param_name in used_names:
            param_name = draw(param_name_strategy)

        param["name"] = param_name
        used_names.add(param_name)
        params.append(param)

    return params


# Strategy for generating a valid ToolSchema instance
@composite
def tool_schema_strategy(draw, min_params=0, max_params=8):
    """
        Generates a valid ToolSchema instance with a random set of
        parameter definitions.

        :param min_params: Minimum number of parameters.
        :param max_params: Maximum number of parameters.

        :returns: A ToolSchema instance.
    """
    params = draw(param_list_strategy(min_size=min_params, max_size=max_params))
    schema = ToolSchema(parameters=params)
    return schema


# Strategy for generating a valid input dictionary matching a schema
@composite
def valid_inputs_for_schema(draw, schema):
    """
        Generates a dictionary of valid input values that satisfy
        all required parameters and type constraints of the given schema.

        :param schema: A ToolSchema instance.

        :returns: A dictionary of valid input values.
    """
    values = {}

    for param_def in schema.parameters:
        param_name = param_def["name"]
        param_type = param_def["type"]
        is_required = param_def.get("required", True)

        if is_required is True:
            value = draw(_value_strategy_for_type(param_type))
            values[param_name] = value
        else:
            include_optional = draw(st.booleans())
            if include_optional is True:
                value = draw(_value_strategy_for_type(param_type))
                values[param_name] = value

    return values



# ---------------------------------------------------------------------------
# Property 1: ToolSchema JSON round-trip
# Feature: tool-capability-system, Property 1: ToolSchema JSON round-trip
# **Validates: Requirements 3.8, 3.9, 3.10, 3.11, 3.12, 16.3, 16.4, 16.6**
# ---------------------------------------------------------------------------

@given(
    schema=tool_schema_strategy(),
    settings=settings(max_examples=100)
)
def test_property_1_json_round_trip(schema):
    """
        Property 1: ToolSchema JSON round-trip.

        For any valid ToolSchema instance, calling to_json() and then
        from_json() on the resulting string produces a ToolSchema whose
        as_dict() output equals the original's as_dict() output.

        **Validates: Requirements 3.8, 3.9, 3.10, 3.11, 3.12, 16.3, 16.4, 16.6**
    """

    original_dict = schema.as_dict()
    json_str = schema.to_json()
    restored = ToolSchema.from_json(json_str)
    restored_dict = restored.as_dict()

    assert restored_dict == original_dict, (
        "Round-trip as_dict mismatch: {!r} != {!r}".format(
            restored_dict, original_dict
        )
    )

    # Also verify parameter_count is preserved
    assert restored.parameter_count == schema.parameter_count, (
        "Round-trip parameter_count mismatch: {} != {}".format(
            restored.parameter_count, schema.parameter_count
        )
    )
    return


# ---------------------------------------------------------------------------
# Property 2: ToolSchema validates correct inputs as valid
# Feature: tool-capability-system, Property 2: ToolSchema validates correct inputs as valid
# **Validates: Requirements 3.1, 3.2, 3.5**
# ---------------------------------------------------------------------------

@composite
def _schema_with_valid_inputs(draw):
    """
        Generates a ToolSchema and a valid input dictionary for it.

        :returns: A tuple of (schema, values).
    """
    schema = draw(tool_schema_strategy())
    values = draw(valid_inputs_for_schema(schema))
    return (schema, values)


@given(
    test_data=_schema_with_valid_inputs(),
    settings=settings(max_examples=100)
)
def test_property_2_validates_correct_inputs_as_valid(test_data):
    """
        Property 2: ToolSchema validates correct inputs as valid.

        For any valid ToolSchema and any input dictionary that includes
        all required parameters with values matching their declared type
        constraints, validate() returns an empty list.

        **Validates: Requirements 3.1, 3.2, 3.5**
    """
    schema, values = test_data

    errors = schema.validate(values)

    assert errors == [], (
        "Valid inputs should produce no errors, got: {!r}".format(errors)
    )
    return


# ---------------------------------------------------------------------------
# Property 3: ToolSchema reports missing required parameters
# Feature: tool-capability-system, Property 3: ToolSchema reports missing required parameters
# **Validates: Requirements 3.6**
# ---------------------------------------------------------------------------

@composite
def _missing_required_param_data(draw):
    """
        Generates test data for property 3: a schema with at least one required
        parameter, an omitted required parameter name, and valid inputs for
        all other parameters.

        :returns: A tuple of (schema, omitted_name, values).
    """
    params = draw(param_list_strategy(min_size=1, max_size=8))

    has_required = False
    for p in params:
        if p.get("required", True) is True:
            has_required = True
            break

    if has_required is False:
        params[0]["required"] = True

    schema = ToolSchema(parameters=params)

    required_names = []
    for p in schema.parameters:
        is_required = p.get("required", True)
        if is_required is True:
            required_names.append(p["name"])

    omitted_name = draw(st.sampled_from(required_names))

    values = {}
    for param_def in schema.parameters:
        param_name = param_def["name"]
        param_type = param_def["type"]

        if param_name == omitted_name:
            continue

        is_required = param_def.get("required", True)
        if is_required is True:
            value = draw(_value_strategy_for_type(param_type))
            values[param_name] = value
        else:
            include_optional = draw(st.booleans())
            if include_optional is True:
                value = draw(_value_strategy_for_type(param_type))
                values[param_name] = value

    return (schema, omitted_name, values)


@given(
    test_data=_missing_required_param_data(),
    settings=settings(max_examples=100)
)
def test_property_3_reports_missing_required_parameters(test_data):
    """
        Property 3: ToolSchema reports missing required parameters.

        For any valid ToolSchema with at least one required parameter,
        and any input dictionary missing that required parameter,
        validate() returns a non-empty list containing an error string
        that includes the missing parameter's name.

        **Validates: Requirements 3.6**
    """
    schema, omitted_name, values = test_data

    errors = schema.validate(values)

    errors_not_empty = len(errors) > 0
    assert errors_not_empty is True, (
        "Missing required parameter '{}' should produce errors".format(omitted_name)
    )

    name_found_in_errors = False
    for error_str in errors:
        if omitted_name in error_str:
            name_found_in_errors = True
            break

    assert name_found_in_errors is True, (
        "Error list should contain the missing parameter name '{}', got: {!r}".format(
            omitted_name, errors
        )
    )
    return



# ---------------------------------------------------------------------------
# Property 4: ToolSchema reports type mismatches
# Feature: tool-capability-system, Property 4: ToolSchema reports type mismatches
# **Validates: Requirements 3.7**
# ---------------------------------------------------------------------------

# Mapping from type name to a strategy that generates a value of a DIFFERENT type
_MISMATCHED_TYPE_STRATEGIES = {
    "string": st.integers(min_value=-100, max_value=100),
    "integer": st.text(min_size=1, max_size=10),
    "float": st.text(min_size=1, max_size=10),
    "boolean": st.text(min_size=1, max_size=10),
    "list": st.text(min_size=1, max_size=10),
    "dictionary": st.text(min_size=1, max_size=10),
}


@composite
def _type_mismatch_data(draw):
    """
        Generates test data for property 4: a schema, a target parameter with
        a mismatched value, and valid inputs for all other parameters.

        :returns: A tuple of (schema, target_name, target_type, mismatched_value, values).
    """
    params = draw(param_list_strategy(min_size=1, max_size=8))
    schema = ToolSchema(parameters=params)

    target_param = draw(st.sampled_from(schema.parameters))
    target_name = target_param["name"]
    target_type = target_param["type"]

    values = {}
    for param_def in schema.parameters:
        param_name = param_def["name"]
        param_type = param_def["type"]

        if param_name == target_name:
            continue

        is_required = param_def.get("required", True)
        if is_required is True:
            value = draw(_value_strategy_for_type(param_type))
            values[param_name] = value

    mismatched_strategy = _MISMATCHED_TYPE_STRATEGIES[target_type]
    mismatched_value = draw(mismatched_strategy)
    values[target_name] = mismatched_value

    return (schema, target_name, target_type, mismatched_value, values)


@given(
    test_data=_type_mismatch_data(),
    settings=settings(max_examples=100)
)
def test_property_4_reports_type_mismatches(test_data):
    """
        Property 4: ToolSchema reports type mismatches.

        For any valid ToolSchema parameter with a declared type constraint,
        and any input value whose type does not match the constraint,
        validate() returns a non-empty list containing an error string
        that includes the parameter name, the expected type, and the
        actual type.

        **Validates: Requirements 3.7**
    """
    schema, target_name, target_type, mismatched_value, values = test_data

    errors = schema.validate(values)

    errors_not_empty = len(errors) > 0
    assert errors_not_empty is True, (
        "Type mismatch for parameter '{}' (expected '{}', got '{}') "
        "should produce errors".format(
            target_name, target_type, type(mismatched_value).__name__
        )
    )

    actual_type_name = type(mismatched_value).__name__
    name_found = False
    expected_type_found = False
    actual_type_found = False

    for error_str in errors:
        if target_name in error_str:
            name_found = True
        if target_type in error_str:
            expected_type_found = True
        if actual_type_name in error_str:
            actual_type_found = True

    assert name_found is True, (
        "Error should contain parameter name '{}', got: {!r}".format(
            target_name, errors
        )
    )
    assert expected_type_found is True, (
        "Error should contain expected type '{}', got: {!r}".format(
            target_type, errors
        )
    )
    assert actual_type_found is True, (
        "Error should contain actual type '{}', got: {!r}".format(
            actual_type_name, errors
        )
    )
    return


# ---------------------------------------------------------------------------
# Unit tests for ToolSchema
# Feature: tool-capability-system, Task 1.4
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.13, 18.5, 18.6**
# ---------------------------------------------------------------------------


def test_empty_schema_validates_any_input():
    """
        An empty ToolSchema (no parameters) validates any input dictionary
        and returns an empty error list.

        **Validates: Requirements 3.5, 3.13**
    """
    schema = ToolSchema(parameters=[])

    errors = schema.validate({})
    assert errors == [], "Empty schema should validate empty input, got: {!r}".format(errors)

    errors_with_extra = schema.validate({"extra_key": "extra_value"})
    assert errors_with_extra == [], (
        "Empty schema should validate input with extra keys, got: {!r}".format(errors_with_extra)
    )

    return


def test_empty_schema_none_parameters():
    """
        A ToolSchema constructed with None parameters behaves as an empty schema.

        **Validates: Requirements 3.13**
    """
    schema = ToolSchema(parameters=None)

    assert schema.parameter_count == 0, (
        "None-parameter schema should have 0 parameters, got: {}".format(schema.parameter_count)
    )

    errors = schema.validate({"anything": 42})
    assert errors == [], "None-parameter schema should validate any input, got: {!r}".format(errors)

    return


def test_default_values_applied_for_optional_parameters():
    """
        When an optional parameter with a default value is missing from the
        input dictionary, validate() applies the default value to the input.

        **Validates: Requirements 3.2, 3.3**
    """
    params = [
        {"name": "greeting", "type": "string", "required": False, "default": "hello"},
        {"name": "count", "type": "integer", "required": False, "default": 10},
    ]
    schema = ToolSchema(parameters=params)

    values = {}
    errors = schema.validate(values)

    assert errors == [], "Optional params with defaults should produce no errors, got: {!r}".format(errors)
    assert values.get("greeting") == "hello", (
        "Default for 'greeting' should be 'hello', got: {!r}".format(values.get("greeting"))
    )
    assert values.get("count") == 10, (
        "Default for 'count' should be 10, got: {!r}".format(values.get("count"))
    )

    return


def test_default_values_not_applied_when_value_provided():
    """
        When an optional parameter with a default value is present in the
        input dictionary, validate() does not overwrite the provided value.

        **Validates: Requirements 3.2, 3.3**
    """
    params = [
        {"name": "greeting", "type": "string", "required": False, "default": "hello"},
    ]
    schema = ToolSchema(parameters=params)

    values = {"greeting": "world"}
    errors = schema.validate(values)

    assert errors == [], "Provided optional value should produce no errors, got: {!r}".format(errors)
    assert values["greeting"] == "world", (
        "Provided value should not be overwritten, got: {!r}".format(values["greeting"])
    )

    return


def test_parameter_description_storage():
    """
        Parameter definitions with a description field store and expose
        the description through the parameters property.

        **Validates: Requirements 3.4**
    """
    params = [
        {"name": "file_path", "type": "string", "required": True, "description": "Path to the file."},
        {"name": "encoding", "type": "string", "required": False, "description": "File encoding."},
        {"name": "no_desc", "type": "integer", "required": True},
    ]
    schema = ToolSchema(parameters=params)

    retrieved_params = schema.parameters

    assert retrieved_params[0]["description"] == "Path to the file.", (
        "First param description mismatch: {!r}".format(retrieved_params[0].get("description"))
    )
    assert retrieved_params[1]["description"] == "File encoding.", (
        "Second param description mismatch: {!r}".format(retrieved_params[1].get("description"))
    )

    has_description = "description" in retrieved_params[2]
    assert has_description is False, (
        "Third param should not have a description key, got: {!r}".format(retrieved_params[2])
    )

    return


def test_toolschema_repr_output():
    """
        ToolSchema __repr__ returns 'ToolSchema(parameter_count=N)' where N
        is the number of defined parameters.

        **Validates: Requirements 18.5**
    """
    schema_empty = ToolSchema(parameters=[])
    repr_empty = repr(schema_empty)
    assert repr_empty == "ToolSchema(parameter_count=0)", (
        "Empty schema repr mismatch: {!r}".format(repr_empty)
    )

    params = [
        {"name": "a", "type": "string"},
        {"name": "b", "type": "integer"},
        {"name": "c", "type": "boolean"},
    ]
    schema_three = ToolSchema(parameters=params)
    repr_three = repr(schema_three)
    assert repr_three == "ToolSchema(parameter_count=3)", (
        "Three-param schema repr mismatch: {!r}".format(repr_three)
    )

    return


def test_toolschema_str_output():
    """
        ToolSchema __str__ returns 'ToolSchema: name1: type1, name2: type2'
        for schemas with parameters, or 'ToolSchema: (no parameters)' for
        empty schemas.

        **Validates: Requirements 18.6**
    """
    schema_empty = ToolSchema(parameters=[])
    str_empty = str(schema_empty)
    assert str_empty == "ToolSchema: (no parameters)", (
        "Empty schema str mismatch: {!r}".format(str_empty)
    )

    params = [
        {"name": "name", "type": "string"},
        {"name": "age", "type": "integer"},
    ]
    schema_two = ToolSchema(parameters=params)
    str_two = str(schema_two)
    assert str_two == "ToolSchema: name: string, age: integer", (
        "Two-param schema str mismatch: {!r}".format(str_two)
    )

    return


def test_toolschema_supported_types_constant():
    """
        ToolSchema.SUPPORTED_TYPES contains exactly the six expected type
        strings.

        **Validates: Requirements 3.1**
    """
    expected_types = {"string", "integer", "float", "boolean", "list", "dictionary"}
    assert ToolSchema.SUPPORTED_TYPES == expected_types, (
        "SUPPORTED_TYPES mismatch: {!r}".format(ToolSchema.SUPPORTED_TYPES)
    )

    return


def test_toolschema_type_map_constant():
    """
        ToolSchema.TYPE_MAP maps each supported type string to the correct
        Python built-in type.

        **Validates: Requirements 3.1**
    """
    expected_map = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "list": list,
        "dictionary": dict,
    }
    assert ToolSchema.TYPE_MAP == expected_map, (
        "TYPE_MAP mismatch: {!r}".format(ToolSchema.TYPE_MAP)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
