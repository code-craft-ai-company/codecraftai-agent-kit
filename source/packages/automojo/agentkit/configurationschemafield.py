"""
    Defines the ConfigurationSchemaField class representing a single field
    within a ConfigurationSchema in the automojo-agent-kit framework.

    A ConfigurationSchemaField contains a field path, type constraint,
    required flag, optional default value, description, and optional
    validation callable. The type constraint is validated against a set
    of valid types at construction time.
"""

import json

from automojo.agentkit.errors import SemanticError


class ConfigurationSchemaField:
    """
        Immutable object representing a single field within a ConfigurationSchema.

        Contains a field path, type constraint, required flag, optional default,
        description, and optional validation callable.

        :param field_path: Dot-separated path string identifying the field.
        :param type_constraint: The expected type as a string (one of VALID_TYPES).
        :param required: Whether this field is required in the configuration.
        :param default_value: An optional default value for the field.
        :param description: A human-readable description of the field.
        :param validation_callable: An optional callable for custom validation.

        :raises: SemanticError
    """

    VALID_TYPES = {"string", "integer", "float", "boolean", "list", "dictionary"}

    TYPE_MAP = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "list": list,
        "dictionary": dict,
    }

    def __init__(self, field_path: str, type_constraint: str, required: bool = True,
                 default_value=None, description: str = "",
                 validation_callable=None) -> None:
        self._field_path = field_path
        self._type_constraint = type_constraint
        self._required = required
        self._default_value = default_value
        self._description = description
        self._validation_callable = validation_callable

        if self._type_constraint not in self.VALID_TYPES:
            errmsg = "Invalid type constraint '{}'. Valid types: {}".format(
                self._type_constraint, ", ".join(sorted(self.VALID_TYPES)))
            raise SemanticError(errmsg)

        return

    @property
    def field_path(self) -> str:
        """
            The dot-separated path string identifying this field.

            :returns: The field path string.
        """
        return self._field_path

    @property
    def type_constraint(self) -> str:
        """
            The expected type constraint as a string.

            :returns: The type constraint string.
        """
        return self._type_constraint

    @property
    def required(self) -> bool:
        """
            Whether this field is required in the configuration.

            :returns: True if the field is required.
        """
        return self._required

    @property
    def default_value(self):
        """
            The optional default value for this field.

            :returns: The default value, or None if not set.
        """
        return self._default_value

    @property
    def description(self) -> str:
        """
            A human-readable description of this field.

            :returns: The description string.
        """
        return self._description

    @property
    def validation_callable(self):
        """
            The optional callable for custom validation.

            :returns: The validation callable, or None if not set.
        """
        return self._validation_callable

    def validate_value(self, value) -> list:
        """
            Validates a value against this field's type constraint and custom validation.

            :param value: The value to validate.

            :returns: A list of validation error strings. Empty list if valid.
        """
        errors = []

        expected_type = self.TYPE_MAP[self._type_constraint]

        is_correct_type = isinstance(value, expected_type)
        if is_correct_type is False:
            actual_type_name = type(value).__name__
            error_msg = "Field '{}': expected type '{}', got '{}'".format(
                self._field_path, self._type_constraint, actual_type_name)
            errors.append(error_msg)

        if self._validation_callable is not None:
            custom_result = self._validation_callable(value)
            if custom_result is not None:
                if len(custom_result) > 0:
                    errors.append(custom_result)

        return errors

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the field definition,
            excluding the validation callable.

            :returns: A dictionary with field_path, type_constraint, required,
                default_value, and description.
        """
        result = {
            "field_path": self._field_path,
            "type_constraint": self._type_constraint,
            "required": self._required,
            "default_value": self._default_value,
            "description": self._description,
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the field definition,
            excluding the validation callable.

            :returns: A JSON string containing the field definition.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "ConfigurationSchemaField":
        """
            Constructs a ConfigurationSchemaField from a dictionary.

            :param data: A dictionary containing field_path, type_constraint,
                and optionally required, default_value, and description.

            :returns: A ConfigurationSchemaField instance reconstructed from the dictionary.
        """
        field_path = data["field_path"]
        type_constraint = data["type_constraint"]
        required = data.get("required", True)
        default_value = data.get("default_value", None)
        description = data.get("description", "")

        field = cls(
            field_path=field_path,
            type_constraint=type_constraint,
            required=required,
            default_value=default_value,
            description=description,
        )
        return field

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            field path, type constraint, and required flag.

            :returns: A repr string for debugging.
        """
        repr_str = "ConfigurationSchemaField(field_path={!r}, type_constraint={!r}, required={})".format(
            self._field_path, self._type_constraint, self._required
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the field path,
            type, and description.

            :returns: A human-readable string.
        """
        str_val = "ConfigurationSchemaField '{}' (type={}, description={})".format(
            self._field_path, self._type_constraint, self._description
        )
        return str_val
