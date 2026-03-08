"""
    Property-based tests for the automojo.agentkit.configurationschemafield module.

    Uses the automojo.testbase.properties engine to verify that ConfigurationSchemaField instances
    survive a JSON round-trip (to_json followed by from_dict on the parsed JSON)
    with all serializable fields preserved.

    **Validates: Requirement 6 AC 10**
"""

import json

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

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


# ---------------------------------------------------------------------------
# Property 3: ConfigurationSchemaField JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    field_path=st.text(min_size=1, max_size=50),
    type_constraint=_type_constraint_strategy,
    required=st.booleans(),
    default_value=_default_value_strategy,
    description=st.text(min_size=0, max_size=100),
    settings=settings(max_examples=50),
)
def test_configurationschemafield_json_round_trip(field_path, type_constraint, required, default_value, description):
    """
        **Validates: Requirement 6 AC 10**

        FOR ALL valid ConfigurationSchemaField instances (excluding the validation
        callable), calling to_json and then from_dict on the parsed JSON SHALL
        produce a ConfigurationSchemaField with equivalent field_path,
        type_constraint, required, default_value, and description values.
    """
    original = ConfigurationSchemaField(
        field_path=field_path,
        type_constraint=type_constraint,
        required=required,
        default_value=default_value,
        description=description,
    )

    json_str = original.to_json()
    parsed_data = json.loads(json_str)
    reconstructed = ConfigurationSchemaField.from_dict(parsed_data)

    reconstructed_field_path = reconstructed.field_path
    assert reconstructed_field_path == field_path, (
        "Round-trip field_path mismatch: expected {!r}, got {!r}".format(
            field_path, reconstructed_field_path)
    )

    reconstructed_type_constraint = reconstructed.type_constraint
    assert reconstructed_type_constraint == type_constraint, (
        "Round-trip type_constraint mismatch: expected {!r}, got {!r}".format(
            type_constraint, reconstructed_type_constraint)
    )

    reconstructed_required = reconstructed.required
    assert reconstructed_required == required, (
        "Round-trip required mismatch: expected {!r}, got {!r}".format(
            required, reconstructed_required)
    )

    reconstructed_default_value = reconstructed.default_value
    assert reconstructed_default_value == default_value, (
        "Round-trip default_value mismatch: expected {!r}, got {!r}".format(
            default_value, reconstructed_default_value)
    )

    reconstructed_description = reconstructed.description
    assert reconstructed_description == description, (
        "Round-trip description mismatch: expected {!r}, got {!r}".format(
            description, reconstructed_description)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
