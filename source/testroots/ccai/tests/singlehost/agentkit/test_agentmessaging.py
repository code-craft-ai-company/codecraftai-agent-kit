"""
    Tests for Agent messaging integration.

    Contains unit tests for the Agent messaging properties, methods,
    lifecycle integration, and plugin discovery for the Communication
    & Messaging feature.

    Feature: communication-messaging
"""

import logging
import threading
import time

from collections import deque

from ccai.agentkit.addressresolver import AddressResolver
from ccai.agentkit.agent import Agent
from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.jsonmessageserializer import JsonMessageSerializer
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.messagepattern import MessagePattern
from ccai.agentkit.messagerouter import MessageRouter
from ccai.agentkit.messagingconfiguration import MessagingConfiguration
from ccai.agentkit.messagingerrors import MessageRoutingError
from ccai.agentkit.messagingerrors import MessageTimeoutError
from ccai.agentkit.msgpackmessageserializer import MsgpackMessageSerializer
from ccai.agentkit.pubsubbroker import PubSubBroker
from ccai.agentkit.subscription import Subscription
from ccai.agentkit.transport import Transport
from ccai.agentkit.transportconfiguration import TransportConfiguration
from ccai.agentkit.transportregistry import TransportRegistry
from ccai.agentkit.transports.messagequeuetransport import MessageQueueTransport
from ccai.agentkit.steps.agentstep import AgentStep
from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.workflowcontext import WorkflowContext


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
        Verify that when codecraftai-extension is not available, initialize
        succeeds without error.
    """
    _reset_registry()

    config = _create_config(name="no-extension-agent")
    agent = MessagingTestAgent(config)

    # _initialize_messaging handles ImportError gracefully when
    # codecraftai-extension is not available. Calling initialize triggers
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


# ---------------------------------------------------------------------------
# Serialization format tests
# ---------------------------------------------------------------------------

class _RecordingBrokerClient:
    """
        Broker client for MessageQueueTransport that records the published
        bodies.
    """

    def __init__(self) -> None:
        self.published = []
        return

    def connect(self, host, port, credentials=None) -> None:
        return

    def disconnect(self) -> None:
        return

    def publish(self, queue_name, body) -> None:
        self.published.append((queue_name, body))
        return

    def consume(self, queue_name):
        return None


def _create_agent_with_transport(name: str, transport_name: str = "test-transport"):
    """
        Creates a MessagingTestAgent with a registered MockTransport and a
        static address for 'recipient-id'.

        :param name: The agent name.
        :param transport_name: The transport name.

        :returns: A tuple of the agent and the MockTransport.
    """
    config = _create_config(name=name)
    agent = MessagingTestAgent(config)

    transport = _create_mock_transport(name=transport_name)
    agent.register_transport(transport=transport)

    agent.address_resolver.register_address(
        "recipient-id", transport_name, {"host": "localhost", "port": 8080}
    )
    return agent, transport


def test_register_transport_attaches_agent_serializer_registry():
    """
        Verify register_transport attaches the Agent's
        MessageSerializerRegistry to the transport.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="attach-registry-agent")

    is_attached = transport.serializer_registry is agent._message_serializer_registry
    assert is_attached is True, \
        "The agent serializer registry should be attached to the transport"
    return


def test_send_message_carries_requested_serialization_format():
    """
        Verify send_message sets the requested serialization format on
        the Message handed to the transport.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="format-agent")
    agent._message_serializer_registry.register(MsgpackMessageSerializer())

    agent.send_message(
        recipient_id="recipient-id",
        payload={"key": "value"},
        transport_name="test-transport",
        serialization_format="msgpack",
    )

    sent_format = transport.sent_messages[0].serialization_format
    assert sent_format == "msgpack", \
        "The sent message should carry 'msgpack', got '{}'".format(sent_format)
    return


def test_send_message_uses_default_serialization_format_from_config():
    """
        Verify that when serialization_format is not provided,
        send_message uses the MessagingConfiguration default.
    """
    _reset_registry()

    config = _create_config(name="default-format-agent")
    agent = MessagingTestAgent(config)
    agent.messaging_config = MessagingConfiguration(
        default_transport="test-transport",
        default_serialization_format="msgpack",
        default_request_timeout=30.0,
    )
    agent.initialize()

    if agent._message_serializer_registry.has_serializer("msgpack") is not True:
        agent._message_serializer_registry.register(MsgpackMessageSerializer())

    transport = _create_mock_transport(name="test-transport")
    agent.register_transport(transport=transport)
    agent.address_resolver.register_address(
        "recipient-id", "test-transport", {"host": "localhost", "port": 8080}
    )

    agent.send_message(recipient_id="recipient-id", payload={"key": "value"})

    sent_format = transport.sent_messages[0].serialization_format
    assert sent_format == "msgpack", \
        "The configured default format should be used, got '{}'".format(sent_format)
    return


def test_send_message_defaults_to_json_without_configuration():
    """
        Verify send_message uses the 'json' format when neither a format
        nor a MessagingConfiguration is provided.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="json-default-agent")

    agent.send_message(
        recipient_id="recipient-id",
        payload={"key": "value"},
        transport_name="test-transport",
    )

    sent_format = transport.sent_messages[0].serialization_format
    assert sent_format == "json", \
        "The default format should be 'json', got '{}'".format(sent_format)
    return


