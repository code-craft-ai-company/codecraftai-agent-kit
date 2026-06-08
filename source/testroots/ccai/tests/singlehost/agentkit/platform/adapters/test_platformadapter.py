"""
    Tests for the ccai.agentkit.platform.adapters.platformadapter module.

    Contains unit tests for the PlatformAdapter abstract base class including
    ABC enforcement, get_all_services, health_check with mock services,
    and __repr__/__str__ output format.

    Feature: cross-platform-runtime

    .. module:: ccai.tests.singlehost.agentkit.platform.adapters.test_platformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for PlatformAdapter abstract base class.
"""

from ccai.agentkit.platform.adapters.platformadapter import PlatformAdapter
from ccai.agentkit.platform.platformconfiguration import PlatformConfiguration
from ccai.agentkit.platform.platformtype import PlatformType
from ccai.agentkit.platform.services.computeservice import ComputeService
from ccai.agentkit.platform.services.messagingservice import MessagingService
from ccai.agentkit.platform.services.storageservice import StorageService
from ccai.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class StubComputeService(ComputeService):
    """Minimal concrete ComputeService for testing."""

    def __init__(self, healthy=True):
        super().__init__(service_name="stub-compute", platform_type=PlatformType.LOCAL)
        self._healthy = healthy
        return

    def invoke(self, function_name, payload, timeout=None):
        return None

    def invoke_async(self, function_name, payload):
        return ""

    def get_invocation_status(self, request_id):
        return None

    def list_functions(self):
        return []

    def is_available(self):
        return True

    def health_check(self):
        if not self._healthy:
            raise RuntimeError("compute unhealthy")
        return True


class StubStorageService(StorageService):
    """Minimal concrete StorageService for testing."""

    def __init__(self, healthy=True):
        super().__init__(service_name="stub-storage", platform_type=PlatformType.LOCAL)
        self._healthy = healthy
        return

    def put_object(self, container_name, object_key, content, content_type=None, metadata=None):
        return

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

    def is_available(self):
        return True

    def health_check(self):
        if not self._healthy:
            raise RuntimeError("storage unhealthy")
        return True


class StubMessagingService(MessagingService):
    """Minimal concrete MessagingService for testing."""

    def __init__(self, healthy=True):
        super().__init__(service_name="stub-messaging", platform_type=PlatformType.LOCAL)
        self._healthy = healthy
        return

    def send_message(self, queue_name, body, attributes=None):
        return ""

    def receive_messages(self, queue_name, max_count=1, wait_time=None):
        return []

    def acknowledge_message(self, queue_name, receipt_handle):
        return

    def create_queue(self, queue_name):
        return

    def delete_queue(self, queue_name):
        return

    def list_queues(self):
        return []

    def is_available(self):
        return True

    def health_check(self):
        if not self._healthy:
            raise RuntimeError("messaging unhealthy")
        return True


class ConcretePlatformAdapter(PlatformAdapter):
    """Minimal concrete PlatformAdapter for testing."""

    def __init__(self, configuration, compute_healthy=True,
                 storage_healthy=True, messaging_healthy=True):
        super().__init__(configuration=configuration)
        self._compute = StubComputeService(healthy=compute_healthy)
        self._storage = StubStorageService(healthy=storage_healthy)
        self._messaging = StubMessagingService(healthy=messaging_healthy)
        return

    @property
    def platform_type(self):
        rtnval = PlatformType.LOCAL
        return rtnval

    def get_compute_service(self):
        return self._compute

    def get_storage_service(self):
        return self._storage

    def get_messaging_service(self):
        return self._messaging


# ---------------------------------------------------------------------------
# ABC enforcement tests
# ---------------------------------------------------------------------------

