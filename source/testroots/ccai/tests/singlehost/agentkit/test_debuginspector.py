"""
    Unit tests for the ccai.agentkit.debuginspector module.

    Tests the DebugInspector class: read-only access to agent state
    using mocked Agent objects via ccai.testbase.mocking.Mock.
"""

from ccai.agentkit.debuginspector import DebugInspector
from ccai.testbase.mocking import Mock


def _create_mock_agent():
    """
        Creates a mock Agent with recursive attribute access configured.

        :returns: A Mock object configured to simulate an Agent.
    """
    mock_agent = Mock()
    mock_agent.configure(recursive=True)
    return mock_agent


def test_lifecycle_state_returns_agent_state():
    """
        Verify that lifecycle_state returns the agent's state property.
    """
    mock_agent = _create_mock_agent()
    ctx = mock_agent.mock_context()
    ctx.set_attribute("state", "RUNNING")

    inspector = DebugInspector(mock_agent)

    result = inspector.lifecycle_state
    assert result == "RUNNING", "lifecycle_state should return agent state"
    return


def test_identity_returns_agent_identity():
    """
        Verify that identity returns the agent's identity property.
    """
    mock_agent = _create_mock_agent()
    mock_identity = Mock()
    mock_identity.configure(recursive=True)
    mock_identity.mock_context().set_attribute("identifier", "agent-001")

    ctx = mock_agent.mock_context()
    ctx.set_attribute("identity", mock_identity)

    inspector = DebugInspector(mock_agent)

    result = inspector.identity
    assert result is mock_identity, "identity should return agent identity"
    return


def test_correlation_context_returns_context():
    """
        Verify that correlation_context returns the logger's correlation
        context from the observability pipeline.
    """
    mock_agent = _create_mock_agent()

    mock_context = Mock()
    mock_context.configure(recursive=True)

    mock_logger = Mock()
    mock_logger.configure(recursive=True)
    mock_logger.mock_context().set_attribute("correlation_context", mock_context)

    mock_observability = Mock()
    mock_observability.configure(recursive=True)
    mock_observability.mock_context().set_attribute("logger", mock_logger)

    mock_agent.mock_context().set_attribute("observability", mock_observability)

    inspector = DebugInspector(mock_agent)

    result = inspector.correlation_context
    assert result is mock_context, "correlation_context should return the logger's context"
    return


def test_correlation_context_returns_none_without_observability():
    """
        Verify that correlation_context returns None when the agent
        has no observability pipeline.
    """
    mock_agent = Mock()
    ctx = mock_agent.mock_context()
    ctx.set_attribute("observability", None)

    inspector = DebugInspector(mock_agent)

    result = inspector.correlation_context
    assert result is None, "correlation_context should be None without observability"
    return


def test_get_tool_names_returns_names():
    """
        Verify that get_tool_names returns tool names from the agent's
        tool registry.
    """
    mock_agent = _create_mock_agent()

    mock_tool_registry = Mock()
    mock_tool_registry.configure(recursive=True)
    mock_tool_registry.mock_context().mock_method(
        "list_names", return_value=["search", "execute"]
    )

    mock_agent.mock_context().set_attribute("tool_registry", mock_tool_registry)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_tool_names()
    assert result == ["search", "execute"], "get_tool_names should return tool names"
    return


def test_get_tool_names_returns_empty_without_registry():
    """
        Verify that get_tool_names returns an empty list when the agent
        has no tool registry.
    """
    mock_agent = Mock()
    ctx = mock_agent.mock_context()
    ctx.set_attribute("tool_registry", None)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_tool_names()
    assert result == [], "get_tool_names should return empty list without registry"
    return


def test_get_llm_providers_returns_providers():
    """
        Verify that get_llm_providers returns providers from the agent's
        LLM provider registry.
    """
    mock_agent = _create_mock_agent()

    mock_llm_registry = Mock()
    mock_llm_registry.configure(recursive=True)
    mock_llm_registry.mock_context().mock_method(
        "list_all", return_value=["openai/gpt-4", "anthropic/claude"]
    )

    mock_agent.mock_context().set_attribute("llm_provider_registry", mock_llm_registry)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_llm_providers()
    assert result == ["openai/gpt-4", "anthropic/claude"], (
        "get_llm_providers should return provider list"
    )
    return


def test_get_llm_providers_returns_empty_without_registry():
    """
        Verify that get_llm_providers returns an empty list when the
        agent has no LLM provider registry.
    """
    mock_agent = Mock()
    ctx = mock_agent.mock_context()
    ctx.set_attribute("llm_provider_registry", None)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_llm_providers()
    assert result == [], "get_llm_providers should return empty list without registry"
    return


