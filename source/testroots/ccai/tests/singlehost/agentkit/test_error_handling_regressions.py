"""
    Regression tests for error-handling bug fixes in agentkit.

    Covers behaviors the prior test suite did not exercise:
      * TransportHealthCheck must invoke ``is_connected()`` (a method) rather
        than truth-testing the bound method object.
      * HttpRequestTool must surface 4xx/5xx responses (status/headers/body)
        instead of reclassifying them as connection errors.
      * ToolExecutor and RetryExecutor must let ``SemanticError`` bubble rather
        than swallowing it into a failure result / retry loop.

    These use stdlib ``unittest.mock`` so they run under a plain pytest runner.
"""

import io
import urllib.error
import urllib.request

from unittest import mock

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.transporthealthcheck import TransportHealthCheck
from ccai.agentkit.builtins.httprequesttool import HttpRequestTool
from ccai.agentkit.retryexecutor import RetryExecutor
from ccai.agentkit.retrypolicy import RetryPolicy
from ccai.agentkit.toolexecutor import ToolExecutor


def test_transport_health_check_calls_is_connected_and_reports_disconnected() -> None:
    """
        ``is_connected`` is a method; a disconnected transport must report
        "unhealthy" (the old code truth-tested the bound method and was always
        "healthy").
    """
    transport = mock.MagicMock(name="transport")
    transport.is_connected = mock.MagicMock(return_value=False)

    health_check = TransportHealthCheck("transport-check", transport)
    status = health_check.check()

    transport.is_connected.assert_called_once_with()
    assert status.status == "unhealthy"

    return


def test_transport_health_check_reports_healthy_when_connected() -> None:
    """
        A connected transport must report "healthy".
    """
    transport = mock.MagicMock(name="transport")
    transport.is_connected = mock.MagicMock(return_value=True)

    health_check = TransportHealthCheck("transport-check", transport)
    status = health_check.check()

    transport.is_connected.assert_called_once_with()
    assert status.status == "healthy"

    return


def test_httprequesttool_returns_4xx_response_instead_of_raising() -> None:
    """
        A 4xx response (raised by urlopen as ``HTTPError``) must be returned as
        a normal result with its status code, headers and body -- not
        reclassified as a connection error.
    """
    http_error = urllib.error.HTTPError(
        url="https://example.com/missing",
        code=404,
        msg="Not Found",
        hdrs={"Content-Type": "text/plain"},
        fp=io.BytesIO(b"resource not found"),
    )

    with mock.patch.object(urllib.request, "urlopen", side_effect=http_error):
        tool = HttpRequestTool()
        inputs = {
            "url": "https://example.com/missing",
            "method": "GET",
            "timeout_seconds": 10.0,
        }
        result = tool.execute(inputs=inputs)

    assert result["status_code"] == 404
    assert result["body"] == "resource not found"
    assert "Content-Type" in result["headers"]

    return


def test_retryexecutor_lets_semanticerror_bubble() -> None:
    """
        A ``SemanticError`` raised by the operation must propagate immediately,
        not be fed through the retry/swallow logic.
    """
    policy = RetryPolicy(
        max_retries=3, backoff_strategy="fixed", base_delay=0.0, max_delay=0.0
    )
    executor = RetryExecutor(policy)

    def operation() -> None:
        raise SemanticError("operation misuse")

    raised = False
    try:
        executor.execute(operation)
    except SemanticError:
        raised = True

    assert raised

    return


def test_toolexecutor_lets_semanticerror_bubble() -> None:
    """
        A ``SemanticError`` raised by ``tool.execute`` must bubble rather than
        being converted into a failure ToolResult.
    """
    tool = mock.MagicMock(name="tool")
    tool.name = "semantic-tool"
    tool.input_schema = None
    tool.output_schema = None
    tool.credential_names = []
    tool.execute = mock.MagicMock(side_effect=SemanticError("tool misuse"))

    executor = ToolExecutor()

    raised = False
    try:
        executor.execute(tool, {"key": "value"})
    except SemanticError:
        raised = True

    assert raised

    return
