"""
    Tests for Agent messaging integration.

    Contains unit tests for the Agent messaging properties, methods,
    lifecycle integration, and plugin discovery for the Communication
    & Messaging feature.

    Feature: communication-messaging
"""

import logging
import os

from automojo.agentkit.addressresolver import AddressResolver
from automojo.agentkit.agent import Agent
from automojo.agentkit.agentaddress import AgentAddress
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.jsonmessageserializer import JsonMessageSerializer
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.message import Message
from automojo.agentkit.messageenvelope import MessageEnvelope
from automojo.agentkit.messagepattern import MessagePattern
from automojo.agentkit.messagerouter import MessageRouter
from automojo.agentkit.messagingconfiguration import MessagingConfiguration
from automojo.agentkit.pubsubbroker import PubSubBroker
from automojo.agentkit.requestresponsehandler import RequestResponseHandler
from automojo.agentkit.subscription import Subscription
from automojo.agentkit.transport import Transport
from automojo.agentkit.transportconfiguration import TransportConfiguration
from automojo.agentkit.transportregistry import TransportRegistry


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


class MessagingTestAgent(Agent):
    """
        Concrete Agent subclass that wires messaging initialization and
        cleanup into the lifecycle methods.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        self.messaging_config = None
        super().__init__(configuration)
        return

    def initialize(self) -> None:
        """
            Initializes messaging then transitions to INITIALIZED state.
        """
        self._initialize_messaging(self.messaging_config)
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
            Stops messaging then transitions to STOPPED state.
        """
        self._stop_messaging()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class MockTransport(Transport):
    """
        A concrete Transport subclass for testing that tracks sent
        messages and returns delivered envelopes.
    """

    def __init__(self, name: str, protocol_type: str = "http",
                 configuration: TransportConfiguration = None) -> None:
        if configuration is None:
            configuration = TransportConfiguration(
                protocol_type="http",
                host="localhost",
                port=8080,
            )
        super().__init__(
            name=name,
            protocol_type=protocol_type,
            configuration=configuration,
        )
        self.sent_messages = []
        return

    def connect(self) -> None:
        """
            Sets the transport to connected state.
        """
        self._connected = True
        return

    def disconnect(self) -> None:
        """
            Sets the transport to disconnected state.
        """
        self._connected = False
        return

    def send(self, message: Message) -> MessageEnvelope:
        """
            Records the sent message and returns a delivered envelope.
        """
        self.sent_messages.append(message)
        envelope = MessageEnvelope(
            message=message,
            transport_name=self._name,
            attempt_count=1,
            delivery_status="delivered",
        )
        return envelope

    def receive(self) -> Message:
        """
            Not implemented for testing.
        """
        return None


def _create_config(name: str = "msg-agent", version: str = "1.0") -> AgentConfiguration:
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


def _create_transport_config() -> TransportConfiguration:
    """
        Creates a TransportConfiguration for testing.

        :returns: A TransportConfiguration instance.
    """
    config = TransportConfiguration(
        protocol_type="http",
        host="localhost",
        port=8080,
    )
    return config


def _create_mock_transport(name: str) -> MockTransport:
    """
        Creates a MockTransport with the given name.

        :param name: The transport name.

        :returns: A MockTransport instance.
    """
    transport = MockTransport(name=name)
    return transport



# ---------------------------------------------------------------------------
# Property tests (read-only properties)
# ---------------------------------------------------------------------------

def test_transports_property_returns_transport_registry():
    """
        Verify Agent.transports property returns a TransportRegistry instance.
    """
    _reset_registry()

    config = _create_config(name="transports-prop-agent")
    agent = MessagingTestAgent(config)

    transports = agent.transports

    is_registry = isinstance(transports, TransportRegistry)
    assert is_registry is True, "Agent.transports should return a TransportRegistry instance"

    return


def test_message_router_property_returns_message_router():
    """
        Verify Agent.message_router property returns a MessageRouter instance.
    """
    _reset_registry()

    config = _create_config(name="router-prop-agent")
    agent = MessagingTestAgent(config)

    router = agent.message_router

    is_router = isinstance(router, MessageRouter)
    assert is_router is True, "Agent.message_router should return a MessageRouter instance"

    return


