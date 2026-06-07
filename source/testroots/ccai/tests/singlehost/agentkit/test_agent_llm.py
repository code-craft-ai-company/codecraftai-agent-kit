"""
    Tests for Agent LLM integration.

    Contains unit tests for the Agent LLM-related properties and methods:
    llm_providers, cost_tracker, register_llm_provider, and complete.

    Feature: llm-integration
"""

import os

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.costtracker import CostTracker
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.llmprovider import LLMProvider
from ccai.agentkit.llmproviderregistry import LLMProviderRegistry
from ccai.agentkit.llmresponse import LLMResponse
from ccai.agentkit.tokenusage import TokenUsage
from ccai.agentkit.costestimate import CostEstimate


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
            Transitions the agent to STOPPED state.
        """
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class StubLLMProvider(LLMProvider):
    """
        A concrete LLMProvider subclass for testing that returns a
        preconfigured LLMResponse from complete().
    """

    def __init__(self, provider_name: str, model_name: str,
                 response: LLMResponse = None, config: dict = None,
                 credential_names: list = None, tags: dict = None) -> None:
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

            :param conversation: The conversation history.

            :returns: The preconfigured LLMResponse.
        """
        return self._response

    def complete_stream(self, conversation, handler, **kwargs):
        """
            Not implemented for testing.
        """
        return self._response


def _create_config(name: str = "llm-agent", version: str = "1.0") -> AgentConfiguration:
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


def _create_stub_response(provider_name: str = "openai",
                          model_name: str = "gpt-4") -> LLMResponse:
    """
        Creates a stub LLMResponse for testing.

        :param provider_name: The provider name.
        :param model_name: The model name.

        :returns: An LLMResponse instance.
    """
    message = LLMMessage(role="assistant", content="Hello, world!")
    token_usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    response = LLMResponse(
        message=message,
        token_usage=token_usage,
        provider_name=provider_name,
        model_name=model_name,
        duration=0.5,
    )
    return response


# ---------------------------------------------------------------------------
# Tests: llm_providers property
# ---------------------------------------------------------------------------

def test_llm_providers_property_returns_registry():
    """
        Verifies that the llm_providers property returns an
        LLMProviderRegistry instance.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    registry = agent.llm_providers

    is_correct_type = isinstance(registry, LLMProviderRegistry)
    assert is_correct_type is True

    return


def test_llm_providers_property_initially_empty():
    """
        Verifies that the llm_providers registry is empty on a
        newly constructed agent.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    count = agent.llm_providers.count

    assert count == 0

    return


# ---------------------------------------------------------------------------
# Tests: cost_tracker property
# ---------------------------------------------------------------------------

def test_cost_tracker_property_returns_tracker():
    """
        Verifies that the cost_tracker property returns a CostTracker
        instance.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    tracker = agent.cost_tracker

    is_correct_type = isinstance(tracker, CostTracker)
    assert is_correct_type is True

    return


def test_cost_tracker_property_initially_zero_requests():
    """
        Verifies that the cost_tracker has zero request count on a
        newly constructed agent.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    request_count = agent.cost_tracker.request_count

    assert request_count == 0

    return


# ---------------------------------------------------------------------------
# Tests: register_llm_provider
# ---------------------------------------------------------------------------

def test_register_llm_provider_adds_to_registry():
    """
        Verifies that register_llm_provider adds the provider to the
        Agent's LLMProviderRegistry.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    response = _create_stub_response()
    provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response,
    )

    agent.register_llm_provider(provider)

    has_provider = agent.llm_providers.has_provider("openai", "gpt-4")
    assert has_provider is True

    count = agent.llm_providers.count
    assert count == 1

    return


def test_register_llm_provider_duplicate_raises_semantic_error():
    """
        Verifies that registering a duplicate provider raises a
        SemanticError.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    response = _create_stub_response()
    provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response,
    )

    agent.register_llm_provider(provider)

    duplicate_provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response,
    )

    raised = False
    try:
        agent.register_llm_provider(duplicate_provider)
    except SemanticError:
        raised = True

    assert raised is True

    return


# ---------------------------------------------------------------------------
# Tests: complete method
# ---------------------------------------------------------------------------

