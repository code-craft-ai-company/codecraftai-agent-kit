"""
    Defines the LLMMessage class for immutable conversation messages.

    LLMMessage encapsulates a role, content string, and optional metadata
    dictionary for a single message in an LLM conversation. The role must
    be one of the valid roles: system, user, assistant, or tool.
"""

import json

from automojo.agentkit.errors import SemanticError


class LLMMessage:
    """
        Immutable message in a conversation with a role, content, and optional metadata.

        Provides read-only access to the role, content, and metadata fields.
        Validates that the role is one of the valid roles at construction time.
        Supports serialization to and from JSON and dictionary representations.

        :param role: The message role (system, user, assistant, tool).
        :param content: The message content string.
        :param metadata: Optional metadata dictionary (e.g. tool call info).
    """

    VALID_ROLES = {"system", "user", "assistant", "tool"}

    def __init__(self, role: str, content: str, metadata: dict = None) -> None:
        if role not in self.VALID_ROLES:
            errmsg = "Invalid message role {!r}. Valid roles are: {}".format(
                role, ", ".join(sorted(self.VALID_ROLES))
            )
            raise SemanticError(errmsg)

        self._role = role
        self._content = content
        self._metadata = dict(metadata) if metadata is not None else {}
        return

    @property
    def role(self) -> str:
        """
            The message role string.

            :returns: The role as a string.
        """
        rtnval = self._role
        return rtnval

    @property
    def content(self) -> str:
        """
            The message content string.

            :returns: The content as a string.
        """
        rtnval = self._content
        return rtnval

    @property
    def metadata(self) -> dict:
        """
            A copy of the metadata dictionary.

            :returns: A dictionary copy of the metadata.
        """
        rtnval = dict(self._metadata)
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the message.

            :returns: A dictionary with role, content, and metadata keys.
        """
        rtnval = {
            "role": self._role,
            "content": self._content,
            "metadata": dict(self._metadata)
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the message.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "LLMMessage":
        """
            Constructs an LLMMessage from a dictionary.

            :param data: A dictionary with role, content, and optional metadata keys.

            :returns: An LLMMessage instance.
        """
        rtnval = cls(
            role=data["role"],
            content=data["content"],
            metadata=data.get("metadata")
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "LLMMessage":
        """
            Deserializes a JSON string into an LLMMessage.

            :param json_str: A JSON string.

            :returns: An LLMMessage instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            role, and a truncated content preview at 50 characters.

            :returns: A repr string for debugging.
        """
        content_preview = self._content[:50] + "..." if len(self._content) > 50 else self._content
        rtnval = "{}(role={!r}, content={!r})".format(
            self.__class__.__name__, self._role, content_preview
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the role and content.

            :returns: A human-readable string.
        """
        rtnval = "[{}] {}".format(self._role, self._content)
        return rtnval

    def __eq__(self, other) -> bool:
        """
            Checks equality based on role, content, and metadata fields.

            :param other: The object to compare against.

            :returns: True if all fields are equal, False otherwise.
        """
        if not isinstance(other, LLMMessage):
            return False

        rtnval = (self._role == other._role and
                  self._content == other._content and
                  self._metadata == other._metadata)
        return rtnval
