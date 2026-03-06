"""
    Defines the LifecycleState enum representing the possible states
    of an agent in the automojo-agent-kit framework.
"""

import enum


class LifecycleState(enum.Enum):
    """
        Enum representing the lifecycle states of an agent.

        Agents transition through these states according to the
        valid transition rules defined in the AgentStateMachine.
    """

    CREATED = "CREATED"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
