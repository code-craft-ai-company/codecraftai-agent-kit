"""
    Defines the MessageQueueTransport class, a concrete Transport
    implementation that uses message queue semantics for reliable
    asynchronous messaging between agents.

    The MessageQueueTransport publishes messages to and consumes
    messages from named queues via a pluggable broker client. The
    broker client is injected through the TransportConfiguration
    options dictionary under the key ``broker_client``, since
    specific queue libraries (pika, kombu, etc.) may not be
    installed in all environments.

    Queue names are configured through the TransportConfiguration
    options dictionary:
    - ``publish_queue``: the queue name used for sending messages
    - ``consume_queue``: the queue name used for receiving messages

    Credential resolution for broker authentication is supported
    through the credential_references in the TransportConfiguration.

    The transport raises TransportError for connection errors and
    queue-not-found conditions.

    Structured logging is performed under the
    automojo.agentkit.messaging.transport.messagequeue logger
    hierarchy.

    .. module:: automojo.agentkit.transports.messagequeuetransport
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Message queue transport implementation for reliable
        asynchronous agent messaging.

    Requirements: 19.1-19.9
"""

import json
import logging

from typing import Dict
from typing import List
from typing import Optional

from automojo.agentkit.message import Message
from automojo.agentkit.messageenvelope import MessageEnvelope
from automojo.agentkit.messagingerrors import TransportError
from automojo.agentkit.transport import Transport
from automojo.agentkit.transportconfiguration import TransportConfiguration


