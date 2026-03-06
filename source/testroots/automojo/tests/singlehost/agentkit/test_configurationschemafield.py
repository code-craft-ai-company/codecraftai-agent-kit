"""
    Unit tests for the automojo.agentkit.configurationschemafield module.

    Tests the ConfigurationSchemaField immutable data type including constructor,
    type constraint validation, validate_value method, custom validation callable,
    serialization, deserialization, and string representations.
"""

import json

from automojo.agentkit.configurationschemafield import ConfigurationSchemaField
from automojo.agentkit.errors import SemanticError


# ---- Constructor Tests ----


def test_constructor_stores_field_path():
    """
        Verify that the constructor stores the field_path field correctly.
    """
    field = ConfigurationSchemaField(
        field_path="database.host",
        type_constraint="string",
    )
    stored_path = field.field_path
    assert stored_path == "database.host", "constructor should store the field_path"
    return


def test_constructor_stores_type_constraint():
    """
        Verify that the constructor stores the type_constraint field correctly.
    """
    field = ConfigurationSchemaField(
        field_path="server.port",
        type_constraint="integer",
    )
    stored_type = field.type_constraint
    assert stored_type == "integer", "constructor should store the type_constraint"
    return


def test_constructor_stores_required_default_true():
    """
        Verify that the constructor defaults required to True.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
    )
    stored_required = field.required
    assert stored_required is True, "constructor should default required to True"
    return


def test_constructor_stores_required_false():
    """
        Verify that the constructor stores required=False correctly.
    """
    field = ConfigurationSchemaField(
        field_path="app.debug",
        type_constraint="boolean",
        required=False,
    )
    stored_required = field.required
    assert stored_required is False, "constructor should store required=False"
    return


def test_constructor_stores_default_value():
    """
        Verify that the constructor stores the default_value field correctly.
    """
    field = ConfigurationSchemaField(
        field_path="app.timeout",
        type_constraint="integer",
        default_value=30,
    )
    stored_default = field.default_value
    assert stored_default == 30, "constructor should store the default_value"
    return


def test_constructor_stores_default_value_none():
    """
        Verify that the constructor defaults default_value to None.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
    )
    stored_default = field.default_value
    assert stored_default is None, "constructor should default default_value to None"
    return


def test_constructor_stores_description():
    """
        Verify that the constructor stores the description field correctly.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        description="The application name",
    )
    stored_desc = field.description
    assert stored_desc == "The application name", "constructor should store the description"
    return


def test_constructor_stores_description_default_empty():
    """
        Verify that the constructor defaults description to an empty string.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
    )
    stored_desc = field.description
    assert stored_desc == "", "constructor should default description to empty string"
    return


def test_constructor_stores_validation_callable():
    """
        Verify that the constructor stores the validation_callable field correctly.
    """
    def my_validator(value):
        return ""

    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        validation_callable=my_validator,
    )
    stored_callable = field.validation_callable
    assert stored_callable is my_validator, "constructor should store the validation_callable"
    return


def test_constructor_stores_validation_callable_default_none():
    """
        Verify that the constructor defaults validation_callable to None.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
    )
    stored_callable = field.validation_callable
    assert stored_callable is None, "constructor should default validation_callable to None"
    return


# ---- Constructor Invalid Type Constraint Tests ----


def test_constructor_raises_semantic_error_for_invalid_type():
    """
        Verify that the constructor raises SemanticError for an invalid type constraint.
    """
    raised = False
    try:
        ConfigurationSchemaField(
            field_path="app.name",
            type_constraint="invalid_type",
        )
    except SemanticError:
        raised = True

    assert raised is True, "constructor should raise SemanticError for invalid type constraint"
    return


def test_constructor_raises_semantic_error_message_contains_invalid_type():
    """
        Verify that the SemanticError message contains the invalid type name.
    """
    error_message = ""
    try:
        ConfigurationSchemaField(
            field_path="app.name",
            type_constraint="foobar",
        )
    except SemanticError as err:
        error_message = str(err)

    has_invalid_type = "foobar" in error_message
    assert has_invalid_type is True, "SemanticError message should contain the invalid type name"
    return


# ---- Valid Type Constraint Tests ----


def test_constructor_accepts_string_type():
    """
        Verify that the constructor accepts 'string' as a valid type constraint.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="string")
    stored_type = field.type_constraint
    assert stored_type == "string", "constructor should accept 'string' type constraint"
    return


