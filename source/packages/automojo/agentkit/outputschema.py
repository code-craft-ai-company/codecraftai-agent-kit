"""
    Defines the OutputSchema class for declarative output validation.

    OutputSchema provides a schema definition with typed fields that can
    be used to validate parsed LLM output. Each field has a name, a type
    constraint, and a required/optional flag. The schema supports
    serialization to and from JSON and dictionary representations.
"""

import json


class OutputSchema:
    """
        Declarative schema for validating parsed LLM output.

        Supports field type constraints and required/optional marking.
        Each field definition is a dictionary with 'name', 'type', and
        optional 'required' keys. Supported types are: string, integer,
        float, boolean, list, and dictionary.

        :param fields: A list of field definition dictionaries.
    """

    SUPPORTED_TYPES = {"string", "integer", "float", "boolean", "list", "dictionary"}

    TYPE_MAP = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "list": list,
        "dictionary": dict,
    }

    def __init__(self, fields: list = None) -> None:
        self._fields = list(fields) if fields is not None else []
        return

    @property
    def fields(self) -> list:
        """
            Returns a copy of the field definitions list.

            :returns: A list of field definition dictionaries.
        """
        rtnval = list(self._fields)
        return rtnval

    def validate(self, parsed_output: object) -> list:
        """
            Validates a parsed output object against this schema.

            Checks that the parsed output is a dictionary, that all required
            fields are present, and that field values match their declared types.

            :param parsed_output: The parsed output (typically a dict).

            :returns: A list of validation error strings. Empty if valid.
        """
        errors = []

        if not isinstance(parsed_output, dict):
            errors.append("Expected a dictionary, got {}.".format(type(parsed_output).__name__))
            return errors

        for field_def in self._fields:
            fname = field_def["name"]
            ftype = field_def["type"]
            required = field_def.get("required", True)

            if fname not in parsed_output:
                if required:
                    errors.append("Missing required field: {!r}.".format(fname))
                continue

            value = parsed_output[fname]
            expected_python_type = self.TYPE_MAP.get(ftype)
            if expected_python_type is not None and not isinstance(value, expected_python_type):
                errors.append("Field {!r} expected type {}, got {}.".format(
                    fname, ftype, type(value).__name__
                ))

        rtnval = errors
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the schema definition.

            :returns: A dictionary with a 'fields' key containing the field definitions.
        """
        rtnval = {"fields": list(self._fields)}
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the schema definition.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "OutputSchema":
        """
            Constructs an OutputSchema from a dictionary.

            :param data: A dictionary with a 'fields' key.

            :returns: An OutputSchema instance.
        """
        rtnval = cls(fields=data.get("fields", []))
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "OutputSchema":
        """
            Deserializes a JSON string into an OutputSchema instance.

            :param json_str: A JSON string.

            :returns: An OutputSchema instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __eq__(self, other) -> bool:
        """
            Checks equality based on the field definitions.

            :param other: The object to compare against.

            :returns: True if field definitions are equal, False otherwise.
        """
        if not isinstance(other, OutputSchema):
            return False

        rtnval = self._fields == other._fields
        return rtnval
