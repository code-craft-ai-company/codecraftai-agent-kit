"""
    Defines the ConcurrencyBridge utility for cross-model communication
    between agents using different concurrency models in the
    codecraftai-agent-kit framework.

    The bridge detects the concurrency model of a target agent and
    adapts lifecycle invocations and hook calls accordingly, allowing
    parent-child agents with different concurrency models to communicate.
"""

import asyncio

from typing import Callable
from typing import Optional

from ccai.agentkit.concurrencymodel import ConcurrencyModel
from ccai.agentkit.transitionrecord import TransitionRecord


def _get_agent_concurrency_model(agent: object) -> ConcurrencyModel:
    """
        Detects the concurrency model of an agent.

        Checks for a concurrency_model property on the agent. If not
        present, returns None to indicate a standard synchronous agent.

        :param agent: The agent instance to inspect.

        :returns: The ConcurrencyModel of the agent, or None for standard agents.
    """
    has_model = hasattr(agent, "concurrency_model")

    if has_model is True:
        model = agent.concurrency_model
        return model

    return None


class ConcurrencyBridge:
    """
        Utility class for cross-model communication between agents
        using different concurrency models.

        Provides static methods to invoke lifecycle operations and
        hook callbacks across concurrency model boundaries. When a
        parent agent and child agent use different concurrency models,
        the bridge adapts the invocation accordingly.
    """

    @staticmethod
    def invoke_lifecycle(agent: object, method_name: str) -> None:
        """
            Invokes a lifecycle method on an agent, adapting to its
            concurrency model.

            For AsyncAgent instances, the async version of the method
            is run on the event loop. For ThreadedAgent and PooledAgent
            instances, the method is called directly (it handles its
            own threading). For standard agents, the method is called
            synchronously.

            :param agent: The agent instance to invoke the method on.
            :param method_name: The name of the lifecycle method
                (e.g., 'initialize', 'start', 'stop').
        """
        model = _get_agent_concurrency_model(agent)

        if model is ConcurrencyModel.ASYNCIO:
            async_method_name = "async_{}".format(method_name)
            has_async_method = hasattr(agent, async_method_name)

            if has_async_method is True:
                async_method = getattr(agent, async_method_name)
                _run_coroutine(async_method())
            else:
                method = getattr(agent, method_name)
                method()
        else:
            method = getattr(agent, method_name)
            method()

        return

    @staticmethod
    def invoke_hook(agent: object, callback: Callable,
                    record: TransitionRecord) -> None:
        """
            Invokes a hook callback on an agent, adapting to the
            concurrency model of the agent that owns the hook.

            For async callbacks, the coroutine is run on the event loop.
            For synchronous callbacks, they are called directly.

            :param agent: The agent instance to pass to the callback.
            :param callback: The hook callback to invoke.
            :param record: The TransitionRecord to pass to the callback.
        """
        is_coroutine_function = asyncio.iscoroutinefunction(callback)

        if is_coroutine_function is True:
            coroutine = callback(agent, record)
            _run_coroutine(coroutine)
        else:
            callback(agent, record)

        return

    @staticmethod
    def adapt_parent_child(parent: object, child: object,
                           method_name: str) -> None:
        """
            Adapts a lifecycle call from a parent agent to a child agent
            that may use a different concurrency model.

            Detects the child's concurrency model and invokes the
            lifecycle method appropriately.

            :param parent: The parent agent instance.
            :param child: The child agent instance.
            :param method_name: The lifecycle method name to invoke on the child.
        """
        ConcurrencyBridge.invoke_lifecycle(child, method_name)
        return


def _run_coroutine(coroutine: object) -> None:
    """
        Runs a coroutine, handling both cases where an event loop
        is already running and where one needs to be created.

        :param coroutine: The coroutine to run.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        asyncio.ensure_future(coroutine)
    else:
        asyncio.run(coroutine)

    return