def test_complete_returns_llm_response():
    """
        Verifies that complete returns the LLMResponse from the provider.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    expected_response = _create_stub_response()
    provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=expected_response,
    )
    agent.register_llm_provider(provider)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    result = agent.complete("openai", "gpt-4", conversation)

    assert result is expected_response

    return


def test_complete_unknown_provider_raises_semantic_error():
    """
        Verifies that complete raises a SemanticError when the provider
        is not found, and the error message includes the provider name,
        model name, and agent identity.
    """
    _reset_registry()

    config = _create_config(name="my-agent")
    agent = LLMTestAgent(configuration=config)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    raised = False
    error_message = ""
    try:
        agent.complete("nonexistent", "unknown-model", conversation)
    except SemanticError as err:
        raised = True
        error_message = str(err)

    assert raised is True

    has_provider_name = "nonexistent" in error_message
    assert has_provider_name is True

    has_model_name = "unknown-model" in error_message
    assert has_model_name is True

    has_agent_identity = agent.identity.identifier in error_message
    assert has_agent_identity is True

    return


def test_complete_records_cost_when_cost_estimate_present():
    """
        Verifies that complete records token usage and cost in the
        CostTracker when the response has a cost_estimate attribute.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    message = LLMMessage(role="assistant", content="Response text")
    token_usage = TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30)
    cost_estimate = CostEstimate(
        prompt_cost=0.002,
        completion_cost=0.001,
        total_cost=0.003,
    )

    response = LLMResponse(
        message=message,
        token_usage=token_usage,
        provider_name="openai",
        model_name="gpt-4",
        duration=1.0,
    )

    # Attach cost_estimate to the response for testing
    response.cost_estimate = cost_estimate

    provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response,
    )
    agent.register_llm_provider(provider)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    agent.complete("openai", "gpt-4", conversation)

    request_count = agent.cost_tracker.request_count
    assert request_count == 1

    return


def test_complete_skips_cost_recording_when_no_cost_estimate():
    """
        Verifies that complete does not record cost when the response
        does not have a cost_estimate attribute (or it is None).
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    expected_response = _create_stub_response()
    provider = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=expected_response,
    )
    agent.register_llm_provider(provider)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    agent.complete("openai", "gpt-4", conversation)

    request_count = agent.cost_tracker.request_count
    assert request_count == 0

    return


def test_complete_passes_kwargs_to_provider():
    """
        Verifies that complete passes keyword arguments through to the
        provider's complete method.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    received_kwargs = {}

    class KwargsCapturingProvider(LLMProvider):
        """
            Provider that captures kwargs for verification.
        """

        def complete(self, conversation, **kwargs):
            received_kwargs.update(kwargs)
            message = LLMMessage(role="assistant", content="ok")
            token_usage = TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2)
            return LLMResponse(
                message=message,
                token_usage=token_usage,
                provider_name="test",
                model_name="test-model",
                duration=0.1,
            )

        def complete_stream(self, conversation, handler, **kwargs):
            return None

    provider = KwargsCapturingProvider(
        provider_name="test",
        model_name="test-model",
    )
    agent.register_llm_provider(provider)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    agent.complete("test", "test-model", conversation, temperature=0.7, max_tokens=100)

    has_temperature = "temperature" in received_kwargs
    assert has_temperature is True
    assert received_kwargs["temperature"] == 0.7

    has_max_tokens = "max_tokens" in received_kwargs
    assert has_max_tokens is True
    assert received_kwargs["max_tokens"] == 100

    return


