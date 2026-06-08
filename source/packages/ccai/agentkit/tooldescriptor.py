"""
    Defines the ToolDescriptor class for immutable tool metadata.

    ToolDescriptor provides a read-only view of a Tool's name, description,
    version, input schema, output schema, and tags. It supports serialization
    to and from JSON for storage and transmission of tool definitions.
"""

import json

from ccai.agentkit.toolschema import ToolSchema


class ToolDescriptor:
    """
        Immutable metadata object describing a Tool's capabilities
        without exposing the Tool implementation.

        :param name: The tool name string.
        :param description: A human-readable description of the tool.
        :param version: The version string for the tool.
        :param input_schema: A ToolSchema defining the tool's input parameters.
        :param output_schema: A ToolSchema defining the tool's output parameters.
        :param tags: An optional dictionary of key-value tags for categorization.
    """

    def __init__(self, name: str, description: str, version: str,
                 input_schema: ToolSchema, output_schema: ToolSchema,
                 tags: dict = None) -> None:
        self._name = name
        self._description = description
        self._version = version
        self._input_schema = input_schema
        self._output_schema = output_schema

        if tags is not None:
            self._tags = dict(tags)
        else:
            self._tags = {}

        return

    @property
    def name(self) -> str:
        """
            The tool name.

            :returns: The name string.
        """
        rtnval = self._name
        return rtnval

    @property
    def description(self) -> str:
        """
            A human-readable description of the tool.

            :returns: The description string.
        """
        rtnval = self._description
        return rtnval

    @property
    def version(self) -> str:
        """
            The version string for the tool.

            :returns: The version string.
        """
        rtnval = self._version
        return rtnval

    @property
    def input_schema(self) -> ToolSchema:
        """
            The ToolSchema defining the tool's input parameters.

            :returns: A ToolSchema instance, or None if no input schema is defined.
        """
        rtnval = self._input_schema
        return rtnval

    @property
    def output_schema(self) -> ToolSchema:
        """
            The ToolSchema defining the tool's output parameters.

            :returns: A ToolSchema instance, or None if no output schema is defined.
        """
        rtnval = self._output_schema
        return rtnval

    @property
    def tags(self) -> dict:
        """
            A defensive copy of the tags dictionary.

            :returns: A dictionary of key-value tags.
        """
        rtnval = dict(self._tags)
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the descriptor fields.

            Input and output schemas are included as their as_dict()
            representations, or None if the schema is None.

            :returns: A dictionary containing all descriptor fields.
        """
        if self._input_schema is not None:
            input_schema_data = self._input_schema.as_dict()
        else:
            input_schema_data = None

        if self._output_schema is not None:
            output_schema_data = self._output_schema.as_dict()
        else:
            output_schema_data = None

        rtnval = {
            "name": self._name,
            "description": self._description,
            "version": self._version,
            "input_schema": input_schema_data,
            "output_schema": output_schema_data,
            "tags": dict(self._tags),
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the descriptor fields.

            :returns: A JSON string containing the descriptor data.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "ToolDescriptor":
        """
            Deserializes a JSON string into a ToolDescriptor instance.

            Reconstructs ToolSchema instances from the embedded schema
            dictionaries in the JSON data.

            :param json_str: A JSON string containing descriptor data.

            :returns: A ToolDescriptor instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)

        name = data["name"]
        description = data["description"]
        version = data["version"]
        tags = data.get("tags", {})

        input_schema_data = data.get("input_schema", None)
        if input_schema_data is not None:
            input_schema = ToolSchema.from_dict(schema_data=input_schema_data)
        else:
            input_schema = None

        output_schema_data = data.get("output_schema", None)
        if output_schema_data is not None:
            output_schema = ToolSchema.from_dict(schema_data=output_schema_data)
        else:
            output_schema = None

        rtnval = cls(
            name=name,
            description=description,
            version=version,
            input_schema=input_schema,
            output_schema=output_schema,
            tags=tags,
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            tool name, and version.

            :returns: A repr string for debugging.
        """
        rtnval = "ToolDescriptor(name='{}', version='{}')".format(
            self._name, self._version
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the tool name
            and description.

            :returns: A human-readable string.
        """
        rtnval = "ToolDescriptor: {} - {}".format(self._name, self._description)
        return rtnval
