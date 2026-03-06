"""
    Defines the ToolRegistry class for tracking available Tool instances
    within an Agent in the automojo-agent-kit framework.

    ToolRegistry provides registration, deregistration, lookup by name,
    lookup by tags, enumeration, and descriptor listing operations for
    Tool instances. Each Agent maintains its own ToolRegistry instance.
"""

import os

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.tool import Tool


class ToolRegistry:
    """
        Registry tracking available Tool instances for an Agent.
        Provides lookup by name, tags, and enumeration.
    """

    def __init__(self) -> None:
        self._tools: dict = {}
        return

    def register(self, tool: Tool) -> None:
        """
            Registers a Tool instance using its name as the key.

            :param tool: The Tool instance to register.

            :raises: SemanticError if a tool with the same name is already registered.
        """
        tool_name = tool.name
        is_duplicate = tool_name in self._tools

        if is_duplicate is True:
            errmsg_lines = [
                "Duplicate tool registration attempted.",
                "  Tool name: '{}'".format(tool_name),
                "  A tool with this name is already registered.",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg)

        self._tools[tool_name] = tool

        return

    def deregister(self, tool_name: str) -> None:
        """
            Removes a Tool from the registry by its name.

            If the tool name is not found, the operation is a no-op.

            :param tool_name: The name of the tool to remove.
        """
        is_present = tool_name in self._tools

        if is_present is True:
            del self._tools[tool_name]

        return

    def lookup(self, tool_name: str) -> Tool:
        """
            Looks up a registered Tool by its name.

            :param tool_name: The name of the tool to look up.

            :returns: The Tool instance if found, or None if not found.
        """
        rtnval = self._tools.get(tool_name, None)
        return rtnval

    def lookup_by_tags(self, **tags: str) -> list:
        """
            Looks up registered Tools by tag key-value pairs.

            Returns tools that match ALL provided tag criteria.

            :param tags: Keyword arguments representing tag key-value pairs to match.

            :returns: A list of Tool instances matching all tag criteria.
        """
        matching_tools = []

        for tool in self._tools.values():
            tool_tags = tool.tags
            all_match = True

            for tag_key, tag_value in tags.items():
                has_key = tag_key in tool_tags

                if has_key is not True:
                    all_match = False
                    break

                tool_tag_value = tool_tags[tag_key]
                values_match = tool_tag_value == tag_value

                if values_match is not True:
                    all_match = False
                    break

            if all_match is True:
                matching_tools.append(tool)

        rtnval = matching_tools
        return rtnval

    def list_all(self) -> list:
        """
            Returns a list of all registered Tool instances.

            :returns: A list of all registered Tool instances.
        """
        rtnval = list(self._tools.values())
        return rtnval

    def list_descriptors(self) -> list:
        """
            Returns a list of ToolDescriptor instances for all registered Tools.

            Provides discovery without exposing Tool implementations.

            :returns: A list of ToolDescriptor instances.
        """
        descriptors = []

        for tool in self._tools.values():
            descriptor = tool.descriptor
            descriptors.append(descriptor)

        rtnval = descriptors
        return rtnval

    def has_tool(self, tool_name: str) -> bool:
        """
            Checks whether a Tool with the given name is registered.

            :param tool_name: The name of the tool to check.

            :returns: True if a tool with the given name is registered, False otherwise.
        """
        rtnval = tool_name in self._tools
        return rtnval

    def clear(self) -> None:
        """
            Removes all registered Tools from the registry.
        """
        self._tools.clear()
        return

    @property
    def count(self) -> int:
        """
            The number of currently registered tools.

            :returns: The count of registered tools.
        """
        rtnval = len(self._tools)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name
            and the count of registered tools.

            :returns: A repr string for debugging.
        """
        rtnval = "ToolRegistry(count={})".format(self.count)
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered tool names.

            :returns: A human-readable string.
        """
        tool_names = list(self._tools.keys())
        rtnval = "ToolRegistry: [{}]".format(", ".join(tool_names))
        return rtnval
