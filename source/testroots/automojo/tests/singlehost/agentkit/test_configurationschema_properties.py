"""
    Property-based tests for the automojo.agentkit.configurationschema module.

    Uses the automojo.testbase.properties engine to verify that ConfigurationSchema instances
    survive a JSON round-trip (to_json followed by from_json) with all fields
    preserved, and that schema validation correctly detects type mismatches.

    **Validates: Requirement 5 AC 12, Requirement 5 AC 1, Requirement 5 AC 2**
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.configurationschema import ConfigurationSchema
from automojo.agentkit.configurationschemafield import ConfigurationSchemaField


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_type_constraint_strategy = st.sampled_from([
    "string", "integer", "float", "boolean", "list", "dictionary",
])

_default_value_strategy = st.one_of(
    st.text(),
    st.integers(),
    st.booleans(),
    st.floats(),
    st.none(),
)


@composite
def _schema_field_strategy(draw):
    """
        Generates a random ConfigurationSchemaField with valid parameters.
    """
    field_path = draw(st.text(min_size=1, max_size=30))
    type_constraint = draw(_type_constraint_strategy)
    required = draw(st.booleans())
    default_value = draw(_default_value_strategy)
    description = draw(st.text(min_size=0, max_size=50))

    field = ConfigurationSchemaField(
        field_path=field_path,
        type_constraint=type_constraint,
        required=required,
        default_value=default_value,
        description=description,
    )
    return field


# ---------------------------------------------------------------------------
# Property 2: ConfigurationSchema JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    name=st.text(min_size=0, max_size=50),
    fields=st.lists(_schema_field_strategy(), max_size=10),
    settings=settings(max_examples=50),
)
def test_configurationschema_json_round_trip(name, fields):
    """
        **Validates: Requirement 5 AC 12**

        FOR ALL valid ConfigurationSchema instances, calling to_json and then
        from_json SHALL produce an equivalent ConfigurationSchema object with
        the same name and field_count, and each field SHALL have the same
        field_path, type_constraint, required, default_value, and description.
    """
    original = ConfigurationSchema(name=name, fields=fields)

    json_str = original.to_json()
    reconstructed = ConfigurationSchema.from_json(json_str)

    reconstructed_name = reconstructed.name
    assert reconstructed_name == name, (
        "Round-trip name mismatch: expected {!r}, got {!r}".format(
            name, reconstructed_name)
    )

    reconstructed_field_count = reconstructed.field_count
    original_field_count = original.field_count
    assert reconstructed_field_count == original_field_count, (
        "Round-trip field_count mismatch: expected {}, got {}".format(
            original_field_count, reconstructed_field_count)
    )

    original_fields = original.fields
    reconstructed_fields = reconstructed.fields

    for idx in range(original_field_count):
        original_field = original_fields[idx]
        reconstructed_field = reconstructed_fields[idx]

        reconstructed_field_path = reconstructed_field.field_path
        original_field_path = original_field.field_path
        assert reconstructed_field_path == original_field_path, (
            "Round-trip field[{}].field_path mismatch: expected {!r}, got {!r}".format(
                idx, original_field_path, reconstructed_field_path)
        )

        reconstructed_type_constraint = reconstructed_field.type_constraint
        original_type_constraint = original_field.type_constraint
        assert reconstructed_type_constraint == original_type_constraint, (
            "Round-trip field[{}].type_constraint mismatch: expected {!r}, got {!r}".format(
                idx, original_type_constraint, reconstructed_type_constraint)
        )

        reconstructed_required = reconstructed_field.required
        original_required = original_field.required
        assert reconstructed_required == original_required, (
            "Round-trip field[{}].required mismatch: expected {!r}, got {!r}".format(
                idx, original_required, reconstructed_required)
        )

        reconstructed_default_value = reconstructed_field.default_value
        original_default_value = original_field.default_value
        assert reconstructed_default_value == original_default_value, (
            "Round-trip field[{}].default_value mismatch: expected {!r}, got {!r}".format(
                idx, original_default_value, reconstructed_default_value)
        )

        reconstructed_description = reconstructed_field.description
        original_description = original_field.description
        assert reconstructed_description == original_description, (
            "Round-trip field[{}].description mismatch: expected {!r}, got {!r}".format(
                idx, original_description, reconstructed_description)
        )

    return


# ---------------------------------------------------------------------------
# Property 12: Schema Validation Type Mismatch Detection
# ---------------------------------------------------------------------------

def _build_nested_config(field_path, value):
    """
        Builds a nested configuration dictionary from a dot-separated field path
        and a value. For example, field_path="a.b.c" and value=42 produces
        {"a": {"b": {"c": 42}}}.

        :param field_path: The dot-separated field path string.
        :param value: The value to place at the leaf.

        :returns: A nested dictionary with the value at the correct path.
    """
    parts = field_path.split(".")
    config = {}
    current = config

    for idx in range(len(parts) - 1):
        part = parts[idx]
        nested = {}
        current[part] = nested
        current = nested

    last_part = parts[-1]
    current[last_part] = value

    return config


@given(
    field_path=st.text(min_size=1, max_size=30),
    mismatched_value=st.integers(),
    description=st.text(min_size=0, max_size=50),
    settings=settings(max_examples=50),
)
def test_schema_validation_type_mismatch_detection(field_path, mismatched_value, description):
    """
        **Validates: Requirement 5 AC 1, Requirement 5 AC 2**

        FOR ALL configuration dictionaries where a field value does not match
        the declared type constraint, the validate method SHALL return a
        ConfigurationValidationResult with is_valid=False and at least one
        error string.

        This test generates a ConfigurationSchemaField with type_constraint="string"
        and provides an integer value, which is always a type mismatch.
    """
    field = ConfigurationSchemaField(
        field_path=field_path,
        type_constraint="string",
        required=True,
        default_value=None,
        description=description,
    )

    schema = ConfigurationSchema(name="test-schema", fields=[field])

    config = _build_nested_config(field_path, mismatched_value)

    result = schema.validate(config)

    result_is_valid = result.is_valid
    assert result_is_valid is False, (
        "Expected is_valid=False for type mismatch, got is_valid=True. "
        "field_path={!r}, type_constraint='string', value={!r}".format(
            field_path, mismatched_value)
    )

    error_count = len(result.errors)
    assert error_count > 0, (
        "Expected at least one error for type mismatch, got 0 errors. "
        "field_path={!r}, type_constraint='string', value={!r}".format(
            field_path, mismatched_value)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
