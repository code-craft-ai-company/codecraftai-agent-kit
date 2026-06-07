"""
    Defines the AddressResolver class for resolving agent identifiers
    to AgentAddress instances using static mappings or dynamic
    AgentRegistry lookup.

    AddressResolver supports two resolution strategies: static address
    resolution from a configured mapping dictionary, and dynamic
    resolution by querying the AgentRegistry. Static resolution is
    attempted first; if no static mapping is found, dynamic resolution
    is attempted. If neither strategy resolves the address, a
    MessageRoutingError is raised.

    .. module:: ccai.agentkit.addressresolver
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent address resolution for message routing.

    Requirements: 8.1-8.8
"""

from typing import Dict
from typing import Optional
from typing import Tuple

from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.messagingerrors import MessageRoutingError


class AddressResolver:
    """
        Resolves agent identifiers to AgentAddress instances using static
        mappings or dynamic AgentRegistry lookup.

        Static address resolution uses a dictionary keyed by
        (agent_identifier, transport_name) tuples. Dynamic resolution
        queries the AgentRegistry for the agent and derives the
        AgentAddress from the agent's registered transport configuration.

        Static resolution is attempted first. If no static mapping is
        found and an AgentRegistry is available, dynamic resolution is
        attempted. If neither strategy resolves the address, a
        MessageRoutingError is raised.

        :param agent_registry: An optional AgentRegistry instance for
            dynamic address resolution.
    """

    def __init__(self, agent_registry=None) -> None:
        self._static_addresses: Dict[Tuple[str, str], AgentAddress] = {}
        self._agent_registry = agent_registry
        return

    def resolve(self, agent_identifier: str, transport_name: str) -> AgentAddress:
        """
            Resolves an agent identifier and transport name to an AgentAddress.

            Attempts static lookup first using the configured address mapping.
            If no static mapping is found and an AgentRegistry is available,
            attempts dynamic resolution by querying the registry.

            :param agent_identifier: The agent identifier string.
            :param transport_name: The transport name string.

            :returns: The resolved AgentAddress.

            :raises MessageRoutingError: If the agent identifier cannot be
                resolved to an AgentAddress.
        """
        lookup_key = (agent_identifier, transport_name)
        static_address = self._static_addresses.get(lookup_key, None)

        if static_address is not None:
            return static_address

        if self._agent_registry is not None:
            dynamic_address = self._resolve_dynamic(agent_identifier, transport_name)

            if dynamic_address is not None:
                return dynamic_address

        raise MessageRoutingError(
            target=agent_identifier,
            detail="Cannot resolve agent '{}' for transport '{}'".format(
                agent_identifier, transport_name
            )
        )

    def _resolve_dynamic(self, agent_identifier: str, transport_name: str) -> Optional[AgentAddress]:
        """
            Attempts dynamic resolution by querying the AgentRegistry.

            Looks up the agent by identifier in the registry and derives
            an AgentAddress from the agent's registered information.

            :param agent_identifier: The agent identifier string.
            :param transport_name: The transport name string.

            :returns: The resolved AgentAddress or None if not found.
        """
        agent = self._agent_registry.lookup(agent_identifier)

        if agent is None:
            return None

        address = AgentAddress(
            agent_identifier=agent_identifier,
            transport_name=transport_name,
        )
        return address

    def register_address(self, agent_identifier: str, transport_name: str,
                         endpoint: dict) -> None:
        """
            Stores a static address mapping.

            Creates an AgentAddress from the provided parameters and
            stores it in the static address mapping dictionary keyed
            by (agent_identifier, transport_name).

            :param agent_identifier: The agent identifier.
            :param transport_name: The transport name.
            :param endpoint: The endpoint dictionary.
        """
        address = AgentAddress(
            agent_identifier=agent_identifier,
            transport_name=transport_name,
            endpoint=endpoint,
        )

        lookup_key = (agent_identifier, transport_name)
        self._static_addresses[lookup_key] = address

        return

    def deregister_address(self, agent_identifier: str, transport_name: str) -> None:
        """
            Removes a static address mapping.

            If the mapping does not exist, the operation is a no-op.

            :param agent_identifier: The agent identifier.
            :param transport_name: The transport name.
        """
        lookup_key = (agent_identifier, transport_name)
        is_present = lookup_key in self._static_addresses

        if is_present is True:
            del self._static_addresses[lookup_key]

        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of registered static addresses.

            :returns: A repr string for debugging.
        """
        static_count = len(self._static_addresses)
        repr_str = "{}(static_addresses={})".format(
            self.__class__.__name__, static_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count of
            static addresses and whether dynamic resolution is enabled.

            :returns: A human-readable string describing the resolver state.
        """
        static_count = len(self._static_addresses)
        has_dynamic = self._agent_registry is not None

        str_val = "AddressResolver: {} static address(es), dynamic_resolution={}".format(
            static_count, has_dynamic
        )
        return str_val
