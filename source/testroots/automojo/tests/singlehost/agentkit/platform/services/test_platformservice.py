"""
    Tests for the automojo.agentkit.platform.services.platformservice module.

    Contains unit tests for the PlatformService abstract base class including
    ABC enforcement, property access via a minimal concrete subclass, and
    __repr__/__str__ output format.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.services.test_platformservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for PlatformService abstract base class.
"""

from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.platformservice import PlatformService


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class ConcretePlatformService(PlatformService):
    """
        Minimal concrete subclass of PlatformService for testing purposes.
    """

    def is_available(self) -> bool:
        rtnval = True
        return rtnval

    def health_check(self) -> bool:
        rtnval = True
        return rtnval


# ---------------------------------------------------------------------------
# ABC enforcement tests
# ---------------------------------------------------------------------------

def test_platformservice_cannot_be_instantiated_directly():
    """
        Verify that PlatformService cannot be instantiated directly because
        it is an abstract base class.
    """
    raised = False
    try:
        PlatformService(
            service_name="test",
            service_type="compute",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "PlatformService should not be instantiable directly (ABC enforcement)"
    )
    return


def test_partial_subclass_missing_health_check_cannot_be_instantiated():
    """
        Verify that a subclass missing the health_check method cannot be
        instantiated.
    """

    class PartialService(PlatformService):
        def is_available(self) -> bool:
            return True

    raised = False
    try:
        PartialService(
            service_name="test",
            service_type="compute",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "Subclass missing health_check should not be instantiable"
    )
    return


def test_partial_subclass_missing_is_available_cannot_be_instantiated():
    """
        Verify that a subclass missing the is_available method cannot be
        instantiated.
    """

    class PartialService(PlatformService):
        def health_check(self) -> bool:
            return True

    raised = False
    try:
        PartialService(
            service_name="test",
            service_type="compute",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "Subclass missing is_available should not be instantiable"
    )
    return


# ---------------------------------------------------------------------------
# Property tests via concrete subclass
# ---------------------------------------------------------------------------

def test_service_name_property():
    """
        Verify that the service_name property returns the value passed
        at construction.
    """
    svc = ConcretePlatformService(
        service_name="my-service",
        service_type="compute",
        platform_type=PlatformType.AWS
    )

    actual = svc.service_name

    assert actual == "my-service", (
        "service_name should be 'my-service', got: {!r}".format(actual)
    )
    return


def test_service_type_property():
    """
        Verify that the service_type property returns the value passed
        at construction.
    """
    svc = ConcretePlatformService(
        service_name="my-service",
        service_type="storage",
        platform_type=PlatformType.AZURE
    )

    actual = svc.service_type

    assert actual == "storage", (
        "service_type should be 'storage', got: {!r}".format(actual)
    )
    return


def test_platform_type_property():
    """
        Verify that the platform_type property returns the PlatformType
        passed at construction.
    """
    svc = ConcretePlatformService(
        service_name="my-service",
        service_type="messaging",
        platform_type=PlatformType.GCP
    )

    actual = svc.platform_type

    assert actual is PlatformType.GCP, (
        "platform_type should be PlatformType.GCP, got: {!r}".format(actual)
    )
    return


def test_configuration_defaults_to_none():
    """
        Verify that the configuration defaults to None when not provided.
    """
    svc = ConcretePlatformService(
        service_name="my-service",
        service_type="compute",
        platform_type=PlatformType.LOCAL
    )

    actual = svc._configuration

    assert actual is None, (
        "configuration should default to None, got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name_service_name_type_platform():
    """
        Verify that __repr__ includes the class name, service name,
        service type, and platform type.
    """
    svc = ConcretePlatformService(
        service_name="test-svc",
        service_type="compute",
        platform_type=PlatformType.AWS
    )

    repr_str = repr(svc)

    has_class = "ConcretePlatformService" in repr_str
    has_name = "test-svc" in repr_str
    has_type = "compute" in repr_str
    has_platform = "aws" in repr_str

    assert has_class is True, "repr should contain the concrete class name"
    assert has_name is True, "repr should contain the service name"
    assert has_type is True, "repr should contain the service type"
    assert has_platform is True, "repr should contain the platform type"
    return


def test_str_includes_class_name_service_name_type_platform():
    """
        Verify that __str__ includes the class name, service name,
        service type, and platform type.
    """
    svc = ConcretePlatformService(
        service_name="test-svc",
        service_type="storage",
        platform_type=PlatformType.AZURE
    )

    str_val = str(svc)

    has_class = "ConcretePlatformService" in str_val
    has_name = "test-svc" in str_val
    has_type = "storage" in str_val
    has_platform = "azure" in str_val

    assert has_class is True, "str should contain the concrete class name"
    assert has_name is True, "str should contain the service name"
    assert has_type is True, "str should contain the service type"
    assert has_platform is True, "str should contain the platform type"
    return


def test_repr_format_matches_design():
    """
        Verify that __repr__ follows the exact format from the design:
        ClassName(service_name=X, service_type=Y, platform_type=Z)
    """
    svc = ConcretePlatformService(
        service_name="my-svc",
        service_type="compute",
        platform_type=PlatformType.LOCAL
    )

    repr_str = repr(svc)

    expected = "ConcretePlatformService(service_name=my-svc, service_type=compute, platform_type=local)"
    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_str_format_matches_design():
    """
        Verify that __str__ follows the exact format from the design:
        ClassName: name=X, type=Y, platform=Z
    """
    svc = ConcretePlatformService(
        service_name="my-svc",
        service_type="compute",
        platform_type=PlatformType.LOCAL
    )

    str_val = str(svc)

    expected = "ConcretePlatformService: name=my-svc, type=compute, platform=local"
    assert str_val == expected, (
        "str format mismatch: expected {!r}, got {!r}".format(expected, str_val)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
