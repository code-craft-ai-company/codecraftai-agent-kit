"""
    Defines the ConcurrencyModel enum representing the supported
    concurrency models for agents in the automojo-agent-kit framework.
"""

import enum


class ConcurrencyModel(enum.Enum):
    """
        Enum representing the concurrency models available for agents.

        Agents can run using different concurrency strategies depending
        on their workload and integration requirements.
    """

    ASYNCIO = "ASYNCIO"
    THREAD = "THREAD"
    THREAD_POOL = "THREAD_POOL"
