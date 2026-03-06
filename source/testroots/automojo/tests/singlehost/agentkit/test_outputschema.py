"""
    Unit tests for the automojo.agentkit.outputschema module.

    Tests OutputSchema construction, field definitions, validation,
    serialization (as_dict, to_json, from_dict, from_json), and equality.

    Feature: llm-integration, Task 11.6
    **Validates: Requirements 8.10, 8.11, 8.12, 8.13, 8.14, 8.15, 8.16, 8.17**
"""

import json

from automojo.agentkit.outputschema import OutputSchema


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_construction_with_mixed_fields():
    """
        OutputSchema constructed with mixed required and optional fields
        stores all field definitions.

        **Validates: Requirements 8.10, 8.11**
    """
    fields = [
        {"name": "title", "type": "string", "required": True},
        {"name": "count", "type": "integer", "required": True},
        {"name": "notes", "type": "string", "required": False},
    ]

    schema = OutputSchema(fields=fields)

    assert len(schema.fields) == 3, (
        "Expected 3 fields, got: {}".format(len(schema.fields))
    )

    return


def test_construction_with_empty_fields():
    """
        OutputSchema constructed with an empty fields list has no fields.

        **Validates: Requirements 8.10**
    """
    schema = OutputSchema(fields=[])

    assert schema.fields == [], (
        "Expected empty fields list, got: {!r}".format(schema.fields)
    )

    return


def test_construction_with_none_fields():
    """
        OutputSchema constructed with None defaults to empty fields list.

        **Validates: Requirements 8.10**
    """
    schema = OutputSchema(fields=None)

    assert schema.fields == [], (
        "Expected empty fields list when None, got: {!r}".format(schema.fields)
    )

    return


def test_fields_returns_copy():
    """
        The fields property returns a copy of the internal list.

        **Validates: Requirements 8.10**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
    ]

    schema = OutputSchema(fields=fields)
    result = schema.fields

    result.append({"name": "extra", "type": "integer", "required": False})

    assert len(schema.fields) == 1, (
        "Modifying returned list should not affect internal state"
    )

    return


# ---------------------------------------------------------------------------
# Validation - correct objects
# ---------------------------------------------------------------------------


def test_validate_correct_object_all_required():
    """
        Validating a correct object with all required fields returns
        an empty error list.

        **Validates: Requirements 8.10, 8.11, 8.12**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "age", "type": "integer", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({"name": "Alice", "age": 30})

    assert errors == [], (
        "Expected no errors for valid object, got: {!r}".format(errors)
    )

    return


def test_validate_correct_object_with_optional_present():
    """
        Validating an object with all required and optional fields present
        returns an empty error list.

        **Validates: Requirements 8.10, 8.11, 8.12**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "notes", "type": "string", "required": False},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({"name": "Alice", "notes": "some notes"})

    assert errors == [], (
        "Expected no errors, got: {!r}".format(errors)
    )

    return


def test_validate_correct_object_with_optional_absent():
    """
        Validating an object with optional fields absent returns
        an empty error list.

        **Validates: Requirements 8.10, 8.11, 8.12**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "notes", "type": "string", "required": False},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({"name": "Alice"})

    assert errors == [], (
        "Expected no errors when optional field absent, got: {!r}".format(errors)
    )

    return


