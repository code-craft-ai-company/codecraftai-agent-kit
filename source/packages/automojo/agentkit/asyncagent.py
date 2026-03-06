"""
    Defines the AsyncAgent abstract base class for agents that run
    their lifecycle methods as async coroutines on an asyncio event loop
    in the automojo-agent-kit framework.

    AsyncAgent extends Agent and provides async versions of all lifecycle
    methods. Subclasses override the async_* methods to implement their
    async behavior. The synchronous lifecycle methods delegate to the
    async versions using the event loop.
"""

import abc
import asyncio

from typing import Optional

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.concurrencymodel import ConcurrencyModel
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.transitionrecord import TransitionRecord


class AsyncAgent(Agent):
    """
        Abstract base class for agents that run lifecycle methods as
        async coroutines on an asyncio event loop.

        Subclasses must implement the async lifecycle methods:
        async_initialize, async_start, async_pause, async_resume,
        async_stop, and async_reset.

        The synchronous lifecycle methods (initialize, start, etc.)
        delegate to the async versions by running them on the event loop.

        :param configuration: The AgentConfiguration for this agent.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        super().__init__(configuration)
        self._concurrency_model: ConcurrencyModel = ConcurrencyModel.ASYNCIO
        return

    @property
    def concurrency_model(self) -> ConcurrencyModel:
        """
            The concurrency model used by this agent.

            :returns: ConcurrencyModel.ASYNCIO
        """
        return self._concurrency_model

    # -----------------------------------------------------------------------
    # Async lifecycle transition helper
    # -----------------------------------------------------------------------

    async def _async_perform_transition(self, target_state: LifecycleState,
                                        transition_point: str,
                                        metadata: Optional[dict] = None) -> TransitionRecord:
        """
            Performs a lifecycle state transition in an async context.

            Delegates to the synchronous _perform_transition method from
            the Agent base class.

            :param target_state: The target LifecycleState.
            :param transition_point: The hook transition point to invoke.
            :param metadata: Optional metadata for the transition.

            :returns: The TransitionRecord for the transition.
        """
        record = self._perform_transition(target_state, transition_point, metadata=metadata)
        return record

    # -----------------------------------------------------------------------
    # Synchronous lifecycle methods (delegate to async versions)
    # -----------------------------------------------------------------------

    def initialize(self) -> None:
        """
            Initializes the agent by running the async_initialize coroutine.
        """
        self._run_async(self.async_initialize())
        return

    def start(self) -> None:
        """
            Starts the agent by running the async_start coroutine.
        """
        self._run_async(self.async_start())
        return

    def pause(self) -> None:
        """
            Pauses the agent by running the async_pause coroutine.
        """
        self._run_async(self.async_pause())
        return

    def resume(self) -> None:
        """
            Resumes the agent by running the async_resume coroutine.
        """
        self._run_async(self.async_resume())
        return

    def stop(self) -> None:
        """
            Stops the agent by running the async_stop coroutine.
        """
        self._run_async(self.async_stop())
        return

    def reset(self) -> None:
        """
            Resets the agent by running the async_reset coroutine.
        """
        self._run_async(self.async_reset())
        return

    # -----------------------------------------------------------------------
    # Async lifecycle methods (to be overridden by subclasses)
    # -----------------------------------------------------------------------

    @abc.abstractmethod
    async def async_initialize(self) -> None:
        """
            Async initialization of the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    async def async_start(self) -> None:
        """
            Async start of the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    async def async_pause(self) -> None:
        """
            Async pause of the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    async def async_resume(self) -> None:
        """
            Async resume of the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    async def async_stop(self) -> None:
        """
            Async stop of the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    async def async_reset(self) -> None:
        """
            Async reset of the agent. Subclasses must implement this method.
        """

    # -----------------------------------------------------------------------
    # Internal helper
    # -----------------------------------------------------------------------

    def _run_async(self, coroutine: object) -> None:
        """
            Runs an async coroutine, handling both cases where an event loop
            is already running and where one needs to be created.

            :param coroutine: The coroutine to run.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            # We are inside a running event loop; create a task
            # The caller must await this or use the event loop to complete it
            future = asyncio.ensure_future(coroutine)
            # If we are in a sync context within an async loop, we cannot block.
            # This path is for when the sync method is called from async code.
            return
        else:
            asyncio.run(coroutine)

        return