def test_complete_multiple_providers():
    """
        Verifies that an agent can have multiple providers registered
        and complete routes to the correct one.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    response_a = _create_stub_response(provider_name="openai", model_name="gpt-4")
    response_b = _create_stub_response(provider_name="anthropic", model_name="claude-3")

    provider_a = StubLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        response=response_a,
    )
    provider_b = StubLLMProvider(
        provider_name="anthropic",
        model_name="claude-3",
        response=response_b,
    )

    agent.register_llm_provider(provider_a)
    agent.register_llm_provider(provider_b)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    result_a = agent.complete("openai", "gpt-4", conversation)
    assert result_a is response_a

    result_b = agent.complete("anthropic", "claude-3", conversation)
    assert result_b is response_b

    return

# ---------------------------------------------------------------------------
# Imports for retry and fallback tests
# ---------------------------------------------------------------------------

import logging
import logging.handlers
import time

from ccai.agentkit.fallbackchain import FallbackChain
from ccai.agentkit.llmerrors import LLMRequestError
from ccai.agentkit.retrypolicy import RetryPolicy
from ccai.testbase.mocking import create_module_patch


# ---------------------------------------------------------------------------
# Helpers for retry and fallback tests
# ---------------------------------------------------------------------------

class FailingLLMProvider(LLMProvider):
    """
        A concrete LLMProvider subclass that fails a configurable number
        of times before returning a successful response.

        :param provider_name: The provider name.
        :param model_name: The model name.
        :param fail_count: Number of times to fail before succeeding.
        :param response: The LLMResponse to return on success.
        :param exception_type: The exception type to raise on failure.
    """

    def __init__(self, provider_name: str, model_name: str,
                 fail_count: int = 0, response: LLMResponse = None,
                 exception_type: type = None) -> None:
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
        )
        self._fail_count = fail_count
        self._response = response
        self._call_count = 0

        if exception_type is not None:
            self._exception_type = exception_type
        else:
            self._exception_type = RuntimeError

        return

    @property
    def call_count(self) -> int:
        return self._call_count

    def complete(self, conversation, **kwargs):
        """
            Fails for the first fail_count calls, then returns the response.

            :param conversation: The conversation history.

            :returns: The preconfigured LLMResponse after fail_count failures.
            :raises: The configured exception type for the first fail_count calls.
        """
        self._call_count = self._call_count + 1

        if self._call_count <= self._fail_count:
            raise self._exception_type(
                "Simulated failure #{} for {}/{}".format(
                    self._call_count, self._provider_name, self._model_name
                )
            )

        return self._response

    def complete_stream(self, conversation, handler, **kwargs):
        """
            Not implemented for testing.
        """
        return self._response


class AlwaysFailingLLMProvider(LLMProvider):
    """
        A concrete LLMProvider subclass that always fails.

        :param provider_name: The provider name.
        :param model_name: The model name.
        :param exception_type: The exception type to raise.
    """

    def __init__(self, provider_name: str, model_name: str,
                 exception_type: type = None) -> None:
        super().__init__(
            provider_name=provider_name,
            model_name=model_name,
        )

        if exception_type is not None:
            self._exception_type = exception_type
        else:
            self._exception_type = RuntimeError

        return

    def complete(self, conversation, **kwargs):
        """
            Always raises an exception.

            :param conversation: The conversation history.

            :raises: The configured exception type.
        """
        raise self._exception_type(
            "Always failing: {}/{}".format(
                self._provider_name, self._model_name
            )
        )

    def complete_stream(self, conversation, handler, **kwargs):
        """
            Not implemented for testing.
        """
        raise self._exception_type("Always failing")


# ---------------------------------------------------------------------------
# Tests: retry behavior
# ---------------------------------------------------------------------------

def test_complete_retries_on_failure_then_succeeds():
    """
        Verifies that when a RetryPolicy is configured and the provider
        fails initially, the request is retried and eventually succeeds.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    expected_response = _create_stub_response(
        provider_name="openai", model_name="gpt-4"
    )

    provider = FailingLLMProvider(
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

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    result = agent.complete(
        "openai", "gpt-4", conversation, retry_policy=retry_policy
    )

    assert result is expected_response

    assert provider.call_count == 3

    return


def test_complete_retry_logs_info_for_each_attempt():
    """
        Verifies that each retry attempt is logged at INFO level with
        the provider name, attempt number, and delay.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    expected_response = _create_stub_response(
        provider_name="openai", model_name="gpt-4"
    )

    provider = FailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
        fail_count=1,
        response=expected_response,
    )
    agent.register_llm_provider(provider)

    retry_policy = RetryPolicy(
        max_retries=3,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    llm_logger = logging.getLogger("ccai.agentkit.llm")
    handler = logging.handlers.MemoryHandler(capacity=100)
    handler.setLevel(logging.DEBUG)
    llm_logger.addHandler(handler)
    llm_logger.setLevel(logging.DEBUG)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    try:
        agent.complete(
            "openai", "gpt-4", conversation, retry_policy=retry_policy
        )

        info_records = [
            r for r in handler.buffer
            if r.levelno == logging.INFO and "Retrying" in r.getMessage()
        ]

        assert len(info_records) >= 1

        first_retry_msg = info_records[0].getMessage()
        has_provider_name = "openai" in first_retry_msg
        assert has_provider_name is True

        has_attempt = "1" in first_retry_msg
        assert has_attempt is True

    finally:
        llm_logger.removeHandler(handler)

    return


def test_complete_no_retry_when_policy_is_none():
    """
        Verifies that when no RetryPolicy is configured, a failure
        propagates immediately without retry.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )
    agent.register_llm_provider(provider)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    raised = False
    try:
        agent.complete("openai", "gpt-4", conversation)
    except RuntimeError:
        raised = True

    assert raised is True

    return


