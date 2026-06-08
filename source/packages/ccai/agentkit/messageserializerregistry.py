"""
    Defines the MessageSerializerRegistry class for tracking available
    MessageSerializer instances within an Agent in the Communication &
    Messaging feature.

    MessageSerializerRegistry provides registration, deregistration,
    lookup by format name, enumeration, and existence checks for
    MessageSerializer instances. Each Agent maintains its own
    MessageSerializerRegistry instance.

    .. module:: ccai.agentkit.messageserializerregistry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Serializer registration and lookup by format name.

    Requirements: 10.1-10.9, 26.11, 26.12
"""

import os

from typing import Dict
from typing import List
from typing import Optional

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.messageserializer import MessageSerializer


class MessageSerializerRegistry:
    """
        Registry tracking available MessageSerializer instances.
        Provides lookup by format name and enumeration.

        Serializers are registered using their format name as the key.
        Duplicate format names are rejected with a SemanticError.
        Lookup by format name returns None when the format name is not
        found.
    """

    def __init__(self) -> None:
        self._serializers: Dict[str, MessageSerializer] = {}
        return

    def register(self, serializer: MessageSerializer) -> None:
        """
            Registers a MessageSerializer instance using its format
            name as the key.

            :param serializer: The MessageSerializer instance to
                register.

            :raises SemanticError: If a serializer with the same
                format name is already registered.
        """
        format_name = serializer.format_name
        is_duplicate = format_name in self._serializers

        if is_duplicate is True:
            errmsg_lines = [
                "Duplicate serializer registration attempted.",
                "  Format name: '{}'".format(format_name),
                "  A serializer with this format name is already registered.",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg)

        self._serializers[format_name] = serializer

        return

    def deregister(self, format_name: str) -> None:
        """
            Removes a MessageSerializer from the registry by its
            format name.

            If the format name is not found, the operation is a no-op.

            :param format_name: The format name of the serializer to
                remove.
        """
        is_present = format_name in self._serializers

        if is_present is True:
            del self._serializers[format_name]

        return

    def lookup(self, format_name: str) -> Optional[MessageSerializer]:
        """
            Looks up a registered MessageSerializer by its format name.

            :param format_name: The format name of the serializer to
                look up.

            :returns: The MessageSerializer instance if found, or None
                if not found.
        """
        rtnval = self._serializers.get(format_name, None)
        return rtnval

    def list_all(self) -> List[MessageSerializer]:
        """
            Returns a list of all registered MessageSerializer
            instances.

            :returns: A list of all registered MessageSerializer
                instances.
        """
        rtnval = list(self._serializers.values())
        return rtnval

    def has_serializer(self, format_name: str) -> bool:
        """
            Checks whether a MessageSerializer with the given format
            name is registered.

            :param format_name: The format name to check.

            :returns: True if a serializer with the given format name
                is registered, False otherwise.
        """
        rtnval = format_name in self._serializers
        return rtnval

    @property
    def count(self) -> int:
        """
            The number of currently registered serializers.

            :returns: The count of registered serializers.
        """
        rtnval = len(self._serializers)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of registered serializers.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(count={})".format(
            self.__class__.__name__, self.count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered
            format names.

            :returns: A human-readable string describing the registry
                contents.
        """
        if self.count == 0:
            str_val = "MessageSerializerRegistry: 0 serializers registered"
            return str_val

        format_names = sorted(self._serializers.keys())

        str_val = "MessageSerializerRegistry: {} serializer(s) registered [{}]".format(
            self.count, ", ".join(format_names)
        )
        return str_val
