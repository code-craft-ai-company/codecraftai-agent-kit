"""
    Tests for the automojo.agentkit.platform.platformruntime module.

    Contains unit tests for PlatformRuntime including construction with mock
    configuration and adapter, service registration, delegation to adapter
    for compute/storage/messaging, registry-based service lookup, health check
    delegation, create_auto with no/full/partial config, extension point
    integration, plugin load failure handling, and __repr__/__str__ output.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.test_platformruntime
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for PlatformRuntime.
"""

import logging
import os
import sys

from automojo.agentkit.platform.adapters.localplatformadapter import LocalPlatformAdapter
from automojo.agentkit.platform.adapters.platformadapter import PlatformAdapter
from automojo.agentkit.platform.errors import PlatformError
from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration
from automojo.agentkit.platform.platformruntime import PlatformRuntime
from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.computeservice import ComputeService
from automojo.agentkit.platform.services.messagingservice import MessagingService
from automojo.agentkit.platform.services.storageservice import StorageService
from automojo.testbase.mocking import Mock, create_module_patch


# ---------------------------------------------------------------------------
# Minimal concrete service stubs for testing
# ---------------------------------------------------------------------------

class StubComputeService(ComputeService):
    """Minimal concrete ComputeService for testing."""

    def __init__(self, service_name="stub-compute",
                 platform_type=PlatformType.LOCAL):
        super().__init__(service_name=service_name, platform_type=platform_type)
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
        return True


class StubStorageService(StorageService):
    """Minimal concrete StorageService for testing."""

    def __init__(self, service_name="stub-storage",
                 platform_type=PlatformType.LOCAL):
        super().__init__(service_name=service_name, platform_type=platform_type)
        return

    def put_object(self, container_name, object_key, content,
                   content_type=None, metadata=None):
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
        return True


class StubMessagingService(MessagingService):
    """Minimal concrete MessagingService for testing."""

    def __init__(self, service_name="stub-messaging",
                 platform_type=PlatformType.LOCAL):
        super().__init__(service_name=service_name, platform_type=platform_type)
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
        return True


class StubPlatformAdapter(PlatformAdapter):
    """Minimal concrete PlatformAdapter for testing PlatformRuntime."""

    def __init__(self, configuration, compute_svc=None, storage_svc=None,
                 messaging_svc=None):
        super().__init__(configuration=configuration)
        self._compute = compute_svc if compute_svc is not None else StubComputeService()
        self._storage = storage_svc if storage_svc is not None else StubStorageService()
        self._messaging = messaging_svc if messaging_svc is not None else StubMessagingService()
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
# Env var helpers (reused from test_platformdetector.py)
# ---------------------------------------------------------------------------

ALL_CLOUD_ENV_VARS = [
    "AWS_LAMBDA_FUNCTION_NAME", "AWS_EXECUTION_ENV", "AWS_REGION",
    "AZURE_FUNCTIONS_ENVIRONMENT", "WEBSITE_SITE_NAME", "AZURE_REGION",
    "GOOGLE_CLOUD_PROJECT", "FUNCTION_NAME", "GCP_REGION",
]


def _save_env_vars():
    """Saves the current values of all cloud env vars."""
    saved = {}
    for var_name in ALL_CLOUD_ENV_VARS:
        saved[var_name] = os.environ.get(var_name)
    return saved


def _restore_env_vars(saved):
    """Restores env vars to their saved values."""
    for var_name, value in saved.items():
        if value is not None:
            os.environ[var_name] = value
        elif var_name in os.environ:
            del os.environ[var_name]
    return


def _clear_all_cloud_env_vars():
    """Removes all cloud env vars from the environment."""
    for var_name in ALL_CLOUD_ENV_VARS:
        if var_name in os.environ:
            del os.environ[var_name]
    return



# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------

def test_construction_with_mock_configuration_and_adapter():
    """
        Verify that PlatformRuntime can be constructed with a
        PlatformConfiguration and a PlatformAdapter.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)

    assert runtime is not None, "PlatformRuntime should be constructed"
    assert runtime.configuration is config, (
        "configuration property should return the provided config"
    )
    assert runtime.adapter is adapter, (
        "adapter property should return the provided adapter"
    )
    return


def test_platform_type_returns_configuration_platform_type():
    """
        Verify that platform_type property returns the platform type
        from the configuration.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AWS)
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)

    assert runtime.platform_type is PlatformType.AWS, (
        "platform_type should return PlatformType.AWS, got: {!r}".format(
            runtime.platform_type)
    )
    return