def test_pubsub_property_returns_pubsub_broker():
    """
        Verify Agent.pubsub property returns a PubSubBroker instance.
    """
    _reset_registry()

    config = _create_config(name="pubsub-prop-agent")
    agent = MessagingTestAgent(config)

    pubsub = agent.pubsub

    is_broker = isinstance(pubsub, PubSubBroker)
    assert is_broker is True, "Agent.pubsub should return a PubSubBroker instance"

    return


def test_address_resolver_property_returns_address_resolver():
    """
        Verify Agent.address_resolver property returns an AddressResolver instance.
    """
    _reset_registry()

    config = _create_config(name="resolver-prop-agent")
    agent = MessagingTestAgent(config)

    resolver = agent.address_resolver

    is_resolver = isinstance(resolver, AddressResolver)
    assert is_resolver is True, "Agent.address_resolver should return an AddressResolver instance"

    return


# ---------------------------------------------------------------------------
# Messaging method tests
# ---------------------------------------------------------------------------

def test_register_transport_adds_to_registry():
    """
        Verify register_transport makes a transport discoverable in the
        Agent's TransportRegistry.
    """
    _reset_registry()

    config = _create_config(name="reg-transport-agent")
    agent = MessagingTestAgent(config)

    transport = _create_mock_transport(name="test-transport")
    agent.register_transport(transport=transport)

    has_transport = agent.transports.has_transport("test-transport")
    assert has_transport is True, "Transport should be discoverable after registration"

    lookup_result = agent.transports.lookup("test-transport")
    is_same = lookup_result is transport
    assert is_same is True, "Lookup should return the same transport instance"

    return


def test_send_message_returns_message_envelope():
    """
        Verify send_message with a registered transport and static address
        returns a MessageEnvelope with delivery_status 'delivered'.
    """
    _reset_registry()

    config = _create_config(name="send-msg-agent")
    agent = MessagingTestAgent(config)

    transport = _create_mock_transport(name="test-transport")
    agent.register_transport(transport=transport)

    agent.address_resolver.register_address(
        "recipient-id", "test-transport", {"host": "localhost", "port": 8080}
    )

    envelope = agent.send_message(
        recipient_id="recipient-id",
        payload={"key": "value"},
        transport_name="test-transport",
    )

    is_envelope = isinstance(envelope, MessageEnvelope)
    assert is_envelope is True, "send_message should return a MessageEnvelope"

    status = envelope.delivery_status
    is_delivered = status == "delivered"
    assert is_delivered is True, "Delivery status should be 'delivered', got '{}'".format(status)

    return


def test_send_message_raises_semantic_error_for_missing_transport():
    """
        Verify send_message raises SemanticError when the requested
        transport is not found in the TransportRegistry.
    """
    _reset_registry()

    config = _create_config(name="missing-transport-agent")
    agent = MessagingTestAgent(config)

    raised = False
    error_message = ""

    try:
        agent.send_message(
            recipient_id="recipient-id",
            payload={"key": "value"},
            transport_name="nonexistent-transport",
        )
    except SemanticError as err:
        raised = True
        error_message = str(err)

    assert raised is True, "send_message should raise SemanticError for missing transport"

    has_transport_name = "nonexistent-transport" in error_message
    assert has_transport_name is True, "Error message should contain the transport name"

    agent_id = agent.identity.identifier
    has_agent_id = agent_id in error_message
    assert has_agent_id is True, "Error message should contain the agent identity '{}'".format(agent_id)

    return


def test_request_delegates_to_request_response_handler():
    """
        Verify request raises SemanticError when the requested transport
        is not found, confirming it delegates through the transport
        lookup path.
    """
    _reset_registry()

    config = _create_config(name="request-agent")
    agent = MessagingTestAgent(config)

    raised = False
    error_message = ""

    try:
        agent.request(
            recipient_id="recipient-id",
            payload={"key": "value"},
            transport_name="nonexistent-transport",
        )
    except SemanticError as err:
        raised = True
        error_message = str(err)

    assert raised is True, "request should raise SemanticError for missing transport"

    has_transport_name = "nonexistent-transport" in error_message
    assert has_transport_name is True, "Error message should contain the transport name"

    return


