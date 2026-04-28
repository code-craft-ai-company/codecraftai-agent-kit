"""
    Tests for the automojo.agentkit.platform.services.storageservice module.

    Contains unit tests for the StorageService abstract base class including
    ABC enforcement, service_type fixed to "storage", property access via
    a minimal concrete subclass, and __repr__/__str__ output format.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.services.test_storageservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for StorageService abstract base class.
"""

from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.platformservice import PlatformService
from automojo.agentkit.platform.services.storageservice import StorageService


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class ConcreteStorageService(StorageService):
    """
        Minimal concrete subclass of StorageService for testing purposes.
    """

    def is_available(self) -> bool:
        rtnval = True
        return rtnval

    def health_check(self) -> bool:
        rtnval = True
        return rtnval

    def put_object(self, container_name, object_key, content,
                   content_type=None, metadata=None):
        return

    def get_object(self, container_name, object_key):
        return None

    def delete_object(self, container_name, object_key):
        return

    def list_objects(self, container_name, prefix=None):
        rtnval = []
        return rtnval

    def object_exists(self, container_name, object_key):
        rtnval = False
        return rtnval

    def create_container(self, container_name):
        return

    def delete_container(self, container_name):
        return

    def list_containers(self):
        rtnval = []
        return rtnval


# ---------------------------------------------------------------------------
# ABC enforcement tests
# ---------------------------------------------------------------------------

def test_storageservice_cannot_be_instantiated_directly():
    """
        Verify that StorageService cannot be instantiated directly because
        it is an abstract base class.
    """
    raised = False
    try:
        StorageService(
            service_name="test",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "StorageService should not be instantiable directly (ABC enforcement)"
    )
    return


def test_partial_subclass_missing_put_object_cannot_be_instantiated():
    """
        Verify that a subclass missing the put_object method cannot be
        instantiated.
    """

    class PartialStorage(StorageService):
        def is_available(self):
            return True

        def health_check(self):
            return True

        def get_object(self, container_name, object_key):
            return None

        def delete_object(self, container_name, object_key):
            return

        def list_objects(self, container_name, prefix=None):
            return []

        def object_exists(self, container_name, object_key):
            return False

        def create_container(self, container_name):
            return

        def delete_container(self, container_name):
            return

        def list_containers(self):
            return []

    raised = False
    try:
        PartialStorage(
            service_name="test",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "Subclass missing put_object should not be instantiable"
    )
    return


# ---------------------------------------------------------------------------
# Inheritance and service_type tests
# ---------------------------------------------------------------------------

def test_storageservice_inherits_from_platformservice():
    """
        Verify that StorageService is a subclass of PlatformService.
    """
    svc = ConcreteStorageService(
        service_name="storage-svc",
        platform_type=PlatformType.AWS
    )

    is_platform_service = isinstance(svc, PlatformService)

    assert is_platform_service is True, (
        "StorageService should inherit from PlatformService"
    )
    return


def test_service_type_is_storage():
    """
        Verify that StorageService sets service_type to "storage".
    """
    svc = ConcreteStorageService(
        service_name="storage-svc",
        platform_type=PlatformType.AWS
    )

    actual = svc.service_type

    assert actual == "storage", (
        "service_type should be 'storage', got: {!r}".format(actual)
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
    svc = ConcreteStorageService(
        service_name="my-storage",
        platform_type=PlatformType.AZURE
    )

    actual = svc.service_name

    assert actual == "my-storage", (
        "service_name should be 'my-storage', got: {!r}".format(actual)
    )
    return


def test_platform_type_property():
    """
        Verify that the platform_type property returns the PlatformType
        passed at construction.
    """
    svc = ConcreteStorageService(
        service_name="my-storage",
        platform_type=PlatformType.GCP
    )

    actual = svc.platform_type

    assert actual is PlatformType.GCP, (
        "platform_type should be PlatformType.GCP, got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name_service_name_platform():
    """
        Verify that __repr__ includes the class name, service name,
        and platform type.
    """
    svc = ConcreteStorageService(
        service_name="s3-svc",
        platform_type=PlatformType.AWS
    )

    repr_str = repr(svc)

    has_class = "ConcreteStorageService" in repr_str
    has_name = "s3-svc" in repr_str
    has_platform = "aws" in repr_str

    assert has_class is True, "repr should contain the concrete class name"
    assert has_name is True, "repr should contain the service name"
    assert has_platform is True, "repr should contain the platform type"
    return


def test_repr_format_matches_design():
    """
        Verify that __repr__ follows the exact format from the design:
        ClassName(service_name=X, platform_type=Y)
    """
    svc = ConcreteStorageService(
        service_name="my-storage",
        platform_type=PlatformType.LOCAL
    )

    repr_str = repr(svc)

    expected = "ConcreteStorageService(service_name=my-storage, platform_type=local)"
    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_str_format_matches_design():
    """
        Verify that __str__ follows the exact format from the design:
        ClassName: name=X, platform=Y
    """
    svc = ConcreteStorageService(
        service_name="my-storage",
        platform_type=PlatformType.LOCAL
    )

    str_val = str(svc)

    expected = "ConcreteStorageService: name=my-storage, platform=local"
    assert str_val == expected, (
        "str format mismatch: expected {!r}, got {!r}".format(expected, str_val)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
