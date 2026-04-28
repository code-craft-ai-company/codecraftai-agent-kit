"""
    Defines the WorkflowResult class representing an immutable object
    encapsulating the outcome of a workflow execution in the Workflow
    & Orchestration feature.

    A WorkflowResult contains the workflow name, overall execution
    status, the list of individual StepResult objects, the final
    output dictionary from terminal steps, total execution duration
    in seconds, and optional error information. The class provides
    JSON serialization and deserialization for persistence and
    transmission.
"""

import json

from typing import List, Optional

from automojo.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from automojo.agentkit.stepresult import StepResult


class WorkflowResult:
    """
        Immutable object encapsulating the outcome of a workflow
        execution.

        A WorkflowResult captures the workflow name, overall
        execution status, the list of StepResult objects for each
        executed step, the final output dictionary from terminal
        steps, total execution duration in seconds, and optional
        error information. All fields are exposed as read-only
        properties. The is_success property returns True when the
        execution status is COMPLETED.

        :param workflow_name: The name of the executed workflow.
        :param status: The WorkflowExecutionStatus indicating the
            overall outcome.
        :param step_results: An optional list of StepResult objects
            for each executed step. Defaults to an empty list.
        :param final_output: An optional dictionary of final output
            values from terminal steps. Defaults to an empty dictionary.
        :param duration: The total execution duration in seconds as
            a float. Defaults to 0.0.
        :param error: An optional error message string when the
            workflow failed or encountered an error.
    """

    def __init__(self, workflow_name: str, status: WorkflowExecutionStatus,
                 step_results: Optional[List[StepResult]] = None,
                 final_output: Optional[dict] = None,
                 duration: float = 0.0,
                 error: Optional[str] = None) -> None:
        self._workflow_name = workflow_name
        self._status = status
        self._step_results = list(step_results) if step_results is not None else []
        self._final_output = dict(final_output) if final_output is not None else {}
        self._duration = duration
        self._error = error
        return

    @property
    def workflow_name(self) -> str:
        """
            The name of the executed workflow.

            :returns: The workflow name string.
        """
        return self._workflow_name

    @property
    def status(self) -> WorkflowExecutionStatus:
        """
            The overall execution status indicating the outcome of
            the workflow.

            :returns: The WorkflowExecutionStatus member.
        """
        return self._status

    @property
    def step_results(self) -> List[StepResult]:
        """
            The list of StepResult objects for each executed step
            in the workflow.

            :returns: A list of StepResult objects. Empty list when
                no steps were executed.
        """
        return self._step_results

    @property
    def final_output(self) -> dict:
        """
            The dictionary of final output values from terminal steps
            in the workflow.

            :returns: A dictionary of final output values. Empty
                dictionary when no terminal output was produced.
        """
        return self._final_output

    @property
    def duration(self) -> float:
        """
            The total execution duration in seconds.

            :returns: The duration as a float in seconds.
        """
        return self._duration

    @property
    def error(self) -> Optional[str]:
        """
            The error message string when the workflow failed or
            encountered an error.

            :returns: The error message string or None when no
                error occurred.
        """
        return self._error

    @property
    def is_success(self) -> bool:
        """
            Indicates whether the workflow execution completed
            successfully.

            :returns: True when the execution status is COMPLETED,
                False otherwise.
        """
        rtnval = self._status == WorkflowExecutionStatus.COMPLETED
        return rtnval

    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """
            Returns the StepResult for the step with the given
            identifier, or None when the step was not executed.

            Iterates the step_results list to find a StepResult
            whose step_id matches the provided identifier.

            :param step_id: The unique identifier of the step to
                look up.

            :returns: The matching StepResult or None when the step
                identifier is not found.
        """
        for step_result in self._step_results:
            if step_result.step_id == step_id:
                return step_result

        return None

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the workflow
            result fields.

            The status is serialized as its string value. The
            step_results are serialized as a list of dictionaries
            using each StepResult's as_dict method.

            :returns: A dictionary containing workflow_name, status,
                step_results, final_output, duration, and error.
        """
        step_results_dicts = [sr.as_dict() for sr in self._step_results]

        rtnval = {
            "workflow_name": self._workflow_name,
            "status": self._status.value,
            "step_results": step_results_dicts,
            "final_output": self._final_output,
            "duration": self._duration,
            "error": self._error
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the workflow
            result fields.

            :returns: A JSON string containing all workflow result
                fields.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowResult":
        """
            Deserializes a JSON string into a WorkflowResult instance.

            The status field is deserialized using
            WorkflowExecutionStatus.from_string. Each entry in the
            step_results list is deserialized using StepResult.from_json.

            :param json_str: A JSON string containing workflow result
                fields.

            :returns: A WorkflowResult instance reconstructed from the
                JSON data.
        """
        data = json.loads(json_str)

        status = WorkflowExecutionStatus.from_string(data["status"])

        step_results = []
        raw_step_results = data.get("step_results", [])
        for sr_data in raw_step_results:
            sr_json = json.dumps(sr_data)
            step_result = StepResult.from_json(sr_json)
            step_results.append(step_result)

        rtnval = cls(
            workflow_name=data["workflow_name"],
            status=status,
            step_results=step_results,
            final_output=data.get("final_output"),
            duration=data.get("duration", 0.0),
            error=data.get("error")
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, workflow name, and execution status.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(workflow_name={!r}, status={})".format(
            self.__class__.__name__, self._workflow_name, self._status.value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the workflow
            name, status, step count, and total duration.

            :returns: A human-readable string describing the workflow
                result.
        """
        step_count = len(self._step_results)
        str_val = "WorkflowResult: {} [status: {}, steps: {}, duration: {:.3f}s]".format(
            self._workflow_name, self._status.value, step_count, self._duration
        )
        return str_val