def test_send_message_unregistered_format_raises_semantic_error():
    """
        Verify send_message raises SemanticError naming the format and the
        agent when no serializer is registered for the requested format,
        and sends nothing.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="bad-format-agent")

    error_message = None
    try:
        agent.send_message(
            recipient_id="recipient-id",
            payload={"key": "value"},
            transport_name="test-transport",
            serialization_format="protobuf",
        )
    except SemanticError as err:
        error_message = str(err)

    assert error_message is not None, \
        "send_message should raise SemanticError for an unregistered format"
    assert "protobuf" in error_message, \
        "The error should name the format, got: {}".format(error_message)
    assert agent.identity.identifier in error_message, \
        "The error should name the agent, got: {}".format(error_message)
    assert len(transport.sent_messages) == 0, \
        "Nothing should be sent for an unregistered format"
    return


def test_send_message_serializes_wire_body_in_requested_format():
    """
        Verify the serialization format passed to send_message controls
        the bytes a real transport puts on the wire.
    """
    _reset_registry()

    config = _create_config(name="wire-format-agent")
    agent = MessagingTestAgent(config)
    agent._message_serializer_registry.register(MsgpackMessageSerializer())

    broker_client = _RecordingBrokerClient()
    transport_config = TransportConfiguration(
        protocol_type="message_queue",
        host="localhost",
        port=5672,
        options={"broker_client": broker_client, "publish_queue": "outbound"},
    )
    transport = MessageQueueTransport(name="mq", configuration=transport_config)
    transport.connect()
    agent.register_transport(transport=transport)
    agent.address_resolver.register_address(
        "recipient-id", "mq", {"host": "localhost", "port": 5672}
    )

    agent.send_message(
        recipient_id="recipient-id",
        payload={"key": "value"},
        transport_name="mq",
        serialization_format="msgpack",
    )
    agent.send_message(
        recipient_id="recipient-id",
        payload={"key": "value"},
        transport_name="mq",
    )

    (_, msgpack_body), (_, json_body) = broker_client.published

    msgpack_data = MsgpackMessageSerializer().deserialize(msgpack_body)
    assert msgpack_data["payload"] == {"key": "value"}, \
        "The msgpack body should decode to the payload, got {}".format(msgpack_data)
    assert msgpack_data["serialization_format"] == "msgpack", \
        "The msgpack body should record its format"

    json_data = JsonMessageSerializer().deserialize(json_body)
    assert json_data["serialization_format"] == "json", \
        "The default body should be JSON, got {}".format(json_data)
    return


def test_request_carries_requested_serialization_format():
    """
        Verify request sets the requested serialization format on the
        correlated request Message handed to the transport.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="request-format-agent")
    agent._message_serializer_registry.register(MsgpackMessageSerializer())

    timed_out = False
    try:
        agent.request(
            recipient_id="recipient-id",
            payload={"key": "value"},
            transport_name="test-transport",
            serialization_format="msgpack",
            timeout=0.05,
        )
    except MessageTimeoutError:
        timed_out = True

    assert timed_out is True, \
        "The request should time out because the mock transport never responds"

    sent_message = transport.sent_messages[0]
    assert sent_message.serialization_format == "msgpack", \
        "The request message should carry 'msgpack', got '{}'".format(
            sent_message.serialization_format)
    assert sent_message.correlation_id is not None, \
        "The request message should carry a correlation identifier"
    return


# ---------------------------------------------------------------------------
# Receive path tests
# ---------------------------------------------------------------------------

