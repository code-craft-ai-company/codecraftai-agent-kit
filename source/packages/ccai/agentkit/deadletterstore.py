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
        ...

    @abc.abstractmethod
    def retrieve(self, identifier: str) -> Optional[DeadLetterEntry]:
        ...

    @abc.abstractmethod
    def search(self, query: DeadLetterQuery) -> DeadLetterQueryResult:
        ...

    @abc.abstractmethod
    def delete(self, identifier: str) -> None:
        ...

    @abc.abstractmethod
    def purge(self) -> None:
        ...

    @abc.abstractmethod
    def count(self) -> int:
        ...

    def __repr__(self) -> str:
        repr_str = "{}(store_name={!r})".format(self.__class__.__name__, self._store_name)
        return repr_str

    def __str__(self) -> str:
        str_val = "{} store_name='{}'".format(self.__class__.__name__, self._store_name)
        return str_val
