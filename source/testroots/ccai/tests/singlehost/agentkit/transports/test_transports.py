"""
    Unit tests for the built-in transport implementations in the
    ccai.agentkit.transports package.

    Tests HttpTransport, WebSocketTransport, GrpcTransport, and
    MessageQueueTransport including connect, disconnect, send,
    receive, and error cases.

    Uses testbase mocking for HTTP/WebSocket/gRPC/queue clients.

    .. module:: ccai.tests.singlehost.agentkit.transports.test_transports
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for built-in transport implementations.

    Requirements: 16.1-16.8, 17.1-17.8, 18.1-18.8, 19.1-19.9
"""

import json
import urllib.error

from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.message import Message
from ccai.agentkit.messagepattern import MessagePattern
from ccai.agentkit.messagingerrors import TransportError
from ccai.agentkit.transportconfiguration import TransportConfiguration

from ccai.agentkit.transports.httptransport import HttpTransport
from ccai.agentkit.transports.websockettransport import WebSocketTransport
from ccai.agentkit.transports.grpctransport import GrpcTransport
from ccai.agentkit.transports.messagequeuetransport import MessageQueueTransport

from ccai.testbase.mocking import Mock
from ccai.testbase.mocking import create_module_patch


# =========================================================================
# Test helpers
# =========================================================================

def _create_http_configuration(tls=False, path=None, headers=None,
                               timeout=30.0, credential_references=None):
    """
        Creates a TransportConfiguration for HTTP transport tests.
    """
    options = {}
    if tls:
        options["tls"] = True

    cfg = TransportConfiguration(
        protocol_type="http",
        host="localhost",
        port=8080,
        path=path,
        headers=headers if headers is not None else {},
        timeout=timeout,
        options=options,
        credential_references=credential_references,
    )
    return cfg


def _create_ws_configuration(tls=False, path=None):
    """
        Creates a TransportConfiguration for WebSocket transport tests.
    """
    options = {}
    if tls:
        options["tls"] = True

    cfg = TransportConfiguration(
        protocol_type="websocket",
        host="localhost",
        port=9090,
        path=path,
        options=options,
    )
    return cfg


def _create_grpc_configuration(tls=False, credential_references=None):
    """
        Creates a TransportConfiguration for gRPC transport tests.
    """
    options = {}
    if tls:
        options["tls"] = True

    cfg = TransportConfiguration(
        protocol_type="grpc",
        host="localhost",
        port=50051,
        options=options,
        credential_references=credential_references,
    )
    return cfg


def _create_mq_configuration(broker_client=None, publish_queue=None,
                              consume_queue=None, credential_references=None):
    """
        Creates a TransportConfiguration for MessageQueue transport tests.
    """
    options = {}
    if broker_client is not None:
        options["broker_client"] = broker_client
    if publish_queue is not None:
        options["publish_queue"] = publish_queue
    if consume_queue is not None:
        options["consume_queue"] = consume_queue

    cfg = TransportConfiguration(
        protocol_type="message_queue",
        host="localhost",
        port=5672,
        options=options,
        credential_references=credential_references,
    )
    return cfg


def _create_test_message(pattern=MessagePattern.FIRE_AND_FORGET):
    """
        Creates a test Message for transport send/receive tests.
    """
    sender = AgentAddress(
        agent_identifier="sender-agent",
        transport_name="test-transport",
    )
    recipient = AgentAddress(
        agent_identifier="recipient-agent",
        transport_name="test-transport",
    )
    message = Message(
        sender=sender,
        recipient=recipient,
        payload={"action": "test"},
        pattern=pattern,
    )
    return message


def _create_mock_broker_client():
    """
        Creates a mock broker client for MessageQueueTransport tests.
    """
    mock_client = Mock()
    mock_client.configure(recursive=True)
    ctx = mock_client.mock_context()
    ctx.mock_method("connect", return_value=None)
    ctx.mock_method("disconnect", return_value=None)
    ctx.mock_method("publish", return_value=None)
    ctx.mock_method("consume", return_value=None)
    return mock_client


# =========================================================================
# HttpTransport - Construction and Properties (Requirements 16.1, 16.2)
# =========================================================================

def test_http_transport_construction():
    """
        Verify HttpTransport can be constructed with valid parameters.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)

    assert transport.name == "http-test", \
        "name should be 'http-test'"
    assert transport.protocol_type == "http", \
        "protocol_type should be 'http'"
    assert transport.is_connected() is False, \
        "Should not be connected initially"
    return


def test_http_transport_with_tags():
    """
        Verify HttpTransport accepts tags at construction.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(
        name="http-test",
        configuration=cfg,
        tags={"env": "test"},
    )

    assert transport.tags == {"env": "test"}, \
        "tags should match provided dictionary"
    return


def test_http_transport_with_credential_names():
    """
        Verify HttpTransport accepts credential_names at construction.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(
        name="http-test",
        configuration=cfg,
        credential_names=["api-key"],
    )

    assert transport.credential_names == ["api-key"], \
        "credential_names should match provided list"
    return


# =========================================================================
# HttpTransport - Connect and Disconnect (Requirements 16.3, 16.4)
# =========================================================================

def test_http_transport_connect():
    """
        Verify HttpTransport connect sets connected status.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)

    transport.connect()

    assert transport.is_connected() is True, \
        "Should be connected after connect"
    return


