"""
    Unit tests for ConfigurationManager schema validation behavior.

    Tests that schema validation is triggered after layer addition when a
    schema is provided, that ConfigurationValidationError is raised for
    invalid configuration, and that no error is raised when configuration
    is valid.

    Requirements: 1.7, 1.8
"""

from ccai.agentkit.configurationerrors import ConfigurationValidationError
from ccai.agentkit.configurationmanager import ConfigurationManager
from ccai.agentkit.configurationschema import ConfigurationSchema
from ccai.agentkit.configurationschemafield import ConfigurationSchemaField


def _create_schema_with_required_integer(schema_name="test-schema", field_path="timeout"):
    """
        Helper that creates a ConfigurationSchema with a single required
        integer field.

        :param schema_name: The name for the schema.
        :param field_path: The field path for the required integer field.

        :returns: A ConfigurationSchema instance.
    """
    schema = ConfigurationSchema(name=schema_name)
    schema.add_field(ConfigurationSchemaField(
        field_path=field_path,
        type_constraint="integer",
        required=True
    ))
    return schema


def _create_schema_with_two_required_fields():
    """
        Helper that creates a ConfigurationSchema with two required fields:
        a required integer 'timeout' and a required string 'name'.

        :returns: A ConfigurationSchema instance.
    """
    schema = ConfigurationSchema(name="two-field-schema")
    schema.add_field(ConfigurationSchemaField(
        field_path="timeout",
        type_constraint="integer",
        required=True
    ))
    schema.add_field(ConfigurationSchemaField(
        field_path="name",
        type_constraint="string",
        required=True
    ))
    return schema


# ---- Valid Config Does Not Raise ----


def test_load_from_dict_with_valid_config_does_not_raise():
    """
        Verify that loading a valid configuration dictionary when a schema
        is provided does not raise a ConfigurationValidationError.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-valid", schema=schema)

    manager.load_from_dict({"timeout": 30})

    retrieved_value = manager.get("timeout")
    assert retrieved_value == 30, "valid config should be loaded without error"
    return


def test_load_defaults_with_valid_config_does_not_raise():
    """
        Verify that loading valid defaults when a schema is provided does
        not raise a ConfigurationValidationError.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-defaults-valid", schema=schema)

    manager.load_defaults({"timeout": 10})

    retrieved_value = manager.get("timeout")
    assert retrieved_value == 10, "valid defaults should be loaded without error"
    return


def test_set_with_valid_value_does_not_raise():
    """
        Verify that calling set with a value that satisfies the schema does
        not raise a ConfigurationValidationError.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-set-valid", schema=schema)

    manager.set("timeout", 60)

    retrieved_value = manager.get("timeout")
    assert retrieved_value == 60, "set with valid value should succeed without error"
    return


# ---- Type Mismatch Raises ConfigurationValidationError ----


def test_load_from_dict_with_type_mismatch_raises_validation_error():
    """
        Verify that loading a configuration dictionary with a type mismatch
        raises ConfigurationValidationError when a schema is provided.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-type-err", schema=schema)

    caught_error = None
    try:
        manager.load_from_dict({"timeout": "not-an-integer"})
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "type mismatch should raise ConfigurationValidationError"
    return


def test_load_defaults_with_type_mismatch_raises_validation_error():
    """
        Verify that loading defaults with a type mismatch raises
        ConfigurationValidationError when a schema is provided.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-defaults-type-err", schema=schema)

    caught_error = None
    try:
        manager.load_defaults({"timeout": "bad-value"})
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "type mismatch in defaults should raise ConfigurationValidationError"
    return


# ---- Missing Required Field Raises ConfigurationValidationError ----


def test_load_from_dict_missing_required_field_raises_validation_error():
    """
        Verify that loading a configuration dictionary missing a required
        field raises ConfigurationValidationError.
    """
    schema = _create_schema_with_two_required_fields()
    manager = ConfigurationManager(agent_identifier="agent-missing-field", schema=schema)

    caught_error = None
    try:
        manager.load_from_dict({"timeout": 30})
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "missing required field should raise ConfigurationValidationError"
    return


# ---- Error Contains Schema Name ----


def test_validation_error_contains_schema_name():
    """
        Verify that the raised ConfigurationValidationError contains the
        schema name from the ConfigurationSchema.
    """
    schema = _create_schema_with_required_integer(schema_name="my-agent-schema")
    manager = ConfigurationManager(agent_identifier="agent-schema-name", schema=schema)

    caught_error = None
    try:
        manager.load_from_dict({"timeout": "wrong-type"})
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "should raise ConfigurationValidationError"
    error_schema_name = caught_error.schema_name
    assert error_schema_name == "my-agent-schema", "error should contain the schema name"
    return


# ---- Error Contains Error Messages ----


def test_validation_error_contains_error_messages():
    """
        Verify that the raised ConfigurationValidationError contains
        descriptive error messages in its errors list.
    """
    schema = _create_schema_with_two_required_fields()
    manager = ConfigurationManager(agent_identifier="agent-err-msgs", schema=schema)

    caught_error = None
    try:
        manager.load_from_dict({})
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "should raise ConfigurationValidationError"
    error_list = caught_error.errors
    error_count = len(error_list)
    assert error_count > 0, "error should contain at least one error message"
    return


# ---- Set Triggers Validation ----


def test_set_triggers_validation_when_schema_present():
    """
        Verify that the set method triggers schema validation and raises
        ConfigurationValidationError when the resulting config is invalid.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-set-validate", schema=schema)

    manager.set("timeout", 30)

    caught_error = None
    try:
        manager.set("timeout", "not-an-integer")
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "set with invalid value should raise ConfigurationValidationError"
    return


# ---- Load Defaults Triggers Validation ----


def test_load_defaults_triggers_validation_when_schema_present():
    """
        Verify that the load_defaults method triggers schema validation
        and raises ConfigurationValidationError when the config is invalid.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-defaults-validate", schema=schema)

    caught_error = None
    try:
        manager.load_defaults({"timeout": [1, 2, 3]})
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "load_defaults with invalid type should raise ConfigurationValidationError"
    return


# ---- Manager Remains Usable After Validation Error ----


def test_manager_usable_after_validation_error():
    """
        Verify that the ConfigurationManager is still usable after a
        ConfigurationValidationError is raised. Loading valid config
        after an invalid attempt should succeed.
    """
    schema = _create_schema_with_required_integer()
    manager = ConfigurationManager(agent_identifier="agent-recover", schema=schema)

    caught_error = None
    try:
        manager.load_from_dict({"timeout": "bad-value"})
    except ConfigurationValidationError as err:
        caught_error = err

    assert caught_error is not None, "invalid config should raise error"

    manager.load_from_dict({"timeout": 42})

    retrieved_value = manager.get("timeout")
    assert retrieved_value == 42, "manager should be usable after a validation error"
    return
