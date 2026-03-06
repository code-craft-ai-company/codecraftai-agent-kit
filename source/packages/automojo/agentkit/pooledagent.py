"""
    Defines the PooledAgent abstract base class for agents that run
    on a shared thread pool executor in the automojo-agent-kit framework.

    PooledAgent extends Agent and provides class-level pool management.
    Lifecycle methods are submitted to the shared pool for execution.
    Subclasses implement the abstract lifecycle methods.
"""

import abc
import threading

from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.concurrencymodel import ConcurrencyModel
from automojo.agentkit.lifecyclestate import LifecycleState


class PooledAgent(Agent):
    """
        Abstract base class for agents that run on a shared thread pool executor.

        Provides class-level pool management via get_pool() and shutdown_pool().
        Lifecycle methods can be submitted to the pool using submit_lifecycle().
        Subclasses must implement the abstract lifecycle methods: initialize,
        start, pause, resume, stop, and reset.

        :param configuration: The AgentConfiguration for this agent.
        :param max_workers: Optional maximum number of workers for the pool.
            Only used if the class-level pool has not been created yet.
    """

    _pool: Optional[ThreadPoolExecutor] = None
    _pool_lock: threading.Lock = threading.Lock()
    _pool_max_workers: Optional[int] = None

    def __init__(self, configuration: AgentConfiguration,
                 max_workers: Optional[int] = None) -> None:
        super().__init__(configuration)
        self._concurrency_model: ConcurrencyModel = ConcurrencyModel.THREAD_POOL

        if max_workers is not None:
            PooledAgent._pool_max_workers = max_workers

        return

    @property
    def concurrency_model(self) -> ConcurrencyModel:
        """
            The concurrency model used by this agent.

            :returns: ConcurrencyModel.THREAD_POOL
        """
        return self._concurrency_model

    @classmethod
    def get_pool(cls, max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """
            Returns the shared thread pool executor, creating it if necessary.

            :param max_workers: Optional maximum number of workers. Only used
                when creating the pool for the first time.

            :returns: The shared ThreadPoolExecutor instance.
        """
        with cls._pool_lock:
            if cls._pool is None:
                workers = max_workers
                if workers is None:
                    workers = cls._pool_max_workers
                cls._pool = ThreadPoolExecutor(max_workers=workers)

        return cls._pool

    @classmethod
    def shutdown_pool(cls, wait: bool = True) -> None:
        """
            Shuts down the shared thread pool executor.

            :param wait: Whether to wait for pending futures to complete.
        """
        with cls._pool_lock:
            if cls._pool is not None:
                cls._pool.shutdown(wait=wait)
                cls._pool = None

        return

    @classmethod
    def _reset_pool(cls) -> None:
        """
            Resets the pool reference without shutting down.

            This method is intended for testing purposes only.
        """
        with cls._pool_lock:
            cls._pool = None
            cls._pool_max_workers = None

        return

    def submit_lifecycle(self, method_name: str) -> Future:
        """
            Submits a lifecycle method to the shared thread pool for execution.

            :param method_name: The name of the lifecycle method to invoke
                (e.g., 'initialize', 'start', 'stop').

            :returns: A Future representing the pending execution.
        """
        pool = self.get_pool()
        method = getattr(self, method_name)
        future = pool.submit(method)
        return future
