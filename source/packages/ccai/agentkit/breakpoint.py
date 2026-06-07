"""
    Defines the Breakpoint class representing an immutable condition at
    which a DebugSession pauses execution.

    A Breakpoint contains a breakpoint type string validated against a
    set of valid types, an optional target name string, and an optional
    condition expression string. The matches method determines whether
    a given event type and target name satisfy the breakpoint criteria.
"""

import os

from typing import Optional

from ccai.agentkit.errors import SemanticError


class Breakpoint:
    """
        An immutable object representing a condition at which the
        DebugSession pauses execution.

        The breakpoint_type must be one of the VALID_TYPES. When a
        target_name is provided, the breakpoint only matches events
        with both a matching type and matching target name. When no
        target_name is provided, the breakpoint matches any event
        with a matching type.

        :param breakpoint_type: The type of breakpoint, must be one
            of VALID_TYPES.
        :param target_name: An optional target name to match against.
        :param condition: An optional condition expression string.
    """

    VALID_TYPES = (
        "lifecycle",
        "tool",
        "llm",
        "workflow_step",
        "message",
        "memory",
        "custom",
    )

    def __init__(self, breakpoint_type: str, target_name: str = None,
                 condition: str = None) -> None:

        if breakpoint_type not in self.VALID_TYPES:
            error_lines = [
                "Invalid breakpoint type: {!r}.".format(breakpoint_type),
                "Valid breakpoint types are: {}.".format(
                    ", ".join(self.VALID_TYPES)
                ),
            ]
            error_msg = os.linesep.join(error_lines)
            raise SemanticError(error_msg)

        self._breakpoint_type = breakpoint_type
        self._target_name = target_name
        self._condition = condition

        return

    @property
    def breakpoint_type(self) -> str:
        """
            The type of breakpoint.

            :returns: The breakpoint type string.
        """
        return self._breakpoint_type

    @property
    def target_name(self) -> Optional[str]:
        """
            The optional target name to match against.

            :returns: The target name string or None.
        """
        return self._target_name

    @property
    def condition(self) -> Optional[str]:
        """
            The optional condition expression string.

            :returns: The condition string or None.
        """
        return self._condition

    def matches(self, event_type: str, target_name: str = None) -> bool:
        """
            Determines whether this breakpoint matches the given event
            type and optional target name.

            When the breakpoint has a target_name, both the breakpoint
            type and target name must match. When the breakpoint has no
            target_name, only the breakpoint type must match.

            :param event_type: The event type string to match against.
            :param target_name: An optional target name string to match
                against.

            :returns: True if the breakpoint matches, False otherwise.
        """
        if self._breakpoint_type != event_type:
            return False

        if self._target_name is not None:
            if self._target_name != target_name:
                return False

        return True

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the breakpoint fields.

            :returns: A dictionary containing all breakpoint fields.
        """
        result = {
            "breakpoint_type": self._breakpoint_type,
            "target_name": self._target_name,
            "condition": self._condition,
        }
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            breakpoint type, and target name.

            :returns: A repr string for debugging.
        """
        repr_str = "Breakpoint(breakpoint_type={!r}, target_name={!r})".format(
            self._breakpoint_type, self._target_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the breakpoint
            type, target name, and condition expression.

            :returns: A human-readable string.
        """
        str_val = "Breakpoint: type={}, target_name={}, condition={}".format(
            self._breakpoint_type, self._target_name, self._condition
        )
        return str_val
