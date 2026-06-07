"""
    Defines DeadLetterQuery and DeadLetterQueryResult classes for searching
    the dead letter store.
"""

from datetime import datetime
from typing import List
from typing import Optional

from ccai.agentkit.deadletterentry import DeadLetterEntry


class DeadLetterQuery:
    """
        Immutable object representing a search request against a DeadLetterStore.

        :param operation_type: Optional filter by operation type.
        :param source_component: Optional filter by source component.
        :param agent_identifier: Optional filter by agent identifier.
        :param start_time: Optional filter by start time.
        :param end_time: Optional filter by end time.
        :param max_results: Optional maximum number of results.
    """

    def __init__(self, operation_type: Optional[str] = None,
                 source_component: Optional[str] = None,
                 agent_identifier: Optional[str] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 max_results: Optional[int] = None) -> None:
        self._operation_type = operation_type
        self._source_component = source_component
        self._agent_identifier = agent_identifier
        self._start_time = start_time
        self._end_time = end_time
        self._max_results = max_results
        return

    @property
    def operation_type(self) -> Optional[str]:
        return self._operation_type

    @property
    def source_component(self) -> Optional[str]:
        return self._source_component

    @property
    def agent_identifier(self) -> Optional[str]:
        return self._agent_identifier

    @property
    def start_time(self) -> Optional[datetime]:
        return self._start_time

    @property
    def end_time(self) -> Optional[datetime]:
        return self._end_time

    @property
    def max_results(self) -> Optional[int]:
        return self._max_results

    def as_dict(self) -> dict:
        result = {
            "operation_type": self._operation_type,
            "source_component": self._source_component,
            "agent_identifier": self._agent_identifier,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
            "max_results": self._max_results
        }
        return result

    def __repr__(self) -> str:
        repr_str = "DeadLetterQuery(operation_type={!r}, source={!r})".format(
            self._operation_type, self._source_component
        )
        return repr_str

    def __str__(self) -> str:
        filters = []
        if self._operation_type:
            filters.append("operation_type='{}'".format(self._operation_type))
        if self._source_component:
            filters.append("source='{}'".format(self._source_component))
        if self._agent_identifier:
            filters.append("agent='{}'".format(self._agent_identifier))
        str_val = "DeadLetterQuery [{}]".format(", ".join(filters) if filters else "no filters")
        return str_val


class DeadLetterQueryResult:
    """
        Immutable object encapsulating the result of a DeadLetterQuery.

        :param entries: The list of matching DeadLetterEntry objects.
        :param total_count: The total count of matches.
    """

    def __init__(self, entries: List[DeadLetterEntry], total_count: int) -> None:
        self._entries = list(entries)
        self._total_count = total_count
        return

    @property
    def entries(self) -> List[DeadLetterEntry]:
        return list(self._entries)

    @property
    def total_count(self) -> int:
        return self._total_count

    def __repr__(self) -> str:
        repr_str = "DeadLetterQueryResult(total_count={})".format(self._total_count)
        return repr_str

    def __str__(self) -> str:
        str_val = "DeadLetterQueryResult: {} entries".format(self._total_count)
        return str_val
