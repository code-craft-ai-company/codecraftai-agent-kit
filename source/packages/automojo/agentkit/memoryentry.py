"""
    Immutable value object representing a single unit of stored memory.

    Contains a unique identifier, content string, optional embedding vector,
    metadata dictionary, tags list, creation timestamp, optional expiration
    timestamp, and a MemoryScope value.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from automojo.agentkit.memoryscope import MemoryScope


class MemoryEntry:
    """
        Immutable object representing a single unit of stored memory.
        Contains a unique identifier, content string, optional embedding vector,
        metadata dictionary, tags list, creation timestamp, optional expiration
        timestamp, and a MemoryScope value.
    """

    def __init__(self, content: str, scope: MemoryScope,
                 identifier: str = None, embedding: list = None,
                 metadata: dict = None, tags: list = None,
                 created_at: datetime = None, expires_at: datetime = None) -> None:
        """
            Constructs a MemoryEntry.

            :param content: The content string of the memory entry.
            :param scope: The MemoryScope value for this entry.
            :param identifier: Optional unique identifier. Auto-generated UUID if not provided.
            :param embedding: Optional embedding vector as a list of floats.
            :param metadata: Optional metadata dictionary.
            :param tags: Optional list of tag strings.
            :param created_at: Optional creation timestamp. Defaults to current UTC time.
            :param expires_at: Optional expiration timestamp.
        """
        self._identifier = identifier if identifier is not None else str(uuid.uuid4())
        self._content = content
        self._scope = scope
        self._embedding = list(embedding) if embedding is not None else None
        self._metadata = dict(metadata) if metadata is not None else {}
        self._tags = list(tags) if tags is not None else []
        self._created_at = created_at if created_at is not None else datetime.now(timezone.utc)
        self._expires_at = expires_at
        return

    @property
    def identifier(self) -> str:
        """
            The unique identifier of this memory entry.

            :returns: The identifier string.
        """
        return self._identifier

    @property
    def content(self) -> str:
        """
            The content string of this memory entry.

            :returns: The content string.
        """
        return self._content

    @property
    def scope(self) -> MemoryScope:
        """
            The visibility scope of this memory entry.

            :returns: The MemoryScope value.
        """
        return self._scope

    @property
    def embedding(self) -> Optional[list]:
        """
            The embedding vector of this memory entry, or None if not set.
            Returns a defensive copy.

            :returns: A list of floats or None.
        """
        if self._embedding is not None:
            rtnval = list(self._embedding)
            return rtnval
        return None

    @property
    def metadata(self) -> dict:
        """
            The metadata dictionary of this memory entry.
            Returns a defensive copy.

            :returns: A dictionary of metadata key-value pairs.
        """
        rtnval = dict(self._metadata)
        return rtnval

    @property
    def tags(self) -> list:
        """
            The tags list of this memory entry.
            Returns a defensive copy.

            :returns: A list of tag strings.
        """
        rtnval = list(self._tags)
        return rtnval

    @property
    def created_at(self) -> datetime:
        """
            The creation timestamp of this memory entry.

            :returns: A datetime object.
        """
        return self._created_at

    @property
    def expires_at(self) -> Optional[datetime]:
        """
            The expiration timestamp of this memory entry, or None if not set.

            :returns: A datetime object or None.
        """
        return self._expires_at

    def is_expired(self, reference_time: datetime = None) -> bool:
        """
            Returns True when the expiration timestamp is set and the
            reference timestamp exceeds the expiration timestamp.

            :param reference_time: Optional reference timestamp. Defaults to current UTC time.

            :returns: True if the entry is expired, False otherwise.
        """
        if self._expires_at is None:
            rtnval = False
            return rtnval

        if reference_time is None:
            reference_time = datetime.now(timezone.utc)

        rtnval = reference_time >= self._expires_at
        return rtnval

    def as_dict(self, brief: bool = False) -> dict:
        """
            Returns a dictionary representation of the entry fields.

            :param brief: If True, excludes the embedding vector.

            :returns: A dictionary with all entry fields.
        """
        rtnval = {
            "identifier": self._identifier,
            "content": self._content,
            "scope": self._scope.value,
            "metadata": dict(self._metadata),
            "tags": list(self._tags),
            "created_at": self._created_at.isoformat(),
            "expires_at": self._expires_at.isoformat() if self._expires_at is not None else None,
        }

        if brief is not True:
            rtnval["embedding"] = list(self._embedding) if self._embedding is not None else None

        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the entry fields.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """
            Constructs a MemoryEntry from a dictionary.

            :param data: A dictionary with entry fields.

            :returns: A MemoryEntry instance.
        """
        created_at = None
        if "created_at" in data and data["created_at"] is not None:
            created_at = datetime.fromisoformat(data["created_at"])

        expires_at = None
        if "expires_at" in data and data["expires_at"] is not None:
            expires_at = datetime.fromisoformat(data["expires_at"])

        scope = MemoryScope.from_string(data["scope"])

        rtnval = cls(
            content=data["content"],
            scope=scope,
            identifier=data.get("identifier"),
            embedding=data.get("embedding"),
            metadata=data.get("metadata"),
            tags=data.get("tags"),
            created_at=created_at,
            expires_at=expires_at,
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryEntry":
        """
            Deserializes a JSON string into a MemoryEntry instance.

            :param json_str: A JSON string.

            :returns: A MemoryEntry instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        content_preview = self._content[:50] + "..." if len(self._content) > 50 else self._content
        rtnval = "{}(identifier={!r}, scope={!r}, content={!r})".format(
            self.__class__.__name__, self._identifier, self._scope.value, content_preview
        )
        return rtnval

    def __str__(self) -> str:
        content_preview = self._content[:80] + "..." if len(self._content) > 80 else self._content
        rtnval = "MemoryEntry: {} [{}] tags={} content={!r}".format(
            self._identifier, self._scope.value, len(self._tags), content_preview
        )
        return rtnval

    def __eq__(self, other) -> bool:
        if not isinstance(other, MemoryEntry):
            rtnval = False
            return rtnval
        rtnval = (
            self._identifier == other._identifier
            and self._content == other._content
            and self._scope == other._scope
            and self._embedding == other._embedding
            and self._metadata == other._metadata
            and self._tags == other._tags
            and self._created_at == other._created_at
            and self._expires_at == other._expires_at
        )
        return rtnval
