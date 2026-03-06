"""
    Defines the TransitionRecord class representing an immutable record
    of a lifecycle state transition in the automojo-agent-kit framework.
"""

from datetime import datetime

from typing import Optional

from automojo.agentkit.lifecyclestate import LifecycleState


class TransitionRecord:
    """
        Immutable record of a lifecycle state transition.

        Captures the previous state, new state, timestamp, and optional
        metadata associated with a state transition event.

        :param previous_state: The state before the transition.
        :param new_state: The state after the transition.
        :param timestamp: The UTC timestamp of the transition.
        :param metadata: Optional dictionary of metadata for the transition.
    """

    def __init__(self, previous_state: LifecycleState, new_state: LifecycleState,
                 timestamp: datetime, metadata: Optional[dict] = None) -> None:
        self._previous_state = previous_state
        self._new_state = new_state
        self._timestamp = timestamp

        if metadata is not None:
            self._metadata = dict(metadata)
        else:
            self._metadata = {}

        return

    @property
    def previous_state(self) -> LifecycleState:
        """
            The lifecycle state before the transition.

            :returns: The previous LifecycleState.
        """
        return self._previous_state

    @property
    def new_state(self) -> LifecycleState:
        """
            The lifecycle state after the transition.

            :returns: The new LifecycleState.
        """
        return self._new_state

    @property
    def timestamp(self) -> datetime:
        """
            The UTC timestamp when the transition occurred.

            :returns: The datetime of the transition.
        """
        return self._timestamp

    @property
    def metadata(self) -> dict:
        """
            A defensive copy of the metadata associated with the transition.

            :returns: A dictionary copy of the metadata.
        """
        return dict(self._metadata)

    def __repr__(self) -> str:
        """
            Returns a detailed string representation of the transition record.

            :returns: A repr string for debugging.
        """
        repr_str = "TransitionRecord(previous_state={!r}, new_state={!r}, timestamp={!r})".format(
            self._previous_state, self._new_state, self._timestamp
        )
        return repr_str