def test_get_memory_store_names_returns_names():
    """
        Verify that get_memory_store_names returns names from the agent's
        memory store registry.
    """
    mock_agent = _create_mock_agent()

    mock_memory_registry = Mock()
    mock_memory_registry.configure(recursive=True)
    mock_memory_registry.mock_context().mock_method(
        "list_names", return_value=["short_term", "long_term"]
    )

    mock_agent.mock_context().set_attribute("memory_store_registry", mock_memory_registry)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_memory_store_names()
    assert result == ["short_term", "long_term"], (
        "get_memory_store_names should return store names"
    )
    return


def test_get_metrics_snapshot_returns_snapshot():
    """
        Verify that get_metrics_snapshot returns a snapshot from the
        agent's metrics collector.
    """
    mock_agent = _create_mock_agent()

    mock_snapshot = Mock()
    mock_snapshot.configure(recursive=True)

    mock_collector = Mock()
    mock_collector.configure(recursive=True)
    mock_collector.mock_context().mock_method("snapshot", return_value=mock_snapshot)

    mock_observability = Mock()
    mock_observability.configure(recursive=True)
    mock_observability.mock_context().set_attribute("metrics_collector", mock_collector)

    mock_agent.mock_context().set_attribute("observability", mock_observability)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_metrics_snapshot()
    assert result is mock_snapshot, "get_metrics_snapshot should return the snapshot"
    return


def test_get_active_span_returns_span():
    """
        Verify that get_active_span returns the active span from the
        agent's tracer.
    """
    mock_agent = _create_mock_agent()

    mock_span = Mock()
    mock_span.configure(recursive=True)

    mock_tracer = Mock()
    mock_tracer.configure(recursive=True)
    mock_tracer.mock_context().set_attribute("active_span", mock_span)

    mock_observability = Mock()
    mock_observability.configure(recursive=True)
    mock_observability.mock_context().set_attribute("tracer", mock_tracer)

    mock_agent.mock_context().set_attribute("observability", mock_observability)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_active_span()
    assert result is mock_span, "get_active_span should return the active span"
    return


def test_get_execution_recording_returns_recording():
    """
        Verify that get_execution_recording returns the recording from
        the agent's execution recorder.
    """
    mock_agent = _create_mock_agent()

    mock_recording = Mock()
    mock_recording.configure(recursive=True)

    mock_recorder = Mock()
    mock_recorder.configure(recursive=True)
    mock_recorder.mock_context().mock_method("get_recording", return_value=mock_recording)

    mock_observability = Mock()
    mock_observability.configure(recursive=True)
    mock_observability.mock_context().set_attribute("execution_recorder", mock_recorder)

    mock_agent.mock_context().set_attribute("observability", mock_observability)

    inspector = DebugInspector(mock_agent)

    result = inspector.get_execution_recording()
    assert result is mock_recording, "get_execution_recording should return the recording"
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    mock_agent = _create_mock_agent()
    mock_identity = Mock()
    mock_identity.configure(recursive=True)
    mock_identity.mock_context().set_attribute("identifier", "agent-001")
    mock_agent.mock_context().set_attribute("identity", mock_identity)

    inspector = DebugInspector(mock_agent)

    repr_str = repr(inspector)
    assert "DebugInspector" in repr_str, "__repr__ should contain class name"
    return


def test_repr_contains_agent_id():
    """
        Verify that __repr__ contains the agent identifier.
    """
    mock_agent = _create_mock_agent()
    mock_identity = Mock()
    mock_identity.configure(recursive=True)
    mock_identity.mock_context().set_attribute("identifier", "agent-001")
    mock_agent.mock_context().set_attribute("identity", mock_identity)

    inspector = DebugInspector(mock_agent)

    repr_str = repr(inspector)
    assert "agent-001" in repr_str, "__repr__ should contain agent_id"
    return


def test_str_contains_lifecycle_state():
    """
        Verify that __str__ contains the lifecycle state.
    """
    mock_agent = _create_mock_agent()
    mock_identity = Mock()
    mock_identity.configure(recursive=True)
    mock_identity.mock_context().set_attribute("identifier", "agent-002")
    mock_agent.mock_context().set_attribute("identity", mock_identity)
    mock_agent.mock_context().set_attribute("state", "INITIALIZED")

    inspector = DebugInspector(mock_agent)

    str_val = str(inspector)
    assert "INITIALIZED" in str_val, "__str__ should contain lifecycle state"
    return
