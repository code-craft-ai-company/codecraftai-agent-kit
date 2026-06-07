"""
    .. module:: ccai.tests.singlehost.agentkit.test_memorystoreregistry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryStoreRegistry class.
"""

import ccai.testbase as testbase

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.inmemorystore import InMemoryStore
from ccai.agentkit.memorystoreregistry import MemoryStoreRegistry


# ---- Helper Functions ----


def _create_store(name: str = "test-store") -> InMemoryStore:
    """
        Creates an InMemoryStore with the given name for testing.

        :param name: The store name.

        :returns: An InMemoryStore instance.
    """
    rtnval = InMemoryStore(store_name=name)
    return rtnval


# ---- Tests ----


def test_memorystoreregistry_construction():
    """
        Verifies that a newly constructed MemoryStoreRegistry has zero
        registered stores.
    """
    registry = MemoryStoreRegistry()

    testbase.assert_equal(registry.count, 0,
        "A new MemoryStoreRegistry should have count 0.")
    return


def test_memorystoreregistry_register():
    """
        Verifies that registering a MemoryStore adds it to the registry
        and increments the count.
    """
    registry = MemoryStoreRegistry()
    store = _create_store("alpha")

    registry.register(store=store)

    testbase.assert_equal(registry.count, 1,
        "Registry count should be 1 after registering one store.")
    testbase.assert_true(registry.has_store("alpha"),
        "Registry should have store 'alpha' after registration.")
    return


def test_memorystoreregistry_register_duplicate_raises_semantic_error():
    """
        Verifies that registering a MemoryStore with a name that is already
        registered raises a SemanticError.
    """
    registry = MemoryStoreRegistry()
    store_a = _create_store("alpha")
    store_b = _create_store("alpha")

    registry.register(store=store_a)

    raised = False
    try:
        registry.register(store=store_b)
    except SemanticError:
        raised = True

    testbase.assert_true(raised,
        "Registering a duplicate store name should raise SemanticError.")
    return


def test_memorystoreregistry_deregister():
    """
        Verifies that deregistering a MemoryStore removes it from the registry.
    """
    registry = MemoryStoreRegistry()
    store = _create_store("alpha")
    registry.register(store=store)

    registry.deregister(name="alpha")

    testbase.assert_equal(registry.count, 0,
        "Registry count should be 0 after deregistering the only store.")
    testbase.assert_false(registry.has_store("alpha"),
        "Registry should not have store 'alpha' after deregistration.")
    return


def test_memorystoreregistry_deregister_unknown_name():
    """
        Verifies that deregistering an unknown name does not raise an error.
    """
    registry = MemoryStoreRegistry()

    registry.deregister(name="nonexistent")

    testbase.assert_equal(registry.count, 0,
        "Registry count should remain 0 after deregistering an unknown name.")
    return


def test_memorystoreregistry_lookup_returns_store():
    """
        Verifies that lookup returns the registered MemoryStore instance.
    """
    registry = MemoryStoreRegistry()
    store = _create_store("alpha")
    registry.register(store=store)

    result = registry.lookup(name="alpha")

    testbase.assert_true(result is store,
        "Lookup should return the same MemoryStore instance that was registered.")
    return


def test_memorystoreregistry_lookup_returns_none_for_unknown():
    """
        Verifies that lookup returns None when the name is not registered.
    """
    registry = MemoryStoreRegistry()

    result = registry.lookup(name="nonexistent")

    testbase.assert_true(result is None,
        "Lookup should return None for an unknown store name.")
    return


def test_memorystoreregistry_list_all():
    """
        Verifies that list_all returns all registered MemoryStore instances.
    """
    registry = MemoryStoreRegistry()
    store_a = _create_store("alpha")
    store_b = _create_store("beta")
    registry.register(store=store_a)
    registry.register(store=store_b)

    result = registry.list_all()

    testbase.assert_equal(len(result), 2,
        "list_all should return 2 stores.")
    testbase.assert_true(store_a in result,
        "list_all should include store 'alpha'.")
    testbase.assert_true(store_b in result,
        "list_all should include store 'beta'.")
    return


def test_memorystoreregistry_list_all_empty():
    """
        Verifies that list_all returns an empty list when no stores are registered.
    """
    registry = MemoryStoreRegistry()

    result = registry.list_all()

    testbase.assert_equal(len(result), 0,
        "list_all should return an empty list for an empty registry.")
    return


