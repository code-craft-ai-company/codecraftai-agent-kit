"""
    Defines the DebugInspector class that provides read-only access
    to the current agent state during a DebugSession pause.

    The DebugInspector wraps an Agent instance and exposes read-only
    properties and methods for inspecting lifecycle state, identity,
    correlation context, tool names, LLM providers, memory store
    names, metrics snapshots, active spans, and execution recordings.

    Uses defensive access via getattr with defaults where the Agent
    class may not yet have all observability methods available.
"""


class DebugInspector:
    """
        A component that provides read-only access to the current
        agent state during a DebugSession pause.

        Wraps an Agent instance and exposes read-only properties
        and methods for inspecting the agent's internal state
        without modifying agent behavior.

        :param agent: The Agent instance to inspect.
    """

    def __init__(self, agent) -> None:

        self._agent = agent

        return

    @property
    def lifecycle_state(self):
        """
            The agent's current lifecycle state.

            :returns: The LifecycleState value, or None if not
                available.
        """
        state = getattr(self._agent, "state", None)
        return state

    @property
    def identity(self):
        """
            The agent's identity.

            :returns: The AgentIdentity instance, or None if not
                available.
        """
        identity = getattr(self._agent, "identity", None)
        return identity

    @property
    def correlation_context(self):
        """
            The agent's current correlation context.

            :returns: The CorrelationContext instance, or None if
                not available.
        """
        observability = getattr(self._agent, "observability", None)
        if observability is not None:
            logger = getattr(observability, "logger", None)
            if logger is not None:
                context = getattr(logger, "correlation_context", None)
                return context

        return None

    def get_tool_names(self) -> list:
        """
            Returns the list of registered tool names from the
            agent's tool registry.

            :returns: A list of tool name strings, or an empty
                list if not available.
        """
        tool_registry = getattr(self._agent, "tool_registry", None)
        if tool_registry is not None:
            names_method = getattr(tool_registry, "list_names", None)
            if names_method is not None:
                names = names_method()
                return names

        return []

    def get_llm_providers(self) -> list:
        """
            Returns the list of registered LLM provider name-model
            pairs from the agent's LLM provider registry.

            :returns: A list of provider entries, or an empty list
                if not available.
        """
        llm_registry = getattr(self._agent, "llm_provider_registry", None)
        if llm_registry is not None:
            providers_method = getattr(llm_registry, "list_all", None)
            if providers_method is not None:
                providers = providers_method()
                return providers

        return []

    def get_memory_store_names(self) -> list:
        """
            Returns the list of registered memory store names from
            the agent's memory store registry.

            :returns: A list of memory store name strings, or an
                empty list if not available.
        """
        memory_registry = getattr(self._agent, "memory_store_registry", None)
        if memory_registry is not None:
            names_method = getattr(memory_registry, "list_names", None)
            if names_method is not None:
                names = names_method()
                return names

        return []

    def get_metrics_snapshot(self):
        """
            Returns the current MetricsSnapshot from the agent's
            MetricsCollector.

            :returns: A MetricsSnapshot instance, or None if not
                available.
        """
        observability = getattr(self._agent, "observability", None)
        if observability is not None:
            collector = getattr(observability, "metrics_collector", None)
            if collector is not None:
                snapshot_method = getattr(collector, "snapshot", None)
                if snapshot_method is not None:
                    snapshot = snapshot_method()
                    return snapshot

        return None

    def get_active_span(self):
        """
            Returns the current active TraceSpan from the agent's
            Tracer.

            :returns: A TraceSpan instance, or None if no span is
                active or not available.
        """
        observability = getattr(self._agent, "observability", None)
        if observability is not None:
            tracer = getattr(observability, "tracer", None)
            if tracer is not None:
                active_span = getattr(tracer, "active_span", None)
                return active_span

        return None

    def get_execution_recording(self):
        """
            Returns the current ExecutionRecording from the agent's
            ExecutionRecorder.

            :returns: An ExecutionRecording instance, or None if not
                available.
        """
        observability = getattr(self._agent, "observability", None)
        if observability is not None:
            recorder = getattr(observability, "execution_recorder", None)
            if recorder is not None:
                recording_method = getattr(recorder, "get_recording", None)
                if recording_method is not None:
                    recording = recording_method()
                    return recording

        return None

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class
            name and agent identifier.

            :returns: A repr string for debugging.
        """
        agent_identity = getattr(self._agent, "identity", None)
        if agent_identity is not None:
            agent_id = getattr(agent_identity, "identifier", "unknown")
        else:
            agent_id = "unknown"

        repr_str = "DebugInspector(agent_id={!r})".format(agent_id)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent
            identifier and current lifecycle state.

            :returns: A human-readable string.
        """
        agent_identity = getattr(self._agent, "identity", None)
        if agent_identity is not None:
            agent_id = getattr(agent_identity, "identifier", "unknown")
        else:
            agent_id = "unknown"

        state = self.lifecycle_state
        str_val = "DebugInspector: agent_id={}, lifecycle_state={}".format(
            agent_id, state
        )
        return str_val