def test_constructor_accepts_integer_type():
    """
        Verify that the constructor accepts 'integer' as a valid type constraint.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="integer")
    stored_type = field.type_constraint
    assert stored_type == "integer", "constructor should accept 'integer' type constraint"
    return


def test_constructor_accepts_float_type():
    """
        Verify that the constructor accepts 'float' as a valid type constraint.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="float")
    stored_type = field.type_constraint
    assert stored_type == "float", "constructor should accept 'float' type constraint"
    return


def test_constructor_accepts_boolean_type():
    """
        Verify that the constructor accepts 'boolean' as a valid type constraint.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="boolean")
    stored_type = field.type_constraint
    assert stored_type == "boolean", "constructor should accept 'boolean' type constraint"
    return


def test_constructor_accepts_list_type():
    """
        Verify that the constructor accepts 'list' as a valid type constraint.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="list")
    stored_type = field.type_constraint
    assert stored_type == "list", "constructor should accept 'list' type constraint"
    return


def test_constructor_accepts_dictionary_type():
    """
        Verify that the constructor accepts 'dictionary' as a valid type constraint.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="dictionary")
    stored_type = field.type_constraint
    assert stored_type == "dictionary", "constructor should accept 'dictionary' type constraint"
    return


# ---- validate_value Tests ----


def test_validate_value_returns_empty_list_for_matching_string():
    """
        Verify that validate_value returns an empty list when a string value
        matches the 'string' type constraint.
    """
    field = ConfigurationSchemaField(field_path="app.name", type_constraint="string")
    errors = field.validate_value("hello")
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list for matching string type"
    return


def test_validate_value_returns_empty_list_for_matching_integer():
    """
        Verify that validate_value returns an empty list when an integer value
        matches the 'integer' type constraint.
    """
    field = ConfigurationSchemaField(field_path="app.port", type_constraint="integer")
    errors = field.validate_value(8080)
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list for matching integer type"
    return


def test_validate_value_returns_empty_list_for_matching_float():
    """
        Verify that validate_value returns an empty list when a float value
        matches the 'float' type constraint.
    """
    field = ConfigurationSchemaField(field_path="app.rate", type_constraint="float")
    errors = field.validate_value(3.14)
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list for matching float type"
    return


def test_validate_value_returns_empty_list_for_matching_boolean():
    """
        Verify that validate_value returns an empty list when a boolean value
        matches the 'boolean' type constraint.
    """
    field = ConfigurationSchemaField(field_path="app.debug", type_constraint="boolean")
    errors = field.validate_value(True)
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list for matching boolean type"
    return


def test_validate_value_returns_empty_list_for_matching_list():
    """
        Verify that validate_value returns an empty list when a list value
        matches the 'list' type constraint.
    """
    field = ConfigurationSchemaField(field_path="app.items", type_constraint="list")
    errors = field.validate_value([1, 2, 3])
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list for matching list type"
    return


def test_validate_value_returns_empty_list_for_matching_dictionary():
    """
        Verify that validate_value returns an empty list when a dict value
        matches the 'dictionary' type constraint.
    """
    field = ConfigurationSchemaField(field_path="app.settings", type_constraint="dictionary")
    errors = field.validate_value({"key": "value"})
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list for matching dictionary type"
    return


def test_validate_value_returns_error_for_mismatching_type():
    """
        Verify that validate_value returns an error when an integer value
        is provided for a 'string' type constraint.
    """
    field = ConfigurationSchemaField(field_path="app.name", type_constraint="string")
    errors = field.validate_value(42)
    error_count = len(errors)
    assert error_count > 0, "validate_value should return errors for mismatching type"
    return


def test_validate_value_error_contains_field_path():
    """
        Verify that the type mismatch error string contains the field path.
    """
    field = ConfigurationSchemaField(field_path="database.host", type_constraint="string")
    errors = field.validate_value(123)
    first_error = errors[0]
    has_field_path = "database.host" in first_error
    assert has_field_path is True, "type mismatch error should contain the field path"
    return


def test_validate_value_error_contains_expected_type():
    """
        Verify that the type mismatch error string contains the expected type.
    """
    field = ConfigurationSchemaField(field_path="app.port", type_constraint="string")
    errors = field.validate_value(8080)
    first_error = errors[0]
    has_expected_type = "string" in first_error
    assert has_expected_type is True, "type mismatch error should contain the expected type"
    return


def test_validate_value_error_contains_actual_type():
    """
        Verify that the type mismatch error string contains the actual type name.
    """
    field = ConfigurationSchemaField(field_path="app.name", type_constraint="string")
    errors = field.validate_value(42)
    first_error = errors[0]
    has_actual_type = "int" in first_error
    assert has_actual_type is True, "type mismatch error should contain the actual type name"
    return


# ---- validate_value with Custom Validation Callable Tests ----


def test_validate_value_with_callable_returning_error():
    """
        Verify that validate_value includes the custom validation error
        when the callable returns a non-empty string.
    """
    def must_start_with_a(value):
        if isinstance(value, str) and value.startswith("a") is False:
            return "Value must start with 'a'"
        return ""

    field = ConfigurationSchemaField(
        field_path="app.prefix",
        type_constraint="string",
        validation_callable=must_start_with_a,
    )
    errors = field.validate_value("hello")
    error_count = len(errors)
    assert error_count == 1, "validate_value should include custom validation error"

    first_error = errors[0]
    has_custom_msg = "must start with" in first_error
    assert has_custom_msg is True, "error should contain the custom validation message"
    return


def test_validate_value_with_callable_returning_empty_string():
    """
        Verify that validate_value returns an empty list when the custom
        validation callable returns an empty string (no error).
    """
    def always_valid(value):
        return ""

    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        validation_callable=always_valid,
    )
    errors = field.validate_value("hello")
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list when callable returns empty string"
    return


def test_validate_value_with_callable_returning_none():
    """
        Verify that validate_value returns an empty list when the custom
        validation callable returns None.
    """
    def returns_none(value):
        return None

    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        validation_callable=returns_none,
    )
    errors = field.validate_value("hello")
    error_count = len(errors)
    assert error_count == 0, "validate_value should return empty list when callable returns None"
    return


def test_validate_value_type_mismatch_and_callable_error_combined():
    """
        Verify that validate_value returns both type mismatch and custom
        validation errors when both conditions are met.
    """
    def always_error(value):
        return "custom error"

    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        validation_callable=always_error,
    )
    errors = field.validate_value(42)
    error_count = len(errors)
    assert error_count == 2, "validate_value should return both type mismatch and custom errors"
    return


# ---- as_dict Tests ----


def test_as_dict_excludes_validation_callable():
    """
        Verify that as_dict does not include the validation_callable field.
    """
    def my_validator(value):
        return ""

    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        description="The name",
        validation_callable=my_validator,
    )
    result = field.as_dict()
    has_callable = "validation_callable" in result
    assert has_callable is False, "as_dict should exclude validation_callable"
    return


def test_as_dict_contains_all_expected_keys():
    """
        Verify that as_dict returns a dictionary with all expected keys.
    """
    field = ConfigurationSchemaField(
        field_path="db.port",
        type_constraint="integer",
        required=False,
        default_value=5432,
        description="Database port",
    )
    result = field.as_dict()

    result_path = result["field_path"]
    result_type = result["type_constraint"]
    result_required = result["required"]
    result_default = result["default_value"]
    result_desc = result["description"]

    assert result_path == "db.port", "as_dict field_path should match"
    assert result_type == "integer", "as_dict type_constraint should match"
    assert result_required is False, "as_dict required should match"
    assert result_default == 5432, "as_dict default_value should match"
    assert result_desc == "Database port", "as_dict description should match"
    return


# ---- to_json Tests ----


def test_to_json_returns_valid_json_string():
    """
        Verify that to_json returns a valid JSON string that can be parsed.
    """
    field = ConfigurationSchemaField(
        field_path="app.debug",
        type_constraint="boolean",
        required=True,
        default_value=False,
        description="Enable debug mode",
    )
    json_str = field.to_json()
    parsed = json.loads(json_str)

    parsed_path = parsed["field_path"]
    parsed_type = parsed["type_constraint"]

    assert parsed_path == "app.debug", "to_json field_path should match after parsing"
    assert parsed_type == "boolean", "to_json type_constraint should match after parsing"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs a ConfigurationSchemaField with equivalent fields.
    """
    data = {
        "field_path": "cache.ttl",
        "type_constraint": "integer",
        "required": False,
        "default_value": 300,
        "description": "Cache time-to-live in seconds",
    }
    field = ConfigurationSchemaField.from_dict(data)

    field_path = field.field_path
    field_type = field.type_constraint
    field_required = field.required
    field_default = field.default_value
    field_desc = field.description

    assert field_path == "cache.ttl", "from_dict should reconstruct field_path"
    assert field_type == "integer", "from_dict should reconstruct type_constraint"
    assert field_required is False, "from_dict should reconstruct required"
    assert field_default == 300, "from_dict should reconstruct default_value"
    assert field_desc == "Cache time-to-live in seconds", "from_dict should reconstruct description"
    return


