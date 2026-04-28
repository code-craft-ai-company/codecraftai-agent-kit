"""
    Registry that tracks all available MemoryStore instances within
    a runtime, providing lookup by name and enumeration.
"""

from typing import Optional

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.memorystore import MemoryStore


class MemoryStoreRegistry:
    """
        Registry that tracks all available MemoryStore instances,
        providing lookup by name and enumeration.
    """

    def __init__(self) -> None:
        """
            Constructs a MemoryStoreRegistry with an empty stores dictionary.
        """
        self._stores = {}
        return

    def register(self, store: MemoryStore) -> None:
        """
            Registers a MemoryStore instance using the store name as key.

            :param store: The MemoryStore to register.

            :raises: SemanticError if a store with the same name is already registered.
        """
        name = store.store_name
        if name in self._stores:
            errmsg = "A MemoryStore with name {!r} is already registered.".format(name)
            raise SemanticError(errmsg)

        self._stores[name] = store
        return

    def deregister(self, name: str) -> None:
        """
            Deregisters a MemoryStore by name.

            :param name: The store name to deregister.
        """
        if name in self._stores:
            del self._stores[name]
        return

    def lookup(self, name: str) -> Optional[MemoryStore]:
        """
            Looks up a registered MemoryStore by name.

            :param name: The store name.

            :returns: The MemoryStore instance, or None if not found.
        """
        rtnval = self._stores.get(name)
        return rtnval

    def list_all(self) -> list:
        """
            Returns a list of all registered MemoryStore instances.

            :returns: A list of MemoryStore instances.
        """
        rtnval = list(self._stores.values())
        return rtnval

    @property
    def count(self) -> int:
        """
            The count of currently registered stores.

            :returns: The store count as an integer.
        """
        rtnval = len(self._stores)
        return rtnval

    def has_store(self, name: str) -> bool:
        """
            Returns True if a MemoryStore with the given name is registered.

            :param name: The store name.

            :returns: True if registered, False otherwise.
        """
        rtnval = name in self._stores
        return rtnval

    def clear(self) -> None:
        """
            Removes all registered stores.
        """
        self._stores = {}
        return

    def __repr__(self) -> str:
        rtnval = "{}(count={})".format(self.__class__.__name__, len(self._stores))
        return rtnval

    def __str__(self) -> str:
        names = list(self._stores.keys())
        rtnval = "MemoryStoreRegistry: [{}]".format(", ".join(names))
        return rtnval