def test_validate_all_supported_types():
    """
        Validating an object with all supported types returns no errors.

        **Validates: Requirements 8.10, 8.12**
    """
    fields = [
        {"name": "s", "type": "string", "required": True},
        {"name": "i", "type": "integer", "required": True},
        {"name": "f", "type": "float", "required": True},
        {"name": "b", "type": "boolean", "required": True},
        {"name": "l", "type": "list", "required": True},
        {"name": "d", "type": "dictionary", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({
        "s": "hello",
        "i": 42,
        "f": 3.14,
        "b": True,
        "l": [1, 2, 3],
        "d": {"key": "value"},
    })

    assert errors == [], (
        "Expected no errors for all supported types, got: {!r}".format(errors)
    )

    return


# ---------------------------------------------------------------------------
# Validation - missing required fields
# ---------------------------------------------------------------------------


def test_validate_missing_required_field():
    """
        Validating an object missing a required field returns an error.

        **Validates: Requirements 8.10, 8.11, 8.12**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "age", "type": "integer", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({"name": "Alice"})

    assert len(errors) == 1, (
        "Expected 1 error for missing required field, got: {}".format(len(errors))
    )
    assert "age" in errors[0], (
        "Error should mention the missing field 'age', got: {!r}".format(errors[0])
    )

    return


def test_validate_multiple_missing_required_fields():
    """
        Validating an object missing multiple required fields returns
        multiple errors.

        **Validates: Requirements 8.10, 8.11, 8.12**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "age", "type": "integer", "required": True},
        {"name": "active", "type": "boolean", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({})

    assert len(errors) == 3, (
        "Expected 3 errors for 3 missing required fields, got: {}".format(len(errors))
    )

    return


# ---------------------------------------------------------------------------
# Validation - type mismatches
# ---------------------------------------------------------------------------


def test_validate_type_mismatch_string():
    """
        Validating an object with a type mismatch returns an error.

        **Validates: Requirements 8.10, 8.12**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({"name": 42})

    assert len(errors) == 1, (
        "Expected 1 type mismatch error, got: {}".format(len(errors))
    )
    assert "name" in errors[0], (
        "Error should mention field 'name', got: {!r}".format(errors[0])
    )

    return


def test_validate_type_mismatch_integer():
    """
        Validating a string where integer is expected returns an error.

        **Validates: Requirements 8.10, 8.12**
    """
    fields = [
        {"name": "count", "type": "integer", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate({"count": "not-a-number"})

    assert len(errors) == 1, (
        "Expected 1 type mismatch error, got: {}".format(len(errors))
    )

    return


def test_validate_non_dict_input():
    """
        Validating a non-dictionary input returns an error.

        **Validates: Requirements 8.12**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    errors = schema.validate("not a dict")

    assert len(errors) == 1, (
        "Expected 1 error for non-dict input, got: {}".format(len(errors))
    )
    assert "dictionary" in errors[0].lower() or "dict" in errors[0].lower(), (
        "Error should mention dictionary, got: {!r}".format(errors[0])
    )

    return


def test_validate_empty_schema_accepts_any_dict():
    """
        An empty schema validates any dictionary as valid.

        **Validates: Requirements 8.12**
    """
    schema = OutputSchema(fields=[])

    errors = schema.validate({"anything": "goes"})

    assert errors == [], (
        "Empty schema should accept any dict, got: {!r}".format(errors)
    )

    return


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_as_dict():
    """
        as_dict returns a dictionary with the fields key.

        **Validates: Requirements 8.13**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    result = schema.as_dict()

    assert "fields" in result, "as_dict should contain 'fields' key"
    assert len(result["fields"]) == 1, (
        "Expected 1 field in as_dict, got: {}".format(len(result["fields"]))
    )

    return


def test_to_json():
    """
        to_json returns a valid JSON string.

        **Validates: Requirements 8.14**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
    ]
    schema = OutputSchema(fields=fields)

    json_str = schema.to_json()
    parsed = json.loads(json_str)

    assert "fields" in parsed, "JSON should contain 'fields' key"

    return


def test_from_dict():
    """
        from_dict constructs an OutputSchema from a dictionary.

        **Validates: Requirements 8.15**
    """
    data = {
        "fields": [
            {"name": "name", "type": "string", "required": True},
        ]
    }

    schema = OutputSchema.from_dict(data)

    assert len(schema.fields) == 1, (
        "Expected 1 field from from_dict, got: {}".format(len(schema.fields))
    )

    return


def test_from_json():
    """
        from_json constructs an OutputSchema from a JSON string.

        **Validates: Requirements 8.16**
    """
    data = {
        "fields": [
            {"name": "name", "type": "string", "required": True},
            {"name": "count", "type": "integer", "required": False},
        ]
    }
    json_str = json.dumps(data)

    schema = OutputSchema.from_json(json_str)

    assert len(schema.fields) == 2, (
        "Expected 2 fields from from_json, got: {}".format(len(schema.fields))
    )

    return


def test_json_round_trip():
    """
        to_json followed by from_json produces an equivalent OutputSchema.

        **Validates: Requirements 8.17**
    """
    fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "score", "type": "float", "required": False},
    ]
    original = OutputSchema(fields=fields)

    json_str = original.to_json()
    restored = OutputSchema.from_json(json_str)

    assert original == restored, (
        "Round-trip should produce equal OutputSchema"
    )

    return


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------


def test_eq_same_fields():
    """
        Two OutputSchema instances with the same fields are equal.

        **Validates: Requirements 8.17**
    """
    fields = [{"name": "x", "type": "string", "required": True}]

    schema_a = OutputSchema(fields=fields)
    schema_b = OutputSchema(fields=fields)

    assert schema_a == schema_b, "Schemas with same fields should be equal"

    return


def test_eq_different_fields():
    """
        Two OutputSchema instances with different fields are not equal.

        **Validates: Requirements 8.17**
    """
    schema_a = OutputSchema(fields=[{"name": "x", "type": "string", "required": True}])
    schema_b = OutputSchema(fields=[{"name": "y", "type": "integer", "required": False}])

    assert schema_a != schema_b, "Schemas with different fields should not be equal"

    return


def test_eq_non_outputschema():
    """
        An OutputSchema is not equal to a non-OutputSchema object.

        **Validates: Requirements 8.17**
    """
    schema = OutputSchema(fields=[])

    assert schema != "not a schema", (
        "OutputSchema should not be equal to a string"
    )

    return
