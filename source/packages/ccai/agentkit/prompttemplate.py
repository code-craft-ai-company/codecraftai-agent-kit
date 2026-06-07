"""
    Defines the PromptTemplate class for named, versioned prompt templates.

    PromptTemplate encapsulates a name, version, template string with
    placeholder variables using Python str.format syntax, and an optional
    description. Placeholder variable names are extracted automatically
    from the template string. The render method replaces placeholders
    with provided values, raising SemanticError for missing variables.
"""

import json
import string

from ccai.agentkit.errors import SemanticError


class PromptTemplate:
    """
        A named, versioned template string with placeholder variables
        using Python str.format syntax.

        Provides read-only access to the name, version, template, description,
        and extracted variable names. Supports rendering with variable values,
        serialization to and from JSON and dictionary representations.

        :param name: The template name.
        :param version: The template version string.
        :param template: The template string with {placeholder} variables.
        :param description: Optional description.
    """

    def __init__(self, name: str, version: str, template: str,
                 description: str = "") -> None:
        self._name = name
        self._version = version
        self._template = template
        self._description = description
        self._variables = self._extract_variables()
        return

    def _extract_variables(self) -> list:
        """
            Extracts placeholder variable names from the template string
            using string.Formatter to parse the template.

            :returns: A list of unique variable name strings in order of appearance.
        """
        formatter = string.Formatter()
        variables = []

        for _, field_name, _, _ in formatter.parse(self._template):
            if field_name is not None and field_name not in variables:
                variables.append(field_name)

        rtnval = variables
        return rtnval

    @property
    def name(self) -> str:
        """
            The template name string.

            :returns: The name as a string.
        """
        rtnval = self._name
        return rtnval

    @property
    def version(self) -> str:
        """
            The template version string.

            :returns: The version as a string.
        """
        rtnval = self._version
        return rtnval

    @property
    def template(self) -> str:
        """
            The template string with placeholder variables.

            :returns: The template as a string.
        """
        rtnval = self._template
        return rtnval

    @property
    def description(self) -> str:
        """
            The optional description string.

            :returns: The description as a string.
        """
        rtnval = self._description
        return rtnval

    @property
    def variables(self) -> list:
        """
            A copy of the list of placeholder variable names extracted
            from the template string.

            :returns: A list of variable name strings.
        """
        rtnval = list(self._variables)
        return rtnval

    def render(self, values: dict) -> str:
        """
            Renders the template with the provided variable values.

            :param values: A dictionary mapping variable names to values.

            :returns: The rendered prompt string.
            :raises: SemanticError if required variables are missing.
        """
        missing = [v for v in self._variables if v not in values]

        if len(missing) > 0:
            errmsg = "PromptTemplate {!r} v{} is missing required variables: {}".format(
                self._name, self._version, ", ".join(missing)
            )
            raise SemanticError(errmsg)

        rtnval = self._template.format(**values)
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the template fields.

            :returns: A dictionary with name, version, template, and description keys.
        """
        rtnval = {
            "name": self._name,
            "version": self._version,
            "template": self._template,
            "description": self._description
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the template fields.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "PromptTemplate":
        """
            Constructs a PromptTemplate from a dictionary.

            :param data: A dictionary with name, version, template, and optional description keys.

            :returns: A PromptTemplate instance.
        """
        rtnval = cls(
            name=data["name"],
            version=data["version"],
            template=data["template"],
            description=data.get("description", "")
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "PromptTemplate":
        """
            Deserializes a JSON string into a PromptTemplate.

            :param json_str: A JSON string.

            :returns: A PromptTemplate instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            name, and version.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(name={!r}, version={!r})".format(
            self.__class__.__name__, self._name, self._version
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the name, version,
            and variable names.

            :returns: A human-readable string.
        """
        rtnval = "PromptTemplate: {} v{} [variables: {}]".format(
            self._name, self._version, ", ".join(self._variables)
        )
        return rtnval

    def __eq__(self, other) -> bool:
        """
            Checks equality based on name, version, template, and description fields.

            :param other: The object to compare against.

            :returns: True if all fields are equal, False otherwise.
        """
        if not isinstance(other, PromptTemplate):
            return False

        rtnval = (self._name == other._name and
                  self._version == other._version and
                  self._template == other._template and
                  self._description == other._description)
        return rtnval
