"""
    Defines the DeadLetterQueue class for managing permanently failed
    operations in the Error Handling & Resilience feature.
"""

import logging

from typing import Callable
from typing import Optional

from ccai.agentkit.deadletterentry import DeadLetterEntry
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.deadletterquery import DeadLetterQueryResult
from ccai.agentkit.deadletterstore import DeadLetterStore


class DeadLetterQueue:
    """
        Queue for storing operations and messages that have permanently failed.

        :param store: The DeadLetterStore backend.
    """

    def __init__(self, store: DeadLetterStore) -> None:
        self._store = store
        self._logger = logging.getLogger("ccai.agentkit.resilience")
        return

    @property
    def store(self) -> DeadLetterStore:
        return self._store

    @property
    def entry_count(self) -> int:
        return self._store.count()

    def enqueue(self, operation_type: str, payload: dict,
                exception_info: str, retry_attempts: int,
                source_component: str, agent_identifier: str,
                metadata: Optional[dict] = None) -> DeadLetterEntry:
        """
            Creates a DeadLetterEntry and stores it.

            :returns: The created DeadLetterEntry.
        """
        entry = DeadLetterEntry(
            operation_type=operation_type,
            payload=payload,
            exception_info=exception_info,
            retry_attempts=retry_attempts,
            source_component=source_component,
            agent_identifier=agent_identifier,
            metadata=metadata
        )
        self._store.store(entry)

        self._logger.warning(
            "Dead letter enqueued: operation='%s', source='%s', agent='%s', id='%s'",
            operation_type, source_component, agent_identifier, entry.identifier
        )

        return entry

    def query(self, query: DeadLetterQuery) -> DeadLetterQueryResult:
        """
            Searches the dead letter store.

            :param query: The DeadLetterQuery.

            :returns: A DeadLetterQueryResult.
        """
        return self._store.search(query)

    def get_entry(self, identifier: str) -> Optional[DeadLetterEntry]:
        """
            Retrieves a specific entry by identifier.

            :param identifier: The entry identifier.

            :returns: The DeadLetterEntry or None.
        """
        return self._store.retrieve(identifier)

    def replay(self, identifier: str, callable_op: Callable) -> bool:
        """
            Replays a dead letter entry by invoking the callable with the payload.
            Removes the entry on success, updates metadata on failure.

            :param identifier: The entry identifier.
            :param callable_op: The callable to invoke with the payload.

            :returns: True if replay succeeded, False otherwise.
        """
        entry = self._store.retrieve(identifier)
        if entry is None:
            return False

        try:
            callable_op(entry.payload)
            self._store.delete(identifier)
            return True
        except Exception as exc:
            self._logger.warning(
                "Dead letter replay failed for id='%s': %s", identifier, str(exc)
            )
            return False

    def purge(self) -> None:
        """
            Removes all entries from the dead letter store.
        """
        self._store.purge()
        return

    def __repr__(self) -> str:
        repr_str = "DeadLetterQueue(entry_count={})".format(self.entry_count)
        return repr_str

    def __str__(self) -> str:
        str_val = "DeadLetterQueue: {} entries, store='{}'".format(
            self.entry_count, self._store.store_name
        )
        return str_val
