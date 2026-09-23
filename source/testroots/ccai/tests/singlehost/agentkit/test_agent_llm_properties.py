"""
    Property-based tests for Agent LLM integration.

    Uses the ccai.testbase.properties engine to verify:
    - Property 37: Agent LLMProviderRegistry cleared on stop
    - Property 38: Agent complete raises SemanticError for unknown provider
    - Property 39: LLM error fields are accessible

    **Validates: Requirements 12.4, 12.6, 15.2, 15.4**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmerrors import LLMRequestError, LLMResponseParsingError
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.llmprovider import LLMProvider


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


class LLMTestAgent(Agent):
    """
        Concrete Agent subclass for testing LLM integration properties.
    """

    def initialize(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        self._stop_llm_providers()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class StubLLMProvider(LLMProvider):
    """
        A concrete LLMProvider subclass for testing that does nothing.
    """

    def __init__(self, provider_name: str, model_name: str,
                 config: dict = None, credential_names: list = None,
                 tags: dict = None) -> None:
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            config=config,
            credential_names=credential_names,
            tags=tags,
        )
        return

    def complete(self, conversation, **kwargs):
        return None

    def complete_stream(self, conversation, handler, **kwargs):
        return None


def _create_config(name: str = "llm-prop-agent", version: str = "1.0") -> AgentConfiguration:
    """
        Creates an AgentConfiguration with the given identity parameters.
    """
    identity_data = {"name": name, "version": version}
    config_data = {"identity": identity_data}
    config = AgentConfiguration.from_dict(config_data)
    return config


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_identifier = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=15,
)

_model_name_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=15,
)

_error_category = st.sampled_from(list(LLMRequestError.VALID_CATEGORIES))

_content_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789 .,!?",
    min_size=0,
    max_size=300,
)

_error_message_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789 .,!?",
    min_size=1,
    max_size=100,
)


@composite
def _unique_provider_pairs(draw):
    """
        Draws a list of unique (provider_name, model_name) pairs.
    """
    count = draw(st.integers(min_value=1, max_value=5))
    pairs = []
    seen = set()

    for _ in range(count):
        pname = draw(_identifier)
        mname = draw(_model_name_text)
        key = (pname, mname)

        while key in seen:
            pname = draw(_identifier)
            mname = draw(_model_name_text)
            key = (pname, mname)

        seen.add(key)
        pairs.append(key)

    return pairs


# ---------------------------------------------------------------------------
# Property 37: Agent LLMProviderRegistry cleared on stop
# ---------------------------------------------------------------------------

@given(provider_pairs=_unique_provider_pairs(), constraints={"max_examples": 50})
def test_agent_llm_registry_cleared_on_stop(
    provider_pairs: list,
) -> None:
    """
        **Validates: Requirements 12.6**

        For any Agent with N registered LLMProviders, after the Agent
        transitions to STOPPED state, the Agent's LLMProviderRegistry
        count shall be zero.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    try:
        agent.initialize()
        agent.start()

        for pname, mname in provider_pairs:
            provider = StubLLMProvider(provider_name=pname, model_name=mname)
            agent.register_llm_provider(provider)

        assert agent.llm_providers.count == len(provider_pairs), (
            "Expected {} providers registered, got {}".format(
                len(provider_pairs), agent.llm_providers.count
            )
        )

        agent.stop()

        assert agent.llm_providers.count == 0, (
            "Expected 0 providers after stop, got {}".format(
                agent.llm_providers.count
            )
        )
    finally:
        _reset_registry()

    return


# ---------------------------------------------------------------------------
# Property 38: Agent complete raises SemanticError for unknown provider
# ---------------------------------------------------------------------------

@given(
    provider_name=_identifier,
    model_name=_model_name_text,
    constraints={"max_examples": 50},
)
def test_agent_complete_raises_semantic_error_for_unknown_provider(
    provider_name: str,
    model_name: str,
) -> None:
    """
        **Validates: Requirements 12.4**

        For any Agent and any provider_name + model_name combination not
        registered in the Agent's LLMProviderRegistry, calling complete()
        shall raise SemanticError that includes the provider name, model
        name, and agent identity.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    try:
        conversation = LLMConversation(messages=[
            LLMMessage(role="user", content="hello"),
        ])

        raised = False
        error_message = ""

        try:
            agent.complete(provider_name, model_name, conversation)
        except SemanticError as exc:
            raised = True
            error_message = str(exc)

        assert raised is True, (
            "complete() should raise SemanticError for unknown provider "
            "{!r} model {!r}".format(provider_name, model_name)
        )

        assert provider_name in error_message, (
            "SemanticError message should contain provider name {!r}, "
            "got: {}".format(provider_name, error_message)
        )

        assert model_name in error_message, (
            "SemanticError message should contain model name {!r}, "
            "got: {}".format(model_name, error_message)
        )

        agent_identifier = agent.identity.identifier
        assert agent_identifier in error_message, (
            "SemanticError message should contain agent identity {!r}, "
            "got: {}".format(agent_identifier, error_message)
        )
    finally:
        _reset_registry()

    return


# ---------------------------------------------------------------------------
# Property 39: LLM error fields are accessible
# ---------------------------------------------------------------------------

@given(
    provider_name=_identifier,
    model_name=_model_name_text,
    category=_error_category,
    constraints={"max_examples": 50},
)
def test_llm_request_error_fields_are_accessible(
    provider_name: str,
    model_name: str,
    category: str,
) -> None:
    """
        **Validates: Requirements 15.2**

        For any LLMRequestError, the provider_name, model_name, category,
        and cause properties shall be accessible and match the constructor
        arguments.
    """
    cause = Exception("test cause")

    error = LLMRequestError(
        provider_name=provider_name,
        model_name=model_name,
        category=category,
        cause=cause,
    )

    assert error.provider_name == provider_name, (
        "provider_name should be {!r}, got {!r}".format(
            provider_name, error.provider_name
        )
    )

    assert error.model_name == model_name, (
        "model_name should be {!r}, got {!r}".format(
            model_name, error.model_name
        )
    )

    assert error.category == category, (
        "category should be {!r}, got {!r}".format(
            category, error.category
        )
    )

    assert error.cause is cause, (
        "cause should be the same exception instance"
    )

    return


@given(
    parser_name=_identifier,
    raw_text=_content_text,
    error_message=_error_message_text,
    constraints={"max_examples": 50},
)
def test_llm_response_parsing_error_fields_are_accessible(
    parser_name: str,
    raw_text: str,
    error_message: str,
) -> None:
    """
        **Validates: Requirements 15.4**

        For any LLMResponseParsingError, the parser_name, raw_text, and
        error_message properties shall be accessible and match the
        constructor arguments.
    """
    error = LLMResponseParsingError(
        parser_name=parser_name,
        raw_text=raw_text,
        message=error_message,
    )

    assert error.parser_name == parser_name, (
        "parser_name should be {!r}, got {!r}".format(
            parser_name, error.parser_name
        )
    )

    assert error.raw_text == raw_text, (
        "raw_text should be {!r}, got {!r}".format(
            raw_text, error.raw_text
        )
    )

    assert error.error_message == error_message, (
        "error_message should be {!r}, got {!r}".format(
            error_message, error.error_message
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