def test_http_transport_connect_builds_base_url():
    """
        Verify HttpTransport connect builds the correct base URL.
    """
    cfg = _create_http_configuration(path="/api/messages")
    transport = HttpTransport(name="http-test", configuration=cfg)

    transport.connect()

    assert transport._base_url == "http://localhost:8080/api/messages", \
        "Base URL should include host, port, and path"
    return


def test_http_transport_connect_tls_url():
    """
        Verify HttpTransport connect builds https URL when TLS is enabled.
    """
    cfg = _create_http_configuration(tls=True)
    transport = HttpTransport(name="http-test", configuration=cfg)

    transport.connect()

    assert transport._base_url.startswith("https://"), \
        "Base URL should use https scheme when TLS is enabled"
    return


def test_http_transport_connect_with_auth_credential():
    """
        Verify HttpTransport connect resolves authorization credential.
    """
    cfg = _create_http_configuration(
        credential_references={"authorization": "Bearer test-token"},
    )
    transport = HttpTransport(name="http-test", configuration=cfg)

    transport.connect()

    assert transport._default_headers.get("Authorization") == "Bearer test-token", \
        "Authorization header should be set from credential reference"
    return


def test_http_transport_connect_sets_content_type():
    """
        Verify HttpTransport connect sets Content-Type header.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)

    transport.connect()

    assert transport._default_headers.get("Content-Type") == "application/json", \
        "Content-Type header should be 'application/json'"
    return


def test_http_transport_disconnect():
    """
        Verify HttpTransport disconnect clears connected status.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)

    transport.connect()
    transport.disconnect()

    assert transport.is_connected() is False, \
        "Should not be connected after disconnect"
    assert transport._base_url is None, \
        "Base URL should be cleared after disconnect"
    assert transport._default_headers == {}, \
        "Default headers should be cleared after disconnect"
    return


# =========================================================================
# HttpTransport - Send (Requirements 16.5, 16.6, 13.1-13.4)
# =========================================================================

def test_http_transport_send_not_connected_raises_transport_error():
    """
        Verify HttpTransport send raises TransportError when not connected.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)
    message = _create_test_message()

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.transport_name == "http-test", \
            "TransportError should include transport name"
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised when not connected"
    return



def test_http_transport_send_success():
    """
        Verify HttpTransport send returns a delivered MessageEnvelope
        when urlopen succeeds.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    # Patch urllib.request.urlopen to simulate a successful HTTP POST
    import urllib.request as urllib_request_module
    patch = create_module_patch(urllib_request_module, "urlopen", recursive=True)
    mock_urlopen = patch.activate()
    mock_urlopen.configure(return_value=Mock())

    try:
        envelope = transport.send(message)

        assert envelope is not None, \
            "send should return a MessageEnvelope"
        assert envelope.delivery_status == "delivered", \
            "delivery_status should be 'delivered'"
        assert envelope.transport_name == "http-test", \
            "transport_name should be 'http-test'"
        assert envelope.message is message, \
            "envelope message should be the sent message"
        assert envelope.attempt_count == 1, \
            "attempt_count should be 1"
    finally:
        patch.deactivate()

    return


def test_http_transport_send_fire_and_forget():
    """
        Verify HttpTransport send with FIRE_AND_FORGET pattern returns
        delivered envelope.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)
    transport.connect()
    message = _create_test_message(pattern=MessagePattern.FIRE_AND_FORGET)

    import urllib.request as urllib_request_module
    patch = create_module_patch(urllib_request_module, "urlopen", recursive=True)
    mock_urlopen = patch.activate()
    mock_urlopen.configure(return_value=Mock())

    try:
        envelope = transport.send(message)

        assert envelope.delivery_status == "delivered", \
            "FIRE_AND_FORGET should return 'delivered' status"
    finally:
        patch.deactivate()

    return


def test_http_transport_send_5xx_raises_transport_error():
    """
        Verify HttpTransport send raises TransportError on HTTP 5xx response.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    import urllib.request as urllib_request_module
    patch = create_module_patch(urllib_request_module, "urlopen", recursive=True)
    mock_urlopen = patch.activate()

    http_error = urllib.error.HTTPError(
        url="http://localhost:8080",
        code=500,
        msg="Internal Server Error",
        hdrs=None,
        fp=None,
    )
    def _raise_http_error():
        raise http_error
    mock_urlopen.configure(side_effect=_raise_http_error)

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.transport_name == "http-test", \
            "TransportError should include transport name"
        assert err.operation == "send", \
            "TransportError should include operation 'send'"
    finally:
        patch.deactivate()

    assert raised is True, \
        "TransportError should be raised for 5xx response"
    return


