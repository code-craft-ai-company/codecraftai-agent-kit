"""
    Unit tests for the automojo.agentkit.configurationschema module.

    Tests the ConfigurationSchema class including constructor, add_field,
    get_field, validate method, serialization, deserialization, and
    string representations.

    Requirements: 5.1, 5.3, 5.4, 5.5, 5.6, 5.7
"""

import json

from automojo.agentkit.configurationschema import ConfigurationSchema
from automojo.agentkit.configurationschemafield import ConfigurationSchemaField


# ---- Constructor Tests ----


def test_constructor_stores_name():
    """
        Verify that the constructor stores the name field correctly.
    """
    schema = ConfigurationSchema(name="agent-config")
    stored_name = schema.name
    assert stored_name == "agent-config", "constructor should store the name field"
    return


def test_constructor_stores_fields():
    """
        Verify that the constructor stores the fields list correctly.
    """
    field = ConfigurationSchemaField(field_path="app.name", type_constraint="string")
    schema = ConfigurationSchema(name="test-schema", fields=[field])
    stored_fields = schema.fields
    field_count = len(stored_fields)
    assert field_count == 1, "constructor should store the fields list"
    return


def test_constructor_defaults_fields_to_empty_list():
    """
        Verify that the constructor defaults fields to an empty list when not provided.
    """
    schema = ConfigurationSchema(name="empty-schema")
    stored_fields = schema.fields
    field_count = len(stored_fields)
    assert field_count == 0, "constructor should default fields to an empty list"
    return


# ---- Read-Only Property Tests ----


def test_name_property_returns_expected_value():
    """
        Verify that the name property returns the expected value.
    """
    schema = ConfigurationSchema(name="my-schema")
    name_value = schema.name
    assert name_value == "my-schema", "name property should return the expected value"
    return


def test_fields_property_returns_defensive_copy():
    """
        Verify that the fields property returns a defensive copy.
    """
    field = ConfigurationSchemaField(field_path="a.b", type_constraint="string")
    schema = ConfigurationSchema(name="copy-schema", fields=[field])
    first_copy = schema.fields
    first_copy.append("injected")
    second_copy = schema.fields
    second_count = len(second_copy)
    assert second_count == 1, "fields property should return a defensive copy"
    return


def test_field_count_returns_correct_count():
    """
        Verify that the field_count property returns the correct count.
    """
    field_a = ConfigurationSchemaField(field_path="a", type_constraint="string")
    field_b = ConfigurationSchemaField(field_path="b", type_constraint="integer")
    schema = ConfigurationSchema(name="count-schema", fields=[field_a, field_b])
    count = schema.field_count
    assert count == 2, "field_count should return the correct count"
    return


# ---- add_field Tests ----


def test_add_field_increases_field_count():
    """
        Verify that add_field increases the field count by one.
    """
    schema = ConfigurationSchema(name="add-schema")
    field = ConfigurationSchemaField(field_path="app.debug", type_constraint="boolean")
    schema.add_field(field)
    count = schema.field_count
    assert count == 1, "add_field should increase the field count"
    return


def test_add_field_makes_field_retrievable():
    """
        Verify that a field added via add_field is retrievable via get_field.
    """
    schema = ConfigurationSchema(name="retrieve-schema")
    field = ConfigurationSchemaField(field_path="db.host", type_constraint="string")
    schema.add_field(field)
    retrieved = schema.get_field("db.host")
    retrieved_path = retrieved.field_path
    assert retrieved_path == "db.host", "add_field should make the field retrievable via get_field"
    return


# ---- get_field Tests ----


def test_get_field_returns_matching_field():
    """
        Verify that get_field returns the field matching the given path.
    """
    field = ConfigurationSchemaField(field_path="server.port", type_constraint="integer")
    schema = ConfigurationSchema(name="get-schema", fields=[field])
    result = schema.get_field("server.port")
    result_path = result.field_path
    assert result_path == "server.port", "get_field should return the matching field"
    return


def test_get_field_returns_none_for_unknown_path():
    """
        Verify that get_field returns None when the field path is not defined.
    """
    schema = ConfigurationSchema(name="none-schema")
    result = schema.get_field("nonexistent.path")
    assert result is None, "get_field should return None for unknown field path"
    return


# ---- validate Tests ----


def test_validate_returns_valid_result_for_valid_config():
    """
        Verify that validate returns a valid result when the configuration
        satisfies all schema fields.
    """
    field = ConfigurationSchemaField(field_path="app.name", type_constraint="string")
    schema = ConfigurationSchema(name="valid-schema", fields=[field])
    config = {"app": {"name": "my-agent"}}
    result = schema.validate(config)
    is_valid = result.is_valid
    assert is_valid is True, "validate should return valid result for valid config"
    return


def test_validate_returns_errors_for_missing_required_field():
    """
        Verify that validate returns errors when a required field is missing.
    """
    field = ConfigurationSchemaField(
        field_path="app.name",
        type_constraint="string",
        required=True,
    )
    schema = ConfigurationSchema(name="missing-schema", fields=[field])
    config = {}
    result = schema.validate(config)
    is_valid = result.is_valid
    error_count = len(result.errors)
    assert is_valid is False, "validate should return invalid result for missing required field"
    assert error_count > 0, "validate should return at least one error for missing required field"
    return


def test_validate_error_message_contains_field_path_for_missing_field():
    """
        Verify that the error message for a missing required field contains
        the field path.
    """
    field = ConfigurationSchemaField(
        field_path="database.host",
        type_constraint="string",
        required=True,
    )
    schema = ConfigurationSchema(name="msg-schema", fields=[field])
    config = {}
    result = schema.validate(config)
    first_error = result.errors[0]
    has_path = "database.host" in first_error
    assert has_path is True, "error message should contain the field path"
    return


