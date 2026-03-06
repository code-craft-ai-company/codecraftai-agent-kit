"""
    Defines the PluginDependency class representing an immutable dependency
    of a plugin on another plugin or package, with an optional version
    constraint, in the automojo-agent-kit framework.

    A PluginDependency contains a dependency name and an optional version
    constraint string. The is_satisfied_by method checks whether a given
    plugin name and version satisfy the dependency.
"""

import json


class PluginDependency:
    """
        Immutable object representing a dependency of a plugin on another
        plugin or package, with an optional version constraint.

        :param name: The dependency name string.
        :param version_constraint: An optional version constraint string.
    """

    def __init__(self, name: str, version_constraint: str = None) -> None:
        self._name = name
        self._version_constraint = version_constraint
        return

    @property
    def name(self) -> str:
        """
            The dependency name string.

            :returns: The dependency name.
        """
        return self._name

    @property
    def version_constraint(self) -> str:
        """
            The optional version constraint string.

            :returns: The version constraint string, or None.
        """
        return self._version_constraint

    def is_satisfied_by(self, plugin_name: str, version: str) -> bool:
        """
            Returns whether the provided plugin satisfies this dependency.
            When no version constraint is specified, matches by name only.
            When a version constraint is specified, performs a simple string
            equality check against the version parameter.

            :param plugin_name: The plugin name to check.
            :param version: The plugin version to check.

            :returns: True if the dependency is satisfied.
        """
        if plugin_name != self._name:
            return False

        if self._version_constraint is None:
            return True

        is_match = (version == self._version_constraint)
        return is_match

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the dependency fields.

            :returns: A dictionary with name and version_constraint.
        """
        result = {
            "name": self._name,
            "version_constraint": self._version_constraint
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the dependency fields.

            :returns: A JSON string containing all dependency fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "PluginDependency":
        """
            Constructs a PluginDependency from a dictionary.

            :param data: A dictionary containing name and version_constraint.

            :returns: A PluginDependency instance reconstructed from the dictionary.
        """
        name = data["name"]
        version_constraint = data.get("version_constraint", None)

        dependency = cls(
            name=name,
            version_constraint=version_constraint
        )
        return dependency

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            dependency name, and version constraint.

            :returns: A repr string for debugging.
        """
        repr_str = "PluginDependency(name={!r}, version_constraint={!r})".format(
            self._name, self._version_constraint
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the dependency name
            and version constraint.

            :returns: A human-readable string.
        """
        str_val = "PluginDependency '{}' (version_constraint={!r})".format(
            self._name, self._version_constraint
        )
        return str_val
