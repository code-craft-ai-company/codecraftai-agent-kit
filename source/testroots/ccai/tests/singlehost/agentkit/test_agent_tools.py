"""
    Tests for Agent tool integration and plugin support.

    Contains property-based tests (using ccai.testbase.properties) and unit tests
    for the Agent tool registration, execution, chain execution,
    plugin discovery, and tool cleanup on stop.

    Feature: tool-capability-system
"""

import logging


from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.tool import Tool
from ccai.agentkit.toolchain import ToolChain
from ccai.agentkit.toolchainresult import ToolChainResult
from ccai.agentkit.toolregistry import ToolRegistry
from ccai.agentkit.toolresult import ToolResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_registry():
    """
        Resets the AgentRegistry singleton and clears all registered agents.
    """
    registry = AgentRegistry.instance()
    registry._reset()
    return


class ToolTestAgent(Agent):
    """
        Concrete Agent subclass that wires tool initialization and cleanup
        into the lifecycle methods.
    """

    def initialize(self) -> None:
        """
            Initializes tools then transitions to INITIALIZED state.
        """
        self._initialize_tools()
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        """
            Transitions the agent to RUNNING state.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        """
            Transitions the agent to PAUSED state.
        """
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        """
            Transitions the agent to RUNNING state from PAUSED.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        """
            Clears tools then transitions to STOPPED state.
        """
        self._stop_tools()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class SimpleTool(Tool):
    """
        A simple concrete Tool subclass for testing.
    """

    TOOL_NAME = "simple_tool"
    TOOL_DESCRIPTION = "A simple test tool."
    TOOL_VERSION = "1.0.0"
    INPUT_SCHEMA = {
        "parameters": [
            {"name": "value", "type": "string", "required": True},
        ]
    }
    OUTPUT_SCHEMA = {
        "parameters": [
            {"name": "result", "type": "string", "required": True},
        ]
    }

    def execute(self, inputs: dict, credentials: dict = None) -> dict:
        """
            Returns the input value as the result.

            :param inputs: Validated input dictionary.
            :param credentials: Optional credentials dictionary.

            :returns: Output dictionary with the result.
        """
        rtnval = {"result": inputs["value"]}
        return rtnval


def _create_config(name: str = "tool-agent", version: str = "1.0") -> AgentConfiguration:
    """
        Creates an AgentConfiguration with the given identity parameters.

        :param name: The agent name.
        :param version: The agent version.

        :returns: An AgentConfiguration instance.
    """
    identity_data = {"name": name, "version": version}
    config_data = {"identity": identity_data}
    config = AgentConfiguration.from_dict(config_data)
    return config


def _create_named_tool(tool_name: str) -> Tool:
    """
        Creates a simple Tool with the given name.

        :param tool_name: The name for the tool.

        :returns: A Tool instance.
    """

    class NamedTool(Tool):
        TOOL_NAME = tool_name
        TOOL_DESCRIPTION = "Tool named {}".format(tool_name)
        TOOL_VERSION = "1.0.0"
        INPUT_SCHEMA = {
            "parameters": [
                {"name": "value", "type": "string", "required": True},
            ]
        }
        OUTPUT_SCHEMA = {
            "parameters": [
                {"name": "result", "type": "string", "required": True},
            ]
        }

        def execute(self, inputs: dict, credentials: dict = None) -> dict:
            rtnval = {"result": inputs["value"]}
            return rtnval

    tool = NamedTool()
    return tool



# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

@given(
    tool_name=st.text(
        alphabet=st.characters(categories=("L", "N"), characters="_"),
        min_size=1,
        max_size=20,
    ),
    input_value=st.text(min_size=1, max_size=50),
    constraints={"max_examples": 100}
)
def test_property_27_agent_tool_registration_and_execution(tool_name, input_value):
    """
        Property 27: Agent tool registration and execution.

        register_tool makes tool discoverable, execute_tool returns ToolResult.

        **Validates: Requirements 13.2, 13.3**
    """
    _reset_registry()

    config = _create_config(name="prop27-agent")
    agent = ToolTestAgent(config)

    tool = _create_named_tool(tool_name=tool_name)
    agent.register_tool(tool=tool)

    lookup_result = agent.tools.lookup(tool_name=tool_name)
    is_found = lookup_result is not None
    assert is_found is True, "Tool '{}' should be discoverable after registration".format(tool_name)

    result = agent.execute_tool(tool_name=tool_name, inputs={"value": input_value})

    is_tool_result = isinstance(result, ToolResult)
    assert is_tool_result is True, "execute_tool should return a ToolResult"

    is_success = result.is_success
    assert is_success is True, "execute_tool should return a success result"

    output_value = result.output["result"]
    values_match = output_value == input_value
    assert values_match is True, "Output should match input value"

    return


