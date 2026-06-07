"""
    Defines the InMemoryDeadLetterStore for in-process dead letter storage.
"""

from typing import Optional

from ccai.agentkit.deadletterentry import DeadLetterEntry
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.deadletterquery import DeadLetterQueryResult
from ccai.agentkit.deadletterstore import DeadLetterStore


class InMemoryDeadLetterStore(DeadLetterStore):
    """
        In-process dictionary-based dead letter store.
    """

    def __init__(self) -> None:
        super().__init__("in_memory")
        self._entries = {}
        return

    def store(self, entry: DeadLetterEntry) -> None:
        self._entries[entry.identifier] = entry
        return

    def retrieve(self, identifier: str) -> Optional[DeadLetterEntry]:
        return self._entries.get(identifier)

    def search(self, query: DeadLetterQuery) -> DeadLetterQueryResult:
        matches = list(self._entries.values())

        if query.operation_type is not None:
            matches = [e for e in matches if e.operation_type == query.operation_type]
        if query.source_component is not None:
            matches = [e for e in matches if e.source_component == query.source_component]
        if query.agent_identifier is not None:
            matches = [e for e in matches if e.agent_identifier == query.agent_identifier]
        if query.start_time is not None:
            matches = [e for e in matches if e.timestamp >= query.start_time]
        if query.end_time is not None:
            matches = [e for e in matches if e.timestamp <= query.end_time]

        total_count = len(matches)

        if query.max_results is not None:
            matches = matches[:query.max_results]

        result = DeadLetterQueryResult(entries=matches, total_count=total_count)
        return result

    def delete(self, identifier: str) -> None:
        self._entries.pop(identifier, None)
        return

    def purge(self) -> None:
        self._entries.clear()
        return

    def count(self) -> int:
        return len(self._entries)