def test_http_transport_send_connection_error_raises_transport_error():
    """
        Verify HttpTransport send raises TransportError on connection error.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    import urllib.request as urllib_request_module
    patch = create_module_patch(urllib_request_module, "urlopen", recursive=True)
    mock_urlopen = patch.activate()

    url_error = urllib.error.URLError(reason="Connection refused")
    def _raise_url_error():
        raise url_error
    mock_urlopen.configure(side_effect=_raise_url_error)

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.transport_name == "http-test", \
            "TransportError should include transport name"
        assert err.operation == "send", \
            "TransportError should include operation 'send'"
    finally:
        patch.deactivate()

    assert raised is True, \
        "TransportError should be raised for connection error"
    return


def test_http_transport_send_timeout_raises_transport_error():
    """
        Verify HttpTransport send raises TransportError on timeout.
    """
    cfg = _create_http_configuration(timeout=5.0)
    transport = HttpTransport(name="http-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    import urllib.request as urllib_request_module
    patch = create_module_patch(urllib_request_module, "urlopen", recursive=True)
    mock_urlopen = patch.activate()

    def _raise_timeout():
        raise TimeoutError("Request timed out")
    mock_urlopen.configure(side_effect=_raise_timeout)

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.transport_name == "http-test", \
            "TransportError should include transport name"
        assert err.operation == "send", \
            "TransportError should include operation 'send'"
    finally:
        patch.deactivate()

    assert raised is True, \
        "TransportError should be raised for timeout"
    return


def test_http_transport_send_4xx_raises_transport_error():
    """
        Verify HttpTransport send raises TransportError on HTTP 4xx response.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    import urllib.request as urllib_request_module
    patch = create_module_patch(urllib_request_module, "urlopen", recursive=True)
    mock_urlopen = patch.activate()

    http_error = urllib.error.HTTPError(
        url="http://localhost:8080",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=None,
    )
    def _raise_http_error():
        raise http_error
    mock_urlopen.configure(side_effect=_raise_http_error)

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.operation == "send", \
            "TransportError should include operation 'send'"
    finally:
        patch.deactivate()

    assert raised is True, \
        "TransportError should be raised for 4xx response"
    return


# =========================================================================
# HttpTransport - Receive (Requirement 16.7)
# =========================================================================

def test_http_transport_receive_raises_transport_error():
    """
        Verify HttpTransport receive always raises TransportError
        because HTTP does not support passive receive.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.transport_name == "http-test", \
            "TransportError should include transport name"
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should always be raised for HTTP receive"
    return


# =========================================================================
# HttpTransport - Repr and Str (Requirement 16.8)
# =========================================================================

def test_http_transport_repr():
    """
        Verify HttpTransport __repr__ includes class name and transport name.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)

    repr_str = repr(transport)

    assert "HttpTransport" in repr_str, \
        "__repr__ should include class name"
    assert "http-test" in repr_str, \
        "__repr__ should include transport name"
    return


def test_http_transport_str():
    """
        Verify HttpTransport __str__ includes transport name and status.
    """
    cfg = _create_http_configuration()
    transport = HttpTransport(name="http-test", configuration=cfg)

    str_val = str(transport)

    assert "http-test" in str_val, \
        "__str__ should include transport name"
    assert "http" in str_val, \
        "__str__ should include protocol type"
    return



# =========================================================================
# WebSocketTransport - Construction and Properties (Requirements 17.1, 17.2)
# =========================================================================

def test_ws_transport_construction():
    """
        Verify WebSocketTransport can be constructed with valid parameters.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    assert transport.name == "ws-test", \
        "name should be 'ws-test'"
    assert transport.protocol_type == "websocket", \
        "protocol_type should be 'websocket'"
    assert transport.is_connected() is False, \
        "Should not be connected initially"
    assert transport.connection_state == "disconnected", \
        "connection_state should be 'disconnected' initially"
    return


# =========================================================================
# WebSocketTransport - Connect and Disconnect (Requirements 17.3, 17.4)
# =========================================================================

def test_ws_transport_connect_success():
    """
        Verify WebSocketTransport connect sets connected status and
        connection_state to 'connected'.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    # Patch the websockets.sync.client module import
    import sys

    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)

    mock_ws_sync_client = Mock()
    mock_ws_sync_client.configure(recursive=True)
    mock_ws_sync_client.mock_context().mock_method("connect", return_value=mock_ws_client)

    # Insert mock module into sys.modules
    mock_websockets = Mock()
    mock_websockets.configure(recursive=True)

    mock_sync = Mock()
    mock_sync.configure(recursive=True)

    had_websockets = "websockets" in sys.modules
    had_sync = "websockets.sync" in sys.modules
    had_client = "websockets.sync.client" in sys.modules

    old_websockets = sys.modules.get("websockets")
    old_sync = sys.modules.get("websockets.sync")
    old_client = sys.modules.get("websockets.sync.client")

    sys.modules["websockets"] = mock_websockets
    sys.modules["websockets.sync"] = mock_sync
    sys.modules["websockets.sync.client"] = mock_ws_sync_client

    try:
        transport.connect()

        assert transport.is_connected() is True, \
            "Should be connected after connect"
        assert transport.connection_state == "connected", \
            "connection_state should be 'connected'"
    finally:
        if had_websockets:
            sys.modules["websockets"] = old_websockets
        else:
            sys.modules.pop("websockets", None)
        if had_sync:
            sys.modules["websockets.sync"] = old_sync
        else:
            sys.modules.pop("websockets.sync", None)
        if had_client:
            sys.modules["websockets.sync.client"] = old_client
        else:
            sys.modules.pop("websockets.sync.client", None)

    return


