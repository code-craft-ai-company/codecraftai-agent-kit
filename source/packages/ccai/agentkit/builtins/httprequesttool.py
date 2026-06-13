"""
    Built-in tool for making HTTP requests.

    Provides the HttpRequestTool class which makes HTTP requests using
    urllib and returns the response status code, headers, and body.
"""

import os
import urllib.request
import urllib.error

from ccai.agentkit.tool import Tool
from ccai.agentkit.toolerrors import ToolExecutionError


class HttpRequestTool(Tool):
    """
        Makes an HTTP request to the specified URL.

        Accepts required url and method parameters, and optional headers,
        body, and timeout_seconds parameters. Returns the response status
        code, headers, and body. Raises ToolExecutionError for timeout
        and connection errors.
    """

    TOOL_NAME = "http_request"
    TOOL_DESCRIPTION = "Makes an HTTP request to the specified URL."
    TOOL_VERSION = "1.0.0"

    INPUT_SCHEMA = {
        "parameters": [
            {
                "name": "url",
                "type": "string",
                "required": True,
                "description": "Request URL.",
            },
            {
                "name": "method",
                "type": "string",
                "required": True,
                "description": "HTTP method (GET, POST, PUT, DELETE, PATCH).",
            },
            {
                "name": "headers",
                "type": "dictionary",
                "required": False,
                "description": "Request headers.",
            },
            {
                "name": "body",
                "type": "string",
                "required": False,
                "description": "Request body.",
            },
            {
                "name": "timeout_seconds",
                "type": "float",
                "required": False,
                "default": 30.0,
                "description": "Request timeout in seconds.",
            },
        ]
    }

    OUTPUT_SCHEMA = {
        "parameters": [
            {
                "name": "status_code",
                "type": "integer",
                "required": True,
                "description": "HTTP response status code.",
            },
            {
                "name": "headers",
                "type": "dictionary",
                "required": True,
                "description": "Response headers.",
            },
            {
                "name": "body",
                "type": "string",
                "required": True,
                "description": "Response body.",
            },
        ]
    }

    def execute(self, inputs: dict, credentials: dict = None) -> dict:
        """
            Makes an HTTP request using the provided inputs.

            :param inputs: Dictionary containing 'url', 'method', and optional
                'headers', 'body', 'timeout_seconds'.
            :param credentials: Optional dictionary of resolved credentials
                for authentication headers.

            :returns: A dictionary with 'status_code', 'headers', and 'body' keys.

            :raises: ToolExecutionError
        """
        url = inputs["url"]
        method = inputs["method"]
        request_headers = inputs.get("headers", None)
        body = inputs.get("body", None)
        timeout_seconds = inputs.get("timeout_seconds", 30.0)

        if request_headers is None:
            request_headers = {}

        if credentials is not None:
            for cred_key, cred_value in credentials.items():
                request_headers[cred_key] = cred_value

        body_bytes = None
        if body is not None:
            body_bytes = body.encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=body_bytes,
            headers=request_headers,
            method=method,
        )

        try:
            response = urllib.request.urlopen(
                url=request,
                timeout=timeout_seconds,
            )

            status_code = response.status
            response_headers = dict(response.getheaders())
            response_body = response.read().decode("utf-8")

        except urllib.error.HTTPError as http_err:
            # HTTPError is a subclass of URLError and MUST be caught first; a
            # 4xx/5xx is a real HTTP response whose status/headers/body we return
            # rather than reclassifying it as a connection error below.
            status_code = http_err.code
            response_headers = dict(http_err.headers.items())
            response_body = http_err.read().decode("utf-8")

        except urllib.error.URLError as url_err:
            if isinstance(url_err.reason, TimeoutError) or "timed out" in str(url_err):
                err_msg_lines = [
                    "HTTP request timed out.",
                    "URL: {}".format(url),
                    "METHOD: {}".format(method),
                    "TIMEOUT: {} seconds".format(timeout_seconds),
                ]
                err_msg = os.linesep.join(err_msg_lines)
                raise ToolExecutionError(tool_name=self.TOOL_NAME, cause=TimeoutError(err_msg)) from url_err

            err_msg_lines = [
                "HTTP request connection error.",
                "URL: {}".format(url),
                "DETAIL: {}".format(str(url_err)),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ToolExecutionError(tool_name=self.TOOL_NAME, cause=ConnectionError(err_msg)) from url_err

        rtnval = {
            "status_code": status_code,
            "headers": response_headers,
            "body": response_body,
        }

        return rtnval
