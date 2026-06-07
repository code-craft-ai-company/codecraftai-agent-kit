"""
    Defines the PluginDescriptor class representing immutable metadata
    describing a discovered plugin in the codecraftai-agent-kit framework.

    A PluginDescriptor contains a plugin name, version, description, author,
    a list of extension point names, a list of PluginDependency objects,
    and a PluginStatus value.
"""

import json

from ccai.agentkit.plugindependency import PluginDependency
from ccai.agentkit.pluginstatus import PluginStatus


class PluginDescriptor:
    """
        Immutable metadata object describing a discovered plugin.
        Contains plugin name, version, description, author, extension points,
        dependencies, and status.

        :param name: The plugin name string.
        :param version: The plugin version string.
        :param description: The plugin description string.
        :param author: The plugin author string.
        :param extension_points: An optional list of extension point name strings.
        :param dependencies: An optional list of PluginDependency objects.
        :param status: The plugin lifecycle status, defaults to DISCOVERED.
    """

    def __init__(self, name: str, version: str, description: str, author: str,
                 extension_points: list = None, dependencies: list = None,
                 status: PluginStatus = PluginStatus.DISCOVERED) -> None:
        self._name = name
        self._version = version
        self._description = description
        self._author = author

        if extension_points is not None:
            self._extension_points = list(extension_points)
        else:
            self._extension_points = []

        if dependencies is not None:
            self._dependencies = list(dependencies)
        else:
            self._dependencies = []

        self._status = status
        return

    @property
    def name(self) -> str:
        """
            The plugin name string.

            :returns: The plugin name.
        """
        return self._name

    @property
    def version(self) -> str:
        """
            The plugin version string.

            :returns: The plugin version.
        """
        return self._version

    @property
    def description(self) -> str:
        """
            The plugin description string.

            :returns: The plugin description.
        """
        return self._description

    @property
    def author(self) -> str:
        """
            The plugin author string.

            :returns: The plugin author.
        """
        return self._author

    @property
    def extension_points(self) -> list:
        """
            A defensive copy of the list of extension point name strings.

            :returns: A list copy of the extension point names.
        """
        return list(self._extension_points)

    @property
    def dependencies(self) -> list:
        """
            A defensive copy of the list of PluginDependency objects.

            :returns: A list copy of the dependencies.
        """
        return list(self._dependencies)

    @property
    def status(self) -> PluginStatus:
        """
            The plugin lifecycle status.

            :returns: The PluginStatus value.
        """
        return self._status

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the descriptor fields.
            Dependencies are serialized using their as_dict method.
            Status is serialized as its string value.

            :returns: A dictionary with all descriptor fields.
        """
        dependencies_list = []
        for dep in self._dependencies:
            dependencies_list.append(dep.as_dict())

        result = {
            "name": self._name,
            "version": self._version,
            "description": self._description,
            "author": self._author,
            "extension_points": list(self._extension_points),
            "dependencies": dependencies_list,
            "status": self._status.value
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the descriptor fields.

            :returns: A JSON string containing all descriptor fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "PluginDescriptor":
        """
            Constructs a PluginDescriptor from a dictionary.
            Dependencies are reconstructed from their dictionary representations.
            Status is reconstructed via PluginStatus.from_string.

            :param data: A dictionary containing all descriptor fields.

            :returns: A PluginDescriptor instance reconstructed from the dictionary.
        """
        name = data["name"]
        version = data["version"]
        description = data["description"]
        author = data["author"]
        extension_points = data.get("extension_points", None)

        raw_dependencies = data.get("dependencies", None)
        dependencies = None
        if raw_dependencies is not None:
            dependencies = []
            for dep_data in raw_dependencies:
                dep = PluginDependency.from_dict(dep_data)
                dependencies.append(dep)

        raw_status = data.get("status", None)
        if raw_status is not None:
            status = PluginStatus.from_string(raw_status)
        else:
            status = PluginStatus.DISCOVERED

        descriptor = cls(
            name=name,
            version=version,
            description=description,
            author=author,
            extension_points=extension_points,
            dependencies=dependencies,
            status=status
        )
        return descriptor

    @classmethod
    def from_json(cls, json_str: str) -> "PluginDescriptor":
        """
            Deserializes a JSON string into a PluginDescriptor instance.

            :param json_str: A JSON string containing descriptor fields.

            :returns: A PluginDescriptor instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        descriptor = cls.from_dict(data)
        return descriptor

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            plugin name, version, and status.

            :returns: A repr string for debugging.
        """
        repr_str = "PluginDescriptor(name={!r}, version={!r}, status={!r})".format(
            self._name, self._version, self._status.value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the plugin name,
            version, description, and status.

            :returns: A human-readable string.
        """
        str_val = "PluginDescriptor '{}' v{} (status={}, description={!r})".format(
            self._name, self._version, self._status.value, self._description
        )
        return str_val
