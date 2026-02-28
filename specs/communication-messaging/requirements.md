# Requirements Document — Communication & Messaging

## Introduction

The Communication & Messaging feature extends the `automojo-agent-kit` SDK with a unified system for agent-to-agent communication and message exchange. It defines a pluggable transport layer abstraction with a common interface supporting multiple protocols (HTTP, WebSocket, gRPC, message queues), an agent-to-agent communication protocol with addressing and routing, pub/sub messaging for event-driven communication, request/response and fire-and-forget messaging patterns, and message serialization/deserialization across multiple formats (JSON, Protobuf, MessagePack). The system integrates with the Agent base class so agents can send and receive messages, with the AgentRegistry for agent address resolution, with `automojo-extension` so transport and serializer plugins can be discovered and loaded, with `automojo-credentials` for transport authentication, with `automojo-dataprofiles` for data profile management, and with `automojo-this-app` for settings and environment configuration.

## Glossary

- **Transport**: An abstract base class representing a communication channel for sending and receiving messages. A Transport encapsulates protocol-specific connection management, message sending, and message receiving. Concrete implementations wrap specific protocols (HTTP, WebSocket, gRPC, message queue).
- **TransportRegistry**: A registry that tracks all available Transport instances within a runtime, providing lookup by name, protocol type, and enumeration. Each Agent maintains a TransportRegistry instance.
- **TransportConfiguration**: A configuration object that defines the transport protocol type, connection parameters, authentication settings, and protocol-specific options for a Transport instance.
- **Message**: An immutable object representing a unit of communication between agents, containing a unique identifier, sender address, recipient address, payload, headers dictionary, correlation identifier for request/response tracking, timestamp, and message pattern (request, response, fire-and-forget, event).
- **MessageEnvelope**: An immutable wrapper around a Message that adds transport-level metadata including the transport name, delivery attempt count, and delivery status.
- **MessagePattern**: An enumeration defining the communication pattern of a Message: REQUEST (expects a response), RESPONSE (reply to a request), FIRE_AND_FORGET (no response expected), and EVENT (pub/sub broadcast).
- **MessageHandler**: A callback interface invoked when a Message is received by an Agent. The handler receives the Message and an optional reply callback for request/response patterns.
- **MessageRouter**: A component that routes incoming messages to registered MessageHandler callbacks based on message topic, pattern, or custom filter criteria.
- **MessageSerializer**: An abstract base class for serializing and deserializing message payloads between Python objects and wire format bytes. Concrete implementations handle specific formats (JSON, Protobuf, MessagePack).
- **MessageSerializerRegistry**: A registry that tracks available MessageSerializer instances, providing lookup by format name.
- **AgentAddress**: An immutable object representing the network-addressable identity of an Agent, containing the agent identifier, transport name, and protocol-specific endpoint information (host, port, path).
- **AddressResolver**: A component that resolves an agent identifier to an AgentAddress using the AgentRegistry and transport configuration. The AddressResolver supports static and dynamic address resolution.
- **PubSubBroker**: A component that manages topic-based publish/subscribe messaging, maintaining topic subscriptions and routing published messages to all subscribers of a topic.
- **Subscription**: An immutable object representing an agent's subscription to a topic, containing the subscriber agent identifier, topic string, an optional message filter, and the MessageHandler callback.
- **RequestResponseHandler**: A component that manages the lifecycle of request/response message exchanges, including correlation tracking, timeout management, and response delivery.
- **MessagingConfiguration**: A configuration object that defines the default transport, serialization format, request timeout, and pub/sub settings for an Agent's messaging system.
- **Agent**: The base agent class defined in the Core Agent Framework that owns a TransportRegistry, MessageRouter, and PubSubBroker for communication.
- **AgentRegistry**: The singleton registry defined in the Core Agent Framework that tracks all Agent instances, used by the AddressResolver for agent lookup.
- **ExtensionPoint**: An integration surface provided by `automojo-extension` that allows external plugins to register Transport and MessageSerializer implementations with an Agent.
- **CredentialReference**: A named reference resolved through `automojo-credentials` that provides secure access to secrets required by a Transport (TLS certificates, API keys, authentication tokens).
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **TransportError**: An exception raised when a Transport operation fails due to a connection, send, or receive error.
- **MessageSerializationError**: An exception raised when a MessageSerializer fails to serialize or deserialize a message payload.
- **MessageRoutingError**: An exception raised when the MessageRouter cannot route a message to a handler.
- **MessageTimeoutError**: An exception raised when a request/response exchange exceeds the configured timeout duration.

## Requirements

### Requirement 1: Transport Abstraction

**User Story:** As a developer, I want a well-defined transport base class with a common interface, so that I can send and receive messages over different protocols through a consistent API regardless of the underlying transport.

#### Acceptance Criteria

