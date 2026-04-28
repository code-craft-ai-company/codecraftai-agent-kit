"""
    Defines the TransportRegistry class for tracking available
    Transport instances within an Agent in the Communication &
    Messaging feature.

    TransportRegistry provides registration, deregistration,
    lookup by name, lookup by protocol type, lookup by tags,
    enumeration, and existence checks for Transport instances.
    Each Agent maintains its own TransportRegistry instance.

    .. module:: automojo.agentkit.transportregistry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Per-agent transport registration and lookup.

    Requirements: 3.1-3.11, 26.9, 26.10
"""

import os

from typing import Dict
from typing import List
from typing import Optional

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.transport import Transport


class TransportRegistry:
    """
        Registry tracking available Transport instances for an Agent.
        Provides lookup by name, protocol type, tags, and enumeration.

        Transports are registered using their name as the key. Duplicate
        names are rejected with a SemanticError. Lookup by name returns
        None when the name is not found. Lookup by protocol type and
        tags returns a list of matching Transport instances.
    """

    def __init__(self) -> None:
        self._transports: Dict[str, Transport] = {}
        return

    def register(self, transport: Transport) -> None:
        """
            Registers a Transport instance using its name as the key.

            :param transport: The Transport instance to register.

            :raises SemanticError: If a transport with the same name
                is already registered.
        """
        transport_name = transport.name
        is_duplicate = transport_name in self._transports

        if is_duplicate is True:
            errmsg_lines = [
                "Duplicate transport registration attempted.",
                "  Transport name: '{}'".format(transport_name),
                "  A transport with this name is already registered.",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg)

        self._transports[transport_name] = transport

        return

    def deregister(self, transport_name: str) -> None:
        """
            Removes a Transport from the registry by its name.

            If the transport name is not found, the operation is
            a no-op.

            :param transport_name: The name of the transport to remove.
        """
        is_present = transport_name in self._transports

        if is_present is True:
            del self._transports[transport_name]

        return

    def lookup(self, transport_name: str) -> Optional[Transport]:
        """
            Looks up a registered Transport by its name.

            :param transport_name: The name of the transport to look up.

            :returns: The Transport instance if found, or None if not
                found.
        """
        rtnval = self._transports.get(transport_name, None)
        return rtnval

    def lookup_by_protocol(self, protocol_type: str) -> List[Transport]:
        """
            Looks up registered Transports by protocol type.

            Returns all transports whose protocol_type matches the
            provided value.

            :param protocol_type: The protocol type string to match
                (e.g. "http", "websocket", "grpc", "message_queue").

            :returns: A list of Transport instances matching the
                protocol type.
        """
        matching_transports = []

        for transport in self._transports.values():
            transport_protocol = transport.protocol_type
            is_match = transport_protocol == protocol_type

            if is_match is True:
                matching_transports.append(transport)

        rtnval = matching_transports
        return rtnval

    def lookup_by_tags(self, **tags: str) -> List[Transport]:
        """
            Looks up registered Transports by tag key-value pairs.

            Returns transports that match ALL provided tag criteria.

            :param tags: Keyword arguments representing tag key-value
                pairs to match.

            :returns: A list of Transport instances matching all tag
                criteria.
        """
        matching_transports = []

        for transport in self._transports.values():
            transport_tags = transport.tags
            all_match = True

            for tag_key, tag_value in tags.items():
                has_key = tag_key in transport_tags

                if has_key is not True:
                    all_match = False
                    break

                transport_tag_value = transport_tags[tag_key]
                values_match = transport_tag_value == tag_value

                if values_match is not True:
                    all_match = False
                    break

            if all_match is True:
                matching_transports.append(transport)

        rtnval = matching_transports
        return rtnval

    def list_all(self) -> List[Transport]:
        """
            Returns a list of all registered Transport instances.

            :returns: A list of all registered Transport instances.
        """
        rtnval = list(self._transports.values())
        return rtnval

    def has_transport(self, transport_name: str) -> bool:
        """
            Checks whether a Transport with the given name is
            registered.

            :param transport_name: The name of the transport to check.

            :returns: True if a transport with the given name is
                registered, False otherwise.
        """
        rtnval = transport_name in self._transports
        return rtnval

    @property
    def count(self) -> int:
        """
            The number of currently registered transports.

            :returns: The count of registered transports.
        """
        rtnval = len(self._transports)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of registered transports.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(count={})".format(
            self.__class__.__name__, self.count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered
            transport names and protocol types.

            :returns: A human-readable string describing the registry
                contents.
        """
        if self.count == 0:
            str_val = "TransportRegistry: 0 transports registered"
            return str_val

        entries = []
        for transport_name, transport in sorted(self._transports.items()):
            entries.append("{}({})".format(
                transport_name, transport.protocol_type
            ))

        str_val = "TransportRegistry: {} transport(s) registered [{}]".format(
            self.count, ", ".join(entries)
        )
        return str_val