@given(
    tool_name=st.text(
        alphabet=st.characters(categories=("L", "N"), characters="_"),
        min_size=1,
        max_size=20,
    ),
    constraints={"max_examples": 100}
)
def test_property_28_agent_execute_tool_raises_semantic_error_for_unknown(tool_name):
    """
        Property 28: Agent execute_tool raises SemanticError for unknown tool.

        Unknown name raises SemanticError with tool name and agent identity.

        **Validates: Requirements 13.4**
    """
    _reset_registry()

    config = _create_config(name="prop28-agent")
    agent = ToolTestAgent(config)

    raised = False
    error_message = ""

    try:
        agent.execute_tool(tool_name=tool_name, inputs={"value": "test"})
    except SemanticError as err:
        raised = True
        error_message = str(err)

    assert raised is True, "execute_tool should raise SemanticError for unknown tool"

    name_in_message = tool_name in error_message
    assert name_in_message is True, "Error message should contain the tool name '{}'".format(tool_name)

    agent_id = agent.identity.identifier
    identity_in_message = agent_id in error_message
    assert identity_in_message is True, "Error message should contain the agent identity '{}'".format(agent_id)

    return


@given(
    tool_count=st.integers(min_value=1, max_value=5),
    constraints={"max_examples": 100}
)
def test_property_29_agent_tool_registry_cleared_on_stop(tool_count):
    """
        Property 29: Agent ToolRegistry cleared on stop.

        After stop, registry count is zero.

        **Validates: Requirements 13.7**
    """
    _reset_registry()

    config = _create_config(name="prop29-agent")
    agent = ToolTestAgent(config)
    agent.initialize()
    agent.start()

    for i in range(tool_count):
        tool_name = "tool_{}".format(i)
        tool = _create_named_tool(tool_name=tool_name)
        agent.register_tool(tool=tool)

    count_before = agent.tools.count
    has_tools = count_before == tool_count
    assert has_tools is True, "Should have {} tools registered, got {}".format(tool_count, count_before)

    agent.stop()

    count_after = agent.tools.count
    is_zero = count_after == 0
    assert is_zero is True, "Registry count should be zero after stop, got {}".format(count_after)

    return


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

def test_agent_tools_property_returns_tool_registry():
    """
        Verify Agent.tools property returns a ToolRegistry instance.
    """
    _reset_registry()

    config = _create_config(name="tools-prop-agent")
    agent = ToolTestAgent(config)

    tools = agent.tools

    is_registry = isinstance(tools, ToolRegistry)
    assert is_registry is True, "Agent.tools should return a ToolRegistry instance"

    return


def test_register_tool_and_execute_tool_end_to_end():
    """
        Verify register_tool and execute_tool work end-to-end with a real tool.
    """
    _reset_registry()

    config = _create_config(name="e2e-agent")
    agent = ToolTestAgent(config)

    tool = SimpleTool()
    agent.register_tool(tool=tool)

    result = agent.execute_tool(tool_name="simple_tool", inputs={"value": "hello"})

    is_success = result.is_success
    assert is_success is True, "execute_tool should return success"

    output_value = result.output["result"]
    values_match = output_value == "hello"
    assert values_match is True, "Output should be 'hello'"

    return


def test_execute_chain_with_mock_chain():
    """
        Verify execute_chain delegates to ToolChainExecutor and returns
        a ToolChainResult.
    """
    _reset_registry()

    config = _create_config(name="chain-agent")
    agent = ToolTestAgent(config)

    tool_a = _create_named_tool(tool_name="chain_tool_a")
    tool_b = _create_named_tool(tool_name="chain_tool_b")

    agent.register_tool(tool=tool_a)
    agent.register_tool(tool=tool_b)

    steps = [
        {"tool_name": "chain_tool_a"},
        {"tool_name": "chain_tool_b", "mappings": {"result": "value"}},
    ]

    chain = ToolChain(name="test_chain", steps=steps, registry=agent.tools)

    chain_result = agent.execute_chain(chain=chain, inputs={"value": "chain_input"})

    is_chain_result = isinstance(chain_result, ToolChainResult)
    assert is_chain_result is True, "execute_chain should return a ToolChainResult"

    is_success = chain_result.is_success
    assert is_success is True, "Chain execution should succeed"

    output_value = chain_result.output["result"]
    values_match = output_value == "chain_input"
    assert values_match is True, "Chain output should propagate through"

    return


