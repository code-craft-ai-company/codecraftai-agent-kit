"""
    Defines the HealthStatus class representing the result of a health check.
"""

import json

from datetime import datetime
from typing import Optional

from automojo.agentkit.errors import SemanticError


VALID_STATUSES = {"healthy", "degraded", "unhealthy"}


class HealthStatus:
    """
        Immutable object representing the result of a health check.

        :param check_name: The name of the health check.
        :param status: The status string (healthy, degraded, unhealthy).
        :param detail: Optional detail message.
        :param response_time: Response time in seconds.
        :param timestamp: The datetime of the check. Defaults to UTC now.
    """

    def __init__(self, check_name: str, status: str,
                 detail: Optional[str] = None,
                 response_time: float = 0.0,
                 timestamp: Optional[datetime] = None) -> None:
        if status not in VALID_STATUSES:
            errmsg = "Invalid health status '{}'. Valid values are: {}.".format(
                status, ", ".join(sorted(VALID_STATUSES))
            )
            raise SemanticError(errmsg)

        self._check_name = check_name
        self._status = status
        self._detail = detail
        self._response_time = response_time
        self._timestamp = timestamp if timestamp is not None else datetime.utcnow()
        return

    @property
    def check_name(self) -> str:
        return self._check_name

    @property
    def status(self) -> str:
        return self._status

    @property
    def detail(self) -> Optional[str]:
        return self._detail

    @property
    def response_time(self) -> float:
        return self._response_time

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def is_healthy(self) -> bool:
        return self._status == "healthy"

    def as_dict(self) -> dict:
        result = {
            "check_name": self._check_name,
            "status": self._status,
            "detail": self._detail,
            "response_time": self._response_time,
            "timestamp": self._timestamp.isoformat()
        }
        return result

    def to_json(self) -> str:
        data = self.as_dict()
        return json.dumps(data)

    @classmethod
    def from_dict(cls, data: dict) -> "HealthStatus":
        return cls(
            check_name=data["check_name"],
            status=data["status"],
            detail=data.get("detail"),
            response_time=data.get("response_time", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        )

    @classmethod
    def from_json(cls, json_str: str) -> "HealthStatus":
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return "HealthStatus(check_name={!r}, status={!r})".format(
            self._check_name, self._status
        )

    def __str__(self) -> str:
        return "HealthStatus check='{}', status={}, response_time={:.3f}s".format(
            self._check_name, self._status, self._response_time
        )