class _InMemoryBroker:
    """
        In-process message broker made of named FIFO queues, shared by the
        broker clients of several MessageQueueTransports.
    """

    def __init__(self) -> None:
        self._queues = {}
        self._lock = threading.Lock()
        return

    def put(self, queue_name, body) -> None:
        with self._lock:
            if queue_name not in self._queues:
                self._queues[queue_name] = deque()
            self._queues[queue_name].append(body)
        return

    def take(self, queue_name):
        with self._lock:
            queue = self._queues.get(queue_name, None)
            if queue is None or len(queue) == 0:
                return None
            body = queue.popleft()
        return body

    def create_client(self):
        client = _InMemoryBrokerClient(self)
        return client


class _InMemoryBrokerClient:
    """
        Broker client for MessageQueueTransport backed by an _InMemoryBroker.
    """

    def __init__(self, broker) -> None:
        self._broker = broker
        return

    def connect(self, host, port, credentials=None) -> None:
        return

    def disconnect(self) -> None:
        return

    def publish(self, queue_name, body) -> None:
        self._broker.put(queue_name, body)
        return

    def consume(self, queue_name):
        body = self._broker.take(queue_name)
        return body


class _CapturingLogHandler(logging.Handler):
    """
        Logging handler that keeps the records it receives.
    """

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records = []
        return

    def emit(self, record) -> None:
        self.records.append(record)
        return


def _create_queue_agent(name: str, broker: _InMemoryBroker, publish_queue: str,
                        consume_queue: str) -> MessagingTestAgent:
    """
        Creates a MessagingTestAgent with a connected MessageQueueTransport
        named 'mq' that publishes to publish_queue and consumes from
        consume_queue on the in-memory broker.
    """
    config = _create_config(name=name)
    agent = MessagingTestAgent(config)

    transport_config = TransportConfiguration(
        protocol_type="message_queue",
        host="localhost",
        port=5672,
        options={
            "broker_client": broker.create_client(),
            "publish_queue": publish_queue,
            "consume_queue": consume_queue,
        },
    )
    transport = MessageQueueTransport(name="mq", configuration=transport_config)
    transport.connect()
    agent.register_transport(transport=transport)
    return agent


def _create_addressed_message(pattern: MessagePattern, payload: object,
                              correlation_id: str = None, headers: dict = None) -> Message:
    """
        Creates a Message from 'remote-agent' to 'local-agent'.
    """
    message = Message(
        sender=AgentAddress(agent_identifier="remote-agent", transport_name="mq"),
        recipient=AgentAddress(agent_identifier="local-agent", transport_name="mq"),
        payload=payload,
        pattern=pattern,
        headers=headers,
        correlation_id=correlation_id,
    )
    return message


def _wait_until(condition, timeout: float = 5.0) -> bool:
    """
        Polls condition until it returns True or the timeout expires.

        :returns: True if the condition became True, False on timeout.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition() is True:
            return True
        time.sleep(0.01)
    rtnval = condition()
    return rtnval


def test_receive_message_delivers_reply_to_waiting_request():
    """
        Verify a RESPONSE handed to receive_message with the correlation
        identifier of a pending request completes the waiting request()
        call with that response.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="reply-delivery-agent")

    def _reply_when_request_is_sent():
        _wait_until(lambda: len(transport.sent_messages) > 0)
        request_message = transport.sent_messages[0]
        response = Message(
            sender=request_message.recipient,
            recipient=request_message.sender,
            payload={"answer": 42},
            pattern=MessagePattern.RESPONSE,
            correlation_id=request_message.correlation_id,
        )
        agent.receive_message(message=response, transport_name="test-transport")
        return

    replier = threading.Thread(target=_reply_when_request_is_sent, daemon=True)
    replier.start()

    response = agent.request(
        recipient_id="recipient-id",
        payload={"question": "?"},
        transport_name="test-transport",
        timeout=5.0,
    )
    replier.join(5.0)

    assert response.payload == {"answer": 42}, \
        "request() should return the delivered response, got {!r}".format(response.payload)
    assert response.correlation_id == transport.sent_messages[0].correlation_id, \
        "The response should carry the request's correlation identifier"
    return


def test_receive_message_routes_non_reply_messages_to_handlers():
    """
        Verify receive_message routes messages that are not correlated
        replies through the MessageRouter, and raises MessageRoutingError
        when no handler matches.
    """
    _reset_registry()

    config = _create_config(name="routing-agent")
    agent = MessagingTestAgent(config)

    routed = []
    agent.message_router.register_by_pattern(MessagePattern.FIRE_AND_FORGET, routed.append)
    agent.message_router.register_by_pattern(MessagePattern.REQUEST, routed.append)

    notice = _create_addressed_message(MessagePattern.FIRE_AND_FORGET, {"note": 1})
    request_message = _create_addressed_message(MessagePattern.REQUEST, {"ask": 1}, correlation_id="corr-1")

    agent.receive_message(message=notice, transport_name="mq")
    agent.receive_message(message=request_message, transport_name="mq")

    assert routed == [notice, request_message], \
        "Both messages should reach their handlers in order, got {}".format(routed)

    event_message = _create_addressed_message(MessagePattern.EVENT, {"unhandled": True})
    raised = False
    try:
        agent.receive_message(message=event_message, transport_name="mq")
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "A message with no matching handler should raise MessageRoutingError"
    return


