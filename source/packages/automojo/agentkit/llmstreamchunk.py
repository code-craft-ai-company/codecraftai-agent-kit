"""
    Defines the LlmStreamChunk class for immutable streaming response chunks.

    LlmStreamChunk encapsulates a partial content string and an optional
    metadata dictionary from a streaming LLM response. The chunk is
    immutable once constructed.
"""


class LlmStreamChunk:
    """
        Immutable partial content from a streaming LLM response.

        Provides read-only access to the content string and metadata
        dictionary. The metadata property returns a copy to preserve
        immutability.

        :param content: The partial content string from the stream.
        :param metadata: Optional metadata dictionary.
    """

    def __init__(self, content: str, metadata: dict = None) -> None:
        self._content = content
        self._metadata = dict(metadata) if metadata is not None else {}
        return

    @property
    def content(self) -> str:
        """
            The partial content string from the stream.

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

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name
            and a truncated content preview at 30 characters.

            :returns: A repr string for debugging.
        """
        preview = self._content[:30] + "..." if len(self._content) > 30 else self._content
        rtnval = "{}(content={!r})".format(self.__class__.__name__, preview)
        return rtnval

    def __str__(self) -> str:
        """
            Returns the partial content string.

            :returns: The content string.
        """
        rtnval = self._content
        return rtnval
