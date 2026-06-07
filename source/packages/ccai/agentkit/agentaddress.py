"""
    Defines the AgentAddress class representing the network-addressable
    identity of an Agent in the Communication & Messaging feature.

    AgentAddress is an immutable object containing the agent identifier,
    transport name, and protocol-specific endpoint information. It supports
    serialization to and from JSON and dictionary representations, and
    equality comparison by agent identifier and transport name.

    .. module:: ccai.agentkit.agentaddress
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable agent endpoint address for message routing.
"""

import json

from typing import Dict
from typing import Optional


class AgentAddress:
    """
        Immutable object representing the network-addressable identity of an Agent.

        Contains the agent identifier, transport name, and protocol-specific
        endpoint information as a dictionary (supporting keys such as "host",
        "port", "path", "queue_name", "topic"). Supports serialization to
        dictionary and JSON formats, and deserialization from JSON.

        Two AgentAddress instances are considered equal when they share the
        same agent_identifier and transport_name. The hash is also based on
        these two fields, enabling use as dictionary keys and set members.

        :param agent_identifier: The unique identifier of the agent.
        :param transport_name: The name of the transport used to reach the agent.
        :param endpoint: Optional dictionary of protocol-specific endpoint information.
    """

    def __init__(self, agent_identifier: str, transport_name: str,
                 endpoint: Optional[Dict] = None) -> None:

        self._agent_identifier = agent_identifier
        self._transport_name = transport_name

        if endpoint is not None:
            self._endpoint = dict(endpoint)
        else:
            self._endpoint = {}

        return

    @property
    def agent_identifier(self) -> str:
        """
            The unique identifier of the agent.

            :returns: The agent identifier string.
        """
        return self._agent_identifier

    @property
    def transport_name(self) -> str:
        """
            The name of the transport used to reach the agent.

            :returns: The transport name string.
        """
        return self._transport_name

    @property
    def endpoint(self) -> Dict:
        """
            A defensive copy of the protocol-specific endpoint information.

            :returns: A dictionary copy of the endpoint information.
        """
        return dict(self._endpoint)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the address fields.

            :returns: A dictionary with agent_identifier, transport_name,
                and endpoint.
        """
        result = {
            "agent_identifier": self._agent_identifier,
            "transport_name": self._transport_name,
            "endpoint": dict(self._endpoint)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the address fields.

            :returns: A JSON string containing agent_identifier, transport_name,
                and endpoint.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "AgentAddress":
        """
            Constructs an AgentAddress from a dictionary.

            :param data: A dictionary containing agent_identifier, transport_name,
                and optionally endpoint.

            :returns: An AgentAddress instance reconstructed from the dictionary data.
        """
        agent_identifier = data["agent_identifier"]
        transport_name = data["transport_name"]
        endpoint = data.get("endpoint", {})

        address = cls(
            agent_identifier=agent_identifier,
            transport_name=transport_name,
            endpoint=endpoint
        )
        return address

    @classmethod
    def from_json(cls, json_str: str) -> "AgentAddress":
        """
            Deserializes a JSON string into an AgentAddress instance.

            :param json_str: A JSON string containing address fields.

            :returns: An AgentAddress instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        address = cls.from_dict(data)
        return address

    def __eq__(self, other: object) -> bool:
        """
            Compares two AgentAddress instances by agent_identifier and
            transport_name.

            :param other: The object to compare against.

            :returns: True if both agent_identifier and transport_name match,
                False otherwise.
        """
        if not isinstance(other, AgentAddress):
            return NotImplemented

        is_equal = (self._agent_identifier == other._agent_identifier
                    and self._transport_name == other._transport_name)
        return is_equal

    def __hash__(self) -> int:
        """
            Returns a hash based on agent_identifier and transport_name,
            enabling use as a dictionary key or set member.

            :returns: An integer hash value.
        """
        hash_val = hash((self._agent_identifier, self._transport_name))
        return hash_val

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            agent identifier, and transport name.

            :returns: A repr string for debugging.
        """
        repr_str = "AgentAddress(agent_identifier={!r}, transport_name={!r})".format(
            self._agent_identifier, self._transport_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent identifier,
            transport name, and endpoint information.

            :returns: A human-readable string.
        """
        str_val = "AgentAddress: agent={}, transport={}, endpoint={}".format(
            self._agent_identifier, self._transport_name, self._endpoint
        )
        return str_val