def test_receive_message_ignores_late_reply_with_warning():
    """
        Verify a reply that arrives after its request timed out is logged
        at WARNING and ignored: it raises nothing and is not routed.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="late-reply-agent")

    routed = []
    agent.message_router.register_by_pattern(MessagePattern.RESPONSE, routed.append)

    timed_out = False
    try:
        agent.request(
            recipient_id="recipient-id",
            payload={"question": "?"},
            transport_name="test-transport",
            timeout=0.05,
        )
    except MessageTimeoutError:
        timed_out = True

    assert timed_out is True, "The request should time out first"

    request_message = transport.sent_messages[0]
    late_reply = Message(
        sender=request_message.recipient,
        recipient=request_message.sender,
        payload={"answer": "too late"},
        pattern=MessagePattern.RESPONSE,
        correlation_id=request_message.correlation_id,
    )

    capture = _CapturingLogHandler()
    rrh_logger = logging.getLogger("ccai.agentkit.messaging.requestresponse")
    rrh_logger.addHandler(capture)
    try:
        agent.receive_message(message=late_reply, transport_name="test-transport")
    finally:
        rrh_logger.removeHandler(capture)

    assert routed == [], \
        "A late reply should not be routed to handlers, got {}".format(routed)

    warnings = []
    for record in capture.records:
        if record.levelno == logging.WARNING and request_message.correlation_id in record.getMessage():
            warnings.append(record)
    assert len(warnings) == 1, \
        "The late reply should be logged at WARNING once, got {}".format(
            [record.getMessage() for record in capture.records])
    return


def test_reply_rejects_message_that_is_not_a_correlated_request():
    """
        Verify reply raises SemanticError for a message that is not a
        REQUEST carrying a correlation identifier.
    """
    _reset_registry()

    agent, transport = _create_agent_with_transport(name="reply-misuse-agent")
    notice = _create_addressed_message(MessagePattern.FIRE_AND_FORGET, {"note": 1})

    raised = False
    try:
        agent.reply(request_message=notice, payload={"answer": 1})
    except SemanticError:
        raised = True

    assert raised is True, "reply should raise SemanticError for a non-request message"
    assert len(transport.sent_messages) == 0, "Nothing should be sent"
    return


def test_poll_transport_returns_none_when_empty_and_dispatches_message():
    """
        Verify poll_transport returns None for an empty queue and receives
        and dispatches a queued message.
    """
    _reset_registry()

    broker = _InMemoryBroker()
    agent = _create_queue_agent("poll-agent", broker, publish_queue="out", consume_queue="inbox")

    handled = []
    agent.message_router.register_by_topic("orders", handled.append)

    empty_result = agent.poll_transport("mq")
    assert empty_result is None, \
        "poll_transport should return None for an empty queue, got {!r}".format(empty_result)

    order = _create_addressed_message(MessagePattern.FIRE_AND_FORGET, {"order": 7}, headers={"topic": "orders"})
    broker.put("inbox", JsonMessageSerializer().serialize(order.as_dict()))

    polled = agent.poll_transport("mq")

    assert polled is not None and polled.identifier == order.identifier, \
        "poll_transport should return the received message, got {!r}".format(polled)
    assert len(handled) == 1 and handled[0].payload == {"order": 7}, \
        "The received message should be dispatched to its handler, got {}".format(handled)
    return


def test_receive_loop_keeps_running_after_undispatchable_message():
    """
        Verify a receive loop logs a message that matches no handler and
        keeps receiving the next messages.
    """
    _reset_registry()

    broker = _InMemoryBroker()
    agent = _create_queue_agent("resilient-agent", broker, publish_queue="out", consume_queue="inbox")

    handled = []
    agent.message_router.register_by_topic("orders", handled.append)

    unroutable = _create_addressed_message(MessagePattern.FIRE_AND_FORGET, {"lost": True})
    order = _create_addressed_message(MessagePattern.FIRE_AND_FORGET, {"order": 8}, headers={"topic": "orders"})
    broker.put("inbox", JsonMessageSerializer().serialize(unroutable.as_dict()))
    broker.put("inbox", JsonMessageSerializer().serialize(order.as_dict()))

    agent.start_receiving("mq", poll_interval=0.01)
    try:
        was_handled = _wait_until(lambda: len(handled) == 1)
        still_receiving = agent.is_receiving("mq")
    finally:
        agent.stop_receiving()

    assert was_handled is True, \
        "The loop should dispatch the message after the unroutable one"
    assert handled[0].identifier == order.identifier, \
        "The handled message should be the routable one"
    assert still_receiving is True, \
        "The loop should still be running after the dispatch failure"
    assert agent.is_receiving("mq") is False, \
        "stop_receiving should end the loop"
    return


def test_request_reply_end_to_end_between_agents_over_message_queue():
    """
        Verify request/reply between two agents over MessageQueueTransports
        on a shared in-process broker: the responder's receive loop routes
        the REQUEST to its handler, the handler replies, and the
        requester's receive loop completes the waiting request() call.
    """
    _reset_registry()

    broker = _InMemoryBroker()
    requester = _create_queue_agent(
        "requester-agent", broker, publish_queue="responder-inbox", consume_queue="requester-inbox"
    )
    responder = _create_queue_agent(
        "responder-agent", broker, publish_queue="requester-inbox", consume_queue="responder-inbox"
    )

    received_requests = []

    def _handle_request(message):
        received_requests.append(message)
        numbers = message.payload["numbers"]
        total = sum(numbers)
        responder.reply(request_message=message, payload={"total": total})
        return

    responder.message_router.register_by_pattern(MessagePattern.REQUEST, _handle_request)

    requester.start_receiving("mq", poll_interval=0.01)
    responder.start_receiving("mq", poll_interval=0.01)
    try:
        response = requester.request(
            recipient_id=responder.identity.identifier,
            payload={"numbers": [1, 2, 3]},
            transport_name="mq",
            timeout=5.0,
        )
    finally:
        requester.stop_receiving()
        responder.stop_receiving()

    assert response.pattern == MessagePattern.RESPONSE, \
        "request() should return a RESPONSE, got {}".format(response.pattern)
    assert response.payload == {"total": 6}, \
        "The response payload should come from the responder, got {!r}".format(response.payload)
    assert response.correlation_id == received_requests[0].correlation_id, \
        "The response should carry the request's correlation identifier"
    assert response.sender.agent_identifier == responder.identity.identifier, \
        "The response should come from the responder agent"
    return


def test_agentstep_completes_with_reply_from_agent_over_message_queue():
    """
        Verify an AgentStep with a timeout completes with the payload the
        target agent replies with over MessageQueueTransports.
    """
    _reset_registry()

    broker = _InMemoryBroker()
    requester = _create_queue_agent(
        "step-requester-agent", broker, publish_queue="worker-inbox", consume_queue="step-inbox"
    )
    worker = _create_queue_agent(
        "step-worker-agent", broker, publish_queue="step-inbox", consume_queue="worker-inbox"
    )

    def _handle_task(message):
        task = message.payload["inputs"]["task"]
        worker.reply(request_message=message, payload={"result": "done", "task": task})
        return

    worker.message_router.register_by_pattern(MessagePattern.REQUEST, _handle_task)

    step = AgentStep(
        step_id="delegate",
        name="Delegate",
        target_agent_id=worker.identity.identifier,
        transport_name="mq",
        timeout=5.0,
    )
    context = WorkflowContext(inputs={"task": "build"}, agent=requester)

    requester.start_receiving("mq", poll_interval=0.01)
    worker.start_receiving("mq", poll_interval=0.01)
    try:
        result = step.execute(context)
    finally:
        requester.stop_receiving()
        worker.stop_receiving()

    assert result.status == StepExecutionStatus.COMPLETED, \
        "The step should complete, error={}".format(result.error)
    assert result.output == {"result": "done", "task": "build"}, \
        "The step output should be the reply payload, got {}".format(result.output)
    return


def test_stop_messaging_stops_receive_loops():
    """
        Verify stopping the agent's messaging ends its receive loops.
    """
    _reset_registry()

    broker = _InMemoryBroker()
    agent = _create_queue_agent("stopping-agent", broker, publish_queue="out", consume_queue="inbox")
    agent.initialize()
    agent.start()

    agent.start_receiving("mq", poll_interval=0.01)
    assert agent.is_receiving("mq") is True, "The receive loop should be running"

    agent.stop()

    assert agent.is_receiving("mq") is False, \
        "Stopping the agent should end the receive loop"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