def test_publish_delegates_to_pubsub_broker():
    """
        Verify publish constructs an EVENT message and delegates to
        the PubSubBroker.
    """
    _reset_registry()

    config = _create_config(name="publish-agent")
    agent = MessagingTestAgent(config)

    received_messages = []

    def handler(message):
        received_messages.append(message)
        return

    agent.subscribe(topic="test.topic", handler=handler)

    agent.publish(topic="test.topic", payload={"event": "data"})

    message_count = len(received_messages)
    has_message = message_count == 1
    assert has_message is True, "Handler should receive 1 message, got {}".format(message_count)

    received_msg = received_messages[0]
    pattern = received_msg.pattern
    is_event = pattern is MessagePattern.EVENT
    assert is_event is True, "Published message should have EVENT pattern"

    payload = received_msg.payload
    payload_match = payload == {"event": "data"}
    assert payload_match is True, "Payload should match published data"

    return


def test_subscribe_delegates_to_pubsub_broker():
    """
        Verify subscribe returns a Subscription from the PubSubBroker.
    """
    _reset_registry()

    config = _create_config(name="subscribe-agent")
    agent = MessagingTestAgent(config)

    def handler(message):
        return

    subscription = agent.subscribe(topic="test.topic", handler=handler)

    is_subscription = isinstance(subscription, Subscription)
    assert is_subscription is True, "subscribe should return a Subscription instance"

    topic = subscription.topic
    topic_match = topic == "test.topic"
    assert topic_match is True, "Subscription topic should be 'test.topic', got '{}'".format(topic)

    subscriber_id = subscription.subscriber_agent_id
    agent_id = agent.identity.identifier
    id_match = subscriber_id == agent_id
    assert id_match is True, "Subscriber agent ID should match agent identity"

    return



# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------

def test_initialize_messaging_constructs_components():
    """
        Verify that after initialize, all messaging components are non-None.
    """
    _reset_registry()

    config = _create_config(name="init-components-agent")
    agent = MessagingTestAgent(config)
    agent.initialize()

    transports = agent.transports
    is_not_none = transports is not None
    assert is_not_none is True, "transports should not be None after initialize"

    router = agent.message_router
    is_not_none = router is not None
    assert is_not_none is True, "message_router should not be None after initialize"

    pubsub = agent.pubsub
    is_not_none = pubsub is not None
    assert is_not_none is True, "pubsub should not be None after initialize"

    resolver = agent.address_resolver
    is_not_none = resolver is not None
    assert is_not_none is True, "address_resolver should not be None after initialize"

    return


def test_initialize_messaging_with_configuration():
    """
        Verify that with a MessagingConfiguration, the RequestResponseHandler
        uses the configured default_request_timeout.
    """
    _reset_registry()

    config = _create_config(name="init-config-agent")
    agent = MessagingTestAgent(config)

    messaging_config = MessagingConfiguration(
        default_transport="test-transport",
        default_serialization_format="json",
        default_request_timeout=60.0,
    )
    agent.messaging_config = messaging_config

    agent.initialize()

    handler = agent._request_response_handler
    is_not_none = handler is not None
    assert is_not_none is True, "RequestResponseHandler should not be None"

    default_timeout = handler._default_timeout
    timeout_match = default_timeout == 60.0
    assert timeout_match is True, "Default timeout should be 60.0, got {}".format(default_timeout)

    return


def test_initialize_messaging_default_json_serializer():
    """
        Verify that without a MessagingConfiguration, a JsonMessageSerializer
        is registered by default.
    """
    _reset_registry()

    config = _create_config(name="default-serializer-agent")
    agent = MessagingTestAgent(config)
    agent.initialize()

    serializer_registry = agent._message_serializer_registry
    has_json = serializer_registry.has_serializer("json")
    assert has_json is True, "JsonMessageSerializer should be registered by default"

    serializer = serializer_registry.lookup("json")
    is_json = isinstance(serializer, JsonMessageSerializer)
    assert is_json is True, "Default serializer should be a JsonMessageSerializer instance"

    return


