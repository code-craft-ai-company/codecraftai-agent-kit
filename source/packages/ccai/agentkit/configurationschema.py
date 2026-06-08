"""
    Defines the ConfigurationSchema class representing a declarative schema
    definition for agent configuration in the codecraftai-agent-kit framework.

    A ConfigurationSchema contains a schema name and a list of
    ConfigurationSchemaField objects defining the expected configuration
    fields. It provides validation of configuration dictionaries against
    the schema definition and supports JSON serialization round-trips.
"""

import json

from ccai.agentkit.configurationschemafield import ConfigurationSchemaField
from ccai.agentkit.configurationvalidationresult import ConfigurationValidationResult


class ConfigurationSchema:
    """
        Declarative schema definition describing the expected structure, types,
        constraints, and default values of an Agent's configuration.

        :param name: The name identifying this configuration schema.
        :param fields: An optional list of ConfigurationSchemaField objects.
    """

    def __init__(self, name: str, fields: list = None) -> None:
        self._name = name

        if fields is not None:
            self._fields = list(fields)
        else:
            self._fields = []

        return

    @property
    def name(self) -> str:
        """
            The name identifying this configuration schema.

            :returns: The schema name string.
        """
        return self._name

    @property
    def fields(self) -> list:
        """
            A defensive copy of the list of ConfigurationSchemaField objects.

            :returns: A list of ConfigurationSchemaField objects.
        """
        return list(self._fields)

    @property
    def field_count(self) -> int:
        """
            The count of defined ConfigurationSchemaField objects.

            :returns: The number of fields in this schema.
        """
        count = len(self._fields)
        return count

    def add_field(self, field: ConfigurationSchemaField) -> None:
        """
            Adds a ConfigurationSchemaField to the schema definition.

            :param field: The ConfigurationSchemaField to add.
        """
        self._fields.append(field)
        return

    def get_field(self, field_path: str) -> ConfigurationSchemaField:
        """
            Returns the ConfigurationSchemaField matching the given field path,
            or None when the field path is not defined.

            :param field_path: The dot-separated field path string to look up.

            :returns: The matching ConfigurationSchemaField, or None.
        """
        for field in self._fields:
            if field.field_path == field_path:
                return field

        return None

    def validate(self, configuration: dict) -> ConfigurationValidationResult:
        """
            Validates a configuration dictionary against this schema.

            For each field in the schema, resolves the value from the
            configuration using the dot-separated field path. Reports
            errors for missing required fields and type mismatches.

            :param configuration: The configuration dictionary to validate.

            :returns: A ConfigurationValidationResult with the validation outcome.
        """
        errors = []
        warnings = []

        for field in self._fields:
            value = self._resolve_field_value(configuration, field.field_path)

            if value is None and field.required is True:
                error_msg = "Required field '{}' is missing".format(field.field_path)
                errors.append(error_msg)
                continue

            if value is None and field.required is False:
                continue

            field_errors = field.validate_value(value)
            errors.extend(field_errors)

        has_errors = len(errors) > 0
        valid = has_errors is False

        result = ConfigurationValidationResult(valid=valid, errors=errors, warnings=warnings)
        return result

    def _resolve_field_value(self, configuration: dict, field_path: str):
        """
            Resolves a value from a configuration dictionary using a
            dot-separated field path.

            :param configuration: The configuration dictionary to traverse.
            :param field_path: The dot-separated path string.

            :returns: The resolved value, or None if not found.
        """
        parts = field_path.split(".")
        current = configuration

        for part in parts:
            if isinstance(current, dict) is False:
                return None

            if part not in current:
                return None

            current = current[part]

        return current

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the schema definition.

            :returns: A dictionary with name and fields.
        """
        result = {
            "name": self._name,
            "fields": [field.as_dict() for field in self._fields],
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the schema definition.

            :returns: A JSON string containing the schema definition.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "ConfigurationSchema":
        """
            Constructs a ConfigurationSchema from a dictionary.

            :param data: A dictionary containing name and fields.

            :returns: A ConfigurationSchema instance reconstructed from the dictionary.
        """
        name = data["name"]
        fields_data = data.get("fields", [])

        fields = []
        for field_data in fields_data:
            field = ConfigurationSchemaField.from_dict(field_data)
            fields.append(field)

        schema = cls(name=name, fields=fields)
        return schema

    @classmethod
    def from_json(cls, json_str: str) -> "ConfigurationSchema":
        """
            Deserializes a JSON string into a ConfigurationSchema instance.

            :param json_str: A JSON string containing schema fields.

            :returns: A ConfigurationSchema instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        schema = cls.from_dict(data)
        return schema

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            schema name, and field count.

            :returns: A repr string for debugging.
        """
        repr_str = "ConfigurationSchema(name={!r}, field_count={})".format(
            self._name, len(self._fields)
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the schema name
            and field count.

            :returns: A human-readable string.
        """
        str_val = "ConfigurationSchema '{}' ({} fields)".format(
            self._name, len(self._fields)
        )
        return str_val
