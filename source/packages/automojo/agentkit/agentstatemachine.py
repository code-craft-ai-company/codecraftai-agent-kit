"""
    Defines the AgentStateMachine class that governs valid lifecycle
    state transitions for agents in the automojo-agent-kit framework.

    The state machine enforces a well-defined transition table, records
    transition history, and provides thread-safe state management.
"""

import os
import threading

from datetime import datetime
from datetime import timezone
from typing import Dict
from typing import List

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.transitionrecord import TransitionRecord


class AgentStateMachine:
    """
        State machine that enforces valid lifecycle transitions for an agent.

        Manages the current lifecycle state, validates transitions against
        a predefined transition table, and records a history of all
        transitions with timestamps.
    """

    VALID_TRANSITIONS: Dict[LifecycleState, List[LifecycleState]] = {
        LifecycleState.CREATED: [LifecycleState.INITIALIZED],
        LifecycleState.INITIALIZED: [LifecycleState.RUNNING, LifecycleState.STOPPED],
        LifecycleState.RUNNING: [LifecycleState.PAUSED, LifecycleState.STOPPED, LifecycleState.ERROR],
        LifecycleState.PAUSED: [LifecycleState.RUNNING, LifecycleState.STOPPED],
        LifecycleState.ERROR: [LifecycleState.STOPPED],
        LifecycleState.STOPPED: [LifecycleState.INITIALIZED],
    }

    def __init__(self) -> None:
        self._current_state: LifecycleState = LifecycleState.CREATED
        self._history: List[TransitionRecord] = []
        self._lock: threading.Lock = threading.Lock()
        return

    @property
    def current_state(self) -> LifecycleState:
        """
            The current lifecycle state of the state machine.

            :returns: The current LifecycleState.
        """
        return self._current_state

    @property
    def transition_history(self) -> List[TransitionRecord]:
        """
            The history of all state transitions as a list of TransitionRecord instances.

            :returns: A list of TransitionRecord instances in chronological order.
        """
        return list(self._history)

    def get_valid_transitions(self) -> List[LifecycleState]:
        """
            Returns the list of valid target states from the current state.

            :returns: A list of LifecycleState values that are valid targets.
        """
        valid_targets = list(self.VALID_TRANSITIONS[self._current_state])
        return valid_targets

    def transition_to(self, target_state: LifecycleState, metadata: dict = None) -> TransitionRecord:
        """
            Attempts to transition the state machine to the specified target state.

            Validates the transition against the transition table, records the
            transition in history, and returns the transition record.

            :param target_state: The desired target LifecycleState.
            :param metadata: Optional dictionary of metadata for the transition.

            :returns: A TransitionRecord capturing the transition details.
            :raises: SemanticError
        """
        with self._lock:
            valid_targets = self.VALID_TRANSITIONS[self._current_state]
            is_valid = target_state in valid_targets

            if is_valid is not True:
                valid_names = [state.value for state in valid_targets]
                err_msg_lines = [
                    "Invalid state transition requested."
                ]
                err_msg_lines.append("  Current state: {}".format(self._current_state.value))
                err_msg_lines.append("  Target state: {}".format(target_state.value))
                err_msg_lines.append("  Valid transitions from {}: {}".format(
                    self._current_state.value, valid_names
                ))
                err_msg = os.linesep.join(err_msg_lines)
                raise SemanticError(err_msg)

            previous_state = self._current_state
            now = datetime.now(tz=timezone.utc)

            self._current_state = target_state

            record = TransitionRecord(
                previous_state=previous_state,
                new_state=target_state,
                timestamp=now,
                metadata=metadata
            )
            self._history.append(record)

        return record

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name and current state.

            :returns: A repr string for debugging.
        """
        repr_str = "AgentStateMachine(current_state={!r})".format(self._current_state)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable string of the current state.

            :returns: A string describing the current state.
        """
        str_val = "AgentStateMachine: {}".format(self._current_state.value)
        return str_val