def test_ws_transport_connect_builds_ws_url():
    """
        Verify WebSocketTransport connect builds the correct ws:// URL.
    """
    cfg = _create_ws_configuration(path="/ws")
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    url = transport._build_ws_url()

    assert url == "ws://localhost:9090/ws", \
        "WebSocket URL should include host, port, and path"
    return


def test_ws_transport_connect_builds_wss_url():
    """
        Verify WebSocketTransport connect builds wss:// URL when TLS enabled.
    """
    cfg = _create_ws_configuration(tls=True)
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    url = transport._build_ws_url()

    assert url.startswith("wss://"), \
        "WebSocket URL should use wss scheme when TLS is enabled"
    return


def test_ws_transport_connect_import_error_raises_transport_error():
    """
        Verify WebSocketTransport connect raises TransportError when
        websockets package is not installed.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    import sys

    # Ensure websockets is not importable
    had_websockets = "websockets" in sys.modules
    had_sync = "websockets.sync" in sys.modules
    had_client = "websockets.sync.client" in sys.modules

    old_websockets = sys.modules.get("websockets")
    old_sync = sys.modules.get("websockets.sync")
    old_client = sys.modules.get("websockets.sync.client")

    # Remove any cached websockets modules
    sys.modules.pop("websockets", None)
    sys.modules.pop("websockets.sync", None)
    sys.modules.pop("websockets.sync.client", None)

    # Create a mock that raises ImportError when connect is called
    # We need to make the import itself fail
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "websockets.sync.client" or name == "websockets":
            raise ImportError("No module named 'websockets'")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = mock_import

    raised = False
    try:
        transport.connect()
    except TransportError as err:
        raised = True
        assert err.transport_name == "ws-test", \
            "TransportError should include transport name"
        assert err.operation == "connect", \
            "TransportError should include operation 'connect'"
    finally:
        builtins.__import__ = original_import
        if had_websockets:
            sys.modules["websockets"] = old_websockets
        if had_sync:
            sys.modules["websockets.sync"] = old_sync
        if had_client:
            sys.modules["websockets.sync.client"] = old_client

    assert raised is True, \
        "TransportError should be raised when websockets is not installed"
    assert transport.connection_state == "disconnected", \
        "connection_state should be 'disconnected' after failed connect"
    return


def test_ws_transport_disconnect():
    """
        Verify WebSocketTransport disconnect clears connected status
        and sets connection_state to 'disconnected'.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    # Manually set connected state to simulate a connected transport
    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)
    mock_ws_client.mock_context().mock_method("close", return_value=None)

    transport._ws_client = mock_ws_client
    transport._connected = True
    transport._connection_state = "connected"

    transport.disconnect()

    assert transport.is_connected() is False, \
        "Should not be connected after disconnect"
    assert transport.connection_state == "disconnected", \
        "connection_state should be 'disconnected'"
    return


def test_ws_transport_disconnect_error_raises_transport_error():
    """
        Verify WebSocketTransport disconnect raises TransportError
        when close fails.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)
    def _raise_close_error():
        raise RuntimeError("Close failed")
    mock_ws_client.mock_context().mock_method(
        "close", side_effect=_raise_close_error
    )

    transport._ws_client = mock_ws_client
    transport._connected = True
    transport._connection_state = "connected"

    raised = False
    try:
        transport.disconnect()
    except TransportError as err:
        raised = True
        assert err.operation == "disconnect", \
            "TransportError should include operation 'disconnect'"

    assert raised is True, \
        "TransportError should be raised when close fails"
    assert transport.connection_state == "disconnected", \
        "connection_state should be 'disconnected' after failed disconnect"
    return


# =========================================================================
# WebSocketTransport - Send (Requirements 17.5, 17.6)
# =========================================================================

def test_ws_transport_send_not_connected_raises_transport_error():
    """
        Verify WebSocketTransport send raises TransportError when
        not connected.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)
    message = _create_test_message()

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.transport_name == "ws-test", \
            "TransportError should include transport name"
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised when not connected"
    return


def test_ws_transport_send_success():
    """
        Verify WebSocketTransport send returns a delivered MessageEnvelope.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)
    message = _create_test_message()

    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)
    mock_ws_client.mock_context().mock_method("send", return_value=None)

    transport._ws_client = mock_ws_client
    transport._connected = True
    transport._connection_state = "connected"

    envelope = transport.send(message)

    assert envelope is not None, \
        "send should return a MessageEnvelope"
    assert envelope.delivery_status == "delivered", \
        "delivery_status should be 'delivered'"
    assert envelope.transport_name == "ws-test", \
        "transport_name should be 'ws-test'"
    assert envelope.message is message, \
        "envelope message should be the sent message"
    return


def test_ws_transport_send_connection_loss_raises_transport_error():
    """
        Verify WebSocketTransport send raises TransportError on
        connection loss and updates connection_state.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)
    message = _create_test_message()

    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)
    def _raise_connection_lost():
        raise ConnectionError("Connection lost")
    mock_ws_client.mock_context().mock_method(
        "send", side_effect=_raise_connection_lost
    )

    transport._ws_client = mock_ws_client
    transport._connected = True
    transport._connection_state = "connected"

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised on connection loss"
    assert transport.connection_state == "disconnected", \
        "connection_state should be 'disconnected' after connection loss"
    assert transport.is_connected() is False, \
        "Should not be connected after connection loss"
    return