def test_memorystoreregistry_count():
    """
        Verifies that the count property reflects the number of registered stores.
    """
    registry = MemoryStoreRegistry()
    testbase.assert_equal(registry.count, 0,
        "Count should be 0 for an empty registry.")

    registry.register(store=_create_store("alpha"))
    testbase.assert_equal(registry.count, 1,
        "Count should be 1 after registering one store.")

    registry.register(store=_create_store("beta"))
    testbase.assert_equal(registry.count, 2,
        "Count should be 2 after registering two stores.")
    return


def test_memorystoreregistry_has_store():
    """
        Verifies that has_store returns True for registered names and False otherwise.
    """
    registry = MemoryStoreRegistry()
    store = _create_store("alpha")
    registry.register(store=store)

    testbase.assert_true(registry.has_store("alpha"),
        "has_store should return True for a registered name.")
    testbase.assert_false(registry.has_store("beta"),
        "has_store should return False for an unregistered name.")
    return


def test_memorystoreregistry_clear():
    """
        Verifies that clear removes all registered stores.
    """
    registry = MemoryStoreRegistry()
    registry.register(store=_create_store("alpha"))
    registry.register(store=_create_store("beta"))
    registry.register(store=_create_store("gamma"))

    registry.clear()

    testbase.assert_equal(registry.count, 0,
        "Count should be 0 after clearing the registry.")
    testbase.assert_false(registry.has_store("alpha"),
        "has_store should return False for 'alpha' after clear.")
    testbase.assert_false(registry.has_store("beta"),
        "has_store should return False for 'beta' after clear.")
    testbase.assert_false(registry.has_store("gamma"),
        "has_store should return False for 'gamma' after clear.")
    return


def test_memorystoreregistry_repr():
    """
        Verifies that __repr__ includes the class name and count.
    """
    registry = MemoryStoreRegistry()
    registry.register(store=_create_store("alpha"))

    result = repr(registry)

    testbase.assert_true("MemoryStoreRegistry" in result,
        "repr should include the class name 'MemoryStoreRegistry'.")
    testbase.assert_true("count=1" in result,
        "repr should include 'count=1' for a registry with one store.")
    return


def test_memorystoreregistry_repr_empty():
    """
        Verifies that __repr__ shows count=0 for an empty registry.
    """
    registry = MemoryStoreRegistry()

    result = repr(registry)

    testbase.assert_true("count=0" in result,
        "repr should include 'count=0' for an empty registry.")
    return


def test_memorystoreregistry_str():
    """
        Verifies that __str__ lists the registered store names.
    """
    registry = MemoryStoreRegistry()
    registry.register(store=_create_store("alpha"))
    registry.register(store=_create_store("beta"))

    result = str(registry)

    testbase.assert_true("MemoryStoreRegistry" in result,
        "str should include 'MemoryStoreRegistry'.")
    testbase.assert_true("alpha" in result,
        "str should include store name 'alpha'.")
    testbase.assert_true("beta" in result,
        "str should include store name 'beta'.")
    return


def test_memorystoreregistry_str_empty():
    """
        Verifies that __str__ shows an empty list for an empty registry.
    """
    registry = MemoryStoreRegistry()

    result = str(registry)

    testbase.assert_true("MemoryStoreRegistry: []" in result,
        "str should show 'MemoryStoreRegistry: []' for an empty registry.")
    return


def test_memorystoreregistry_register_multiple_then_lookup_each():
    """
        Verifies that multiple stores can be registered and each can be
        looked up independently.
    """
    registry = MemoryStoreRegistry()
    store_a = _create_store("alpha")
    store_b = _create_store("beta")
    store_c = _create_store("gamma")

    registry.register(store=store_a)
    registry.register(store=store_b)
    registry.register(store=store_c)

    testbase.assert_true(registry.lookup("alpha") is store_a,
        "Lookup 'alpha' should return store_a.")
    testbase.assert_true(registry.lookup("beta") is store_b,
        "Lookup 'beta' should return store_b.")
    testbase.assert_true(registry.lookup("gamma") is store_c,
        "Lookup 'gamma' should return store_c.")
    return


def test_memorystoreregistry_deregister_then_register_same_name():
    """
        Verifies that after deregistering a store, a new store with the
        same name can be registered.
    """
    registry = MemoryStoreRegistry()
    store_a = _create_store("alpha")
    store_b = _create_store("alpha")

    registry.register(store=store_a)
    registry.deregister(name="alpha")
    registry.register(store=store_b)

    result = registry.lookup(name="alpha")
    testbase.assert_true(result is store_b,
        "After deregister and re-register, lookup should return the new store.")
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