1. THE Transport base class SHALL define an abstract interface that includes methods for connect (establish a connection), disconnect (close a connection), send (send a Message), receive (receive a Message), and is_connected (check connection status).
2. THE Transport base class SHALL require all subclasses to provide an implementation for the connect, disconnect, send, and receive methods.
3. THE Transport base class SHALL expose a read-only property for the transport name as a string.
4. THE Transport base class SHALL expose a read-only property for the protocol type as a string (one of "http", "websocket", "grpc", "message_queue").
5. THE Transport base class SHALL expose a read-only property for the TransportConfiguration.
6. THE Transport base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the transport requires for authentication.
7. THE Transport base class SHALL accept an optional dictionary of tags at construction time for categorization and discovery purposes.
8. WHEN a Transport subclass does not provide a transport name, THEN THE Transport base class SHALL raise a SemanticError indicating that a transport name is required.
9. WHEN a Transport subclass does not provide a protocol type, THEN THE Transport base class SHALL raise a SemanticError indicating that a protocol type is required.
10. THE Transport base class SHALL provide a __repr__ method that includes the class name, transport name, and protocol type.
11. THE Transport base class SHALL provide a __str__ method that returns a human-readable summary including the transport name, protocol type, and connection status.

### Requirement 2: Transport Configuration

**User Story:** As a developer, I want to configure transports declaratively, so that I can define connection parameters and protocol options without modifying code.

#### Acceptance Criteria

1. THE TransportConfiguration SHALL contain the protocol type as a string, a host string, a port integer, an optional path string, an optional headers dictionary, an optional timeout in seconds as a float with a default value of 30.0, and a protocol-specific options dictionary.
2. THE TransportConfiguration SHALL support loading configuration from a Python dictionary.
3. THE TransportConfiguration SHALL support loading configuration from a JSON file path.
4. THE TransportConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE TransportConfiguration SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
6. THE TransportConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. THE TransportConfiguration SHALL support CredentialReference entries for transport authentication that are resolved through `automojo-credentials` at initialization time.
8. IF a CredentialReference cannot be resolved, THEN THE TransportConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
9. IF an invalid protocol type is provided, THEN THE TransportConfiguration SHALL raise a ConfigurationError identifying the invalid protocol type and listing the valid protocol types.
10. THE TransportConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration, excluding resolved credential values.
11. THE TransportConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration, excluding resolved credential values.
12. THE TransportConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration, excluding resolved credential values.
13. THE TransportConfiguration SHALL provide a class method from_dict that constructs a TransportConfiguration from a dictionary.
14. THE TransportConfiguration SHALL provide a class method from_json that deserializes a JSON string into a TransportConfiguration instance.
15. THE TransportConfiguration SHALL provide a class method from_yaml that deserializes a YAML string into a TransportConfiguration instance.
16. FOR ALL valid TransportConfiguration instances, calling to_json and then from_json SHALL produce an equivalent TransportConfiguration object (round-trip property).
17. FOR ALL valid TransportConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent TransportConfiguration object (round-trip property).
18. THE TransportConfiguration SHALL provide a __repr__ method that includes the class name, protocol type, host, and port.
19. THE TransportConfiguration SHALL provide a __str__ method that returns a human-readable summary including the protocol type, host, port, and timeout.

### Requirement 3: Transport Registry

**User Story:** As a developer, I want a registry that tracks available transports, so that I can discover and look up transports by name or protocol type.

#### Acceptance Criteria

1. THE TransportRegistry SHALL support registration of a Transport instance using the transport name as the registration key.
2. IF a Transport with a duplicate name is registered, THEN THE TransportRegistry SHALL raise a SemanticError that includes the duplicate transport name.
3. THE TransportRegistry SHALL support deregistration of a Transport by name.
4. THE TransportRegistry SHALL support lookup of a registered Transport by name, returning the Transport instance or None when the name is not found.
5. THE TransportRegistry SHALL support lookup of registered Transports by protocol type, returning a list of Transport instances matching the provided protocol type.
6. THE TransportRegistry SHALL support lookup of registered Transports by tag key-value pairs, returning a list of Transport instances that match all provided tag criteria.
7. THE TransportRegistry SHALL support enumeration of all registered Transport instances as a list.
8. THE TransportRegistry SHALL expose a read-only property for the count of currently registered transports.
9. THE TransportRegistry SHALL provide a has_transport method that accepts a transport name and returns a boolean indicating whether a Transport with the given name is registered.
10. THE TransportRegistry SHALL provide a __repr__ method that includes the class name and the count of registered transports.
11. THE TransportRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered transport names and protocol types.

### Requirement 4: Message Definition

**User Story:** As a developer, I want a well-defined message object with sender, recipient, payload, and metadata, so that I can exchange structured data between agents in a consistent format.

#### Acceptance Criteria

1. THE Message SHALL contain a unique string identifier, a sender AgentAddress, a recipient AgentAddress, a payload as a Python object (dictionary, list, string, or bytes), a headers dictionary, an optional correlation identifier string for request/response tracking, a timestamp, and a MessagePattern value.
2. WHEN a Message is created without an explicit unique identifier, THE Message SHALL generate a UUID-based identifier automatically.
3. WHEN a Message is created without an explicit timestamp, THE Message SHALL set the timestamp to the current UTC time.
4. THE Message SHALL expose all fields as read-only properties.
5. THE Message SHALL provide an as_dict method that returns a dictionary representation of the message fields.
6. THE Message SHALL provide a to_json method that returns a JSON string representation of the message fields.
7. THE Message SHALL provide a class method from_dict that constructs a Message from a dictionary.
8. THE Message SHALL provide a class method from_json that deserializes a JSON string into a Message instance.
9. FOR ALL valid Message instances with JSON-serializable payloads, calling to_json and then from_json SHALL produce an equivalent Message object (round-trip property).
10. THE Message SHALL provide a __repr__ method that includes the class name, identifier, pattern, and a truncated payload preview.
11. THE Message SHALL provide a __str__ method that returns a human-readable summary including the sender, recipient, pattern, and a truncated payload preview.

