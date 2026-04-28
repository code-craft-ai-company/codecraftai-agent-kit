"""
    Configuration object defining how expired MemoryEntry objects are handled.

    Contains the default time-to-live duration and the cleanup interval.
"""

import json
from typing import Optional


class ExpirationPolicy:
    """
        Configuration object defining how expired MemoryEntry objects are handled.
        Contains the default time-to-live duration and the cleanup interval.
    """

    def __init__(self, default_ttl: float = None, cleanup_interval: float = 300.0) -> None:
        """
            Constructs an ExpirationPolicy.

            :param default_ttl: Optional default time-to-live in seconds.
            :param cleanup_interval: Cleanup interval in seconds. Defaults to 300.
        """
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        return

    @property
    def default_ttl(self) -> Optional[float]:
        """
            The default time-to-live in seconds, or None if not set.

            :returns: A float or None.
        """
        return self._default_ttl

    @property
    def cleanup_interval(self) -> float:
        """
            The cleanup interval in seconds.

            :returns: A float.
        """
        return self._cleanup_interval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the policy fields.

            :returns: A dictionary with default_ttl and cleanup_interval.
        """
        rtnval = {
            "default_ttl": self._default_ttl,
            "cleanup_interval": self._cleanup_interval,
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the policy fields.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "ExpirationPolicy":
        """
            Constructs an ExpirationPolicy from a dictionary.

            :param data: A dictionary with policy fields.

            :returns: An ExpirationPolicy instance.
        """
        rtnval = cls(
            default_ttl=data.get("default_ttl"),
            cleanup_interval=data.get("cleanup_interval", 300.0),
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "ExpirationPolicy":
        """
            Deserializes a JSON string into an ExpirationPolicy instance.

            :param json_str: A JSON string.

            :returns: An ExpirationPolicy instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        rtnval = "{}(default_ttl={}, cleanup_interval={})".format(
            self.__class__.__name__, self._default_ttl, self._cleanup_interval
        )
        return rtnval

    def __str__(self) -> str:
        ttl_str = "{}s".format(self._default_ttl) if self._default_ttl is not None else "none"
        rtnval = "ExpirationPolicy: ttl={}, cleanup_interval={}s".format(
            ttl_str, self._cleanup_interval
        )
        return rtnval

    def __eq__(self, other) -> bool:
        if not isinstance(other, ExpirationPolicy):
            rtnval = False
            return rtnval
        rtnval = (
            self._default_ttl == other._default_ttl
            and self._cleanup_interval == other._cleanup_interval
        )
        return rtnval