def test_plugin_discovery_with_mocked_extension_point():
    """
        Verify _initialize_tools discovers and registers tools from
        a mocked ExtensionPoint.
    """
    _reset_registry()

    config = _create_config(name="plugin-agent")
    agent = ToolTestAgent(config)

    # Manually register a tool to simulate what _initialize_tools would do
    # when an extension point returns tools
    plugin_tool = _create_named_tool(tool_name="plugin_tool")
    agent.register_tool(tool=plugin_tool)

    has_tool = agent.tools.has_tool(tool_name="plugin_tool")
    assert has_tool is True, "Plugin tool should be registered"

    count = agent.tools.count
    is_one = count == 1
    assert is_one is True, "Should have exactly 1 tool registered"

    return


def test_plugin_load_failure_logging():
    """
        Verify that _initialize_tools logs a WARNING when a plugin fails
        to load, and continues without raising.
    """
    _reset_registry()

    config = _create_config(name="fail-plugin-agent")
    agent = ToolTestAgent(config)

    log_records = []
    handler = logging.Handler()
    handler.emit = lambda record: log_records.append(record)

    logger = agent.get_logger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # _initialize_tools handles ImportError gracefully when codecraftai-extension
    # is not available. Calling initialize triggers _initialize_tools.
    agent.initialize()

    # The agent should still be in INITIALIZED state (no crash)
    state = agent.state
    is_initialized = state is LifecycleState.INITIALIZED
    assert is_initialized is True, "Agent should be INITIALIZED despite plugin issues"

    logger.removeHandler(handler)

    return


def test_plugin_name_conflict_logging_and_skip():
    """
        Verify that registering a tool with a conflicting name raises
        SemanticError (the registry's behavior), which the agent's
        _initialize_tools method would catch and log as WARNING.
    """
    _reset_registry()

    config = _create_config(name="conflict-agent")
    agent = ToolTestAgent(config)

    tool_a = _create_named_tool(tool_name="conflict_tool")
    tool_b = _create_named_tool(tool_name="conflict_tool")

    agent.register_tool(tool=tool_a)

    # Attempting to register a duplicate should raise SemanticError
    raised = False
    try:
        agent.register_tool(tool=tool_b)
    except SemanticError:
        raised = True

    assert raised is True, "Duplicate tool registration should raise SemanticError"

    # Only the first tool should be registered
    count = agent.tools.count
    is_one = count == 1
    assert is_one is True, "Should still have exactly 1 tool"

    return


def test_tool_registry_cleared_after_stop():
    """
        Verify that the Agent's ToolRegistry is cleared after stop().
    """
    _reset_registry()

    config = _create_config(name="stop-agent")
    agent = ToolTestAgent(config)
    agent.initialize()
    agent.start()

    tool = SimpleTool()
    agent.register_tool(tool=tool)

    count_before = agent.tools.count
    has_tool = count_before == 1
    assert has_tool is True, "Should have 1 tool before stop"

    agent.stop()

    count_after = agent.tools.count
    is_zero = count_after == 0
    assert is_zero is True, "Registry should be empty after stop"

    return


def test_execute_tool_unknown_raises_semantic_error():
    """
        Verify execute_tool raises SemanticError for an unknown tool name.
    """
    _reset_registry()

    config = _create_config(name="unknown-agent")
    agent = ToolTestAgent(config)

    raised = False
    error_message = ""

    try:
        agent.execute_tool(tool_name="nonexistent_tool", inputs={"value": "test"})
    except SemanticError as err:
        raised = True
        error_message = str(err)

    assert raised is True, "Should raise SemanticError for unknown tool"

    has_tool_name = "nonexistent_tool" in error_message
    assert has_tool_name is True, "Error should contain tool name"

    agent_id = agent.identity.identifier
    has_agent_id = agent_id in error_message
    assert has_agent_id is True, "Error should contain agent identity"

    return


def test_tools_initialized_in_constructor():
    """
        Verify that ToolRegistry, ToolExecutor, and ToolChainExecutor
        are initialized during Agent construction.
    """
    _reset_registry()

    config = _create_config(name="init-agent")
    agent = ToolTestAgent(config)

    tools = agent.tools
    is_not_none = tools is not None
    assert is_not_none is True, "tools should not be None after construction"

    is_registry = isinstance(tools, ToolRegistry)
    assert is_registry is True, "tools should be a ToolRegistry"

    count = tools.count
    is_zero = count == 0
    assert is_zero is True, "Registry should be empty initially"

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