def test_platformadapter_cannot_be_instantiated_directly():
    """
        Verify that PlatformAdapter cannot be instantiated directly because
        it is an abstract base class.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)

    raised = False
    try:
        PlatformAdapter(configuration=config)
    except TypeError:
        raised = True

    assert raised is True, (
        "PlatformAdapter should not be instantiable directly (ABC enforcement)"
    )
    return


def test_partial_subclass_missing_platform_type_cannot_be_instantiated():
    """
        Verify that a subclass missing the platform_type property cannot
        be instantiated.
    """

    class PartialAdapter(PlatformAdapter):
        def get_compute_service(self):
            return None
        def get_storage_service(self):
            return None
        def get_messaging_service(self):
            return None

    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)

    raised = False
    try:
        PartialAdapter(configuration=config)
    except TypeError:
        raised = True

    assert raised is True, (
        "Subclass missing platform_type should not be instantiable"
    )
    return


def test_partial_subclass_missing_get_compute_service_cannot_be_instantiated():
    """
        Verify that a subclass missing get_compute_service cannot be
        instantiated.
    """

    class PartialAdapter(PlatformAdapter):
        @property
        def platform_type(self):
            return PlatformType.LOCAL
        def get_storage_service(self):
            return None
        def get_messaging_service(self):
            return None

    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)

    raised = False
    try:
        PartialAdapter(configuration=config)
    except TypeError:
        raised = True

    assert raised is True, (
        "Subclass missing get_compute_service should not be instantiable"
    )
    return


# ---------------------------------------------------------------------------
# get_all_services tests
# ---------------------------------------------------------------------------

def test_get_all_services_returns_three_services():
    """
        Verify that get_all_services returns a list of three services.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(configuration=config)

    services = adapter.get_all_services()

    assert len(services) == 3, (
        "get_all_services should return 3 services, got: {}".format(len(services))
    )
    return


def test_get_all_services_contains_compute_storage_messaging():
    """
        Verify that get_all_services returns compute, storage, and messaging.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(configuration=config)

    services = adapter.get_all_services()
    service_types = [s.service_type for s in services]

    assert "compute" in service_types, "get_all_services should include compute"
    assert "storage" in service_types, "get_all_services should include storage"
    assert "messaging" in service_types, "get_all_services should include messaging"
    return


# ---------------------------------------------------------------------------
# health_check tests
# ---------------------------------------------------------------------------

def test_health_check_all_healthy():
    """
        Verify that health_check returns all True when all services are healthy.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(configuration=config)

    result = adapter.health_check()

    assert result["stub-compute"] is True, "compute should be healthy"
    assert result["stub-storage"] is True, "storage should be healthy"
    assert result["stub-messaging"] is True, "messaging should be healthy"
    return


def test_health_check_unhealthy_service_returns_false():
    """
        Verify that health_check returns False for a service whose
        health_check raises an exception.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(
        configuration=config,
        compute_healthy=False
    )

    result = adapter.health_check()

    assert result["stub-compute"] is False, (
        "compute should be unhealthy, got: {!r}".format(result.get("stub-compute"))
    )
    assert result["stub-storage"] is True, "storage should still be healthy"
    assert result["stub-messaging"] is True, "messaging should still be healthy"
    return


def test_health_check_multiple_unhealthy_services():
    """
        Verify that health_check correctly reports multiple unhealthy services.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(
        configuration=config,
        compute_healthy=False,
        storage_healthy=False
    )

    result = adapter.health_check()

    assert result["stub-compute"] is False, "compute should be unhealthy"
    assert result["stub-storage"] is False, "storage should be unhealthy"
    assert result["stub-messaging"] is True, "messaging should still be healthy"
    return


def test_health_check_returns_dict_with_service_names():
    """
        Verify that health_check returns a dict keyed by service names.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(configuration=config)

    result = adapter.health_check()

    assert isinstance(result, dict), "health_check should return a dict"
    assert "stub-compute" in result, "result should contain stub-compute"
    assert "stub-storage" in result, "result should contain stub-storage"
    assert "stub-messaging" in result, "result should contain stub-messaging"
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name_and_platform_type():
    """
        Verify that __repr__ includes the class name and platform type.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(configuration=config)

    repr_str = repr(adapter)

    assert "ConcretePlatformAdapter" in repr_str, (
        "repr should contain the concrete class name, got: {!r}".format(repr_str)
    )
    assert "local" in repr_str, (
        "repr should contain the platform type, got: {!r}".format(repr_str)
    )
    return


def test_repr_format_matches_design():
    """
        Verify that __repr__ follows the format:
        ClassName(platform_type=X)
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(configuration=config)

    repr_str = repr(adapter)
    expected = "ConcretePlatformAdapter(platform_type=local)"

    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_str_includes_platform_and_service_names():
    """
        Verify that __str__ includes the platform type and service names.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = ConcretePlatformAdapter(configuration=config)

    str_val = str(adapter)

    assert "ConcretePlatformAdapter" in str_val, (
        "str should contain the class name, got: {!r}".format(str_val)
    )
    assert "local" in str_val, (
        "str should contain the platform type, got: {!r}".format(str_val)
    )
    assert "stub-compute" in str_val, (
        "str should contain compute service name, got: {!r}".format(str_val)
    )
    assert "stub-storage" in str_val, (
        "str should contain storage service name, got: {!r}".format(str_val)
    )
    assert "stub-messaging" in str_val, (
        "str should contain messaging service name, got: {!r}".format(str_val)
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
