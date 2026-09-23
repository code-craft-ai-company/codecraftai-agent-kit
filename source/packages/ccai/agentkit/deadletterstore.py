"""
    Defines the DeadLetterStore abstract base class for persisting
    DeadLetterEntry objects.
"""

import abc

from typing import Optional

from ccai.agentkit.deadletterentry import DeadLetterEntry
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.deadletterquery import DeadLetterQueryResult


class DeadLetterStore(abc.ABC):
    """
        Abstract base class for persisting DeadLetterEntry objects.

        :param store_name: The name of the store.
    """

    def __init__(self, store_name: str) -> None:
        self._store_name = store_name
        return

    @property
    def store_name(self) -> str:
        return self._store_name

    @abc.abstractmethod
    def store(self, entry: DeadLetterEntry) -> None:
        """
            Persists a dead letter entry in the store.

            :param entry: The dead letter entry to persist.
        """

    @abc.abstractmethod
    def retrieve(self, identifier: str) -> Optional[DeadLetterEntry]:
        """
            Retrieves the dead letter entry with the specified identifier.

            :param identifier: The identifier of the entry to retrieve.

            :returns: The matching entry, or None if no entry has the identifier.
        """

    @abc.abstractmethod
    def search(self, query: DeadLetterQuery) -> DeadLetterQueryResult:
        """
            Searches the store for dead letter entries matching a query.

            :param query: The query describing the entries to match.

            :returns: The query result containing the matching entries.
        """

    @abc.abstractmethod
    def delete(self, identifier: str) -> None:
        """
            Deletes the dead letter entry with the specified identifier.

            :param identifier: The identifier of the entry to delete.
        """

    @abc.abstractmethod
    def purge(self) -> None:
        """
            Removes all dead letter entries from the store.
        """

    @abc.abstractmethod
    def count(self) -> int:
        """
            Returns the number of dead letter entries in the store.

            :returns: The number of stored entries.
        """

    def __repr__(self) -> str:
        repr_str = "{}(store_name={!r})".format(self.__class__.__name__, self._store_name)
        return repr_str

    def __str__(self) -> str:
        str_val = "{} store_name='{}'".format(self.__class__.__name__, self._store_name)
        return str_val