def test_stop_messaging_disconnects_transports():
    """
        Verify that after stop, connected transports are disconnected.
    """
    _reset_registry()

    config = _create_config(name="stop-disconnect-agent")
    agent = MessagingTestAgent(config)
    agent.initialize()
    agent.start()

    transport = _create_mock_transport(name="stop-transport")
    agent.register_transport(transport=transport)
    transport.connect()

    is_connected_before = transport.is_connected()
    assert is_connected_before is True, "Transport should be connected before stop"

    agent.stop()

    is_connected_after = transport.is_connected()
    assert is_connected_after is not True, "Transport should be disconnected after stop"

    return


def test_stop_messaging_clears_transport_registry():
    """
        Verify that after stop, the transport registry count is 0.
    """
    _reset_registry()

    config = _create_config(name="stop-clear-agent")
    agent = MessagingTestAgent(config)
    agent.initialize()
    agent.start()

    transport = _create_mock_transport(name="clear-transport")
    agent.register_transport(transport=transport)

    count_before = agent.transports.count
    has_transport = count_before == 1
    assert has_transport is True, "Should have 1 transport before stop"

    agent.stop()

    count_after = agent.transports.count
    is_zero = count_after == 0
    assert is_zero is True, "Transport registry count should be 0 after stop, got {}".format(count_after)

    return


def test_stop_messaging_removes_subscriptions():
    """
        Verify that after stop, the PubSubBroker has no subscriptions.
    """
    _reset_registry()

    config = _create_config(name="stop-subs-agent")
    agent = MessagingTestAgent(config)
    agent.initialize()
    agent.start()

    def handler(message):
        return

    agent.subscribe(topic="topic.a", handler=handler)
    agent.subscribe(topic="topic.b", handler=handler)

    sub_count_before = len(agent.pubsub._subscriptions)
    has_subs = sub_count_before == 2
    assert has_subs is True, "Should have 2 subscriptions before stop"

    agent.stop()

    sub_count_after = len(agent.pubsub._subscriptions)
    is_zero = sub_count_after == 0
    assert is_zero is True, "PubSubBroker should have 0 subscriptions after stop, got {}".format(sub_count_after)

    return


# ---------------------------------------------------------------------------
# Plugin discovery tests
# ---------------------------------------------------------------------------

def test_initialize_messaging_handles_missing_extension():
    """
        Verify that when automojo-extension is not available, initialize
        succeeds without error.
    """
    _reset_registry()

    config = _create_config(name="no-extension-agent")
    agent = MessagingTestAgent(config)

    # _initialize_messaging handles ImportError gracefully when
    # automojo-extension is not available. Calling initialize triggers
    # _initialize_messaging.
    agent.initialize()

    state = agent.state
    is_initialized = state is LifecycleState.INITIALIZED
    assert is_initialized is True, "Agent should be INITIALIZED despite missing extension"

    return


def test_send_message_uses_default_transport_from_config():
    """
        Verify that when transport_name is not provided, send_message
        uses the MessagingConfiguration.default_transport.
    """
    _reset_registry()

    config = _create_config(name="default-transport-agent")
    agent = MessagingTestAgent(config)

    messaging_config = MessagingConfiguration(
        default_transport="my-default-transport",
        default_serialization_format="json",
        default_request_timeout=30.0,
    )
    agent.messaging_config = messaging_config

    agent.initialize()

    transport = _create_mock_transport(name="my-default-transport")
    agent.register_transport(transport=transport)

    agent.address_resolver.register_address(
        "recipient-id", "my-default-transport", {"host": "localhost", "port": 9090}
    )

    # Call send_message without specifying transport_name
    envelope = agent.send_message(
        recipient_id="recipient-id",
        payload={"default": "transport"},
    )

    is_envelope = isinstance(envelope, MessageEnvelope)
    assert is_envelope is True, "send_message should return a MessageEnvelope"

    status = envelope.delivery_status
    is_delivered = status == "delivered"
    assert is_delivered is True, "Delivery status should be 'delivered'"

    transport_name = envelope.transport_name
    name_match = transport_name == "my-default-transport"
    assert name_match is True, "Envelope transport_name should be 'my-default-transport', got '{}'".format(transport_name)

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