class MessageQueueTransport(Transport):
    """
        Transport implementation using message queue semantics for
        reliable asynchronous messaging between agents.

        Uses a pluggable broker client that is injected through the
        TransportConfiguration options dictionary under the key
        ``broker_client``. The broker client must provide the
        following interface:

        - ``connect(host, port, credentials=None)``: Establish a
          connection to the message broker.
        - ``disconnect()``: Close the broker connection.
        - ``publish(queue_name, body)``: Publish a bytes payload
          to the named queue.
        - ``consume(queue_name)``: Consume a single message from
          the named queue, returning bytes or None.

        Queue names are configured through the TransportConfiguration
        options dictionary:
        - ``publish_queue``: the queue name used for sending messages
        - ``consume_queue``: the queue name used for receiving messages

        Credential resolution for broker authentication is supported
        through the credential_references in the TransportConfiguration.
        The transport looks for ``username`` and ``password`` keys in
        the credential_references dictionary.

        TransportError is raised for connection errors and
        queue-not-found conditions.

        :param name: The transport name string.
        :param configuration: The TransportConfiguration instance
            defining message queue connection parameters.
        :param credential_names: An optional list of credential
            reference names required for authentication.
        :param tags: An optional dictionary of tags for categorization
            and discovery.
    """

    def __init__(self, name: str, configuration: TransportConfiguration,
                 credential_names: Optional[List[str]] = None,
                 tags: Optional[Dict[str, str]] = None) -> None:

        super().__init__(
            name=name,
            protocol_type="message_queue",
            configuration=configuration,
            credential_names=credential_names,
            tags=tags
        )

        self._mq_logger = logging.getLogger(
            "automojo.agentkit.messaging.transport.messagequeue"
        )
        self._broker_client = None
        self._publish_queue = None
        self._consume_queue = None

        return

    def _resolve_broker_credentials(self) -> Optional[Dict[str, str]]:
        """
            Resolves broker authentication credentials from the
            credential references in the TransportConfiguration.

            Looks for ``username`` and ``password`` keys in the
            configuration's credential_references dictionary.

            :returns: A dictionary with ``username`` and ``password``
                keys, or None if no broker credentials are configured.
        """
        cred_refs = self._configuration.credential_references

        username = cred_refs.get("username", None)
        password = cred_refs.get("password", None)

        if username is not None or password is not None:
            credentials = {
                "username": username,
                "password": password
            }
            return credentials

        return None

    def connect(self) -> None:
        """
            Establishes a connection to the configured message queue
            broker using the injected broker client.

            The broker client is obtained from the TransportConfiguration
            options dictionary under the key ``broker_client``. If no
            broker client is provided, raises a TransportError.

            Queue names are read from the options dictionary under the
            keys ``publish_queue`` and ``consume_queue``.

            Credential resolution for broker authentication is
            supported through the credential_references in the
            TransportConfiguration.

            Sets the transport to connected status upon success.

            :raises TransportError: If no broker client is provided
                or if the connection to the broker fails.
        """
        try:
            options = self._configuration.options

            broker_client = options.get("broker_client", None)

            if broker_client is None:
                self._mq_logger.warning(
                    "Message queue transport connect failed: name=%s, "
                    "error=no broker_client provided in options",
                    self._name
                )
                raise TransportError(
                    transport_name=self._name,
                    operation="connect",
                    cause=ValueError(
                        "No broker_client provided in TransportConfiguration "
                        "options. A broker client must be injected via "
                        "options['broker_client']."
                    )
                )

            self._broker_client = broker_client

            self._publish_queue = options.get("publish_queue", None)
            self._consume_queue = options.get("consume_queue", None)

            host = self._configuration.host
            port = self._configuration.port

            credentials = self._resolve_broker_credentials()

            self._broker_client.connect(
                host, port, credentials=credentials
            )

            self._connected = True

            self._mq_logger.info(
                "Message queue transport connected: name=%s, "
                "endpoint=%s:%s, publish_queue=%s, consume_queue=%s",
                self._name, host, port,
                self._publish_queue, self._consume_queue
            )

        except TransportError:
            raise

        except Exception as ex:
            self._connected = False
            self._broker_client = None

            self._mq_logger.warning(
                "Message queue transport connect failed: name=%s, "
                "endpoint=%s:%s, error=%s",
                self._name, self._configuration.host,
                self._configuration.port, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="connect",
                cause=ex
            )

        return

    def disconnect(self) -> None:
        """
            Closes the connection to the message queue broker
            gracefully.

            Sets the transport to disconnected status.

            :raises TransportError: If the disconnection fails.
        """
        try:
            if self._broker_client is not None:
                self._broker_client.disconnect()

            self._connected = False
            self._broker_client = None
            self._publish_queue = None
            self._consume_queue = None

            self._mq_logger.info(
                "Message queue transport disconnected: name=%s",
                self._name
            )

        except Exception as ex:
            self._connected = False
            self._broker_client = None

            self._mq_logger.warning(
                "Message queue transport disconnect failed: name=%s, "
                "error=%s",
                self._name, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="disconnect",
                cause=ex
            )

        return

    def send(self, message: Message) -> MessageEnvelope:
        """
            Sends a Message by publishing it to the configured
            publish queue.

            The message is serialized to JSON bytes via its as_dict
            method and published to the queue named by the
            ``publish_queue`` option. If no publish queue is
            configured, raises a TransportError.

            :param message: The Message to send.

            :returns: A MessageEnvelope with delivery metadata.

            :raises TransportError: If the transport is not connected,
                if no publish queue is configured, or if the publish
                operation fails.
        """
        if not self._connected or self._broker_client is None:
            errmsg = "Transport '{}' is not connected.".format(self._name)
            self._mq_logger.warning(
                "Message queue transport send failed: name=%s, "
                "reason=not connected",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ConnectionError(errmsg)
            )

        if self._publish_queue is None:
            self._mq_logger.warning(
                "Message queue transport send failed: name=%s, "
                "reason=no publish_queue configured",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ValueError(
                    "No publish_queue configured in TransportConfiguration "
                    "options for transport '{}'.".format(self._name)
                )
            )

        try:
            message_data = message.as_dict()
            body_bytes = json.dumps(message_data).encode("utf-8")

            self._broker_client.publish(self._publish_queue, body_bytes)

            self._mq_logger.info(
                "Message queue transport message sent: name=%s, "
                "message_id=%s, sender=%s, recipient=%s, "
                "pattern=%s, queue=%s",
                self._name, message.identifier,
                message.sender.agent_identifier,
                message.recipient.agent_identifier,
                message.pattern.value, self._publish_queue
            )

            envelope = MessageEnvelope(
                message=message,
                transport_name=self._name,
                attempt_count=1,
                delivery_status="delivered"
            )

            return envelope

        except Exception as ex:
            queue_not_found = False
            ex_str = str(ex).lower()
            if "queue not found" in ex_str or "not found" in ex_str:
                queue_not_found = True

            if queue_not_found:
                self._mq_logger.warning(
                    "Message queue transport send failed "
                    "(queue not found): name=%s, message_id=%s, "
                    "queue=%s",
                    self._name, message.identifier,
                    self._publish_queue
                )
            else:
                self._mq_logger.warning(
                    "Message queue transport send failed: name=%s, "
                    "message_id=%s, queue=%s, error=%s",
                    self._name, message.identifier,
                    self._publish_queue, ex
                )

            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ex
            )

    def receive(self) -> Message:
        """
            Receives a Message by consuming from the configured
            consume queue.

            Consumes a single message from the queue named by the
            ``consume_queue`` option. The consumed bytes are
            deserialized from JSON into a Message instance. If no
            consume queue is configured, raises a TransportError.

            :returns: The received Message.

            :raises TransportError: If the transport is not connected,
                if no consume queue is configured, if the consume
                operation fails, or if no message is available.
        """
        if not self._connected or self._broker_client is None:
            errmsg = "Transport '{}' is not connected.".format(self._name)
            self._mq_logger.warning(
                "Message queue transport receive failed: name=%s, "
                "reason=not connected",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="receive",
                cause=ConnectionError(errmsg)
            )

        if self._consume_queue is None:
            self._mq_logger.warning(
                "Message queue transport receive failed: name=%s, "
                "reason=no consume_queue configured",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="receive",
                cause=ValueError(
                    "No consume_queue configured in TransportConfiguration "
                    "options for transport '{}'.".format(self._name)
                )
            )

        try:
            raw_data = self._broker_client.consume(self._consume_queue)

            if raw_data is None:
                self._mq_logger.warning(
                    "Message queue transport receive failed: name=%s, "
                    "reason=no message available, queue=%s",
                    self._name, self._consume_queue
                )
                raise TransportError(
                    transport_name=self._name,
                    operation="receive",
                    cause=RuntimeError(
                        "No message available on queue '{}' for "
                        "transport '{}'.".format(
                            self._consume_queue, self._name
                        )
                    )
                )

            if isinstance(raw_data, bytes):
                json_str = raw_data.decode("utf-8")
            else:
                json_str = str(raw_data)

            received_message = Message.from_json(json_str)

            self._mq_logger.info(
                "Message queue transport message received: name=%s, "
                "message_id=%s, sender=%s, pattern=%s, queue=%s",
                self._name, received_message.identifier,
                received_message.sender.agent_identifier,
                received_message.pattern.value, self._consume_queue
            )

            return received_message

        except TransportError:
            raise

        except Exception as ex:
            queue_not_found = False
            ex_str = str(ex).lower()
            if "queue not found" in ex_str or "not found" in ex_str:
                queue_not_found = True

            if queue_not_found:
                self._mq_logger.warning(
                    "Message queue transport receive failed "
                    "(queue not found): name=%s, queue=%s",
                    self._name, self._consume_queue
                )
            else:
                self._mq_logger.warning(
                    "Message queue transport receive failed: name=%s, "
                    "queue=%s, error=%s",
                    self._name, self._consume_queue, ex
                )

            raise TransportError(
                transport_name=self._name,
                operation="receive",
                cause=ex
            )
