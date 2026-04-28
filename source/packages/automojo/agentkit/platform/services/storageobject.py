"""
    Defines the StorageObject class representing an immutable stored object
    with key, content, content type, metadata, size, and last modified
    timestamp. Supports serialization to and from dictionary and JSON
    representations with base64-encoded content.

    .. module:: automojo.agentkit.platform.services.storageobject
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable stored object representation for platform storage services.
"""

import base64
import json

from datetime import datetime
from typing import Dict
from typing import Optional


class StorageObject:
    """
        Immutable object representing a stored object in a platform storage
        service. Contains the object key, content as bytes, content type,
        metadata dictionary, size in bytes, and last modified timestamp.

        All fields are exposed as read-only properties. Serialization
        encodes content as base64 for safe transport in JSON.

        :param key: The object key string identifying this object.
        :param content: The object content as bytes.
        :param content_type: The MIME content type string.
        :param metadata: A dictionary of metadata key-value pairs.
        :param size: The size of the content in bytes.
        :param last_modified: The timestamp when the object was last modified.
    """

    def __init__(self, key: str, content: bytes, content_type: str,
                 metadata: Optional[Dict[str, str]] = None,
                 size: int = 0, last_modified: Optional[datetime] = None) -> None:
        self._key = key
        self._content = content
        self._content_type = content_type
        self._metadata = dict(metadata) if metadata is not None else {}
        self._size = size
        self._last_modified = last_modified
        return

    @property
    def key(self) -> str:
        """
            The object key string identifying this object.

            :returns: The key string.
        """
        rtnval = self._key
        return rtnval

    @property
    def content(self) -> bytes:
        """
            The object content as bytes.

            :returns: The content bytes.
        """
        rtnval = self._content
        return rtnval

    @property
    def content_type(self) -> str:
        """
            The MIME content type string.

            :returns: The content type string.
        """
        rtnval = self._content_type
        return rtnval

    @property
    def metadata(self) -> dict:
        """
            A defensive copy of the metadata dictionary.

            :returns: A dictionary copy of the metadata.
        """
        rtnval = dict(self._metadata)
        return rtnval

    @property
    def size(self) -> int:
        """
            The size of the content in bytes.

            :returns: The size integer.
        """
        rtnval = self._size
        return rtnval

    @property
    def last_modified(self) -> datetime:
        """
            The timestamp when the object was last modified.

            :returns: The last modified datetime.
        """
        rtnval = self._last_modified
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the object fields.
            Content is encoded as base64 for safe serialization.

            :returns: A dictionary with all object fields.
        """
        encoded_content = base64.b64encode(self._content).decode("utf-8")
        last_modified_str = self._last_modified.isoformat() if self._last_modified is not None else None
        rtnval = {
            "key": self._key,
            "content": encoded_content,
            "content_type": self._content_type,
            "metadata": dict(self._metadata),
            "size": self._size,
            "last_modified": last_modified_str
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the object fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "StorageObject":
        """
            Constructs a StorageObject from a dictionary, decoding base64
            content back to bytes.

            :param data: Dictionary containing object fields.

            :returns: A StorageObject instance.
        """
        content = base64.b64decode(data["content"])
        last_modified_raw = data.get("last_modified")
        last_modified = datetime.fromisoformat(last_modified_raw) if last_modified_raw is not None else None
        rtnval = cls(
            key=data["key"],
            content=content,
            content_type=data["content_type"],
            metadata=data.get("metadata", {}),
            size=data["size"],
            last_modified=last_modified
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "StorageObject":
        """
            Deserializes a JSON string into a StorageObject instance.

            :param json_str: A JSON string containing object fields.

            :returns: A StorageObject instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            object key, content type, and size.

            :returns: A repr string for debugging.
        """
        rtnval = "StorageObject(key={}, content_type={}, size={})".format(
            self._key, self._content_type, self._size
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the object key,
            content type, and size.

            :returns: A human-readable string.
        """
        rtnval = "StorageObject: key={}, content_type={}, size={}".format(
            self._key, self._content_type, self._size
        )
        return rtnval