def test_from_dict_defaults_optional_fields():
    """
        Verify that from_dict uses defaults for optional fields not present in the dict.
    """
    data = {
        "field_path": "app.name",
        "type_constraint": "string",
    }
    field = ConfigurationSchemaField.from_dict(data)

    field_required = field.required
    field_default = field.default_value
    field_desc = field.description

    assert field_required is True, "from_dict should default required to True"
    assert field_default is None, "from_dict should default default_value to None"
    assert field_desc == "", "from_dict should default description to empty string"
    return


# ---- Round-Trip Tests ----


def test_to_json_from_dict_round_trip():
    """
        Verify that to_json followed by parsing and from_dict produces
        an equivalent ConfigurationSchemaField.
    """
    original = ConfigurationSchemaField(
        field_path="server.host",
        type_constraint="string",
        required=True,
        default_value="localhost",
        description="Server hostname",
    )
    json_str = original.to_json()
    parsed_data = json.loads(json_str)
    reconstructed = ConfigurationSchemaField.from_dict(parsed_data)

    assert reconstructed.field_path == original.field_path, "round-trip field_path should match"
    assert reconstructed.type_constraint == original.type_constraint, "round-trip type_constraint should match"
    assert reconstructed.required == original.required, "round-trip required should match"
    assert reconstructed.default_value == original.default_value, "round-trip default_value should match"
    assert reconstructed.description == original.description, "round-trip description should match"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'ConfigurationSchemaField'.
    """
    field = ConfigurationSchemaField(field_path="a.b", type_constraint="string")
    repr_str = repr(field)
    has_class_name = "ConfigurationSchemaField" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_field_path():
    """
        Verify that __repr__ contains the field path.
    """
    field = ConfigurationSchemaField(field_path="my.special.path", type_constraint="integer")
    repr_str = repr(field)
    has_field_path = "my.special.path" in repr_str
    assert has_field_path is True, "repr should contain the field path"
    return


def test_repr_contains_type_constraint():
    """
        Verify that __repr__ contains the type constraint.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="boolean")
    repr_str = repr(field)
    has_type = "boolean" in repr_str
    assert has_type is True, "repr should contain the type constraint"
    return


def test_repr_contains_required():
    """
        Verify that __repr__ contains the required flag value.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="string", required=False)
    repr_str = repr(field)
    has_required = "False" in repr_str
    assert has_required is True, "repr should contain the required flag value"
    return


# ---- __str__ Tests ----


def test_str_contains_field_path():
    """
        Verify that __str__ contains the field path.
    """
    field = ConfigurationSchemaField(
        field_path="db.connection.pool",
        type_constraint="integer",
        description="Connection pool size",
    )
    str_val = str(field)
    has_field_path = "db.connection.pool" in str_val
    assert has_field_path is True, "str should contain the field path"
    return


def test_str_contains_type():
    """
        Verify that __str__ contains the type constraint.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        description="Application name",
    )
    str_val = str(field)
    has_type = "string" in str_val
    assert has_type is True, "str should contain the type constraint"
    return


def test_str_contains_description():
    """
        Verify that __str__ contains the description.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        description="The application name",
    )
    str_val = str(field)
    has_desc = "The application name" in str_val
    assert has_desc is True, "str should contain the description"
    return