### Requirement 5: Message Pattern

**User Story:** As a developer, I want to classify messages by communication pattern, so that the messaging system can handle request/response, fire-and-forget, and pub/sub patterns appropriately.

#### Acceptance Criteria

1. THE MessagePattern enumeration SHALL define the values REQUEST, RESPONSE, FIRE_AND_FORGET, and EVENT.
2. THE MessagePattern enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding MessagePattern member.
3. IF an invalid string value is provided to the from_string method, THEN THE MessagePattern SHALL raise a SemanticError identifying the invalid value and listing the valid pattern values.

### Requirement 6: Message Envelope

**User Story:** As a developer, I want a transport-level wrapper around messages, so that I can track delivery metadata without modifying the message content.

#### Acceptance Criteria

1. THE MessageEnvelope SHALL contain the wrapped Message, the transport name as a string, the delivery attempt count as an integer, and the delivery status as a string (one of "pending", "delivered", "failed").
2. THE MessageEnvelope SHALL expose all fields as read-only properties.
3. THE MessageEnvelope SHALL provide an as_dict method that returns a dictionary representation of the envelope fields including the wrapped message.
4. THE MessageEnvelope SHALL provide a __repr__ method that includes the class name, message identifier, transport name, and delivery status.
5. THE MessageEnvelope SHALL provide a __str__ method that returns a human-readable summary including the message identifier, transport name, attempt count, and delivery status.

### Requirement 7: Agent Address

**User Story:** As a developer, I want a structured address object for agents, so that messages can be routed to the correct agent endpoint across different transports.

#### Acceptance Criteria

1. THE AgentAddress SHALL contain the agent identifier as a string, the transport name as a string, and protocol-specific endpoint information as a dictionary (supporting keys such as "host", "port", "path", "queue_name", "topic").
2. THE AgentAddress SHALL expose all fields as read-only properties.
3. THE AgentAddress SHALL provide an as_dict method that returns a dictionary representation of the address fields.
4. THE AgentAddress SHALL provide a to_json method that returns a JSON string representation of the address fields.
5. THE AgentAddress SHALL provide a class method from_dict that constructs an AgentAddress from a dictionary.
6. THE AgentAddress SHALL provide a class method from_json that deserializes a JSON string into an AgentAddress instance.
7. FOR ALL valid AgentAddress instances, calling to_json and then from_json SHALL produce an equivalent AgentAddress object (round-trip property).
8. THE AgentAddress SHALL provide a __repr__ method that includes the class name, agent identifier, and transport name.
9. THE AgentAddress SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, transport name, and endpoint information.
10. THE AgentAddress SHALL provide an __eq__ method that compares two AgentAddress instances by agent identifier and transport name.
11. THE AgentAddress SHALL provide a __hash__ method that returns a hash based on the agent identifier and transport name, enabling use as a dictionary key or set member.

### Requirement 8: Address Resolver

**User Story:** As a developer, I want to resolve agent identifiers to network addresses, so that I can send messages to agents without hardcoding endpoint details.

#### Acceptance Criteria

1. THE AddressResolver SHALL provide a resolve method that accepts an agent identifier string and a transport name string and returns an AgentAddress.
2. THE AddressResolver SHALL support static address resolution by looking up addresses from a configured address mapping dictionary.
3. THE AddressResolver SHALL support dynamic address resolution by querying the AgentRegistry for the agent and deriving the AgentAddress from the agent's registered transport configuration.
4. IF the agent identifier cannot be resolved to an AgentAddress, THEN THE AddressResolver SHALL raise a MessageRoutingError that includes the agent identifier and the transport name.
5. THE AddressResolver SHALL provide a register_address method that accepts an agent identifier, transport name, and endpoint dictionary, and stores the mapping for static resolution.
6. THE AddressResolver SHALL provide a deregister_address method that accepts an agent identifier and transport name and removes the static mapping.
7. THE AddressResolver SHALL provide a __repr__ method that includes the class name and the count of registered static addresses.
8. THE AddressResolver SHALL provide a __str__ method that returns a human-readable summary including the count of static addresses and whether dynamic resolution is enabled.

### Requirement 9: Message Serialization

**User Story:** As a developer, I want pluggable message serializers for multiple wire formats, so that I can choose the serialization format that best fits my transport and performance requirements.

#### Acceptance Criteria