# ---------------------------------------------------------------------------
# Service registration tests
# ---------------------------------------------------------------------------

def test_services_registered_in_registry_during_init():
    """
        Verify that all adapter services are registered in the
        PlatformServiceRegistry during construction.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    compute = StubComputeService(service_name="test-compute")
    storage = StubStorageService(service_name="test-storage")
    messaging = StubMessagingService(service_name="test-messaging")
    adapter = StubPlatformAdapter(
        configuration=config,
        compute_svc=compute,
        storage_svc=storage,
        messaging_svc=messaging
    )

    runtime = PlatformRuntime(configuration=config, adapter=adapter)

    found_compute = runtime.get_service("test-compute")
    found_storage = runtime.get_service("test-storage")
    found_messaging = runtime.get_service("test-messaging")

    assert found_compute is compute, (
        "Registry should contain the compute service"
    )
    assert found_storage is storage, (
        "Registry should contain the storage service"
    )
    assert found_messaging is messaging, (
        "Registry should contain the messaging service"
    )
    return


# ---------------------------------------------------------------------------
# Delegation tests: get_compute_service, get_storage_service,
# get_messaging_service
# ---------------------------------------------------------------------------

def test_get_compute_service_delegates_to_adapter():
    """
        Verify that get_compute_service returns the adapter compute service.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    compute = StubComputeService(service_name="my-compute")
    adapter = StubPlatformAdapter(configuration=config, compute_svc=compute)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    result = runtime.get_compute_service()

    assert result is compute, (
        "get_compute_service should delegate to adapter, got: {!r}".format(result)
    )
    return


def test_get_storage_service_delegates_to_adapter():
    """
        Verify that get_storage_service returns the adapter storage service.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    storage = StubStorageService(service_name="my-storage")
    adapter = StubPlatformAdapter(configuration=config, storage_svc=storage)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    result = runtime.get_storage_service()

    assert result is storage, (
        "get_storage_service should delegate to adapter, got: {!r}".format(result)
    )
    return


def test_get_messaging_service_delegates_to_adapter():
    """
        Verify that get_messaging_service returns the adapter messaging service.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    messaging = StubMessagingService(service_name="my-messaging")
    adapter = StubPlatformAdapter(configuration=config, messaging_svc=messaging)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    result = runtime.get_messaging_service()

    assert result is messaging, (
        "get_messaging_service should delegate to adapter, got: {!r}".format(result)
    )
    return


# ---------------------------------------------------------------------------
# get_service delegation tests
# ---------------------------------------------------------------------------

def test_get_service_delegates_to_registry():
    """
        Verify that get_service looks up a service by name from the registry.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    compute = StubComputeService(service_name="registry-compute")
    adapter = StubPlatformAdapter(configuration=config, compute_svc=compute)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    result = runtime.get_service("registry-compute")

    assert result is compute, (
        "get_service should return the service from the registry"
    )
    return


def test_get_service_returns_none_for_unknown_name():
    """
        Verify that get_service returns None for an unregistered service name.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    result = runtime.get_service("nonexistent-service")

    assert result is None, (
        "get_service should return None for unknown name, got: {!r}".format(result)
    )
    return


# ---------------------------------------------------------------------------
# health_check delegation tests
# ---------------------------------------------------------------------------

def test_health_check_delegates_to_adapter():
    """
        Verify that health_check delegates to the adapter and returns
        the adapter health check result.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    result = runtime.health_check()

    assert isinstance(result, dict), (
        "health_check should return a dict, got: {!r}".format(type(result))
    )
    assert "stub-compute" in result, "result should contain stub-compute"
    assert "stub-storage" in result, "result should contain stub-storage"
    assert "stub-messaging" in result, "result should contain stub-messaging"
    assert result["stub-compute"] is True, "stub-compute should be healthy"
    assert result["stub-storage"] is True, "stub-storage should be healthy"
    assert result["stub-messaging"] is True, "stub-messaging should be healthy"
    return


# ---------------------------------------------------------------------------
# create_auto tests
# ---------------------------------------------------------------------------

def test_create_auto_no_config_detects_local():
    """
        Verify that create_auto with no configuration detects LOCAL and
        creates a LocalPlatformAdapter.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    try:
        runtime = PlatformRuntime.create_auto()

        assert runtime.platform_type is PlatformType.LOCAL, (
            "create_auto with no config should detect LOCAL, got: {!r}".format(
                runtime.platform_type)
        )
        assert isinstance(runtime.adapter, LocalPlatformAdapter), (
            "create_auto should create a LocalPlatformAdapter, got: {!r}".format(
                type(runtime.adapter))
        )
    finally:
        _restore_env_vars(saved)

    return


