"""
    Integration tests for Agent LLM integration, plugin support, and
    retry/fallback behavior.

    Tests cover retry behavior, fallback behavior, all-providers-fail error,
    LLMProviderRegistry clearing on stop, logging at correct levels,
    _initialize_llm_providers plugin discovery, and _stop_llm_providers.

    Feature: llm-integration
"""

import logging
import logging.handlers
import time

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.costestimate import CostEstimate
from automojo.agentkit.costtracker import CostTracker
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.fallbackchain import FallbackChain
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.llmconversation import LLMConversation
from automojo.agentkit.llmerrors import LLMRequestError
from automojo.agentkit.llmmessage import LLMMessage
from automojo.agentkit.llmprovider import LLMProvider
from automojo.agentkit.llmproviderregistry import LLMProviderRegistry
from automojo.agentkit.llmresponse import LLMResponse
from automojo.agentkit.retrypolicy import RetryPolicy
from automojo.agentkit.tokenusage import TokenUsage


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
        Concrete Agent subclass for testing LLM integration.
    """

    def initialize(self) -> None:
        """
            Transitions the agent to INITIALIZED state.
        """
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
            Transitions the agent to STOPPED state, clearing LLM providers.
        """
        self._stop_llm_providers()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class FailingProvider(LLMProvider):
    """
        A concrete LLMProvider that fails a configurable number of times
        before returning a successful response.

        :param provider_name: The provider name.
        :param model_name: The model name.
        :param fail_count: Number of times to fail before succeeding.
        :param response: The LLMResponse to return on success.
    """

    def __init__(self, provider_name, model_name, fail_count=0,
                 response=None) -> None:
        super().__init__(provider_name=provider_name, model_name=model_name)
        self._fail_count = fail_count
        self._call_count = 0
        self._response = response
        return

    def complete(self, conversation, **kwargs):
        """
            Fails for the first fail_count calls, then returns the response.
        """
        self._call_count = self._call_count + 1

        if self._call_count <= self._fail_count:
            raise RuntimeError(
                "Provider failure #{}".format(self._call_count)
            )

        return self._response

    def complete_stream(self, conversation, handler, **kwargs):
        """
            Not implemented for testing.
        """
        return None


class StubLLMProvider(LLMProvider):
    """
        A concrete LLMProvider that always returns a preconfigured response.
    """

    def __init__(self, provider_name, model_name, response=None,
                 config=None, credential_names=None, tags=None) -> None:
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
            config=config,
            credential_names=credential_names,
            tags=tags,
        )
        self._response = response
        return

    def complete(self, conversation, **kwargs):
        """
            Returns the preconfigured LLMResponse.
        """
        return self._response

    def complete_stream(self, conversation, handler, **kwargs):
        """
            Not implemented for testing.
        """
        return self._response


class AlwaysFailingProvider(LLMProvider):
    """
        A concrete LLMProvider that always raises RuntimeError.
    """

    def __init__(self, provider_name, model_name) -> None:
        super().__init__(provider_name=provider_name, model_name=model_name)
        return

    def complete(self, conversation, **kwargs):
        """
            Always raises RuntimeError.
        """
        raise RuntimeError(
            "Always failing: {}/{}".format(
                self._provider_name, self._model_name
            )
        )

    def complete_stream(self, conversation, handler, **kwargs):
        """
            Not implemented for testing.
        """
        raise RuntimeError("Always failing")


def _create_config(name="llm-integration-agent", version="1.0"):
    """
        Creates an AgentConfiguration for testing.

        :param name: The agent name.
        :param version: The agent version.

        :returns: An AgentConfiguration instance.
    """
    identity_data = {"name": name, "version": version}
    config_data = {"identity": identity_data}
    config = AgentConfiguration.from_dict(config_data)
    return config


def _create_response(provider_name="openai", model_name="gpt-4"):
    """
        Creates a stub LLMResponse for testing.

        :param provider_name: The provider name.
        :param model_name: The model name.

        :returns: An LLMResponse instance.
    """
    message = LLMMessage(role="assistant", content="Test response")
    token_usage = TokenUsage(
        prompt_tokens=10, completion_tokens=5, total_tokens=15
    )
    response = LLMResponse(
        message=message,
        token_usage=token_usage,
        provider_name=provider_name,
        model_name=model_name,
        duration=0.5,
    )
    return response


def _create_conversation():
    """
        Creates a simple conversation for testing.

        :returns: An LLMConversation instance.
    """
    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])
    return conversation


# ---------------------------------------------------------------------------
# Tests: Retry behavior
# ---------------------------------------------------------------------------

