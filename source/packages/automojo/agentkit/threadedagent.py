"""
    Defines the ThreadedAgent abstract base class for agents that run
    on a dedicated thread in the automojo-agent-kit framework.

    ThreadedAgent extends Agent and provides a run() method that starts
    the agent's lifecycle on a dedicated thread. Subclasses implement
    the abstract lifecycle methods which are invoked on the agent's thread.
"""

import abc
import threading

from typing import Optional

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.concurrencymodel import ConcurrencyModel
from automojo.agentkit.lifecyclestate import LifecycleState


class ThreadedAgent(Agent):
    """
        Abstract base class for agents that run on a dedicated thread.

        Each ThreadedAgent instance manages its own thread. The run()
        method starts the agent's thread, which initializes and starts
        the agent. Subclasses must implement the abstract lifecycle
        methods: initialize, start, pause, resume, stop, and reset.

        :param configuration: The AgentConfiguration for this agent.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        super().__init__(configuration)
        self._concurrency_model: ConcurrencyModel = ConcurrencyModel.THREAD
        self._thread: Optional[threading.Thread] = None
        self._thread_started: bool = False
        return

    @property
    def concurrency_model(self) -> ConcurrencyModel:
        """
            The concurrency model used by this agent.

            :returns: ConcurrencyModel.THREAD
        """
        return self._concurrency_model

    @property
    def thread(self) -> Optional[threading.Thread]:
        """
            The dedicated thread for this agent, or None if not started.

            :returns: The threading.Thread instance or None.
        """
        return self._thread

    def run(self) -> None:
        """
            Starts the agent's dedicated thread.

            Creates a daemon thread that calls the _thread_entry method.
            The thread is named after the agent's identifier for
            debuggability.
        """
        thread_name = "ThreadedAgent-{}".format(self._identity.identifier)
        self._thread = threading.Thread(
            target=self._thread_entry,
            name=thread_name,
            daemon=True
        )
        self._thread_started = True
        self._thread.start()
        return

    def _thread_entry(self) -> None:
        """
            Entry point for the agent's dedicated thread.

            Calls initialize and start on the agent. Subclasses can
            override this method to customize the thread behavior.
        """
        self.initialize()
        self.start()
        return

    def join(self, timeout: Optional[float] = None) -> None:
        """
            Waits for the agent's thread to complete.

            :param timeout: Optional timeout in seconds to wait for the thread.
        """
        if self._thread is not None:
            self._thread.join(timeout=timeout)

        return
