"""
    Defines the FeatureFlag class representing an immutable named boolean
    toggle that controls whether a specific capability or behavior is
    enabled for an Agent in the automojo-agent-kit framework.

    A FeatureFlag contains a flag name, a default value, an optional
    description, and an optional metadata dictionary.
"""

import json


class FeatureFlag:
    """
        Immutable object representing a named boolean toggle that controls
        whether a specific capability or behavior is enabled for an Agent.

        :param name: The flag name string.
        :param default_value: The default boolean value for the flag.
        :param description: An optional description string.
        :param metadata: An optional metadata dictionary.
    """

    def __init__(self, name: str, default_value: bool = False,
                 description: str = None, metadata: dict = None) -> None:
        self._name = name
        self._default_value = default_value
        self._description = description

        if metadata is not None:
            self._metadata = dict(metadata)
        else:
            self._metadata = {}

        return

    @property
    def name(self) -> str:
        """
            The flag name string.

            :returns: The flag name.
        """
        return self._name

    @property
    def default_value(self) -> bool:
        """
            The default boolean value for the flag.

            :returns: The default value.
        """
        return self._default_value

    @property
    def description(self) -> str:
        """
            The optional description string.

            :returns: The description string, or None.
        """
        return self._description

    @property
    def metadata(self) -> dict:
        """
            A defensive copy of the metadata dictionary.

            :returns: A dictionary copy of the metadata.
        """
        return dict(self._metadata)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the flag fields.

            :returns: A dictionary with name, default_value, description, and metadata.
        """
        result = {
            "name": self._name,
            "default_value": self._default_value,
            "description": self._description,
            "metadata": dict(self._metadata)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the flag fields.

            :returns: A JSON string containing all flag fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureFlag":
        """
            Constructs a FeatureFlag from a dictionary.

            :param data: A dictionary containing name, default_value, description, and metadata.

            :returns: A FeatureFlag instance reconstructed from the dictionary.
        """
        name = data["name"]
        default_value = data.get("default_value", False)
        description = data.get("description", None)
        metadata = data.get("metadata", None)

        flag = cls(
            name=name,
            default_value=default_value,
            description=description,
            metadata=metadata
        )
        return flag

    @classmethod
    def from_json(cls, json_str: str) -> "FeatureFlag":
        """
            Deserializes a JSON string into a FeatureFlag instance.

            :param json_str: A JSON string containing flag fields.

            :returns: A FeatureFlag instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        flag = cls.from_dict(data)
        return flag

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            flag name, and default value.

            :returns: A repr string for debugging.
        """
        repr_str = "FeatureFlag(name={!r}, default_value={!r})".format(
            self._name, self._default_value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the flag name,
            default value, and description.

            :returns: A human-readable string.
        """
        str_val = "FeatureFlag '{}' (default={}, description={!r})".format(
            self._name, self._default_value, self._description
        )
        return str_val