# =========================================================================
# WebSocketTransport - Receive (Requirements 17.7)
# =========================================================================

def test_ws_transport_receive_not_connected_raises_transport_error():
    """
        Verify WebSocketTransport receive raises TransportError when
        not connected.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should be raised when not connected"
    return


def test_ws_transport_receive_success():
    """
        Verify WebSocketTransport receive deserializes a JSON text
        frame into a Message.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    test_message = _create_test_message()
    message_json = json.dumps(test_message.as_dict())

    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)
    mock_ws_client.mock_context().mock_method("recv", return_value=message_json)

    transport._ws_client = mock_ws_client
    transport._connected = True
    transport._connection_state = "connected"

    received = transport.receive()

    assert received is not None, \
        "receive should return a Message"
    assert received.identifier == test_message.identifier, \
        "received message identifier should match"
    assert received.sender.agent_identifier == "sender-agent", \
        "received message sender should match"
    return


def test_ws_transport_receive_invalid_json_raises_transport_error():
    """
        Verify WebSocketTransport receive raises TransportError when
        received data is not valid JSON.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)
    mock_ws_client.mock_context().mock_method("recv", return_value="not-valid-json{{{")

    transport._ws_client = mock_ws_client
    transport._connected = True
    transport._connection_state = "connected"

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should be raised for invalid JSON"
    return


def test_ws_transport_receive_connection_loss_raises_transport_error():
    """
        Verify WebSocketTransport receive raises TransportError on
        connection loss and updates connection_state.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    mock_ws_client = Mock()
    mock_ws_client.configure(recursive=True)
    def _raise_connection_lost():
        raise ConnectionError("Connection lost")
    mock_ws_client.mock_context().mock_method(
        "recv", side_effect=_raise_connection_lost
    )

    transport._ws_client = mock_ws_client
    transport._connected = True
    transport._connection_state = "connected"

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should be raised on connection loss"
    assert transport.connection_state == "disconnected", \
        "connection_state should be 'disconnected' after connection loss"
    return


# =========================================================================
# WebSocketTransport - connection_state property (Requirement 17.8)
# =========================================================================

def test_ws_transport_connection_state_property():
    """
        Verify WebSocketTransport connection_state property returns
        valid states.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    assert transport.connection_state == "disconnected", \
        "Initial connection_state should be 'disconnected'"
    assert transport.connection_state in WebSocketTransport.VALID_CONNECTION_STATES, \
        "connection_state should be a valid state"
    return


def test_ws_transport_repr():
    """
        Verify WebSocketTransport __repr__ includes class name.
    """
    cfg = _create_ws_configuration()
    transport = WebSocketTransport(name="ws-test", configuration=cfg)

    repr_str = repr(transport)

    assert "WebSocketTransport" in repr_str, \
        "__repr__ should include class name"
    assert "ws-test" in repr_str, \
        "__repr__ should include transport name"
    return



# =========================================================================
# GrpcTransport - Construction and Properties (Requirements 18.1, 18.2)
# =========================================================================

def test_grpc_transport_construction():
    """
        Verify GrpcTransport can be constructed with valid parameters.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    assert transport.name == "grpc-test", \
        "name should be 'grpc-test'"
    assert transport.protocol_type == "grpc", \
        "protocol_type should be 'grpc'"
    assert transport.is_connected() is False, \
        "Should not be connected initially"
    return


# =========================================================================
# GrpcTransport - Connect and Disconnect (Requirements 18.3, 18.4)
# =========================================================================

def test_grpc_transport_connect_success():
    """
        Verify GrpcTransport connect sets connected status using a
        mock grpc module.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    import sys

    mock_channel = Mock()
    mock_channel.configure(recursive=True)

    mock_grpc = Mock()
    mock_grpc.configure(recursive=True)
    mock_grpc.mock_context().mock_method("insecure_channel", return_value=mock_channel)

    had_grpc = "grpc" in sys.modules
    old_grpc = sys.modules.get("grpc")
    sys.modules["grpc"] = mock_grpc

    try:
        transport.connect()

        assert transport.is_connected() is True, \
            "Should be connected after connect"
    finally:
        if had_grpc:
            sys.modules["grpc"] = old_grpc
        else:
            sys.modules.pop("grpc", None)

    return


def test_grpc_transport_connect_tls():
    """
        Verify GrpcTransport connect creates a secure channel when
        TLS is enabled.
    """
    cfg = _create_grpc_configuration(tls=True)
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    import sys

    mock_channel = Mock()
    mock_channel.configure(recursive=True)

    mock_credentials = Mock()
    mock_credentials.configure(recursive=True)

    mock_grpc = Mock()
    mock_grpc.configure(recursive=True)
    mock_grpc.mock_context().mock_method("ssl_channel_credentials", return_value=mock_credentials)
    mock_grpc.mock_context().mock_method("secure_channel", return_value=mock_channel)

    had_grpc = "grpc" in sys.modules
    old_grpc = sys.modules.get("grpc")
    sys.modules["grpc"] = mock_grpc

    try:
        transport.connect()

        assert transport.is_connected() is True, \
            "Should be connected after TLS connect"
    finally:
        if had_grpc:
            sys.modules["grpc"] = old_grpc
        else:
            sys.modules.pop("grpc", None)

    return


def test_grpc_transport_connect_import_error_raises_transport_error():
    """
        Verify GrpcTransport connect raises TransportError when grpc
        package is not installed.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    import sys
    import builtins

    had_grpc = "grpc" in sys.modules
    old_grpc = sys.modules.get("grpc")
    sys.modules.pop("grpc", None)

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "grpc":
            raise ImportError("No module named 'grpc'")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = mock_import

    raised = False
    try:
        transport.connect()
    except TransportError as err:
        raised = True
        assert err.transport_name == "grpc-test", \
            "TransportError should include transport name"
        assert err.operation == "connect", \
            "TransportError should include operation 'connect'"
    finally:
        builtins.__import__ = original_import
        if had_grpc:
            sys.modules["grpc"] = old_grpc

    assert raised is True, \
        "TransportError should be raised when grpc is not installed"
    return


