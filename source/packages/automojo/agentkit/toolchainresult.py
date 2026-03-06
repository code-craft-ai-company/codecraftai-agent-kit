"""
    Defines the ToolChainResult class for immutable tool chain execution results.

    ToolChainResult encapsulates the outcome of a tool chain execution,
    including the chain name, overall execution status, final output value,
    list of individual ToolResult objects for each step, total execution
    duration, and any error information.
"""


class ToolChainResult:
    """
        Immutable result of a tool chain execution.

        Provides read-only access to the chain name, overall execution status,
        final output dictionary, list of individual ToolResult objects for each
        step, total execution duration in seconds, and any error that occurred
        during execution.

        :param chain_name: The name of the executed tool chain.
        :param status: The overall execution status, either STATUS_SUCCESS or STATUS_FAILURE.
        :param output: An optional dictionary containing the final step output on success.
        :param step_results: An optional list of ToolResult objects for each step.
        :param duration: The total execution duration in seconds as a float.
        :param error: An optional exception from the failed step.
    """

    STATUS_SUCCESS = "success"
    STATUS_FAILURE = "failure"

    def __init__(self, chain_name: str, status: str, output: dict = None,
                 step_results: list = None, duration: float = 0.0,
                 error: Exception = None) -> None:
        self._chain_name = chain_name
        self._status = status
        self._output = output
        self._step_results = list(step_results) if step_results is not None else []
        self._duration = duration
        self._error = error
        return

    @property
    def chain_name(self) -> str:
        """
            The name of the executed tool chain.

            :returns: The chain name string.
        """
        rtnval = self._chain_name
        return rtnval

    @property
    def status(self) -> str:
        """
            The overall execution status of the tool chain.

            :returns: The status string, either STATUS_SUCCESS or STATUS_FAILURE.
        """
        rtnval = self._status
        return rtnval

    @property
    def output(self) -> dict:
        """
            The final step output dictionary from the tool chain execution.

            :returns: A dictionary containing the final output, or None if no output.
        """
        rtnval = self._output
        return rtnval

    @property
    def step_results(self) -> list:
        """
            The list of individual ToolResult objects for each step in the chain.

            :returns: A list of ToolResult objects.
        """
        rtnval = list(self._step_results)
        return rtnval

    @property
    def duration(self) -> float:
        """
            The total execution duration in seconds.

            :returns: The duration as a float.
        """
        rtnval = self._duration
        return rtnval

    @property
    def error(self) -> Exception:
        """
            The exception from the failed step, if any.

            :returns: An Exception instance, or None if execution succeeded.
        """
        rtnval = self._error
        return rtnval

    @property
    def is_success(self) -> bool:
        """
            Whether the tool chain execution completed successfully.

            :returns: True when the status equals STATUS_SUCCESS, False otherwise.
        """
        rtnval = self._status == self.STATUS_SUCCESS
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the chain result fields.

            The step_results field is included as a list of dictionaries
            produced by calling as_dict() on each ToolResult. The error
            field is included as its string representation, or None if
            no error occurred.

            :returns: A dictionary containing all chain result fields.
        """
        step_results_dicts = []
        for step_result in self._step_results:
            step_dict = step_result.as_dict()
            step_results_dicts.append(step_dict)

        if self._error is not None:
            error_value = str(self._error)
        else:
            error_value = None

        rtnval = {
            "chain_name": self._chain_name,
            "status": self._status,
            "output": self._output,
            "step_results": step_results_dicts,
            "duration": self._duration,
            "error": error_value,
        }
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            chain name, and overall execution status.

            :returns: A repr string for debugging.
        """
        rtnval = "ToolChainResult(chain_name='{}', status='{}')".format(
            self._chain_name, self._status
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the chain name,
            status, step count, and total duration.

            :returns: A human-readable string.
        """
        step_count = len(self._step_results)
        rtnval = "ToolChainResult: {} - {} ({} steps, duration: {:.3f}s)".format(
            self._chain_name, self._status, step_count, self._duration
        )
        return rtnval