1. THE MessageSerializer base class SHALL define an abstract interface that includes a serialize method that accepts a Python object and returns bytes, and a deserialize method that accepts bytes and returns a Python object.
2. THE MessageSerializer base class SHALL require all subclasses to provide an implementation for the serialize and deserialize methods.
3. THE MessageSerializer base class SHALL expose a read-only property for the format name as a string (e.g., "json", "protobuf", "msgpack").
4. THE MessageSerializer base class SHALL expose a read-only property for the content type as a string (e.g., "application/json", "application/x-protobuf", "application/x-msgpack").
5. THE framework SHALL provide a JsonMessageSerializer that serializes Python objects to JSON-encoded bytes and deserializes JSON-encoded bytes to Python objects.
6. THE framework SHALL provide a MsgpackMessageSerializer that serializes Python objects to MessagePack-encoded bytes and deserializes MessagePack-encoded bytes to Python objects.
7. THE framework SHALL provide a ProtobufMessageSerializer that serializes Protobuf message objects to Protobuf-encoded bytes and deserializes Protobuf-encoded bytes to Protobuf message objects.
8. WHEN the JsonMessageSerializer receives a Python object that is not JSON-serializable, THEN THE JsonMessageSerializer SHALL raise a MessageSerializationError that includes the object type and the serialization error detail.
9. WHEN the JsonMessageSerializer receives bytes that are not valid JSON, THEN THE JsonMessageSerializer SHALL raise a MessageSerializationError that includes the raw bytes length and the deserialization error detail.
10. WHEN the MsgpackMessageSerializer receives bytes that are not valid MessagePack, THEN THE MsgpackMessageSerializer SHALL raise a MessageSerializationError that includes the raw bytes length and the deserialization error detail.
11. WHEN the ProtobufMessageSerializer receives bytes that are not valid Protobuf for the expected message type, THEN THE ProtobufMessageSerializer SHALL raise a MessageSerializationError that includes the expected message type and the deserialization error detail.
12. FOR ALL valid Python objects that are JSON-serializable, serializing with JsonMessageSerializer and then deserializing SHALL produce an equivalent Python object (round-trip property).
13. FOR ALL valid Python objects that are MessagePack-serializable, serializing with MsgpackMessageSerializer and then deserializing SHALL produce an equivalent Python object (round-trip property).
14. THE MessageSerializer base class SHALL provide a __repr__ method that includes the class name and format name.
15. THE MessageSerializer base class SHALL provide a __str__ method that returns a human-readable summary including the format name and content type.

### Requirement 10: Message Serializer Registry

**User Story:** As a developer, I want a registry that tracks available message serializers, so that I can discover and look up serializers by format name.

#### Acceptance Criteria

1. THE MessageSerializerRegistry SHALL support registration of a MessageSerializer instance using the format name as the registration key.
2. IF a MessageSerializer with a duplicate format name is registered, THEN THE MessageSerializerRegistry SHALL raise a SemanticError that includes the duplicate format name.
3. THE MessageSerializerRegistry SHALL support deregistration of a MessageSerializer by format name.
4. THE MessageSerializerRegistry SHALL support lookup of a registered MessageSerializer by format name, returning the MessageSerializer instance or None when the format name is not found.
5. THE MessageSerializerRegistry SHALL support enumeration of all registered MessageSerializer instances as a list.
6. THE MessageSerializerRegistry SHALL expose a read-only property for the count of currently registered serializers.
7. THE MessageSerializerRegistry SHALL provide a has_serializer method that accepts a format name and returns a boolean indicating whether a MessageSerializer with the given format name is registered.
8. THE MessageSerializerRegistry SHALL provide a __repr__ method that includes the class name and the count of registered serializers.
9. THE MessageSerializerRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered format names.

### Requirement 11: Message Router

**User Story:** As a developer, I want to route incoming messages to registered handlers based on topic or pattern, so that agents can process different message types with dedicated handler logic.

#### Acceptance Criteria

1. THE MessageRouter SHALL support registration of a MessageHandler callback for a specific topic string.
2. THE MessageRouter SHALL support registration of a MessageHandler callback for a specific MessagePattern value.
3. THE MessageRouter SHALL support registration of a MessageHandler callback with a custom filter callable that accepts a Message and returns a boolean.
4. WHEN a Message is received, THE MessageRouter SHALL invoke all registered MessageHandler callbacks whose topic, pattern, or custom filter matches the incoming Message.
5. THE MessageRouter SHALL invoke matching handlers in the order they were registered.
6. IF no registered handler matches an incoming Message, THEN THE MessageRouter SHALL raise a MessageRoutingError that includes the message identifier, topic, and pattern.
7. THE MessageRouter SHALL support deregistration of a MessageHandler callback by a registration identifier returned at registration time.
8. THE MessageRouter SHALL expose a read-only property for the count of registered handlers.
9. IF a MessageHandler callback raises an exception during invocation, THEN THE MessageRouter SHALL log the exception with the message identifier and handler registration identifier, and continue invoking the remaining matching handlers.
10. THE MessageRouter SHALL provide a __repr__ method that includes the class name and the count of registered handlers.
11. THE MessageRouter SHALL provide a __str__ method that returns a human-readable summary including the count of registered handlers and the list of registered topics.

### Requirement 12: Request/Response Pattern

**User Story:** As a developer, I want to send a request message and await a correlated response, so that agents can perform synchronous-style interactions over asynchronous transports.

#### Acceptance Criteria

