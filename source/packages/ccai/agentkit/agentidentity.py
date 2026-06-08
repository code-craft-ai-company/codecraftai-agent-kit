"""
    Defines the AgentIdentity class representing the identity and metadata
    of an agent in the codecraftai-agent-kit framework.

    AgentIdentity contains a unique identifier, human-readable name,
    version string, and descriptive tags. It supports serialization
    to and from JSON and dictionary representations.
"""

import json
import uuid

from typing import Dict
from typing import Optional


class AgentIdentity:
    """
        Identity and metadata for an agent.

        Contains a unique identifier, human-readable name, version string,
        and a dictionary of descriptive tags. Supports serialization to
        dictionary and JSON formats, and deserialization from JSON.

        :param name: The human-readable name of the agent.
        :param version: The version string of the agent.
        :param tags: Optional dictionary of descriptive key-value tags.
        :param identifier: Optional unique identifier. Auto-generates a UUID if not provided.
    """

    def __init__(self, name: str, version: str, tags: Optional[Dict[str, str]] = None,
                 identifier: Optional[str] = None) -> None:

        if identifier is not None:
            self._identifier = identifier
        else:
            self._identifier = str(uuid.uuid4())

        self._name = name
        self._version = version

        if tags is not None:
            self._tags = dict(tags)
        else:
            self._tags = {}

        return

    @property
    def identifier(self) -> str:
        """
            The unique identifier of the agent.

            :returns: The identifier string.
        """
        return self._identifier

    @property
    def name(self) -> str:
        """
            The human-readable name of the agent.

            :returns: The name string.
        """
        return self._name

    @property
    def version(self) -> str:
        """
            The version string of the agent.

            :returns: The version string.
        """
        return self._version

    @property
    def tags(self) -> Dict[str, str]:
        """
            A defensive copy of the descriptive tags dictionary.

            :returns: A dictionary copy of the tags.
        """
        return dict(self._tags)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the identity fields.

            :returns: A dictionary with identifier, name, version, and tags.
        """
        result = {
            "identifier": self._identifier,
            "name": self._name,
            "version": self._version,
            "tags": dict(self._tags)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the identity fields.

            :returns: A JSON string containing identifier, name, version, and tags.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_json(cls, json_str: str) -> "AgentIdentity":
        """
            Deserializes a JSON string into an AgentIdentity instance.

            :param json_str: A JSON string containing identity fields.

            :returns: An AgentIdentity instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)

        identifier = data["identifier"]
        name = data["name"]
        version = data["version"]
        tags = data.get("tags", {})

        identity = cls(
            name=name,
            version=version,
            tags=tags,
            identifier=identifier
        )
        return identity

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            identifier, name, and version.

            :returns: A repr string for debugging.
        """
        repr_str = "AgentIdentity(identifier={!r}, name={!r}, version={!r})".format(
            self._identifier, self._name, self._version
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the name and version.

            :returns: A human-readable string.
        """
        str_val = "AgentIdentity: {} v{}".format(self._name, self._version)
        return str_val
