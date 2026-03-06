"""
    Unit tests for the automojo.agentkit.builtins.httprequesttool module.

    Contains unit tests for HttpRequestTool verifying successful HTTP
    requests with mocked urllib, timeout handling, and connection error
    handling. Uses automojo.testbase.mocking for all mocking.

    Feature: tool-capability-system
"""

import urllib.request
import urllib.error

from automojo.agentkit.builtins.httprequesttool import HttpRequestTool
from automojo.agentkit.toolerrors import ToolExecutionError
from automojo.testbase.mocking import Mock
from automojo.testbase.mocking import create_module_patch


# ---------------------------------------------------------------------------
# Unit tests for HttpRequestTool
# Feature: tool-capability-system, Task 10.7
# **Validates: Requirements 10.1, 10.2, 10.3, 10.4**
# ---------------------------------------------------------------------------


def test_httprequesttool_successful_get_request():
    """
        HttpRequestTool returns status_code, headers, and body for a
        successful HTTP GET request when urlopen is mocked.

        **Validates: Requirements 10.2**
    """
    mock_response = Mock()
    mock_response.configure(recursive=True)
    mock_response_ctx = mock_response.mock_context()
    mock_response_ctx.set_attribute("status", 200)
    mock_response_ctx.mock_method(
        "getheaders",
        return_value=[("Content-Type", "text/plain")],
    )
    mock_response_ctx.mock_method("read", return_value=b"response body")

    patch = create_module_patch(urllib.request, "urlopen", recursive=True)
    mock_urlopen = patch.activate()
    mock_urlopen.configure(return_value=mock_response)

    try:
        tool = HttpRequestTool()

        inputs = {
            "url": "https://example.com/api",
            "method": "GET",
            "timeout_seconds": 10.0,
        }

        result = tool.execute(inputs=inputs)

        assert result["status_code"] == 200, (
            "status_code mismatch: {!r}".format(result["status_code"])
        )

        assert result["body"] == "response body", (
            "body mismatch: {!r}".format(result["body"])
        )

        headers_result = result["headers"]
        assert "Content-Type" in headers_result, (
            "Expected Content-Type in response headers"
        )
    finally:
        patch.deactivate()

    return


def test_httprequesttool_timeout_raises_tool_execution_error():
    """
        HttpRequestTool raises ToolExecutionError when the HTTP request
        times out (URLError wrapping a TimeoutError).

        **Validates: Requirements 10.3**
    """
    timeout_cause = TimeoutError("timed out")
    url_error = urllib.error.URLError(timeout_cause)

    def raise_url_error(*args, **kwargs):
        """
            Side effect callable that raises a URLError wrapping a
            TimeoutError to simulate a request timeout.
        """
        raise url_error

    patch = create_module_patch(urllib.request, "urlopen", recursive=True)
    mock_urlopen = patch.activate()
    mock_urlopen.configure(side_effect=raise_url_error)

    try:
        tool = HttpRequestTool()

        inputs = {
            "url": "https://example.com/slow",
            "method": "GET",
            "timeout_seconds": 5.0,
        }

        raised = False
        caught_error = None

        try:
            tool.execute(inputs=inputs)
        except ToolExecutionError as exec_err:
            raised = True
            caught_error = exec_err

        assert raised is True, (
            "Expected ToolExecutionError for timeout"
        )

        assert caught_error.tool_name == "http_request", (
            "tool_name mismatch: {!r}".format(caught_error.tool_name)
        )

        cause_is_timeout = isinstance(caught_error.cause, TimeoutError)
        assert cause_is_timeout is True, (
            "Expected cause to be TimeoutError, got: {!r}".format(
                type(caught_error.cause)
            )
        )
    finally:
        patch.deactivate()

    return


def test_httprequesttool_connection_error_raises_tool_execution_error():
    """
        HttpRequestTool raises ToolExecutionError when the HTTP request
        fails due to a connection error (URLError without TimeoutError).

        **Validates: Requirements 10.4**
    """
    connection_cause = OSError("Connection refused")
    url_error = urllib.error.URLError(connection_cause)

    def raise_connection_error(*args, **kwargs):
        """
            Side effect callable that raises a URLError wrapping an
            OSError to simulate a connection failure.
        """
        raise url_error

    patch = create_module_patch(urllib.request, "urlopen", recursive=True)
    mock_urlopen = patch.activate()
    mock_urlopen.configure(side_effect=raise_connection_error)

    try:
        tool = HttpRequestTool()

        inputs = {
            "url": "https://unreachable.example.com",
            "method": "POST",
            "body": "test payload",
        }

        raised = False
        caught_error = None

        try:
            tool.execute(inputs=inputs)
        except ToolExecutionError as exec_err:
            raised = True
            caught_error = exec_err

        assert raised is True, (
            "Expected ToolExecutionError for connection error"
        )

        assert caught_error.tool_name == "http_request", (
            "tool_name mismatch: {!r}".format(caught_error.tool_name)
        )

        cause_is_connection = isinstance(caught_error.cause, ConnectionError)
        assert cause_is_connection is True, (
            "Expected cause to be ConnectionError, got: {!r}".format(
                type(caught_error.cause)
            )
        )
    finally:
        patch.deactivate()

    return
