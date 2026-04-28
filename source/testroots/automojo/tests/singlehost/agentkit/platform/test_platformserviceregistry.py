"""
    Tests for the automojo.agentkit.platform.platformserviceregistry module.

    Contains unit tests for the PlatformServiceRegistry including registration,
    deregistration, lookup by name and type, duplicate detection, enumeration,
    count property, has_service, and __repr__/__str__ output.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.test_platformserviceregistry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for PlatformServiceRegistry.
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.platform.platformserviceregistry import PlatformServiceRegistry
from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.platformservice import PlatformService


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class StubPlatformService(PlatformService):
    """
        Minimal concrete subclass of PlatformService for testing the
        PlatformServiceRegistry.
    """

    def is_available(self) -> bool:
        rtnval = True
        return rtnval

    def health_check(self) -> bool:
        rtnval = True
        return rtnval


# ---------------------------------------------------------------------------
# Helper factory
# ---------------------------------------------------------------------------

def _create_stub(service_name: str, service_type: str = "compute",
                 platform_type: PlatformType = PlatformType.LOCAL) -> StubPlatformService:
    """
        Creates a StubPlatformService with the given parameters.
    """
    rtnval = StubPlatformService(
        service_name=service_name,
        service_type=service_type,
        platform_type=platform_type
    )
    return rtnval


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

def test_register_and_lookup_by_name():
    """
        Verify that a registered service can be looked up by name.
    """
    registry = PlatformServiceRegistry()
    svc = _create_stub("my-compute")

    registry.register(svc)
    result = registry.lookup_by_name("my-compute")

    assert result is svc, (
        "lookup_by_name should return the registered service, got: {!r}".format(result)
    )
    return


def test_register_multiple_services():
    """
        Verify that multiple services with different names can be registered.
    """
    registry = PlatformServiceRegistry()
    svc_a = _create_stub("svc-a", service_type="compute")
    svc_b = _create_stub("svc-b", service_type="storage")

    registry.register(svc_a)
    registry.register(svc_b)

    assert registry.lookup_by_name("svc-a") is svc_a, "svc-a should be retrievable"
    assert registry.lookup_by_name("svc-b") is svc_b, "svc-b should be retrievable"
    return


def test_register_duplicate_raises_semantic_error():
    """
        Verify that registering a service with a duplicate name raises
        SemanticError.
    """
    registry = PlatformServiceRegistry()
    svc_a = _create_stub("duplicate-name")
    svc_b = _create_stub("duplicate-name")

    registry.register(svc_a)

    caught = False
    try:
        registry.register(svc_b)
    except SemanticError:
        caught = True

    assert caught is True, (
        "Registering a duplicate service name should raise SemanticError"
    )
    return


def test_register_duplicate_error_mentions_service_name():
    """
        Verify that the SemanticError message includes the duplicate
        service name.
    """
    registry = PlatformServiceRegistry()
    svc_a = _create_stub("my-dup")
    svc_b = _create_stub("my-dup")

    registry.register(svc_a)

    error_message = ""
    try:
        registry.register(svc_b)
    except SemanticError as err:
        error_message = str(err)

    has_name = "my-dup" in error_message

    assert has_name is True, (
        "SemanticError message should mention 'my-dup', got: {!r}".format(error_message)
    )
    return


# ---------------------------------------------------------------------------
# Deregistration tests
# ---------------------------------------------------------------------------

def test_deregister_removes_service():
    """
        Verify that deregister removes the service so it is no longer
        found by lookup_by_name.
    """
    registry = PlatformServiceRegistry()
    svc = _create_stub("to-remove")

    registry.register(svc)
    registry.deregister("to-remove")
    result = registry.lookup_by_name("to-remove")

    assert result is None, (
        "lookup_by_name should return None after deregister, got: {!r}".format(result)
    )
    return


def test_deregister_unknown_name_does_nothing():
    """
        Verify that deregistering a name that is not registered does not
        raise an error.
    """
    registry = PlatformServiceRegistry()

    raised = False
    try:
        registry.deregister("nonexistent")
    except Exception:
        raised = True

    assert raised is False, (
        "Deregistering an unknown name should not raise an exception"
    )
    return


def test_deregister_allows_reregistration():
    """
        Verify that after deregistering a service, a new service with
        the same name can be registered.
    """
    registry = PlatformServiceRegistry()
    svc_a = _create_stub("reuse-name", service_type="compute")
    svc_b = _create_stub("reuse-name", service_type="storage")

    registry.register(svc_a)
    registry.deregister("reuse-name")
    registry.register(svc_b)

    result = registry.lookup_by_name("reuse-name")

    assert result is svc_b, (
        "After deregister and re-register, lookup should return the new service"
    )
    return


# ---------------------------------------------------------------------------
# Lookup tests
# ---------------------------------------------------------------------------

def test_lookup_by_name_returns_none_for_unknown():
    """
        Verify that lookup_by_name returns None when the service name
        is not registered.
    """
    registry = PlatformServiceRegistry()

    result = registry.lookup_by_name("unknown-service")

    assert result is None, (
        "lookup_by_name should return None for unknown name, got: {!r}".format(result)
    )
    return


def test_lookup_by_type_returns_matching_services():
    """
        Verify that lookup_by_type returns only services matching the
        given service type.
    """
    registry = PlatformServiceRegistry()
    compute_a = _create_stub("compute-a", service_type="compute")
    compute_b = _create_stub("compute-b", service_type="compute")
    storage_a = _create_stub("storage-a", service_type="storage")

    registry.register(compute_a)
    registry.register(compute_b)
    registry.register(storage_a)

    result = registry.lookup_by_type("compute")

    assert len(result) == 2, (
        "lookup_by_type('compute') should return 2 services, got: {}".format(len(result))
    )
    assert compute_a in result, "compute-a should be in the result"
    assert compute_b in result, "compute-b should be in the result"
    return


def test_lookup_by_type_excludes_non_matching():
    """
        Verify that lookup_by_type does not include services of a
        different type.
    """
    registry = PlatformServiceRegistry()
    compute_svc = _create_stub("compute-svc", service_type="compute")
    storage_svc = _create_stub("storage-svc", service_type="storage")

    registry.register(compute_svc)
    registry.register(storage_svc)

    result = registry.lookup_by_type("storage")

    assert len(result) == 1, (
        "lookup_by_type('storage') should return 1 service, got: {}".format(len(result))
    )
    assert result[0] is storage_svc, "The result should be the storage service"
    return


def test_lookup_by_type_returns_empty_for_no_match():
    """
        Verify that lookup_by_type returns an empty list when no services
        match the given type.
    """
    registry = PlatformServiceRegistry()
    svc = _create_stub("my-svc", service_type="compute")

    registry.register(svc)

    result = registry.lookup_by_type("messaging")

    assert len(result) == 0, (
        "lookup_by_type('messaging') should return empty list, got: {}".format(len(result))
    )
    return


# ---------------------------------------------------------------------------
# list_all tests
# ---------------------------------------------------------------------------

def test_list_all_returns_all_registered_services():
    """
        Verify that list_all returns all registered services.
    """
    registry = PlatformServiceRegistry()
    svc_a = _create_stub("svc-a", service_type="compute")
    svc_b = _create_stub("svc-b", service_type="storage")
    svc_c = _create_stub("svc-c", service_type="messaging")

    registry.register(svc_a)
    registry.register(svc_b)
    registry.register(svc_c)

    result = registry.list_all()

    assert len(result) == 3, (
        "list_all should return 3 services, got: {}".format(len(result))
    )
    assert svc_a in result, "svc-a should be in list_all"
    assert svc_b in result, "svc-b should be in list_all"
    assert svc_c in result, "svc-c should be in list_all"
    return


def test_list_all_returns_empty_when_no_services():
    """
        Verify that list_all returns an empty list when no services
        are registered.
    """
    registry = PlatformServiceRegistry()

    result = registry.list_all()

    assert len(result) == 0, (
        "list_all should return empty list, got: {}".format(len(result))
    )
    return


# ---------------------------------------------------------------------------
# count property tests
# ---------------------------------------------------------------------------

def test_count_returns_zero_for_empty_registry():
    """
        Verify that count returns 0 when no services are registered.
    """
    registry = PlatformServiceRegistry()

    actual = registry.count

    assert actual == 0, (
        "count should be 0 for empty registry, got: {}".format(actual)
    )
    return


def test_count_reflects_registered_services():
    """
        Verify that count returns the number of registered services.
    """
    registry = PlatformServiceRegistry()
    registry.register(_create_stub("svc-1"))
    registry.register(_create_stub("svc-2"))
    registry.register(_create_stub("svc-3"))

    actual = registry.count

    assert actual == 3, (
        "count should be 3, got: {}".format(actual)
    )
    return


def test_count_decreases_after_deregister():
    """
        Verify that count decreases after a service is deregistered.
    """
    registry = PlatformServiceRegistry()
    registry.register(_create_stub("svc-1"))
    registry.register(_create_stub("svc-2"))

    registry.deregister("svc-1")
    actual = registry.count

    assert actual == 1, (
        "count should be 1 after deregister, got: {}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# has_service tests
# ---------------------------------------------------------------------------

def test_has_service_returns_true_for_registered():
    """
        Verify that has_service returns True for a registered service name.
    """
    registry = PlatformServiceRegistry()
    registry.register(_create_stub("present-svc"))

    actual = registry.has_service("present-svc")

    assert actual is True, (
        "has_service should return True for registered name, got: {!r}".format(actual)
    )
    return


def test_has_service_returns_false_for_unregistered():
    """
        Verify that has_service returns False for an unregistered service name.
    """
    registry = PlatformServiceRegistry()

    actual = registry.has_service("absent-svc")

    assert actual is False, (
        "has_service should return False for unregistered name, got: {!r}".format(actual)
    )
    return


def test_has_service_returns_false_after_deregister():
    """
        Verify that has_service returns False after the service is
        deregistered.
    """
    registry = PlatformServiceRegistry()
    registry.register(_create_stub("temp-svc"))

    registry.deregister("temp-svc")
    actual = registry.has_service("temp-svc")

    assert actual is False, (
        "has_service should return False after deregister, got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name_and_count():
    """
        Verify that __repr__ includes the class name and the count of
        registered services.
    """
    registry = PlatformServiceRegistry()
    registry.register(_create_stub("svc-1"))
    registry.register(_create_stub("svc-2"))

    repr_str = repr(registry)

    has_class = "PlatformServiceRegistry" in repr_str
    has_count = "count=2" in repr_str

    assert has_class is True, "repr should contain 'PlatformServiceRegistry'"
    assert has_count is True, "repr should contain 'count=2'"
    return


def test_repr_format_matches_design():
    """
        Verify that __repr__ follows the exact format from the design:
        PlatformServiceRegistry(count=N)
    """
    registry = PlatformServiceRegistry()
    registry.register(_create_stub("svc-1"))

    repr_str = repr(registry)

    expected = "PlatformServiceRegistry(count=1)"
    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_repr_empty_registry():
    """
        Verify that __repr__ shows count=0 for an empty registry.
    """
    registry = PlatformServiceRegistry()

    repr_str = repr(registry)

    expected = "PlatformServiceRegistry(count=0)"
    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_str_lists_service_names_and_types():
    """
        Verify that __str__ lists the registered service names and their
        service types.
    """
    registry = PlatformServiceRegistry()
    registry.register(_create_stub("compute-svc", service_type="compute"))
    registry.register(_create_stub("storage-svc", service_type="storage"))

    str_val = str(registry)

    has_class = "PlatformServiceRegistry" in str_val
    has_compute = "compute-svc(compute)" in str_val
    has_storage = "storage-svc(storage)" in str_val

    assert has_class is True, "str should contain 'PlatformServiceRegistry'"
    assert has_compute is True, "str should contain 'compute-svc(compute)'"
    assert has_storage is True, "str should contain 'storage-svc(storage)'"
    return


def test_str_empty_registry():
    """
        Verify that __str__ shows an empty list for an empty registry.
    """
    registry = PlatformServiceRegistry()

    str_val = str(registry)

    expected = "PlatformServiceRegistry: []"
    assert str_val == expected, (
        "str format mismatch: expected {!r}, got {!r}".format(expected, str_val)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
