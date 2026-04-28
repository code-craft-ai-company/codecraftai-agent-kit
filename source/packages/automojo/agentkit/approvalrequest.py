"""
    Defines the ApprovalRequest class representing an immutable
    pending approval within a workflow in the Workflow &
    Orchestration feature.

    An ApprovalRequest contains a unique identifier, the workflow
    execution identifier, the step identifier, a description of
    what is being approved, the requesting agent identifier, the
    approval status, optional metadata, an optional rejection
    reason, and a UTC timestamp. The class provides JSON
    serialization and deserialization for persistence and
    reconstruction.
"""

import json
import uuid

from datetime import datetime, timezone
from typing import Optional


class ApprovalRequest:
    """
        Immutable object representing a pending approval within a
        workflow.

        An ApprovalRequest captures the details of an approval
        that must be resolved before a workflow can continue. All
        fields are exposed as read-only properties. The identifier
        defaults to an auto-generated UUID and the timestamp
        defaults to the current UTC time when not provided.

        :param identifier: An optional unique identifier for the
            request. Defaults to an auto-generated UUID string.
        :param execution_id: The unique identifier of the workflow
            execution that created this request.
        :param step_id: The identifier of the workflow step that
            requires approval.
        :param description: A human-readable description of what
            is being approved.
        :param requesting_agent_id: The identifier of the agent
            that requested the approval.
        :param status: The approval status string. Must be one of
            the VALID_STATUSES values. Defaults to "pending".
        :param metadata: An optional dictionary of approval
            metadata. Defaults to an empty dictionary.
        :param rejection_reason: An optional string describing
            the reason for rejection.
        :param timestamp: An optional UTC datetime for the
            request. Defaults to the current UTC time.
    """

    VALID_STATUSES = {"pending", "approved", "rejected", "expired"}

    def __init__(self, execution_id: str, step_id: str,
                 description: str, requesting_agent_id: str,
                 identifier: Optional[str] = None,
                 status: str = "pending",
                 metadata: Optional[dict] = None,
                 rejection_reason: Optional[str] = None,
                 timestamp: Optional[datetime] = None) -> None:
        self._identifier = identifier if identifier is not None else str(uuid.uuid4())
        self._execution_id = execution_id
        self._step_id = step_id
        self._description = description
        self._requesting_agent_id = requesting_agent_id
        self._status = status
        self._metadata = dict(metadata) if metadata is not None else {}
        self._rejection_reason = rejection_reason
        self._timestamp = timestamp if timestamp is not None else datetime.now(timezone.utc)
        return

    @property
    def identifier(self) -> str:
        """
            The unique identifier for this approval request.

            :returns: The identifier string.
        """
        return self._identifier

    @property
    def execution_id(self) -> str:
        """
            The unique identifier of the workflow execution that
            created this request.

            :returns: The execution identifier string.
        """
        return self._execution_id

    @property
    def step_id(self) -> str:
        """
            The identifier of the workflow step that requires
            approval.

            :returns: The step identifier string.
        """
        return self._step_id

    @property
    def description(self) -> str:
        """
            A human-readable description of what is being approved.

            :returns: The description string.
        """
        return self._description

    @property
    def requesting_agent_id(self) -> str:
        """
            The identifier of the agent that requested the approval.

            :returns: The requesting agent identifier string.
        """
        return self._requesting_agent_id

    @property
    def status(self) -> str:
        """
            The current approval status.

            :returns: A status string, one of "pending", "approved",
                "rejected", or "expired".
        """
        return self._status

    @property
    def metadata(self) -> dict:
        """
            Optional approval metadata.

            Returns a defensive copy to preserve immutability.

            :returns: A dictionary of metadata.
        """
        rtnval = dict(self._metadata)
        return rtnval

    @property
    def rejection_reason(self) -> Optional[str]:
        """
            The reason for rejection, or None when the request
            has not been rejected.

            :returns: The rejection reason string or None.
        """
        return self._rejection_reason

    @property
    def timestamp(self) -> datetime:
        """
            The UTC timestamp when the request was created.

            :returns: A datetime object in UTC.
        """
        return self._timestamp

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the approval
            request fields.

            The timestamp is serialized as an ISO format string.

            :returns: A dictionary containing all request fields.
        """
        rtnval = {
            "identifier": self._identifier,
            "execution_id": self._execution_id,
            "step_id": self._step_id,
            "description": self._description,
            "requesting_agent_id": self._requesting_agent_id,
            "status": self._status,
            "metadata": dict(self._metadata),
            "rejection_reason": self._rejection_reason,
            "timestamp": self._timestamp.isoformat()
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the approval
            request fields.

            :returns: A JSON string containing all request fields.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "ApprovalRequest":
        """
            Deserializes a JSON string into an ApprovalRequest
            instance.

            The timestamp is parsed from an ISO format string.

            :param json_str: A JSON string containing approval
                request fields.

            :returns: An ApprovalRequest instance reconstructed
                from the JSON data.
        """
        data = json.loads(json_str)

        timestamp = datetime.fromisoformat(data["timestamp"])

        rtnval = cls(
            identifier=data["identifier"],
            execution_id=data["execution_id"],
            step_id=data["step_id"],
            description=data["description"],
            requesting_agent_id=data["requesting_agent_id"],
            status=data["status"],
            metadata=data.get("metadata"),
            rejection_reason=data.get("rejection_reason"),
            timestamp=timestamp
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, identifier, step identifier, and approval
            status.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(identifier={!r}, step_id={!r}, status={!r})".format(
            self.__class__.__name__, self._identifier,
            self._step_id, self._status
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the
            identifier, description, and approval status.

            :returns: A human-readable string describing the
                approval request.
        """
        str_val = "ApprovalRequest: {} [{}] status={}".format(
            self._identifier, self._description, self._status
        )
        return str_val
