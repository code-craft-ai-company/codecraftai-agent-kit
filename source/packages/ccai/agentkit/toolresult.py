"""
    Defines the ToolResult class for immutable tool execution results.

    ToolResult encapsulates the outcome of a single tool execution,
    including the tool name, execution status, output value, execution
    duration, and any error information.
"""


class ToolResult:
    """
        Immutable result of a single tool execution.

        Provides read-only access to the tool name, execution status,
        output dictionary, execution duration in seconds, and any
        error that occurred during execution.

        :param tool_name: The name of the executed tool.
        :param status: The execution status, either STATUS_SUCCESS or STATUS_FAILURE.
        :param output: An optional dictionary containing the tool output on success.
        :param duration: The execution duration in seconds as a float.
        :param error: An optional exception that occurred during execution.
    """

    STATUS_SUCCESS = "success"
    STATUS_FAILURE = "failure"

    def __init__(self, tool_name: str, status: str, output: dict = None,
                 duration: float = 0.0, error: Exception = None) -> None:
        self._tool_name = tool_name
        self._status = status
        self._output = output
        self._duration = duration
        self._error = error
        return

    @property
    def tool_name(self) -> str:
        """
            The name of the executed tool.

            :returns: The tool name string.
        """
        rtnval = self._tool_name
        return rtnval

    @property
    def status(self) -> str:
        """
            The execution status of the tool.

            :returns: The status string, either STATUS_SUCCESS or STATUS_FAILURE.
        """
        rtnval = self._status
        return rtnval

    @property
    def output(self) -> dict:
        """
            The output dictionary from the tool execution.

            :returns: A dictionary containing the tool output, or None if no output.
        """
        rtnval = self._output
        return rtnval

    @property
    def duration(self) -> float:
        """
            The execution duration in seconds.

            :returns: The duration as a float.
        """
        rtnval = self._duration
        return rtnval

    @property
    def error(self) -> Exception:
        """
            The exception that occurred during execution, if any.

            :returns: An Exception instance, or None if execution succeeded.
        """
        rtnval = self._error
        return rtnval

    @property
    def is_success(self) -> bool:
        """
            Whether the tool execution completed successfully.

            :returns: True when the status equals STATUS_SUCCESS, False otherwise.
        """
        rtnval = self._status == self.STATUS_SUCCESS
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the result fields.

            The error field is included as its string representation,
            or None if no error occurred.

            :returns: A dictionary containing all result fields.
        """
        if self._error is not None:
            error_value = str(self._error)
        else:
            error_value = None

        rtnval = {
            "tool_name": self._tool_name,
            "status": self._status,
            "output": self._output,
            "duration": self._duration,
            "error": error_value,
        }
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            tool name, and execution status.

            :returns: A repr string for debugging.
        """
        rtnval = "ToolResult(tool_name='{}', status='{}')".format(
            self._tool_name, self._status
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the tool name,
            status, and duration.

            :returns: A human-readable string.
        """
        rtnval = "ToolResult: {} - {} (duration: {:.3f}s)".format(
            self._tool_name, self._status, self._duration
        )
        return rtnval