def test_create_auto_with_full_config_uses_provided_platform_type():
    """
        Verify that create_auto with a full PlatformConfiguration uses
        the provided platform type.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    try:
        config = PlatformConfiguration(
            platform_type=PlatformType.LOCAL,
            region="us-west-2"
        )

        runtime = PlatformRuntime.create_auto(configuration=config)

        assert runtime.platform_type is PlatformType.LOCAL, (
            "create_auto should use the provided platform type"
        )
        assert runtime.configuration.region == "us-west-2", (
            "create_auto should preserve the provided region"
        )
    finally:
        _restore_env_vars(saved)

    return


def test_create_auto_with_partial_config_merges_with_env_defaults():
    """
        Verify that create_auto with a partial PlatformConfiguration
        (platform_type=None) merges the detected platform type with
        the provided settings.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    try:
        partial_config = PlatformConfiguration(
            platform_type=None,
            region="eu-west-1",
            options={"custom_key": "custom_value"}
        )

        runtime = PlatformRuntime.create_auto(configuration=partial_config)

        assert runtime.platform_type is PlatformType.LOCAL, (
            "create_auto should detect LOCAL for partial config, got: {!r}".format(
                runtime.platform_type)
        )
        assert runtime.configuration.region == "eu-west-1", (
            "create_auto should preserve the partial config region"
        )
        assert runtime.configuration.options.get("custom_key") == "custom_value", (
            "create_auto should preserve the partial config options"
        )
    finally:
        _restore_env_vars(saved)

    return


def test_create_auto_raises_platform_error_on_failure():
    """
        Verify that create_auto raises PlatformError when auto-configuration
        fails due to an unexpected error.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    # Set conflicting cloud env vars to trigger PlatformDetectionError
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "my-function"
    os.environ["AZURE_FUNCTIONS_ENVIRONMENT"] = "Production"

    try:
        caught = False
        try:
            PlatformRuntime.create_auto()
        except PlatformError:
            caught = True

        assert caught is True, (
            "create_auto should raise PlatformError on detection conflict"
        )
    finally:
        _restore_env_vars(saved)

    return


# ---------------------------------------------------------------------------
# Extension point integration tests
# ---------------------------------------------------------------------------

def test_extension_point_plugin_adapter_used_when_available():
    """
        Verify that create_auto uses a plugin adapter from the extension
        point when one matches the detected platform type.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    # Create a real plugin adapter that matches LOCAL
    plugin_config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    mock_plugin_adapter = StubPlatformAdapter(configuration=plugin_config)

    # Create an adapter entry class that has platform_type and returns
    # the mock plugin adapter when called
    class PluginAdapterEntry:
        platform_type = PlatformType.LOCAL
        def __call__(self, **kwargs):
            return mock_plugin_adapter

    plugin_entry = PluginAdapterEntry()

    # Create a mock ExtensionPoint
    mock_extension_point = Mock()
    mock_extension_point.configure(recursive=True)
    mock_extension_point.mock_context().mock_method(
        "query", return_value=[plugin_entry]
    )

    # Create a mock ExtensionPoint class that returns our mock instance
    mock_ep_class = Mock()
    mock_ep_class.configure(return_value=mock_extension_point)

    # Inject the mock extension module into sys.modules
    mock_extension_module = Mock()
    mock_extension_module.configure(recursive=True)
    mock_extension_module.mock_context().set_attribute(
        "ExtensionPoint", mock_ep_class
    )

    sys.modules["automojo.extension"] = mock_extension_module

    try:
        runtime = PlatformRuntime.create_auto()

        assert runtime.adapter is mock_plugin_adapter, (
            "create_auto should use the plugin adapter from the extension point"
        )
    finally:
        _restore_env_vars(saved)
        if "automojo.extension" in sys.modules:
            del sys.modules["automojo.extension"]

    return


