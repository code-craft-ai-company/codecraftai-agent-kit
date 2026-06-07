"""
    Defines the DebugSession class that enables step-through execution
    of agent operations.

    A DebugSession manages a list of Breakpoint objects and pauses
    execution when an event matches a registered breakpoint. When
    paused, a registered pause callback is invoked with a DebugInspector
    instance for read-only state inspection. The session supports
    continue, step, start, and stop operations.
"""

from typing import Optional

from ccai.agentkit.breakpoint import Breakpoint
from ccai.agentkit.debuginspector import DebugInspector


class DebugSession:
    """
        A component that enables step-through execution of agent
        operations.

        Manages breakpoints and pauses execution when an event
        matches a registered breakpoint. Provides a DebugInspector
        for read-only state inspection during pauses.

        :param agent: The Agent instance to debug.
    """

    def __init__(self, agent) -> None:

        self._agent = agent
        self._breakpoints = []
        self._is_paused = False
        self._is_active = False
        self._inspector = None
        self._pause_callback = None

        return

    @property
    def is_paused(self) -> bool:
        """
            Whether execution is currently paused at a breakpoint.

            :returns: True if paused, False otherwise.
        """
        return self._is_paused

    @property
    def is_active(self) -> bool:
        """
            Whether the debug session is currently enabled.

            :returns: True if the session is active, False otherwise.
        """
        return self._is_active

    @property
    def inspector(self) -> Optional[DebugInspector]:
        """
            The DebugInspector for the current pause, or None when
            execution is not paused.

            :returns: A DebugInspector instance or None.
        """
        return self._inspector

    def add_breakpoint(self, breakpoint: Breakpoint) -> None:
        """
            Registers a breakpoint with the session.

            :param breakpoint: The Breakpoint to register.
        """
        self._breakpoints.append(breakpoint)
        return

    def remove_breakpoint(self, breakpoint: Breakpoint) -> None:
        """
            Deregisters a breakpoint from the session.

            If the breakpoint is not found, this method does nothing.

            :param breakpoint: The Breakpoint to deregister.
        """
        if breakpoint in self._breakpoints:
            self._breakpoints.remove(breakpoint)

        return

    def list_breakpoints(self) -> list:
        """
            Returns the list of registered Breakpoint objects.

            :returns: A list copy of the registered breakpoints.
        """
        result = list(self._breakpoints)
        return result

    def clear_breakpoints(self) -> None:
        """
            Removes all registered breakpoints from the session.
        """
        self._breakpoints.clear()
        return

    def check_breakpoint(self, event_type: str, target_name: str = None) -> None:
        """
            Checks whether any registered breakpoint matches the given
            event type and target name. If a match is found and the
            session is active, pauses execution and invokes the
            registered pause callback with a DebugInspector.

            :param event_type: The event type string to check against.
            :param target_name: An optional target name string to check
                against.
        """
        if not self._is_active:
            return

        matched = False
        for bp in self._breakpoints:
            if bp.matches(event_type, target_name=target_name):
                matched = True
                break

        if not matched:
            return

        self._is_paused = True
        self._inspector = DebugInspector(self._agent)

        if self._pause_callback is not None:
            self._pause_callback(self._inspector)

        return

    def continue_execution(self) -> None:
        """
            Resumes execution after a pause. Clears the paused state
            and the inspector.
        """
        self._is_paused = False
        self._inspector = None
        return

    def step(self) -> None:
        """
            Resumes execution until the next breakpoint-eligible point
            is reached, regardless of whether a breakpoint is registered
            at that point. Clears the current paused state.
        """
        self._is_paused = False
        self._inspector = None
        return

    def start(self) -> None:
        """
            Enables the debug session. After calling start, breakpoint
            checks will be active.
        """
        self._is_active = True
        return

    def stop(self) -> None:
        """
            Disables the debug session and resumes any paused execution.
            Clears the paused state and inspector.
        """
        self._is_active = False
        self._is_paused = False
        self._inspector = None
        return

    def set_pause_callback(self, callback) -> None:
        """
            Sets the callback function to be invoked when execution
            is paused at a breakpoint. The callback receives a
            DebugInspector instance as its single argument.

            :param callback: A callable that accepts a DebugInspector.
        """
        self._pause_callback = callback
        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class
            name, agent identifier, breakpoint count, and pause state.

            :returns: A repr string for debugging.
        """
        agent_identity = getattr(self._agent, "identity", None)
        if agent_identity is not None:
            agent_id = getattr(agent_identity, "identifier", "unknown")
        else:
            agent_id = "unknown"

        breakpoint_count = len(self._breakpoints)
        repr_str = "DebugSession(agent_id={!r}, breakpoints={}, is_paused={})".format(
            agent_id, breakpoint_count, self._is_paused
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent
            identifier, breakpoint count, and whether execution is
            paused.

            :returns: A human-readable string.
        """
        agent_identity = getattr(self._agent, "identity", None)
        if agent_identity is not None:
            agent_id = getattr(agent_identity, "identifier", "unknown")
        else:
            agent_id = "unknown"

        breakpoint_count = len(self._breakpoints)
        str_val = "DebugSession: agent_id={}, breakpoints={}, is_paused={}".format(
            agent_id, breakpoint_count, self._is_paused
        )
        return str_val
