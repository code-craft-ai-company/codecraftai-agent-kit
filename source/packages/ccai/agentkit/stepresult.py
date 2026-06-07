"""
    Defines the StepResult class representing an immutable object
    encapsulating the outcome of a single WorkflowStep execution
    in the Workflow & Orchestration feature.

    A StepResult contains the step identifier, step name, execution
    status, output dictionary, execution duration in seconds, and
    optional error information. The class provides JSON serialization
    and deserialization for persistence and transmission.
"""

import json

from typing import Optional

from ccai.agentkit.stepexecutionstatus import StepExecutionStatus


class StepResult:
    """
        Immutable object encapsulating the outcome of a single
        WorkflowStep execution.

        A StepResult captures the step identifier, step name,
        execution status, output dictionary, execution duration
        in seconds, and optional error information. All fields
        are exposed as read-only properties. The is_success
        property returns True when the execution status is
        COMPLETED.

        :param step_id: The unique identifier of the executed step.
        :param step_name: The human-readable name of the executed step.
        :param status: The StepExecutionStatus indicating the outcome.
        :param output: An optional dictionary of output values produced
            by the step. Defaults to an empty dictionary.
        :param duration: The execution duration in seconds as a float.
            Defaults to 0.0.
        :param error: An optional error message string when the step
            failed or encountered an error.
    """

    def __init__(self, step_id: str, step_name: str, status: StepExecutionStatus,
                 output: Optional[dict] = None, duration: float = 0.0,
                 error: Optional[str] = None) -> None:
        self._step_id = step_id
        self._step_name = step_name
        self._status = status
        self._output = dict(output) if output is not None else {}
        self._duration = duration
        self._error = error
        return

    @property
    def step_id(self) -> str:
        """
            The unique identifier of the executed step.

            :returns: The step identifier string.
        """
        return self._step_id

    @property
    def step_name(self) -> str:
        """
            The human-readable name of the executed step.

            :returns: The step name string.
        """
        return self._step_name

    @property
    def status(self) -> StepExecutionStatus:
        """
            The execution status indicating the outcome of the step.

            :returns: The StepExecutionStatus member.
        """
        return self._status

    @property
    def output(self) -> dict:
        """
            The dictionary of output values produced by the step.

            :returns: A dictionary of output values. Empty dictionary
                when the step produced no output.
        """
        return self._output

    @property
    def duration(self) -> float:
        """
            The execution duration in seconds.

            :returns: The duration as a float in seconds.
        """
        return self._duration

    @property
    def error(self) -> Optional[str]:
        """
            The error message string when the step failed or
            encountered an error.

            :returns: The error message string or None when no
                error occurred.
        """
        return self._error

    @property
    def is_success(self) -> bool:
        """
            Indicates whether the step execution completed successfully.

            :returns: True when the execution status is COMPLETED,
                False otherwise.
        """
        rtnval = self._status == StepExecutionStatus.COMPLETED
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the step result fields.

            The status is serialized as its string value.

            :returns: A dictionary containing step_id, step_name, status,
                output, duration, and error.
        """
        rtnval = {
            "step_id": self._step_id,
            "step_name": self._step_name,
            "status": self._status.value,
            "output": self._output,
            "duration": self._duration,
            "error": self._error
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the step result fields.

            :returns: A JSON string containing all step result fields.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "StepResult":
        """
            Deserializes a JSON string into a StepResult instance.

            The status field is deserialized using
            StepExecutionStatus.from_string.

            :param json_str: A JSON string containing step result fields.

            :returns: A StepResult instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)

        status = StepExecutionStatus.from_string(data["status"])

        rtnval = cls(
            step_id=data["step_id"],
            step_name=data["step_name"],
            status=status,
            output=data.get("output"),
            duration=data.get("duration", 0.0),
            error=data.get("error")
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class
            name, step identifier, and execution status.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(step_id={!r}, status={})".format(
            self.__class__.__name__, self._step_id, self._status.value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the step name,
            status, and duration.

            :returns: A human-readable string describing the step result.
        """
        str_val = "StepResult: {} [status: {}, duration: {:.3f}s]".format(
            self._step_name, self._status.value, self._duration
        )
        return str_val