1. THE RequestResponseHandler SHALL provide a send_request method that accepts a Message with MessagePattern.REQUEST, sends the message through the specified Transport, and returns a correlated response Message.
2. THE RequestResponseHandler SHALL generate a correlation identifier for each outgoing request and set the correlation identifier on the request Message.
3. WHEN a response Message is received with a correlation identifier matching a pending request, THE RequestResponseHandler SHALL deliver the response to the waiting caller.
4. THE RequestResponseHandler SHALL accept a timeout in seconds as a float for each request, defaulting to the value configured in the MessagingConfiguration.
5. IF a response is not received within the timeout duration, THEN THE RequestResponseHandler SHALL raise a MessageTimeoutError that includes the request message identifier, the correlation identifier, and the timeout duration.
6. THE RequestResponseHandler SHALL support multiple concurrent pending requests, each tracked by a unique correlation identifier.
7. THE RequestResponseHandler SHALL provide a read-only property for the count of currently pending requests.
8. THE RequestResponseHandler SHALL provide a cancel method that accepts a correlation identifier and cancels the pending request, raising a MessageTimeoutError to the waiting caller.
9. THE RequestResponseHandler SHALL provide a __repr__ method that includes the class name and the count of pending requests.
10. THE RequestResponseHandler SHALL provide a __str__ method that returns a human-readable summary including the count of pending requests and the default timeout.

### Requirement 13: Fire-and-Forget Pattern

**User Story:** As a developer, I want to send messages without waiting for a response, so that agents can perform non-blocking notifications and commands.

#### Acceptance Criteria

1. WHEN a Message with MessagePattern.FIRE_AND_FORGET is sent through a Transport, THE Transport SHALL send the message and return immediately without waiting for a response.
2. THE Transport SHALL return a MessageEnvelope with delivery status "delivered" when the send operation completes successfully.
3. IF the send operation fails, THEN THE Transport SHALL return a MessageEnvelope with delivery status "failed" and raise a TransportError that includes the message identifier and the transport error detail.
4. THE framework SHALL log each fire-and-forget message send at INFO level including the message identifier, sender address, and recipient address.

### Requirement 14: Pub/Sub Messaging

**User Story:** As a developer, I want topic-based publish/subscribe messaging, so that agents can broadcast events and subscribe to events from other agents without direct coupling.

#### Acceptance Criteria

1. THE PubSubBroker SHALL provide a subscribe method that accepts a topic string, a subscriber agent identifier, and a MessageHandler callback, and returns a Subscription object.
2. THE PubSubBroker SHALL provide an unsubscribe method that accepts a Subscription object and removes the subscription.
3. THE PubSubBroker SHALL provide a publish method that accepts a topic string and a Message with MessagePattern.EVENT, and delivers the message to all subscribers of the topic.
4. WHEN a message is published to a topic, THE PubSubBroker SHALL invoke the MessageHandler callback of each subscriber registered for the topic.
5. THE PubSubBroker SHALL invoke subscriber handlers in the order the subscriptions were registered.
6. IF a subscriber MessageHandler callback raises an exception during invocation, THEN THE PubSubBroker SHALL log the exception with the topic, subscriber agent identifier, and message identifier, and continue delivering to the remaining subscribers.
7. THE PubSubBroker SHALL provide a read-only property for the list of active topic strings.
8. THE PubSubBroker SHALL provide a method that accepts a topic string and returns the count of subscribers for the topic.
9. THE PubSubBroker SHALL provide a method that accepts a topic string and returns the list of subscriber agent identifiers for the topic.
10. THE PubSubBroker SHALL support wildcard topic matching using a "*" character to match a single topic segment and a "#" character to match zero or more topic segments, where segments are separated by "." characters.
11. THE PubSubBroker SHALL provide a __repr__ method that includes the class name and the count of active topics.
12. THE PubSubBroker SHALL provide a __str__ method that returns a human-readable summary including the count of active topics and total subscription count.

### Requirement 15: Subscription

**User Story:** As a developer, I want a structured subscription object, so that I can inspect and manage topic subscriptions.

#### Acceptance Criteria

1. THE Subscription SHALL contain a unique string identifier, the subscriber agent identifier, the topic string, an optional message filter callable, and the MessageHandler callback reference.
2. WHEN a Subscription is created without an explicit unique identifier, THE Subscription SHALL generate a UUID-based identifier automatically.
3. THE Subscription SHALL expose all fields as read-only properties (excluding the filter callable and handler callback internals).
4. THE Subscription SHALL provide an as_dict method that returns a dictionary representation containing the identifier, subscriber agent identifier, and topic string.
5. THE Subscription SHALL provide a __repr__ method that includes the class name, identifier, subscriber agent identifier, and topic.
6. THE Subscription SHALL provide a __str__ method that returns a human-readable summary including the subscriber agent identifier and topic.

### Requirement 16: Built-in HTTP Transport

**User Story:** As a developer, I want a built-in HTTP transport, so that agents can communicate over HTTP without writing custom transport code.

#### Acceptance Criteria

1. THE HttpTransport SHALL implement the Transport interface using HTTP request/response semantics.
2. THE HttpTransport SHALL support sending messages as HTTP POST requests with the serialized message payload as the request body.
3. THE HttpTransport SHALL support configurable HTTP headers from the TransportConfiguration headers dictionary.
4. THE HttpTransport SHALL support TLS connections when the TransportConfiguration specifies HTTPS.
5. THE HttpTransport SHALL resolve CredentialReference names for authentication headers (Bearer tokens, API keys) through `automojo-credentials`.
6. IF an HTTP request fails due to a connection error, THEN THE HttpTransport SHALL raise a TransportError that includes the target URL and the connection error detail.
7. IF an HTTP request fails due to a timeout, THEN THE HttpTransport SHALL raise a TransportError that includes the target URL and the timeout duration.
8. IF an HTTP response has a status code indicating a server error (5xx), THEN THE HttpTransport SHALL raise a TransportError that includes the target URL, the status code, and the response body.