def test_grpc_transport_disconnect():
    """
        Verify GrpcTransport disconnect closes the channel and clears
        connected status.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    mock_channel = Mock()
    mock_channel.configure(recursive=True)
    mock_channel.mock_context().mock_method("close", return_value=None)

    transport._channel = mock_channel
    transport._connected = True

    transport.disconnect()

    assert transport.is_connected() is False, \
        "Should not be connected after disconnect"
    return


def test_grpc_transport_disconnect_error_raises_transport_error():
    """
        Verify GrpcTransport disconnect raises TransportError when
        channel close fails.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    mock_channel = Mock()
    mock_channel.configure(recursive=True)
    def _raise_close_error():
        raise RuntimeError("Close failed")
    mock_channel.mock_context().mock_method(
        "close", side_effect=_raise_close_error
    )

    transport._channel = mock_channel
    transport._connected = True

    raised = False
    try:
        transport.disconnect()
    except TransportError as err:
        raised = True
        assert err.operation == "disconnect", \
            "TransportError should include operation 'disconnect'"

    assert raised is True, \
        "TransportError should be raised when channel close fails"
    return


# =========================================================================
# GrpcTransport - Send (Requirements 18.5, 18.6)
# =========================================================================

def test_grpc_transport_send_not_connected_raises_transport_error():
    """
        Verify GrpcTransport send raises TransportError when not connected.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)
    message = _create_test_message()

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.transport_name == "grpc-test", \
            "TransportError should include transport name"
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised when not connected"
    return


def test_grpc_transport_send_success():
    """
        Verify GrpcTransport send returns a delivered MessageEnvelope
        when the unary call succeeds.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)
    message = _create_test_message()

    # Create a mock callable that simulates the unary_unary call chain
    mock_call_result = b'{"status": "ok"}'

    mock_callable = Mock()
    mock_callable.configure(return_value=mock_call_result)

    mock_channel = Mock()
    mock_channel.configure(recursive=True)
    mock_channel.mock_context().mock_method("unary_unary", return_value=mock_callable)

    transport._channel = mock_channel
    transport._connected = True
    mock_grpc = Mock()
    mock_grpc.configure(recursive=False)
    transport._grpc_module = mock_grpc

    envelope = transport.send(message)

    assert envelope is not None, \
        "send should return a MessageEnvelope"
    assert envelope.delivery_status == "delivered", \
        "delivery_status should be 'delivered'"
    assert envelope.transport_name == "grpc-test", \
        "transport_name should be 'grpc-test'"
    return


def test_grpc_transport_send_error_raises_transport_error():
    """
        Verify GrpcTransport send raises TransportError on general
        send failure.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)
    message = _create_test_message()

    mock_callable = Mock()
    def _raise_send_failed():
        raise RuntimeError("Send failed")
    mock_callable.configure(side_effect=_raise_send_failed)

    mock_channel = Mock()
    mock_channel.configure(recursive=True)
    mock_channel.mock_context().mock_method("unary_unary", return_value=mock_callable)

    transport._channel = mock_channel
    transport._connected = True

    # Use a mock grpc module that does NOT have RpcError attribute
    # so the isinstance check is skipped and the general exception
    # handler is used instead.
    mock_grpc = Mock()
    mock_grpc.configure(recursive=False)
    transport._grpc_module = mock_grpc

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised on send failure"
    return


# =========================================================================
# GrpcTransport - Receive (Requirement 18.7)
# =========================================================================

def test_grpc_transport_receive_raises_transport_error():
    """
        Verify GrpcTransport receive always raises TransportError
        because gRPC does not support standalone passive receive.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.transport_name == "grpc-test", \
            "TransportError should include transport name"
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should always be raised for gRPC receive"
    return


# =========================================================================
# GrpcTransport - Repr and Str (Requirement 18.8)
# =========================================================================

