"""
    Defines the Tool abstract base class for all tools in the codecraftai-agent-kit
    framework.

    Tool provides a declarative interface for defining tool behavior through
    class-level constants (TOOL_NAME, TOOL_DESCRIPTION, TOOL_VERSION,
    INPUT_SCHEMA, OUTPUT_SCHEMA) and an abstract execute method that subclasses
    must implement.

    The Tool base class validates class-level schema declarations at construction
    time, supports optional tags and credential names, and exposes a descriptor
    property for metadata discovery.
"""

import abc
import os

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.toolschema import ToolSchema
from ccai.agentkit.tooldescriptor import ToolDescriptor


class Tool(abc.ABC):
    """
        Abstract base class for all tools. Subclasses define tool behavior
        by implementing the execute method and declaring schemas via
        class-level constants.

        :param tags: An optional dictionary of key-value tags for categorization.
        :param credential_names: An optional list of credential reference names
            that this tool requires for execution.
    """

    TOOL_NAME: str = None
    TOOL_DESCRIPTION: str = ""
    TOOL_VERSION: str = "1.0.0"
    INPUT_SCHEMA: dict = None
    OUTPUT_SCHEMA: dict = None

    def __init__(self, tags: dict = None, credential_names: list = None) -> None:
        self._name = self.TOOL_NAME
        self._description = self.TOOL_DESCRIPTION
        self._version = self.TOOL_VERSION
        self._input_schema = None
        self._output_schema = None

        if tags is not None:
            self._tags = dict(tags)
        else:
            self._tags = {}

        if credential_names is not None:
            self._credential_names = list(credential_names)
        else:
            self._credential_names = []

        if self._name is None:
            errmsg = "A Tool name is required. Set TOOL_NAME on the class or pass name to constructor."
            raise SemanticError(errmsg)

        if self.INPUT_SCHEMA is not None:
            try:
                self._input_schema = ToolSchema.from_dict(schema_data=self.INPUT_SCHEMA)
            except Exception as schema_err:
                errmsg_lines = [
                    "Invalid INPUT_SCHEMA on tool '{}'.".format(self._name),
                    "Schema validation detail: {}".format(str(schema_err)),
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise SemanticError(errmsg) from schema_err

        if self.OUTPUT_SCHEMA is not None:
            try:
                self._output_schema = ToolSchema.from_dict(schema_data=self.OUTPUT_SCHEMA)
            except Exception as schema_err:
                errmsg_lines = [
                    "Invalid OUTPUT_SCHEMA on tool '{}'.".format(self._name),
                    "Schema validation detail: {}".format(str(schema_err)),
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise SemanticError(errmsg) from schema_err

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

    @property
    def credential_names(self) -> list:
        """
            A defensive copy of the credential names list.

            :returns: A list of credential reference name strings.
        """
        rtnval = list(self._credential_names)
        return rtnval

    @property
    def descriptor(self) -> ToolDescriptor:
        """
            Returns a ToolDescriptor containing this Tool's metadata.

            :returns: A ToolDescriptor instance.
        """
        rtnval = ToolDescriptor(
            name=self._name,
            description=self._description,
            version=self._version,
            input_schema=self._input_schema,
            output_schema=self._output_schema,
            tags=self._tags,
        )
        return rtnval

    @abc.abstractmethod
    def execute(self, inputs: dict, credentials: dict = None) -> dict:
        """
            Executes the tool with the given validated inputs.

            :param inputs: Validated input dictionary.
            :param credentials: Optional dictionary of resolved credentials.

            :returns: Output dictionary.
        """
        ...

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            tool name, and version.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(name='{}', version='{}')".format(
            self.__class__.__name__, self._name, self._version
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the tool name
            and description.

            :returns: A human-readable string.
        """
        rtnval = "{} - {}".format(self._name, self._description)
        return rtnval