def test_retry_with_failing_provider_then_succeeds():
    """
        Verifies that when a RetryPolicy is configured and the provider
        fails initially, the request is retried and eventually succeeds.
        Uses a FailingProvider that fails twice then returns a response.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    expected_response = _create_response(
        provider_name="openai", model_name="gpt-4"
    )

    provider = FailingProvider(
        provider_name="openai",
        model_name="gpt-4",
        fail_count=2,
        response=expected_response,
    )
    agent.register_llm_provider(provider)

    retry_policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    conversation = _create_conversation()

    result = agent.complete(
        "openai", "gpt-4", conversation, retry_policy=retry_policy
    )

    assert result is expected_response

    return


# ---------------------------------------------------------------------------
# Tests: Fallback behavior
# ---------------------------------------------------------------------------

def test_fallback_to_second_provider_on_primary_failure():
    """
        Verifies that when the primary provider always fails and a
        FallbackChain is configured, the fallback provider is used.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingProvider(
        provider_name="openai",
        model_name="gpt-4",
    )

    fallback_response = _create_response(
        provider_name="anthropic", model_name="claude-3"
    )
    fallback_provider = StubLLMProvider(
        provider_name="anthropic",
        model_name="claude-3",
        response=fallback_response,
    )

    agent.register_llm_provider(primary_provider)
    agent.register_llm_provider(fallback_provider)

    retry_policy = RetryPolicy(
        max_retries=1,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    fallback_chain = FallbackChain(providers=[
        ("openai", "gpt-4"),
        ("anthropic", "claude-3"),
    ])

    conversation = _create_conversation()

    result = agent.complete(
        "openai", "gpt-4", conversation,
        retry_policy=retry_policy, fallback_chain=fallback_chain,
    )

    assert result is fallback_response

    return


# ---------------------------------------------------------------------------
# Tests: All providers fail
# ---------------------------------------------------------------------------

def test_all_providers_fail_raises_llm_request_error_with_summary():
    """
        Verifies that when all providers in the FallbackChain fail,
        an LLMRequestError is raised and its cause message includes
        a summary of all attempted providers.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingProvider(
        provider_name="openai",
        model_name="gpt-4",
    )
    fallback_provider = AlwaysFailingProvider(
        provider_name="anthropic",
        model_name="claude-3",
    )

    agent.register_llm_provider(primary_provider)
    agent.register_llm_provider(fallback_provider)

    retry_policy = RetryPolicy(
        max_retries=1,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    fallback_chain = FallbackChain(providers=[
        ("openai", "gpt-4"),
        ("anthropic", "claude-3"),
    ])

    conversation = _create_conversation()

    raised = False
    caught_error = None
    try:
        agent.complete(
            "openai", "gpt-4", conversation,
            retry_policy=retry_policy, fallback_chain=fallback_chain,
        )
    except LLMRequestError as err:
        raised = True
        caught_error = err

    assert raised is True

    error_cause_str = str(caught_error.cause)
    has_openai = "openai" in error_cause_str
    assert has_openai is True

    has_anthropic = "anthropic" in error_cause_str
    assert has_anthropic is True

    return


# ---------------------------------------------------------------------------
# Tests: LLMProviderRegistry cleared after Agent.stop()
# ---------------------------------------------------------------------------

def test_registry_cleared_after_agent_stop():
    """
        Verifies that the LLMProviderRegistry is cleared when the
        agent transitions to STOPPED state via stop().
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    response = _create_response()
    provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response,
    )
    agent.register_llm_provider(provider)

    count_before = agent.llm_providers.count
    assert count_before == 1

    agent.initialize()
    agent.start()
    agent.stop()

    count_after = agent.llm_providers.count
    assert count_after == 0

    return


# ---------------------------------------------------------------------------
# Tests: Logging output at correct levels
# ---------------------------------------------------------------------------