def test_grpc_transport_repr():
    """
        Verify GrpcTransport __repr__ includes class name.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    repr_str = repr(transport)

    assert "GrpcTransport" in repr_str, \
        "__repr__ should include class name"
    assert "grpc-test" in repr_str, \
        "__repr__ should include transport name"
    return


def test_grpc_transport_str():
    """
        Verify GrpcTransport __str__ includes transport name.
    """
    cfg = _create_grpc_configuration()
    transport = GrpcTransport(name="grpc-test", configuration=cfg)

    str_val = str(transport)

    assert "grpc-test" in str_val, \
        "__str__ should include transport name"
    return



# =========================================================================
# MessageQueueTransport - Construction (Requirements 19.1, 19.2)
# =========================================================================

def test_mq_transport_construction():
    """
        Verify MessageQueueTransport can be constructed with valid parameters.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(broker_client=mock_client)
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    assert transport.name == "mq-test", \
        "name should be 'mq-test'"
    assert transport.protocol_type == "message_queue", \
        "protocol_type should be 'message_queue'"
    assert transport.is_connected() is False, \
        "Should not be connected initially"
    return


# =========================================================================
# MessageQueueTransport - Connect and Disconnect (Requirements 19.3, 19.4)
# =========================================================================

def test_mq_transport_connect_success():
    """
        Verify MessageQueueTransport connect sets connected status
        using the injected broker client.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(
        broker_client=mock_client,
        publish_queue="outbound",
        consume_queue="inbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    transport.connect()

    assert transport.is_connected() is True, \
        "Should be connected after connect"
    return


def test_mq_transport_connect_no_broker_client_raises_transport_error():
    """
        Verify MessageQueueTransport connect raises TransportError
        when no broker_client is provided in options.
    """
    cfg = _create_mq_configuration()
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    raised = False
    try:
        transport.connect()
    except TransportError as err:
        raised = True
        assert err.transport_name == "mq-test", \
            "TransportError should include transport name"
        assert err.operation == "connect", \
            "TransportError should include operation 'connect'"

    assert raised is True, \
        "TransportError should be raised when no broker_client provided"
    return



def test_mq_transport_connect_broker_error_raises_transport_error():
    """
        Verify MessageQueueTransport connect raises TransportError
        when the broker client connect fails.
    """
    mock_client = Mock()
    mock_client.configure(recursive=True)
    def _raise_broker_unreachable():
        raise ConnectionError("Broker unreachable")
    mock_client.mock_context().mock_method(
        "connect", side_effect=_raise_broker_unreachable
    )

    cfg = _create_mq_configuration(broker_client=mock_client)
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    raised = False
    try:
        transport.connect()
    except TransportError as err:
        raised = True
        assert err.operation == "connect", \
            "TransportError should include operation 'connect'"

    assert raised is True, \
        "TransportError should be raised when broker connect fails"
    return


def test_mq_transport_connect_with_credentials():
    """
        Verify MessageQueueTransport connect passes credentials to
        the broker client.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(
        broker_client=mock_client,
        credential_references={"username": "admin", "password": "secret"},
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    transport.connect()

    assert transport.is_connected() is True, \
        "Should be connected after connect with credentials"
    return


def test_mq_transport_disconnect():
    """
        Verify MessageQueueTransport disconnect clears connected status.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(
        broker_client=mock_client,
        publish_queue="outbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    transport.connect()
    transport.disconnect()

    assert transport.is_connected() is False, \
        "Should not be connected after disconnect"
    return



def test_mq_transport_disconnect_error_raises_transport_error():
    """
        Verify MessageQueueTransport disconnect raises TransportError
        when broker disconnect fails.
    """
    mock_client = Mock()
    mock_client.configure(recursive=True)
    mock_client.mock_context().mock_method("connect", return_value=None)
    def _raise_disconnect_failed():
        raise RuntimeError("Disconnect failed")
    mock_client.mock_context().mock_method(
        "disconnect", side_effect=_raise_disconnect_failed
    )

    cfg = _create_mq_configuration(
        broker_client=mock_client,
        publish_queue="outbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()

    raised = False
    try:
        transport.disconnect()
    except TransportError as err:
        raised = True
        assert err.operation == "disconnect", \
            "TransportError should include operation 'disconnect'"

    assert raised is True, \
        "TransportError should be raised when broker disconnect fails"
    return


# =========================================================================
# MessageQueueTransport - Send (Requirements 19.5, 19.6)
# =========================================================================

def test_mq_transport_send_not_connected_raises_transport_error():
    """
        Verify MessageQueueTransport send raises TransportError when
        not connected.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(broker_client=mock_client)
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    message = _create_test_message()

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.transport_name == "mq-test", \
            "TransportError should include transport name"
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised when not connected"
    return



def test_mq_transport_send_no_publish_queue_raises_transport_error():
    """
        Verify MessageQueueTransport send raises TransportError when
        no publish_queue is configured.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(broker_client=mock_client)
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised when no publish_queue configured"
    return


def test_mq_transport_send_success():
    """
        Verify MessageQueueTransport send returns a delivered
        MessageEnvelope when publish succeeds.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(
        broker_client=mock_client,
        publish_queue="outbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    envelope = transport.send(message)

    assert envelope is not None, \
        "send should return a MessageEnvelope"
    assert envelope.delivery_status == "delivered", \
        "delivery_status should be 'delivered'"
    assert envelope.transport_name == "mq-test", \
        "transport_name should be 'mq-test'"
    assert envelope.message is message, \
        "envelope message should be the sent message"
    return


def test_mq_transport_send_queue_not_found_raises_transport_error():
    """
        Verify MessageQueueTransport send raises TransportError when
        the publish queue is not found.
    """
    mock_client = Mock()
    mock_client.configure(recursive=True)
    mock_client.mock_context().mock_method("connect", return_value=None)
    def _raise_queue_not_found():
        raise RuntimeError("Queue not found: outbound")
    mock_client.mock_context().mock_method(
        "publish", side_effect=_raise_queue_not_found
    )

    cfg = _create_mq_configuration(
        broker_client=mock_client,
        publish_queue="outbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised when queue not found"
    return



def test_mq_transport_send_publish_error_raises_transport_error():
    """
        Verify MessageQueueTransport send raises TransportError on
        general publish failure.
    """
    mock_client = Mock()
    mock_client.configure(recursive=True)
    mock_client.mock_context().mock_method("connect", return_value=None)
    def _raise_publish_failed():
        raise RuntimeError("Publish failed")
    mock_client.mock_context().mock_method(
        "publish", side_effect=_raise_publish_failed
    )

    cfg = _create_mq_configuration(
        broker_client=mock_client,
        publish_queue="outbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()
    message = _create_test_message()

    raised = False
    try:
        transport.send(message)
    except TransportError as err:
        raised = True
        assert err.operation == "send", \
            "TransportError should include operation 'send'"

    assert raised is True, \
        "TransportError should be raised on publish failure"
    return


# =========================================================================
# MessageQueueTransport - Receive (Requirements 19.7, 19.8)
# =========================================================================

def test_mq_transport_receive_not_connected_raises_transport_error():
    """
        Verify MessageQueueTransport receive raises TransportError
        when not connected.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(broker_client=mock_client)
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should be raised when not connected"
    return



def test_mq_transport_receive_no_consume_queue_raises_transport_error():
    """
        Verify MessageQueueTransport receive raises TransportError
        when no consume_queue is configured.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(
        broker_client=mock_client,
        publish_queue="outbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should be raised when no consume_queue configured"
    return


def test_mq_transport_receive_success():
    """
        Verify MessageQueueTransport receive deserializes a consumed
        message from the queue.
    """
    test_message = _create_test_message()
    message_bytes = json.dumps(test_message.as_dict()).encode("utf-8")

    mock_client = Mock()
    mock_client.configure(recursive=True)
    mock_client.mock_context().mock_method("connect", return_value=None)
    mock_client.mock_context().mock_method("consume", return_value=message_bytes)

    cfg = _create_mq_configuration(
        broker_client=mock_client,
        consume_queue="inbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()

    received = transport.receive()

    assert received is not None, \
        "receive should return a Message"
    assert received.identifier == test_message.identifier, \
        "received message identifier should match"
    assert received.sender.agent_identifier == "sender-agent", \
        "received message sender should match"
    return



def test_mq_transport_receive_no_message_available_raises_transport_error():
    """
        Verify MessageQueueTransport receive raises TransportError
        when no message is available on the queue.
    """
    mock_client = Mock()
    mock_client.configure(recursive=True)
    mock_client.mock_context().mock_method("connect", return_value=None)
    mock_client.mock_context().mock_method("consume", return_value=None)

    cfg = _create_mq_configuration(
        broker_client=mock_client,
        consume_queue="inbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should be raised when no message available"
    return


def test_mq_transport_receive_queue_not_found_raises_transport_error():
    """
        Verify MessageQueueTransport receive raises TransportError
        when the consume queue is not found.
    """
    mock_client = Mock()
    mock_client.configure(recursive=True)
    mock_client.mock_context().mock_method("connect", return_value=None)
    def _raise_queue_not_found():
        raise RuntimeError("Queue not found: inbound")
    mock_client.mock_context().mock_method(
        "consume", side_effect=_raise_queue_not_found
    )

    cfg = _create_mq_configuration(
        broker_client=mock_client,
        consume_queue="inbound",
    )
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)
    transport.connect()

    raised = False
    try:
        transport.receive()
    except TransportError as err:
        raised = True
        assert err.operation == "receive", \
            "TransportError should include operation 'receive'"

    assert raised is True, \
        "TransportError should be raised when queue not found"
    return


# =========================================================================
# MessageQueueTransport - Repr and Str (Requirement 19.9)
# =========================================================================

def test_mq_transport_repr():
    """
        Verify MessageQueueTransport __repr__ includes class name.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(broker_client=mock_client)
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    repr_str = repr(transport)

    assert "MessageQueueTransport" in repr_str, \
        "__repr__ should include class name"
    assert "mq-test" in repr_str, \
        "__repr__ should include transport name"
    return


def test_mq_transport_str():
    """
        Verify MessageQueueTransport __str__ includes transport name.
    """
    mock_client = _create_mock_broker_client()
    cfg = _create_mq_configuration(broker_client=mock_client)
    transport = MessageQueueTransport(name="mq-test", configuration=cfg)

    str_val = str(transport)

    assert "mq-test" in str_val, \
        "__str__ should include transport name"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
