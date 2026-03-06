"""
    Defines the DeadLetterEntry class representing a failed operation
    stored in the dead letter queue.
"""

import json
import uuid

from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional


class DeadLetterEntry:
    """
        Immutable object representing a failed operation or message stored
        in the DeadLetterQueue.

        :param operation_type: The original operation type string.
        :param payload: The original payload as a dictionary.
        :param exception_info: The final exception information string.
        :param retry_attempts: The number of retry attempts.
        :param source_component: The source component name.
        :param agent_identifier: The agent identifier.
        :param identifier: Optional unique identifier. Auto-generated if not provided.
        :param timestamp: Optional creation timestamp. Auto-generated if not provided.
        :param metadata: Optional metadata dictionary.
    """

    def __init__(self, operation_type: str, payload: dict,
                 exception_info: str, retry_attempts: int,
                 source_component: str, agent_identifier: str,
                 identifier: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 metadata: Optional[Dict] = None) -> None:
        self._identifier = identifier if identifier is not None else str(uuid.uuid4())
        self._operation_type = operation_type
        self._payload = dict(payload)
        self._exception_info = exception_info
        self._retry_attempts = retry_attempts
        self._source_component = source_component
        self._agent_identifier = agent_identifier
        self._timestamp = timestamp if timestamp is not None else datetime.utcnow()
        self._metadata = dict(metadata) if metadata is not None else {}
        return

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def operation_type(self) -> str:
        return self._operation_type

    @property
    def payload(self) -> dict:
        return dict(self._payload)

    @property
    def exception_info(self) -> str:
        return self._exception_info

    @property
    def retry_attempts(self) -> int:
        return self._retry_attempts

    @property
    def source_component(self) -> str:
        return self._source_component

    @property
    def agent_identifier(self) -> str:
        return self._agent_identifier

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def metadata(self) -> dict:
        return dict(self._metadata)

    def as_dict(self) -> dict:
        result = {
            "identifier": self._identifier,
            "operation_type": self._operation_type,
            "payload": self._payload,
            "exception_info": self._exception_info,
            "retry_attempts": self._retry_attempts,
            "source_component": self._source_component,
            "agent_identifier": self._agent_identifier,
            "timestamp": self._timestamp.isoformat(),
            "metadata": self._metadata
        }
        return result

    def to_json(self) -> str:
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "DeadLetterEntry":
        entry = cls(
            operation_type=data["operation_type"],
            payload=data["payload"],
            exception_info=data["exception_info"],
            retry_attempts=data["retry_attempts"],
            source_component=data["source_component"],
            agent_identifier=data["agent_identifier"],
            identifier=data.get("identifier"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None,
            metadata=data.get("metadata")
        )
        return entry

    @classmethod
    def from_json(cls, json_str: str) -> "DeadLetterEntry":
        data = json.loads(json_str)
        entry = cls.from_dict(data)
        return entry

    def __repr__(self) -> str:
        repr_str = "DeadLetterEntry(id={!r}, operation_type={!r})".format(
            self._identifier, self._operation_type
        )
        return repr_str

    def __str__(self) -> str:
        str_val = "DeadLetterEntry id='{}', operation='{}', source='{}', agent='{}'".format(
            self._identifier, self._operation_type,
            self._source_component, self._agent_identifier
        )
        return str_val