def test_validate_returns_errors_for_type_mismatch():
    """
        Verify that validate returns errors when a field value has the wrong type.
    """
    field = ConfigurationSchemaField(field_path="app.port", type_constraint="integer")
    schema = ConfigurationSchema(name="type-schema", fields=[field])
    config = {"app": {"port": "not-an-integer"}}
    result = schema.validate(config)
    is_valid = result.is_valid
    error_count = len(result.errors)
    assert is_valid is False, "validate should return invalid result for type mismatch"
    assert error_count > 0, "validate should return at least one error for type mismatch"
    return


def test_validate_skips_optional_missing_field():
    """
        Verify that validate does not report errors for optional fields
        that are missing from the configuration.
    """
    field = ConfigurationSchemaField(
        field_path="app.debug",
        type_constraint="boolean",
        required=False,
    )
    schema = ConfigurationSchema(name="optional-schema", fields=[field])
    config = {}
    result = schema.validate(config)
    is_valid = result.is_valid
    assert is_valid is True, "validate should not report errors for optional missing fields"
    return


def test_validate_with_multiple_fields_reports_all_errors():
    """
        Verify that validate reports errors for all invalid fields,
        not just the first one.
    """
    field_a = ConfigurationSchemaField(field_path="a", type_constraint="string", required=True)
    field_b = ConfigurationSchemaField(field_path="b", type_constraint="integer", required=True)
    schema = ConfigurationSchema(name="multi-schema", fields=[field_a, field_b])
    config = {}
    result = schema.validate(config)
    error_count = len(result.errors)
    assert error_count == 2, "validate should report errors for all invalid fields"
    return


# ---- as_dict Tests ----


def test_as_dict_contains_name():
    """
        Verify that as_dict returns a dictionary containing the schema name.
    """
    schema = ConfigurationSchema(name="dict-schema")
    result = schema.as_dict()
    result_name = result["name"]
    assert result_name == "dict-schema", "as_dict should contain the schema name"
    return


def test_as_dict_contains_fields():
    """
        Verify that as_dict returns a dictionary containing the fields list.
    """
    field = ConfigurationSchemaField(field_path="x", type_constraint="string")
    schema = ConfigurationSchema(name="fields-schema", fields=[field])
    result = schema.as_dict()
    fields_list = result["fields"]
    fields_count = len(fields_list)
    assert fields_count == 1, "as_dict should contain the fields list"
    return


# ---- to_json Tests ----


def test_to_json_returns_valid_json_string():
    """
        Verify that to_json returns a valid JSON string that can be parsed.
    """
    field = ConfigurationSchemaField(field_path="app.name", type_constraint="string")
    schema = ConfigurationSchema(name="json-schema", fields=[field])
    json_str = schema.to_json()
    parsed = json.loads(json_str)
    parsed_name = parsed["name"]
    assert parsed_name == "json-schema", "to_json should produce valid parseable JSON"
    return


# ---- from_dict and from_json Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs a ConfigurationSchema with equivalent fields.
    """
    data = {
        "name": "reconstructed-schema",
        "fields": [
            {"field_path": "a.b", "type_constraint": "string", "required": True,
             "default_value": None, "description": "test field"},
        ],
    }
    schema = ConfigurationSchema.from_dict(data)
    schema_name = schema.name
    schema_count = schema.field_count
    assert schema_name == "reconstructed-schema", "from_dict should reconstruct the name"
    assert schema_count == 1, "from_dict should reconstruct the fields"
    return


def test_from_json_reconstructs_equivalent_object():
    """
        Verify that from_json reconstructs a ConfigurationSchema with equivalent fields.
    """
    json_str = json.dumps({
        "name": "json-reconstructed",
        "fields": [
            {"field_path": "x.y", "type_constraint": "integer", "required": False,
             "default_value": 42, "description": ""},
        ],
    })
    schema = ConfigurationSchema.from_json(json_str)
    schema_name = schema.name
    first_field = schema.get_field("x.y")
    first_field_type = first_field.type_constraint
    assert schema_name == "json-reconstructed", "from_json should reconstruct the name"
    assert first_field_type == "integer", "from_json should reconstruct field type_constraint"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'ConfigurationSchema'.
    """
    schema = ConfigurationSchema(name="repr-schema")
    repr_str = repr(schema)
    has_class_name = "ConfigurationSchema" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_schema_name():
    """
        Verify that __repr__ contains the schema name.
    """
    schema = ConfigurationSchema(name="my-special-schema")
    repr_str = repr(schema)
    has_name = "my-special-schema" in repr_str
    assert has_name is True, "repr should contain the schema name"
    return


def test_repr_contains_field_count():
    """
        Verify that __repr__ contains the field count.
    """
    field = ConfigurationSchemaField(field_path="a", type_constraint="string")
    schema = ConfigurationSchema(name="count-repr", fields=[field])
    repr_str = repr(schema)
    has_count = "1" in repr_str
    assert has_count is True, "repr should contain the field count"
    return


# ---- __str__ Tests ----


def test_str_contains_schema_name():
    """
        Verify that __str__ contains the schema name.
    """
    schema = ConfigurationSchema(name="str-schema")
    str_val = str(schema)
    has_name = "str-schema" in str_val
    assert has_name is True, "str should contain the schema name"
    return


def test_str_contains_field_count():
    """
        Verify that __str__ contains the field count.
    """
    field_a = ConfigurationSchemaField(field_path="a", type_constraint="string")
    field_b = ConfigurationSchemaField(field_path="b", type_constraint="integer")
    schema = ConfigurationSchema(name="str-count", fields=[field_a, field_b])
    str_val = str(schema)
    has_count = "2" in str_val
    assert has_count is True, "str should contain the field count"
    return