def test_logging_info_on_completion_begin_and_success():
    """
        Verifies that INFO level log records are emitted for completion
        request begin and success, including provider name and model name.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    response = _create_response(provider_name="openai", model_name="gpt-4")
    provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response,
    )
    agent.register_llm_provider(provider)

    llm_logger = logging.getLogger("automojo.agentkit.llm")
    handler = logging.handlers.MemoryHandler(capacity=100)
    handler.setLevel(logging.DEBUG)
    llm_logger.addHandler(handler)
    llm_logger.setLevel(logging.DEBUG)

    conversation = _create_conversation()

    try:
        agent.complete("openai", "gpt-4", conversation)

        info_records = [
            r for r in handler.buffer if r.levelno == logging.INFO
        ]

        begin_records = [
            r for r in info_records if "begin" in r.getMessage().lower()
        ]
        assert len(begin_records) >= 1

        begin_msg = begin_records[0].getMessage()
        has_provider = "openai" in begin_msg
        assert has_provider is True

        success_records = [
            r for r in info_records if "success" in r.getMessage().lower()
        ]
        assert len(success_records) >= 1

        success_msg = success_records[0].getMessage()
        has_provider_in_success = "openai" in success_msg
        assert has_provider_in_success is True

    finally:
        llm_logger.removeHandler(handler)

    return


def test_logging_warning_on_failure_and_fallback():
    """
        Verifies that WARNING level log records are emitted for completion
        request failure and fallback attempts.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingProvider(
        provider_name="openai",
        model_name="gpt-4",
    )

    fallback_response = _create_response(
        provider_name="anthropic", model_name="claude-3"
    )
    fallback_provider = StubLLMProvider(
        provider_name="anthropic",
        model_name="claude-3",
        response=fallback_response,
    )

    agent.register_llm_provider(primary_provider)
    agent.register_llm_provider(fallback_provider)

    retry_policy = RetryPolicy(
        max_retries=1,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    fallback_chain = FallbackChain(providers=[
        ("openai", "gpt-4"),
        ("anthropic", "claude-3"),
    ])

    llm_logger = logging.getLogger("automojo.agentkit.llm")
    handler = logging.handlers.MemoryHandler(capacity=100)
    handler.setLevel(logging.DEBUG)
    llm_logger.addHandler(handler)
    llm_logger.setLevel(logging.DEBUG)

    conversation = _create_conversation()

    try:
        agent.complete(
            "openai", "gpt-4", conversation,
            retry_policy=retry_policy, fallback_chain=fallback_chain,
        )

        warning_records = [
            r for r in handler.buffer if r.levelno == logging.WARNING
        ]

        failure_records = [
            r for r in warning_records
            if "failure" in r.getMessage().lower()
        ]
        assert len(failure_records) >= 1

        fallback_records = [
            r for r in warning_records
            if "falling back" in r.getMessage().lower()
        ]
        assert len(fallback_records) >= 1

        fallback_msg = fallback_records[0].getMessage()
        has_failed_provider = "openai" in fallback_msg
        assert has_failed_provider is True

        has_fallback_provider = "anthropic" in fallback_msg
        assert has_fallback_provider is True

    finally:
        llm_logger.removeHandler(handler)

    return


# ---------------------------------------------------------------------------
# Tests: _initialize_llm_providers discovers providers from extension point
# ---------------------------------------------------------------------------

def test_initialize_llm_providers_discovers_from_extension_point():
    """
        Verifies that _initialize_llm_providers queries the
        "automojo.agentkit.llm_providers" extension point and registers
        discovered providers with the agent's LLMProviderRegistry.

        Injects a mock automojo.extension module into sys.modules so
        that the dynamic import inside _initialize_llm_providers succeeds.
    """
    import sys
    import types

    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    discovered_provider = StubLLMProvider(
        provider_name="plugin-provider",
        model_name="plugin-model",
        response=_create_response(
            provider_name="plugin-provider", model_name="plugin-model"
        ),
    )

    # Create a mock ExtensionPoint class that returns our discovered provider
    class MockExtensionPoint:
        """
            Mock ExtensionPoint that returns a list of discovered providers.
        """

        def __init__(self, name):
            self._name = name
            return

        def query(self):
            return [discovered_provider]

    # Inject a mock automojo.extension module into sys.modules
    mock_extension_module = types.ModuleType("automojo.extension")
    mock_extension_module.ExtensionPoint = MockExtensionPoint

    had_module = "automojo.extension" in sys.modules
    original_module = sys.modules.get("automojo.extension", None)
    sys.modules["automojo.extension"] = mock_extension_module

    try:
        agent._initialize_llm_providers()

        has_provider = agent.llm_providers.has_provider(
            "plugin-provider", "plugin-model"
        )
        assert has_provider is True

    finally:
        if had_module:
            sys.modules["automojo.extension"] = original_module
        else:
            del sys.modules["automojo.extension"]

    return


# ---------------------------------------------------------------------------
# Tests: _stop_llm_providers clears the registry
# ---------------------------------------------------------------------------

def test_stop_llm_providers_clears_registry():
    """
        Verifies that _stop_llm_providers clears all providers from
        the agent's LLMProviderRegistry.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    response = _create_response()
    provider_a = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response,
    )
    provider_b = StubLLMProvider(
        provider_name="anthropic",
        model_name="claude-3",
        response=response,
    )

    agent.register_llm_provider(provider_a)
    agent.register_llm_provider(provider_b)

    count_before = agent.llm_providers.count
    assert count_before == 2

    agent._stop_llm_providers()

    count_after = agent.llm_providers.count
    assert count_after == 0

    return
