"""
    Immutable object encapsulating the result of a MemoryQuery.

    Contains matching MemoryEntry objects, optional relevance scores,
    and the total count of matches.
"""

from typing import Optional


class MemoryQueryResult:
    """
        Immutable object encapsulating the result of a MemoryQuery.
        Contains matching MemoryEntry objects, optional relevance scores,
        and the total count of matches.
    """

    def __init__(self, entries: list, scores: list = None, total_count: int = None) -> None:
        """
            Constructs a MemoryQueryResult.

            :param entries: List of matching MemoryEntry objects.
            :param scores: Optional list of relevance scores as floats.
            :param total_count: Optional total count of matches. Defaults to len(entries).
        """
        self._entries = list(entries)
        self._scores = list(scores) if scores is not None else None
        self._total_count = total_count if total_count is not None else len(entries)
        return

    @property
    def entries(self) -> list:
        """
            The list of matching MemoryEntry objects.
            Returns a defensive copy.

            :returns: A list of MemoryEntry objects.
        """
        rtnval = list(self._entries)
        return rtnval

    @property
    def scores(self) -> Optional[list]:
        """
            The list of relevance scores, or None if not set.
            Returns a defensive copy.

            :returns: A list of floats or None.
        """
        if self._scores is not None:
            rtnval = list(self._scores)
            return rtnval
        return None

    @property
    def total_count(self) -> int:
        """
            The total count of matches.

            :returns: An integer.
        """
        return self._total_count

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the result fields.

            :returns: A dictionary with entries, scores, and total_count.
        """
        rtnval = {
            "entries": [e.as_dict() for e in self._entries],
            "scores": list(self._scores) if self._scores is not None else None,
            "total_count": self._total_count,
        }
        return rtnval

    def __repr__(self) -> str:
        rtnval = "{}(count={})".format(self.__class__.__name__, self._total_count)
        return rtnval

    def __str__(self) -> str:
        top_ids = [e.identifier for e in self._entries[:5]]
        rtnval = "MemoryQueryResult: {} matches, top: [{}]".format(
            self._total_count, ", ".join(top_ids)
        )
        return rtnval
