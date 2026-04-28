"""
    Immutable object representing a search request against a MemoryStore.

    Supports filtering by tags, metadata, scope, time range, and
    semantic similarity.
"""

import json
from datetime import datetime
from typing import Optional

from automojo.agentkit.memoryscope import MemoryScope


class MemoryQuery:
    """
        Immutable object representing a search request against a MemoryStore.
        Supports filtering by tags, metadata, scope, time range, and
        semantic similarity.
    """

    def __init__(self, tags: list = None, metadata: dict = None,
                 scope: MemoryScope = None, start_time: datetime = None,
                 end_time: datetime = None, semantic_text: str = None,
                 max_results: int = None, min_relevance: float = None) -> None:
        """
            Constructs a MemoryQuery.

            :param tags: Optional list of required tags.
            :param metadata: Optional metadata key-value pairs to match.
            :param scope: Optional MemoryScope filter.
            :param start_time: Optional start of time range.
            :param end_time: Optional end of time range.
            :param semantic_text: Optional semantic query text for similarity search.
            :param max_results: Optional maximum number of results.
            :param min_relevance: Optional minimum relevance score threshold.
        """
        self._tags = list(tags) if tags is not None else None
        self._metadata = dict(metadata) if metadata is not None else None
        self._scope = scope
        self._start_time = start_time
        self._end_time = end_time
        self._semantic_text = semantic_text
        self._max_results = max_results
        self._min_relevance = min_relevance
        return

    @property
    def tags(self) -> Optional[list]:
        """
            The list of required tags, or None if not set.
            Returns a defensive copy.

            :returns: A list of tag strings or None.
        """
        if self._tags is not None:
            rtnval = list(self._tags)
            return rtnval
        return None

    @property
    def metadata(self) -> Optional[dict]:
        """
            The metadata key-value pairs to match, or None if not set.
            Returns a defensive copy.

            :returns: A dictionary or None.
        """
        if self._metadata is not None:
            rtnval = dict(self._metadata)
            return rtnval
        return None

    @property
    def scope(self) -> Optional[MemoryScope]:
        """
            The MemoryScope filter, or None if not set.

            :returns: A MemoryScope value or None.
        """
        return self._scope

    @property
    def start_time(self) -> Optional[datetime]:
        """
            The start of the time range filter, or None if not set.

            :returns: A datetime object or None.
        """
        return self._start_time

    @property
    def end_time(self) -> Optional[datetime]:
        """
            The end of the time range filter, or None if not set.

            :returns: A datetime object or None.
        """
        return self._end_time

    @property
    def semantic_text(self) -> Optional[str]:
        """
            The semantic query text for similarity search, or None if not set.

            :returns: A string or None.
        """
        return self._semantic_text

    @property
    def max_results(self) -> Optional[int]:
        """
            The maximum number of results, or None if not set.

            :returns: An integer or None.
        """
        return self._max_results

    @property
    def min_relevance(self) -> Optional[float]:
        """
            The minimum relevance score threshold, or None if not set.

            :returns: A float or None.
        """
        return self._min_relevance

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the query fields.

            :returns: A dictionary with all query fields.
        """
        rtnval = {
            "tags": list(self._tags) if self._tags is not None else None,
            "metadata": dict(self._metadata) if self._metadata is not None else None,
            "scope": self._scope.value if self._scope is not None else None,
            "start_time": self._start_time.isoformat() if self._start_time is not None else None,
            "end_time": self._end_time.isoformat() if self._end_time is not None else None,
            "semantic_text": self._semantic_text,
            "max_results": self._max_results,
            "min_relevance": self._min_relevance,
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the query fields.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryQuery":
        """
            Constructs a MemoryQuery from a dictionary.

            :param data: A dictionary with query fields.

            :returns: A MemoryQuery instance.
        """
        scope = None
        if "scope" in data and data["scope"] is not None:
            scope = MemoryScope.from_string(data["scope"])

        start_time = None
        if "start_time" in data and data["start_time"] is not None:
            start_time = datetime.fromisoformat(data["start_time"])

        end_time = None
        if "end_time" in data and data["end_time"] is not None:
            end_time = datetime.fromisoformat(data["end_time"])

        rtnval = cls(
            tags=data.get("tags"),
            metadata=data.get("metadata"),
            scope=scope,
            start_time=start_time,
            end_time=end_time,
            semantic_text=data.get("semantic_text"),
            max_results=data.get("max_results"),
            min_relevance=data.get("min_relevance"),
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryQuery":
        """
            Deserializes a JSON string into a MemoryQuery instance.

            :param json_str: A JSON string.

            :returns: A MemoryQuery instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        criteria = []
        if self._tags is not None:
            criteria.append("tags={}".format(len(self._tags)))
        if self._metadata is not None:
            criteria.append("metadata={}".format(len(self._metadata)))
        if self._scope is not None:
            criteria.append("scope={}".format(self._scope.value))
        if self._semantic_text is not None:
            criteria.append("semantic=True")
        if self._max_results is not None:
            criteria.append("max={}".format(self._max_results))
        summary = ", ".join(criteria) if len(criteria) > 0 else "no filters"
        rtnval = "{}({})".format(self.__class__.__name__, summary)
        return rtnval

    def __str__(self) -> str:
        criteria = []
        if self._tags is not None:
            criteria.append("tags: {}".format(self._tags))
        if self._metadata is not None:
            criteria.append("metadata: {}".format(list(self._metadata.keys())))
        if self._scope is not None:
            criteria.append("scope: {}".format(self._scope.value))
        if self._start_time is not None or self._end_time is not None:
            criteria.append("time range: {} to {}".format(self._start_time, self._end_time))
        if self._semantic_text is not None:
            preview = self._semantic_text[:50] + "..." if len(self._semantic_text) > 50 else self._semantic_text
            criteria.append("semantic: {!r}".format(preview))
        summary = "; ".join(criteria) if len(criteria) > 0 else "no filters"
        rtnval = "MemoryQuery: {}".format(summary)
        return rtnval

    def __eq__(self, other) -> bool:
        if not isinstance(other, MemoryQuery):
            rtnval = False
            return rtnval
        rtnval = (
            self._tags == other._tags
            and self._metadata == other._metadata
            and self._scope == other._scope
            and self._start_time == other._start_time
            and self._end_time == other._end_time
            and self._semantic_text == other._semantic_text
            and self._max_results == other._max_results
            and self._min_relevance == other._min_relevance
        )
        return rtnval
