"""
    Defines the ToolSchema class for declarative schema definition of tool
    input or output parameters.

    ToolSchema supports type constraints, required/optional marking, default
    values, validation, and serialization to and from dictionary and JSON
    representations.
"""

import json
import os


class ToolSchema:
    """
        Declarative schema definition for tool input or output parameters.
        Supports type constraints, required/optional marking, defaults, and validation.

        Each parameter in the parameters list is a dictionary with keys:
            - name (str, required): Parameter name
            - type (str, required): One of SUPPORTED_TYPES
            - required (bool, optional): Defaults to True
            - default (any, optional): Default value for optional parameters
            - description (str, optional): Human-readable description

        :param parameters: A list of parameter definition dictionaries.
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

    def __init__(self, parameters: list = None) -> None:
        if parameters is not None:
            self._parameters = list(parameters)
        else:
            self._parameters = []

        return

    @property
    def parameters(self) -> list:
        """
            A defensive copy of the parameter definition list.

            :returns: A list of parameter definition dictionaries.
        """
        rtnval = list(self._parameters)
        return rtnval

    @property
    def parameter_count(self) -> int:
        """
            The number of parameters defined in this schema.

            :returns: The count of parameters.
        """
        rtnval = len(self._parameters)
        return rtnval

    def validate(self, values: dict) -> list:
        """
            Validates a dictionary of values against this schema.

            Checks for missing required parameters, applies default values
            for optional parameters that are absent, and verifies type
            constraints for all provided values.

            :param values: The dictionary of values to validate.

            :returns: A list of validation error strings. Empty list if all values are valid.
        """
        errors = []

        for param_def in self._parameters:
            param_name = param_def["name"]
            param_type = param_def["type"]
            is_required = param_def.get("required", True)

            has_value = param_name in values

            if has_value is False:
                if is_required is True:
                    errmsg = "Missing required parameter: '{}'".format(param_name)
                    errors.append(errmsg)
                else:
                    has_default = "default" in param_def
                    if has_default is True:
                        default_value = param_def["default"]
                        values[param_name] = default_value
            else:
                provided_value = values[param_name]
                expected_python_type = self.TYPE_MAP[param_type]
                is_correct_type = isinstance(provided_value, expected_python_type)

                if is_correct_type is False:
                    actual_type_name = type(provided_value).__name__
                    errmsg = "Parameter '{}': expected type '{}', got '{}'".format(
                        param_name, param_type, actual_type_name
                    )
                    errors.append(errmsg)

        rtnval = errors
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the schema definition.

            :returns: A dictionary with a 'parameters' key containing the list
                of parameter definitions.
        """
        params_copy = []

        for param_def in self._parameters:
            param_copy = dict(param_def)
            params_copy.append(param_copy)

        rtnval = {
            "parameters": params_copy
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the schema definition.

            :returns: A JSON string containing the schema parameters.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_dict(cls, schema_data: dict) -> "ToolSchema":
        """
            Constructs a ToolSchema from a dictionary representation.

            :param schema_data: A dictionary with a 'parameters' key containing
                a list of parameter definition dictionaries.

            :returns: A ToolSchema instance constructed from the dictionary data.
        """
        parameters = schema_data.get("parameters", [])
        rtnval = cls(parameters=parameters)
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "ToolSchema":
        """
            Deserializes a JSON string into a ToolSchema instance.

            :param json_str: A JSON string containing schema data.

            :returns: A ToolSchema instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(schema_data=data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name
            and the count of defined parameters.

            :returns: A repr string for debugging.
        """
        rtnval = "ToolSchema(parameter_count={})".format(self.parameter_count)
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the parameter names
            and their types.

            :returns: A human-readable string.
        """
        if len(self._parameters) == 0:
            rtnval = "ToolSchema: (no parameters)"
            return rtnval

        parts = []
        for param_def in self._parameters:
            param_name = param_def["name"]
            param_type = param_def["type"]
            part = "{}: {}".format(param_name, param_type)
            parts.append(part)

        params_summary = ", ".join(parts)
        rtnval = "ToolSchema: {}".format(params_summary)
        return rtnval
