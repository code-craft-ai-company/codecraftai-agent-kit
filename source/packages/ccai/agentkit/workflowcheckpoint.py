"""
    Defines the WorkflowCheckpoint class representing an immutable
    snapshot of workflow execution state at a specific point in the
    Workflow & Orchestration feature.

    A WorkflowCheckpoint contains the workflow name, execution
    identifier, the set of completed step identifiers, the serialized
    WorkflowContext state, the current step identifier, and a
    timestamp. The class provides JSON serialization and
    deserialization for persistence and reconstruction.
"""

import json

from datetime import datetime, timezone
from typing import Optional


class WorkflowCheckpoint:
    """
        Immutable snapshot of workflow execution state at a specific
        point.

        A WorkflowCheckpoint captures the workflow name, execution
        identifier, the set of completed step identifiers, the
        serialized WorkflowContext state as a dictionary, the current
        step identifier, and a UTC timestamp. All fields are exposed
        as read-only properties. The timestamp defaults to the
        current UTC time when not provided.

        :param workflow_name: The name of the workflow being
            checkpointed.
        :param execution_id: The unique identifier of the workflow
            execution.
        :param completed_step_ids: A set of step identifiers that
            have completed execution.
        :param context_state: A dictionary representing the
            serialized WorkflowContext state.
        :param current_step_id: The identifier of the step that
            was executing or about to execute when the checkpoint
            was taken.
        :param timestamp: An optional UTC datetime for the
            checkpoint. Defaults to the current UTC time.
    """

    def __init__(self, workflow_name: str, execution_id: str,
                 completed_step_ids: set, context_state: dict,
                 current_step_id: str,
                 timestamp: Optional[datetime] = None) -> None:
        self._workflow_name = workflow_name
        self._execution_id = execution_id
        self._completed_step_ids = set(completed_step_ids)
        self._context_state = dict(context_state)
        self._current_step_id = current_step_id
        self._timestamp = timestamp if timestamp is not None else datetime.now(timezone.utc)
        return

    @property
    def workflow_name(self) -> str:
        """
            The name of the workflow being checkpointed.

            :returns: The workflow name string.
        """
        return self._workflow_name

    @property
    def execution_id(self) -> str:
        """
            The unique identifier of the workflow execution.

            :returns: The execution identifier string.
        """
        return self._execution_id

    @property
    def completed_step_ids(self) -> set:
        """
            The set of step identifiers that have completed execution.

            Returns a defensive copy to preserve immutability.

            :returns: A set of step identifier strings.
        """
        rtnval = set(self._completed_step_ids)
        return rtnval

    @property
    def context_state(self) -> dict:
        """
            The serialized WorkflowContext state as a dictionary.

            Returns a defensive copy to preserve immutability.

            :returns: A dictionary representing the context state.
        """
        rtnval = dict(self._context_state)
        return rtnval

    @property
    def current_step_id(self) -> str:
        """
            The identifier of the step that was executing or about
            to execute when the checkpoint was taken.

            :returns: The current step identifier string.
        """
        return self._current_step_id

    @property
    def timestamp(self) -> datetime:
        """
            The UTC timestamp when the checkpoint was taken.

            :returns: A datetime object in UTC.
        """
        return self._timestamp

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the checkpoint
            fields.

            The completed_step_ids set is serialized as a sorted
            list for deterministic JSON output. The timestamp is
            serialized as an ISO format string.

            :returns: A dictionary containing all checkpoint fields.
        """
        rtnval = {
            "workflow_name": self._workflow_name,
            "execution_id": self._execution_id,
            "completed_step_ids": sorted(self._completed_step_ids),
            "context_state": self._context_state,
            "current_step_id": self._current_step_id,
            "timestamp": self._timestamp.isoformat()
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the checkpoint
            fields.

            :returns: A JSON string containing all checkpoint fields.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowCheckpoint":
        """
            Deserializes a JSON string into a WorkflowCheckpoint
            instance.

            The completed_step_ids list is converted back to a set.
            The timestamp is parsed from an ISO format string.

            :param json_str: A JSON string containing checkpoint
                fields.

            :returns: A WorkflowCheckpoint instance reconstructed
                from the JSON data.
        """
        data = json.loads(json_str)

        completed_step_ids = set(data["completed_step_ids"])
        timestamp = datetime.fromisoformat(data["timestamp"])

        rtnval = cls(
            workflow_name=data["workflow_name"],
            execution_id=data["execution_id"],
            completed_step_ids=completed_step_ids,
            context_state=data["context_state"],
            current_step_id=data["current_step_id"],
            timestamp=timestamp
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, workflow name, execution identifier, and the
            count of completed steps.

            :returns: A repr string for debugging.
        """
        completed_count = len(self._completed_step_ids)
        repr_str = "{}(workflow_name={!r}, execution_id={!r}, completed_steps={})".format(
            self.__class__.__name__, self._workflow_name,
            self._execution_id, completed_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the workflow
            name, execution identifier, and timestamp.

            :returns: A human-readable string describing the
                checkpoint.
        """
        str_val = "WorkflowCheckpoint: {} [execution: {}, timestamp: {}]".format(
            self._workflow_name, self._execution_id,
            self._timestamp.isoformat()
        )
        return str_val