### Requirement 17: Built-in WebSocket Transport

**User Story:** As a developer, I want a built-in WebSocket transport, so that agents can communicate over persistent bidirectional connections.

#### Acceptance Criteria

1. THE WebSocketTransport SHALL implement the Transport interface using WebSocket protocol semantics.
2. WHEN the connect method is called, THE WebSocketTransport SHALL establish a persistent WebSocket connection to the configured endpoint.
3. WHEN the disconnect method is called, THE WebSocketTransport SHALL close the WebSocket connection gracefully.
4. THE WebSocketTransport SHALL support sending messages as WebSocket text frames with the serialized message payload.
5. THE WebSocketTransport SHALL support receiving messages from WebSocket text frames and deserializing the payload.
6. THE WebSocketTransport SHALL support TLS connections (wss://) when the TransportConfiguration specifies secure WebSocket.
7. IF the WebSocket connection is lost unexpectedly, THEN THE WebSocketTransport SHALL raise a TransportError that includes the endpoint URL and the disconnection reason.
8. THE WebSocketTransport SHALL provide a read-only property for the connection state as a string (one of "disconnected", "connecting", "connected", "closing").

### Requirement 18: Built-in gRPC Transport

**User Story:** As a developer, I want a built-in gRPC transport, so that agents can communicate using high-performance RPC with schema-defined messages.

#### Acceptance Criteria

1. THE GrpcTransport SHALL implement the Transport interface using gRPC protocol semantics.
2. WHEN the connect method is called, THE GrpcTransport SHALL establish a gRPC channel to the configured endpoint.
3. WHEN the disconnect method is called, THE GrpcTransport SHALL close the gRPC channel gracefully.
4. THE GrpcTransport SHALL support sending messages as gRPC unary calls with the serialized message payload.
5. THE GrpcTransport SHALL support TLS connections when the TransportConfiguration specifies secure gRPC.
6. THE GrpcTransport SHALL resolve CredentialReference names for channel credentials through `automojo-credentials`.
7. IF a gRPC call fails due to a connection error, THEN THE GrpcTransport SHALL raise a TransportError that includes the target endpoint and the gRPC status code.
8. IF a gRPC call fails due to a deadline exceeded, THEN THE GrpcTransport SHALL raise a TransportError that includes the target endpoint and the timeout duration.

### Requirement 19: Built-in Message Queue Transport

**User Story:** As a developer, I want a built-in message queue transport, so that agents can communicate through durable message queues for reliable asynchronous messaging.

#### Acceptance Criteria

1. THE MessageQueueTransport SHALL implement the Transport interface using message queue semantics.
2. WHEN the connect method is called, THE MessageQueueTransport SHALL establish a connection to the configured message queue broker.
3. WHEN the disconnect method is called, THE MessageQueueTransport SHALL close the connection to the message queue broker gracefully.
4. THE MessageQueueTransport SHALL support sending messages by publishing to a named queue.
5. THE MessageQueueTransport SHALL support receiving messages by consuming from a named queue.
6. THE MessageQueueTransport SHALL support configurable queue names from the TransportConfiguration options dictionary.
7. THE MessageQueueTransport SHALL resolve CredentialReference names for broker authentication through `automojo-credentials`.
8. IF a message queue operation fails due to a connection error, THEN THE MessageQueueTransport SHALL raise a TransportError that includes the broker endpoint and the connection error detail.
9. IF a message queue operation fails due to a queue not found error, THEN THE MessageQueueTransport SHALL raise a TransportError that includes the queue name.

### Requirement 20: Messaging Configuration

**User Story:** As a developer, I want to configure the messaging system declaratively, so that I can define default transport, serialization format, timeouts, and pub/sub settings without modifying code.

#### Acceptance Criteria

1. THE MessagingConfiguration SHALL contain the default transport name as a string, the default serialization format name as a string, the default request timeout in seconds as a float, and pub/sub settings as a dictionary.
2. THE MessagingConfiguration SHALL support loading configuration from a Python dictionary.
3. THE MessagingConfiguration SHALL support loading configuration from a JSON file path.
4. THE MessagingConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE MessagingConfiguration SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
6. THE MessagingConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. THE MessagingConfiguration SHALL support CredentialReference entries that are resolved through `automojo-credentials` at initialization time.
8. IF a CredentialReference cannot be resolved, THEN THE MessagingConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
9. THE MessagingConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration, excluding resolved credential values.
10. THE MessagingConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration, excluding resolved credential values.
11. THE MessagingConfiguration SHALL provide a class method from_dict that constructs a MessagingConfiguration from a dictionary.
12. THE MessagingConfiguration SHALL provide a class method from_json that deserializes a JSON string into a MessagingConfiguration instance.
13. FOR ALL valid MessagingConfiguration instances, calling to_json and then from_json SHALL produce an equivalent MessagingConfiguration object (round-trip property).
14. THE MessagingConfiguration SHALL provide a __repr__ method that includes the class name, default transport name, and default serialization format.
15. THE MessagingConfiguration SHALL provide a __str__ method that returns a human-readable summary including the default transport name, default serialization format, and default request timeout.

### Requirement 21: Agent Messaging Integration

**User Story:** As a developer, I want agents to own transports, routers, and pub/sub brokers through the agent interface, so that messaging is scoped to individual agents and integrated with the agent lifecycle.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only transports property that returns the Agent's TransportRegistry instance.
2. THE Agent base class SHALL expose a read-only message_router property that returns the Agent's MessageRouter instance.
3. THE Agent base class SHALL expose a read-only pubsub property that returns the Agent's PubSubBroker instance.
4. THE Agent base class SHALL expose a read-only address_resolver property that returns the Agent's AddressResolver instance.
5. THE Agent base class SHALL provide a register_transport method that accepts a Transport instance and registers the Transport with the Agent's TransportRegistry.
6. THE Agent base class SHALL provide a send_message method that accepts a recipient agent identifier, a payload, and optional parameters (transport name, serialization format, pattern, headers), constructs a Message, resolves the recipient address, serializes the payload, and sends the message through the specified Transport.
7. THE Agent base class SHALL provide a request method that accepts a recipient agent identifier, a payload, and optional parameters (transport name, serialization format, timeout, headers), sends a request Message, and returns the correlated response Message.
8. THE Agent base class SHALL provide a publish method that accepts a topic string and a payload, constructs an event Message, and publishes the message through the PubSubBroker.
9. THE Agent base class SHALL provide a subscribe method that accepts a topic string and a MessageHandler callback, and registers a subscription with the PubSubBroker.
10. IF the requested transport name is not found in the Agent's TransportRegistry, THEN THE send_message method SHALL raise a SemanticError that includes the requested transport name and the agent identity.
11. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL construct the TransportRegistry, MessageRouter, PubSubBroker, AddressResolver, and RequestResponseHandler from the Agent's MessagingConfiguration.
12. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all Transport and MessageSerializer plugins from `automojo-extension` ExtensionPoint entries targeting the Agent.
13. WHEN an Agent transitions to the STOPPED state, THE Agent SHALL disconnect all connected Transports and clear the TransportRegistry.
14. WHEN an Agent transitions to the STOPPED state, THE Agent's PubSubBroker SHALL remove all subscriptions.
15. IF the Agent's MessagingConfiguration is not provided, THEN THE Agent SHALL default to a JsonMessageSerializer and no registered transports.

### Requirement 22: Transport Plugin Integration

**User Story:** As a developer, I want to distribute transports as plugins through `automojo-extension`, so that transport packages can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.transports" through `automojo-extension` for registering Transport plugin implementations.
2. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.message_serializers" through `automojo-extension` for registering MessageSerializer plugin implementations.
3. WHEN an Agent is initialized, THE Agent SHALL query the "automojo.agentkit.transports" ExtensionPoint and register all discovered Transport instances with the Agent's TransportRegistry.
4. WHEN an Agent is initialized, THE Agent SHALL query the "automojo.agentkit.message_serializers" ExtensionPoint and register all discovered MessageSerializer instances with the Agent's MessageSerializerRegistry.
5. IF a Transport plugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
6. IF a Transport plugin provides a Transport with a name that conflicts with an already registered Transport, THEN THE Agent SHALL log the conflict at WARNING level including both transport names and skip the conflicting plugin transport.
7. IF a MessageSerializer plugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
8. IF a MessageSerializer plugin provides a serializer with a format name that conflicts with an already registered serializer, THEN THE Agent SHALL log the conflict at WARNING level including both format names and skip the conflicting plugin serializer.

### Requirement 23: Messaging Error Handling

**User Story:** As a developer, I want well-defined error types for transport, serialization, routing, and timeout failures, so that I can diagnose and handle messaging errors precisely.

#### Acceptance Criteria

1. THE TransportError SHALL inherit from AgentKitError and SHALL be raised when a Transport operation fails due to a connection, send, or receive error.
2. THE TransportError SHALL contain the transport name, the operation name (connect, disconnect, send, receive), and the original exception as the cause.
3. THE MessageSerializationError SHALL inherit from AgentKitError and SHALL be raised when a MessageSerializer fails to serialize or deserialize a message payload.
4. THE MessageSerializationError SHALL contain the serializer format name, the serialization direction (serialize or deserialize), and a descriptive error message.
5. THE MessageRoutingError SHALL inherit from AgentKitError and SHALL be raised when the MessageRouter or AddressResolver cannot route or resolve a message destination.
6. THE MessageRoutingError SHALL contain the message identifier (when available), the target agent identifier or topic, and a descriptive error message.
7. THE MessageTimeoutError SHALL inherit from AgentKitError and SHALL be raised when a request/response exchange exceeds the configured timeout duration.
8. THE MessageTimeoutError SHALL contain the request message identifier, the correlation identifier, and the timeout duration in seconds.
9. ALL messaging-related exceptions SHALL provide a meaningful __repr__ that includes the exception class name and descriptive message.

### Requirement 24: Messaging Serialization

**User Story:** As a developer, I want to serialize and deserialize messages, addresses, configurations, and subscriptions, so that messaging data can be stored, transmitted, and reconstructed.

#### Acceptance Criteria

1. THE Message SHALL provide a to_json method that serializes the message to a JSON string.
2. THE Message SHALL provide a class method from_json that deserializes a JSON string into a Message instance.
3. THE AgentAddress SHALL provide a to_json method that serializes the address to a JSON string.
4. THE AgentAddress SHALL provide a class method from_json that deserializes a JSON string into an AgentAddress instance.
5. THE TransportConfiguration SHALL provide a to_json method that serializes the configuration to a JSON string, excluding resolved credential values.
6. THE TransportConfiguration SHALL provide a class method from_json that deserializes a JSON string into a TransportConfiguration instance.
7. THE MessagingConfiguration SHALL provide a to_json method that serializes the configuration to a JSON string, excluding resolved credential values.
8. THE MessagingConfiguration SHALL provide a class method from_json that deserializes a JSON string into a MessagingConfiguration instance.
9. FOR ALL valid Message instances with JSON-serializable payloads, calling to_json and then from_json SHALL produce an equivalent Message object (round-trip property).
10. FOR ALL valid AgentAddress instances, calling to_json and then from_json SHALL produce an equivalent AgentAddress object (round-trip property).
11. FOR ALL valid TransportConfiguration instances, calling to_json and then from_json SHALL produce an equivalent TransportConfiguration object (round-trip property).
12. FOR ALL valid MessagingConfiguration instances, calling to_json and then from_json SHALL produce an equivalent MessagingConfiguration object (round-trip property).

### Requirement 25: Structured Logging for Messaging Operations

**User Story:** As a developer, I want messaging operations to produce structured log entries, so that I can monitor and debug agent communication using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy under `automojo.agentkit.messaging`.
2. WHEN a Transport connects, THE Transport SHALL log at INFO level including the transport name, protocol type, and endpoint.
3. WHEN a Transport disconnects, THE Transport SHALL log at INFO level including the transport name and protocol type.
4. WHEN a message is sent, THE framework SHALL log at INFO level including the message identifier, sender address, recipient address, transport name, and pattern.
5. WHEN a message is received, THE framework SHALL log at INFO level including the message identifier, sender address, transport name, and pattern.
6. WHEN a message send fails, THE framework SHALL log at WARNING level including the message identifier, transport name, and error detail.
7. WHEN a pub/sub message is published, THE PubSubBroker SHALL log at INFO level including the topic, message identifier, and subscriber count.
8. WHEN a subscription is created, THE PubSubBroker SHALL log at INFO level including the topic and subscriber agent identifier.
9. WHEN a subscription is removed, THE PubSubBroker SHALL log at INFO level including the topic and subscriber agent identifier.
10. WHEN a request/response exchange times out, THE RequestResponseHandler SHALL log at WARNING level including the request message identifier, correlation identifier, and timeout duration.

### Requirement 26: Messaging String Representations

**User Story:** As a developer, I want meaningful string representations on messaging system classes, so that I can quickly inspect messaging state during debugging sessions.

#### Acceptance Criteria

1. THE Transport base class SHALL provide a __repr__ method that includes the class name, transport name, and protocol type.
2. THE Transport base class SHALL provide a __str__ method that returns a human-readable summary including the transport name, protocol type, and connection status.
3. THE Message SHALL provide a __repr__ method that includes the class name, identifier, pattern, and a truncated payload preview.
4. THE Message SHALL provide a __str__ method that returns a human-readable summary including the sender, recipient, pattern, and a truncated payload preview.
5. THE MessageEnvelope SHALL provide a __repr__ method that includes the class name, message identifier, transport name, and delivery status.
6. THE MessageEnvelope SHALL provide a __str__ method that returns a human-readable summary including the message identifier, transport name, attempt count, and delivery status.
7. THE AgentAddress SHALL provide a __repr__ method that includes the class name, agent identifier, and transport name.
8. THE AgentAddress SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, transport name, and endpoint information.
9. THE TransportRegistry SHALL provide a __repr__ method that includes the class name and the count of registered transports.
10. THE TransportRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered transport names and protocol types.
11. THE MessageSerializerRegistry SHALL provide a __repr__ method that includes the class name and the count of registered serializers.
12. THE MessageSerializerRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered format names.
13. THE MessageRouter SHALL provide a __repr__ method that includes the class name and the count of registered handlers.
14. THE MessageRouter SHALL provide a __str__ method that returns a human-readable summary including the count of registered handlers and the list of registered topics.
15. THE PubSubBroker SHALL provide a __repr__ method that includes the class name and the count of active topics.
16. THE PubSubBroker SHALL provide a __str__ method that returns a human-readable summary including the count of active topics and total subscription count.
17. THE RequestResponseHandler SHALL provide a __repr__ method that includes the class name and the count of pending requests.
18. THE RequestResponseHandler SHALL provide a __str__ method that returns a human-readable summary including the count of pending requests and the default timeout.
19. THE Subscription SHALL provide a __repr__ method that includes the class name, identifier, subscriber agent identifier, and topic.
20. THE Subscription SHALL provide a __str__ method that returns a human-readable summary including the subscriber agent identifier and topic.
21. THE TransportConfiguration SHALL provide a __repr__ method that includes the class name, protocol type, host, and port.
22. THE TransportConfiguration SHALL provide a __str__ method that returns a human-readable summary including the protocol type, host, port, and timeout.
23. THE MessagingConfiguration SHALL provide a __repr__ method that includes the class name, default transport name, and default serialization format.
24. THE MessagingConfiguration SHALL provide a __str__ method that returns a human-readable summary including the default transport name, default serialization format, and default request timeout.