def test_plugin_load_failure_logged_and_remaining_plugins_continue():
    """
        Verify that when a plugin adapter fails to load, the failure is
        logged at WARNING level and remaining plugins continue loading.
        Falls back to built-in adapter when no plugin succeeds.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    # Create a failing adapter entry class that has platform_type matching
    # LOCAL but raises when instantiated via __call__
    class FailingAdapterEntry:
        platform_type = PlatformType.LOCAL
        def __call__(self, **kwargs):
            raise RuntimeError("plugin load failed")
        def __str__(self):
            return "FailingAdapterEntry"

    failing_entry = FailingAdapterEntry()

    # Create a mock ExtensionPoint that returns the failing entry
    mock_extension_point = Mock()
    mock_extension_point.configure(recursive=True)
    mock_extension_point.mock_context().mock_method(
        "query", return_value=[failing_entry]
    )

    mock_ep_class = Mock()
    mock_ep_class.configure(return_value=mock_extension_point)

    mock_extension_module = Mock()
    mock_extension_module.configure(recursive=True)
    mock_extension_module.mock_context().set_attribute(
        "ExtensionPoint", mock_ep_class
    )

    sys.modules["automojo.extension"] = mock_extension_module

    # Set up a log handler to capture WARNING messages
    test_logger = logging.getLogger("automojo.agentkit.platform")
    captured_records = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            captured_records.append(record)

    handler = CaptureHandler()
    handler.setLevel(logging.WARNING)
    test_logger.addHandler(handler)

    try:
        runtime = PlatformRuntime.create_auto()

        # Should fall back to built-in LocalPlatformAdapter
        assert isinstance(runtime.adapter, LocalPlatformAdapter), (
            "Should fall back to LocalPlatformAdapter when plugin fails, "
            "got: {!r}".format(type(runtime.adapter))
        )

        # Verify WARNING was logged about the plugin failure
        warning_messages = [
            r.getMessage() for r in captured_records
            if r.levelno == logging.WARNING
        ]
        has_plugin_warning = any(
            "Failed to load" in msg or "plugin" in msg.lower()
            for msg in warning_messages
        )
        assert has_plugin_warning is True, (
            "A WARNING log about plugin load failure should have been emitted, "
            "captured warnings: {!r}".format(warning_messages)
        )
    finally:
        test_logger.removeHandler(handler)
        _restore_env_vars(saved)
        if "automojo.extension" in sys.modules:
            del sys.modules["automojo.extension"]

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name_and_platform_type():
    """
        Verify that __repr__ includes the class name and platform type.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    repr_str = repr(runtime)

    assert "PlatformRuntime" in repr_str, (
        "repr should contain 'PlatformRuntime', got: {!r}".format(repr_str)
    )
    assert "local" in repr_str, (
        "repr should contain the platform type 'local', got: {!r}".format(repr_str)
    )
    return


def test_repr_format_matches_design():
    """
        Verify that __repr__ follows the format:
        PlatformRuntime(platform_type=X)
    """
    config = PlatformConfiguration(platform_type=PlatformType.AWS)
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    repr_str = repr(runtime)

    expected = "PlatformRuntime(platform_type=aws)"
    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_str_includes_platform_region_and_service_count():
    """
        Verify that __str__ includes the platform type, region, and
        service count.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.LOCAL, region="us-east-1"
    )
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    str_val = str(runtime)

    assert "PlatformRuntime" in str_val, (
        "str should contain 'PlatformRuntime', got: {!r}".format(str_val)
    )
    assert "local" in str_val, (
        "str should contain the platform type, got: {!r}".format(str_val)
    )
    assert "us-east-1" in str_val, (
        "str should contain the region, got: {!r}".format(str_val)
    )
    assert "3" in str_val, (
        "str should contain the service count '3', got: {!r}".format(str_val)
    )
    return


def test_str_shows_none_region_when_not_configured():
    """
        Verify that __str__ shows None for region when not configured.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = StubPlatformAdapter(configuration=config)

    runtime = PlatformRuntime(configuration=config, adapter=adapter)
    str_val = str(runtime)

    assert "None" in str_val, (
        "str should contain 'None' for unconfigured region, got: {!r}".format(str_val)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