def test_complete_retries_exhausted_raises_without_fallback():
    """
        Verifies that when all retries are exhausted and no FallbackChain
        is configured, an LLMRequestError is raised.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )
    agent.register_llm_provider(provider)

    retry_policy = RetryPolicy(
        max_retries=2,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    raised = False
    try:
        agent.complete(
            "openai", "gpt-4", conversation, retry_policy=retry_policy
        )
    except LLMRequestError:
        raised = True

    assert raised is True

    return


# ---------------------------------------------------------------------------
# Tests: fallback behavior
# ---------------------------------------------------------------------------

def test_complete_falls_back_to_next_provider_on_failure():
    """
        Verifies that when the primary provider fails and a FallbackChain
        is configured, the next provider in the chain is attempted.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )

    fallback_response = _create_stub_response(
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

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    result = agent.complete(
        "openai", "gpt-4", conversation,
        retry_policy=retry_policy, fallback_chain=fallback_chain,
    )

    assert result is fallback_response

    return


def test_complete_fallback_logs_warning():
    """
        Verifies that each fallback attempt is logged at WARNING level
        with the failed provider and fallback provider names.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )

    fallback_response = _create_stub_response(
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

    llm_logger = logging.getLogger("ccai.agentkit.llm")
    handler = logging.handlers.MemoryHandler(capacity=100)
    handler.setLevel(logging.DEBUG)
    llm_logger.addHandler(handler)
    llm_logger.setLevel(logging.DEBUG)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    try:
        agent.complete(
            "openai", "gpt-4", conversation,
            retry_policy=retry_policy, fallback_chain=fallback_chain,
        )

        warning_records = [
            r for r in handler.buffer
            if r.levelno == logging.WARNING and "Falling back" in r.getMessage()
        ]

        assert len(warning_records) >= 1

        fallback_msg = warning_records[0].getMessage()
        has_failed_provider = "openai" in fallback_msg
        assert has_failed_provider is True

        has_fallback_provider = "anthropic" in fallback_msg
        assert has_fallback_provider is True

    finally:
        llm_logger.removeHandler(handler)

    return


def test_complete_all_providers_fail_raises_llm_request_error():
    """
        Verifies that when all providers in the FallbackChain fail,
        an LLMRequestError is raised with a summary of all attempted
        providers.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )
    fallback_provider = AlwaysFailingLLMProvider(
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

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

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


def test_complete_fallback_with_retry_on_fallback_provider():
    """
        Verifies that the retry policy also applies to fallback providers.
        The fallback provider fails once then succeeds on retry.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )

    fallback_response = _create_stub_response(
        provider_name="anthropic", model_name="claude-3"
    )
    fallback_provider = FailingLLMProvider(
        provider_name="anthropic",
        model_name="claude-3",
        fail_count=1,
        response=fallback_response,
    )

    agent.register_llm_provider(primary_provider)
    agent.register_llm_provider(fallback_provider)

    retry_policy = RetryPolicy(
        max_retries=2,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    fallback_chain = FallbackChain(providers=[
        ("openai", "gpt-4"),
        ("anthropic", "claude-3"),
    ])

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    result = agent.complete(
        "openai", "gpt-4", conversation,
        retry_policy=retry_policy, fallback_chain=fallback_chain,
    )

    assert result is fallback_response

    assert fallback_provider.call_count == 2

    return


def test_complete_without_retry_policy_with_fallback():
    """
        Verifies that when no RetryPolicy is configured but a FallbackChain
        is provided, the first failure immediately triggers fallback.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    primary_provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )

    fallback_response = _create_stub_response(
        provider_name="anthropic", model_name="claude-3"
    )
    fallback_provider = StubLLMProvider(
        provider_name="anthropic",
        model_name="claude-3",
        response=fallback_response,
    )

    agent.register_llm_provider(primary_provider)
    agent.register_llm_provider(fallback_provider)

    fallback_chain = FallbackChain(providers=[
        ("openai", "gpt-4"),
        ("anthropic", "claude-3"),
    ])

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    result = agent.complete(
        "openai", "gpt-4", conversation,
        fallback_chain=fallback_chain,
    )

    assert result is fallback_response

    return


def test_complete_llm_request_error_includes_provider_name():
    """
        Verifies that the LLMRequestError raised when all providers fail
        includes the original provider name.
    """
    _reset_registry()

    config = _create_config()
    agent = LLMTestAgent(configuration=config)

    provider = AlwaysFailingLLMProvider(
        provider_name="openai",
        model_name="gpt-4",
    )
    agent.register_llm_provider(provider)

    retry_policy = RetryPolicy(
        max_retries=1,
        backoff_strategy="fixed",
        base_delay=0.0,
        max_delay=0.0,
    )

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    raised = False
    caught_error = None
    try:
        agent.complete(
            "openai", "gpt-4", conversation, retry_policy=retry_policy
        )
    except LLMRequestError as err:
        raised = True
        caught_error = err

    assert raised is True

    assert caught_error.provider_name == "openai"
    assert caught_error.model_name == "gpt-4"

    return
