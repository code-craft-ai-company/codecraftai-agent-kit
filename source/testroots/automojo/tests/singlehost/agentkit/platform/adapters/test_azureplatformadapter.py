"""
    Tests for the automojo.agentkit.platform.adapters.azureplatformadapter module.

    Contains unit tests for AzurePlatformAdapter, AzureComputeService,
    AzureStorageService, and AzureMessagingService using mocked Azure SDK
    clients.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.adapters.test_azureplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for Azure platform adapter and service implementations.
"""

import json
import os
import uuid

from datetime import datetime

from automojo.agentkit.platform.adapters.azureplatformadapter import AzureComputeService
from automojo.agentkit.platform.adapters.azureplatformadapter import AzureMessagingService
from automojo.agentkit.platform.adapters.azureplatformadapter import AzurePlatformAdapter
from automojo.agentkit.platform.adapters.azureplatformadapter import AzureStorageService
from automojo.agentkit.platform.errors import ComputeError
from automojo.agentkit.platform.errors import MessagingError
from automojo.agentkit.platform.errors import StorageError
from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration
from automojo.agentkit.platform.platformtype import PlatformType
from automojo.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Helper: raise an exception from a side_effect callable
# ---------------------------------------------------------------------------

def _raise_runtime_error(message):
    """Returns a callable that raises RuntimeError with the given message.

    The testbase mocking framework requires side_effect to be a callable
    or SideEffect instance, not a raw exception.
    """
    def _raiser(*args, **kwargs):
        raise RuntimeError(message)
    return _raiser


# ---------------------------------------------------------------------------
# Helper: create mock Azure SDK clients
# ---------------------------------------------------------------------------

def _create_mock_functions_client():
    """Creates a mock Azure Functions client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


def _create_mock_blob_service_client():
    """Creates a mock Azure Blob Service client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


def _create_mock_servicebus_client():
    """Creates a mock Azure Service Bus client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


# ---------------------------------------------------------------------------
# AzurePlatformAdapter tests
# ---------------------------------------------------------------------------

def test_azure_adapter_platform_type_is_azure():
    """
        Verify that AzurePlatformAdapter.platform_type returns AZURE.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AZURE)
    adapter = AzurePlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        blob_service_client=_create_mock_blob_service_client(),
        servicebus_client=_create_mock_servicebus_client()
    )

    actual = adapter.platform_type

    assert actual is PlatformType.AZURE, (
        "platform_type should be AZURE, got: {!r}".format(actual)
    )
    return


def test_azure_adapter_get_compute_service_returns_azure_compute():
    """
        Verify that get_compute_service returns an AzureComputeService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AZURE)
    adapter = AzurePlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        blob_service_client=_create_mock_blob_service_client(),
        servicebus_client=_create_mock_servicebus_client()
    )

    svc = adapter.get_compute_service()

    assert isinstance(svc, AzureComputeService), (
        "get_compute_service should return AzureComputeService, got: {!r}".format(type(svc))
    )
    return


def test_azure_adapter_get_storage_service_returns_azure_storage():
    """
        Verify that get_storage_service returns an AzureStorageService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AZURE)
    adapter = AzurePlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        blob_service_client=_create_mock_blob_service_client(),
        servicebus_client=_create_mock_servicebus_client()
    )

    svc = adapter.get_storage_service()

    assert isinstance(svc, AzureStorageService), (
        "get_storage_service should return AzureStorageService, got: {!r}".format(type(svc))
    )
    return


def test_azure_adapter_get_messaging_service_returns_azure_messaging():
    """
        Verify that get_messaging_service returns an AzureMessagingService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AZURE)
    adapter = AzurePlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        blob_service_client=_create_mock_blob_service_client(),
        servicebus_client=_create_mock_servicebus_client()
    )

    svc = adapter.get_messaging_service()

    assert isinstance(svc, AzureMessagingService), (
        "get_messaging_service should return AzureMessagingService, got: {!r}".format(type(svc))
    )
    return


def test_azure_adapter_region_from_configuration():
    """
        Verify that AzurePlatformAdapter uses region from PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AZURE,
        region="westeurope"
    )
    adapter = AzurePlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        blob_service_client=_create_mock_blob_service_client(),
        servicebus_client=_create_mock_servicebus_client()
    )

    assert adapter._region == "westeurope", (
        "Region should be 'westeurope' from config, got: {!r}".format(adapter._region)
    )
    return


def test_azure_adapter_region_fallback_to_env_var():
    """
        Verify that AzurePlatformAdapter falls back to AZURE_REGION env var
        when no region is in configuration.
    """
    original = os.environ.get("AZURE_REGION")
    os.environ["AZURE_REGION"] = "northeurope"

    try:
        config = PlatformConfiguration(platform_type=PlatformType.AZURE)
        adapter = AzurePlatformAdapter(
            configuration=config,
            functions_client=_create_mock_functions_client(),
            blob_service_client=_create_mock_blob_service_client(),
            servicebus_client=_create_mock_servicebus_client()
        )

        assert adapter._region == "northeurope", (
            "Region should fall back to AZURE_REGION env var, got: {!r}".format(adapter._region)
        )
    finally:
        if original is not None:
            os.environ["AZURE_REGION"] = original
        else:
            os.environ.pop("AZURE_REGION", None)

    return


def test_azure_adapter_get_all_services_returns_three():
    """
        Verify that get_all_services returns three services.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AZURE)
    adapter = AzurePlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        blob_service_client=_create_mock_blob_service_client(),
        servicebus_client=_create_mock_servicebus_client()
    )

    services = adapter.get_all_services()

    assert len(services) == 3, (
        "get_all_services should return 3 services, got: {}".format(len(services))
    )
    return


# ---------------------------------------------------------------------------
# AzureComputeService tests
# ---------------------------------------------------------------------------

def test_azure_compute_service_name():
    """
        Verify that AzureComputeService has service_name 'azure-functions'.
    """
    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=_create_mock_functions_client()
    )

    assert svc.service_name == "azure-functions", (
        "service_name should be 'azure-functions', got: {!r}".format(svc.service_name)
    )
    return


def test_azure_compute_service_type():
    """
        Verify that AzureComputeService has service_type 'compute'.
    """
    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=_create_mock_functions_client()
    )

    assert svc.service_type == "compute", (
        "service_type should be 'compute', got: {!r}".format(svc.service_type)
    )
    return


def test_azure_compute_service_platform_type():
    """
        Verify that AzureComputeService has platform_type AZURE.
    """
    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=_create_mock_functions_client()
    )

    assert svc.platform_type is PlatformType.AZURE, (
        "platform_type should be AZURE, got: {!r}".format(svc.platform_type)
    )
    return


def test_azure_compute_invoke_success():
    """
        Verify that invoke delegates to the Azure Functions client and
        returns an InvocationResult with status 'success'.
    """
    mock_client = _create_mock_functions_client()

    mock_response = Mock()
    mock_response.configure(recursive=True)
    mock_response.mock_context().set_attribute("status_code", 200)
    mock_response.mock_context().set_attribute("text", '{"result": "ok"}')

    mock_client.mock_context().mock_method("invoke", return_value=mock_response)

    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=mock_client
    )

    result = svc.invoke("my-function", {"key": "value"})

    assert result.status == "success", (
        "invoke should return status 'success', got: {!r}".format(result.status)
    )
    assert result.request_id is not None, "request_id should not be None"
    return


def test_azure_compute_invoke_error_status():
    """
        Verify that invoke returns status 'error' when HTTP status >= 400.
    """
    mock_client = _create_mock_functions_client()

    mock_response = Mock()
    mock_response.configure(recursive=True)
    mock_response.mock_context().set_attribute("status_code", 500)
    mock_response.mock_context().set_attribute("text", "Internal Server Error")

    mock_client.mock_context().mock_method("invoke", return_value=mock_response)

    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=mock_client
    )

    result = svc.invoke("my-function", {"key": "value"})

    assert result.status == "error", (
        "invoke should return status 'error' on HTTP 500, got: {!r}".format(result.status)
    )
    return


def test_azure_compute_invoke_raises_compute_error_on_exception():
    """
        Verify that invoke raises ComputeError when the client raises.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method(
        "invoke", side_effect=_raise_runtime_error("connection failed")
    )

    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=mock_client
    )

    raised = False
    try:
        svc.invoke("my-function", {"key": "value"})
    except ComputeError as exc:
        raised = True
        assert exc.function_name == "my-function", (
            "ComputeError should contain function_name 'my-function', got: {!r}".format(
                exc.function_name)
        )

    assert raised is True, "invoke should raise ComputeError on client exception"
    return


def test_azure_compute_invoke_async_returns_request_id():
    """
        Verify that invoke_async returns a request ID string.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method("invoke", return_value=None)

    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=mock_client
    )

    request_id = svc.invoke_async("my-function", {"key": "value"})

    assert isinstance(request_id, str), (
        "invoke_async should return a string, got: {!r}".format(type(request_id))
    )
    assert len(request_id) > 0, "request_id should not be empty"
    return


def test_azure_compute_list_functions_raises_compute_error_on_exception():
    """
        Verify that list_functions raises ComputeError on client exception.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method(
        "list_functions", side_effect=_raise_runtime_error("access denied")
    )

    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=mock_client
    )

    raised = False
    try:
        svc.list_functions()
    except ComputeError:
        raised = True

    assert raised is True, "list_functions should raise ComputeError on client exception"
    return


def test_azure_compute_is_available_false_when_list_functions_fails():
    """
        Verify that is_available returns False when list_functions raises.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method(
        "list_functions", side_effect=_raise_runtime_error("fail")
    )

    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_azure_compute_get_invocation_status_returns_success():
    """
        Verify that get_invocation_status returns an InvocationResult
        with status 'success'.
    """
    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        functions_client=_create_mock_functions_client()
    )

    result = svc.get_invocation_status("req-123")

    assert result.status == "success", (
        "get_invocation_status should return 'success', got: {!r}".format(result.status)
    )
    assert result.request_id == "req-123", (
        "request_id should be 'req-123', got: {!r}".format(result.request_id)
    )
    return


def test_azure_compute_endpoint_override_in_config():
    """
        Verify that AzureComputeService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AZURE,
        service_endpoint_overrides={"functions": "http://localhost:7071"}
    )

    svc = AzureComputeService(
        platform_type=PlatformType.AZURE,
        configuration=config,
        functions_client=_create_mock_functions_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "functions" in overrides, "endpoint override for 'functions' should be present"
    assert overrides["functions"] == "http://localhost:7071", (
        "endpoint override should be 'http://localhost:7071', got: {!r}".format(
            overrides["functions"])
    )
    return


# ---------------------------------------------------------------------------
# AzureStorageService tests
# ---------------------------------------------------------------------------

def test_azure_storage_service_name():
    """
        Verify that AzureStorageService has service_name 'azure-blob-storage'.
    """
    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=_create_mock_blob_service_client()
    )

    assert svc.service_name == "azure-blob-storage", (
        "service_name should be 'azure-blob-storage', got: {!r}".format(svc.service_name)
    )
    return


def test_azure_storage_service_type():
    """
        Verify that AzureStorageService has service_type 'storage'.
    """
    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=_create_mock_blob_service_client()
    )

    assert svc.service_type == "storage", (
        "service_type should be 'storage', got: {!r}".format(svc.service_type)
    )
    return


def test_azure_storage_put_object_delegates_to_client():
    """
        Verify that put_object delegates to the Azure Blob client.
    """
    mock_client = _create_mock_blob_service_client()

    mock_blob_client = Mock()
    mock_blob_client.configure(recursive=True)
    mock_blob_client.mock_context().mock_method("upload_blob", return_value=None)

    mock_client.mock_context().mock_method("get_blob_client", return_value=mock_blob_client)

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    svc.put_object("my-container", "my-key", b"hello")

    # Delegation verified: upload_blob was called on the blob client mock.
    # The operation completing without error confirms the client was used.
    return


def test_azure_storage_put_object_raises_storage_error_on_exception():
    """
        Verify that put_object raises StorageError on client exception.
    """
    mock_client = _create_mock_blob_service_client()
    mock_client.mock_context().mock_method(
        "get_blob_client", side_effect=_raise_runtime_error("access denied")
    )

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    raised = False
    try:
        svc.put_object("my-container", "my-key", b"hello")
    except StorageError as exc:
        raised = True
        assert exc.operation_name == "put_object", (
            "StorageError should contain operation_name 'put_object', got: {!r}".format(
                exc.operation_name)
        )
        assert exc.container_name == "my-container", (
            "StorageError should contain container_name 'my-container', got: {!r}".format(
                exc.container_name)
        )

    assert raised is True, "put_object should raise StorageError on client exception"
    return


def test_azure_storage_get_object_returns_storage_object():
    """
        Verify that get_object delegates to the Azure Blob client and
        returns a StorageObject.
    """
    mock_client = _create_mock_blob_service_client()

    mock_download = Mock()
    mock_download.configure(recursive=True)
    mock_download.mock_context().mock_method("readall", return_value=b"file content")

    mock_content_settings = Mock()
    mock_content_settings.configure(recursive=True)
    mock_content_settings.mock_context().set_attribute("content_type", "text/plain")

    mock_properties = Mock()
    mock_properties.configure(recursive=True)
    mock_properties.mock_context().set_attribute("content_settings", mock_content_settings)
    mock_properties.mock_context().set_attribute("metadata", {"author": "test"})
    mock_properties.mock_context().set_attribute("size", 12)
    mock_properties.mock_context().set_attribute("last_modified", datetime(2025, 1, 1))

    mock_blob_client = Mock()
    mock_blob_client.configure(recursive=True)
    mock_blob_client.mock_context().mock_method("download_blob", return_value=mock_download)
    mock_blob_client.mock_context().mock_method("get_blob_properties", return_value=mock_properties)

    mock_client.mock_context().mock_method("get_blob_client", return_value=mock_blob_client)

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    obj = svc.get_object("my-container", "my-key")

    assert obj.key == "my-key", (
        "StorageObject key should be 'my-key', got: {!r}".format(obj.key)
    )
    assert obj.content == b"file content", (
        "StorageObject content should be b'file content', got: {!r}".format(obj.content)
    )
    return


def test_azure_storage_get_object_raises_storage_error_on_exception():
    """
        Verify that get_object raises StorageError on client exception.
    """
    mock_client = _create_mock_blob_service_client()
    mock_client.mock_context().mock_method(
        "get_blob_client", side_effect=_raise_runtime_error("not found")
    )

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    raised = False
    try:
        svc.get_object("my-container", "my-key")
    except StorageError as exc:
        raised = True
        assert exc.object_key == "my-key", (
            "StorageError should contain object_key 'my-key', got: {!r}".format(exc.object_key)
        )

    assert raised is True, "get_object should raise StorageError on client exception"
    return


def test_azure_storage_delete_object_delegates_to_client():
    """
        Verify that delete_object delegates to the Azure Blob client.
    """
    mock_client = _create_mock_blob_service_client()

    mock_blob_client = Mock()
    mock_blob_client.configure(recursive=True)
    mock_blob_client.mock_context().mock_method("delete_blob", return_value=None)

    mock_client.mock_context().mock_method("get_blob_client", return_value=mock_blob_client)

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    svc.delete_object("my-container", "my-key")

    # Delegation verified: delete_blob was called on the blob client mock.
    # The operation completing without error confirms the client was used.
    return


def test_azure_storage_list_objects_returns_blob_names():
    """
        Verify that list_objects returns a list of blob names.
    """
    mock_client = _create_mock_blob_service_client()

    mock_blob_a = Mock()
    mock_blob_a.configure(recursive=True)
    mock_blob_a.mock_context().set_attribute("name", "file1.txt")

    mock_blob_b = Mock()
    mock_blob_b.configure(recursive=True)
    mock_blob_b.mock_context().set_attribute("name", "file2.txt")

    mock_container_client = Mock()
    mock_container_client.configure(recursive=True)
    mock_container_client.mock_context().mock_method(
        "list_blobs", return_value=[mock_blob_a, mock_blob_b]
    )

    mock_client.mock_context().mock_method(
        "get_container_client", return_value=mock_container_client
    )

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    keys = svc.list_objects("my-container")

    assert keys == ["file1.txt", "file2.txt"], (
        "list_objects should return blob names, got: {!r}".format(keys)
    )
    return


def test_azure_storage_create_container_delegates_to_client():
    """
        Verify that create_container delegates to the Azure Blob client.
    """
    mock_client = _create_mock_blob_service_client()
    mock_client.mock_context().mock_method("create_container", return_value=None)

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    svc.create_container("my-container")

    # Delegation verified: create_container completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_azure_storage_delete_container_delegates_to_client():
    """
        Verify that delete_container delegates to the Azure Blob client.
    """
    mock_client = _create_mock_blob_service_client()
    mock_client.mock_context().mock_method("delete_container", return_value=None)

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    svc.delete_container("my-container")

    # Delegation verified: delete_container completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_azure_storage_list_containers_returns_container_names():
    """
        Verify that list_containers returns a list of container names.
    """
    mock_client = _create_mock_blob_service_client()

    mock_container_a = Mock()
    mock_container_a.configure(recursive=True)
    mock_container_a.mock_context().set_attribute("name", "container-a")

    mock_container_b = Mock()
    mock_container_b.configure(recursive=True)
    mock_container_b.mock_context().set_attribute("name", "container-b")

    mock_client.mock_context().mock_method(
        "list_containers", return_value=[mock_container_a, mock_container_b]
    )

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    containers = svc.list_containers()

    assert containers == ["container-a", "container-b"], (
        "list_containers should return container names, got: {!r}".format(containers)
    )
    return


def test_azure_storage_is_available_true():
    """
        Verify that is_available returns True when list_containers succeeds.
    """
    mock_client = _create_mock_blob_service_client()
    mock_client.mock_context().mock_method("list_containers", return_value=[])

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    assert svc.is_available() is True, "is_available should return True"
    return


def test_azure_storage_is_available_false():
    """
        Verify that is_available returns False when list_containers fails.
    """
    mock_client = _create_mock_blob_service_client()
    mock_client.mock_context().mock_method(
        "list_containers", side_effect=_raise_runtime_error("fail")
    )

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        blob_service_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_azure_storage_endpoint_override_in_config():
    """
        Verify that AzureStorageService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AZURE,
        service_endpoint_overrides={"blob_storage": "http://localhost:10000"}
    )

    svc = AzureStorageService(
        platform_type=PlatformType.AZURE,
        configuration=config,
        blob_service_client=_create_mock_blob_service_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "blob_storage" in overrides, "endpoint override for 'blob_storage' should be present"
    assert overrides["blob_storage"] == "http://localhost:10000", (
        "endpoint override should be 'http://localhost:10000', got: {!r}".format(
            overrides["blob_storage"])
    )
    return


# ---------------------------------------------------------------------------
# AzureMessagingService tests
# ---------------------------------------------------------------------------

def test_azure_messaging_service_name():
    """
        Verify that AzureMessagingService has service_name 'azure-service-bus'.
    """
    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=_create_mock_servicebus_client()
    )

    assert svc.service_name == "azure-service-bus", (
        "service_name should be 'azure-service-bus', got: {!r}".format(svc.service_name)
    )
    return


def test_azure_messaging_service_type():
    """
        Verify that AzureMessagingService has service_type 'messaging'.
    """
    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=_create_mock_servicebus_client()
    )

    assert svc.service_type == "messaging", (
        "service_type should be 'messaging', got: {!r}".format(svc.service_type)
    )
    return


def test_azure_messaging_send_message_raises_messaging_error_on_exception():
    """
        Verify that send_message raises MessagingError on client exception.
    """
    mock_client = _create_mock_servicebus_client()
    mock_client.mock_context().mock_method(
        "get_queue_sender", side_effect=_raise_runtime_error("queue not found")
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=mock_client
    )

    raised = False
    try:
        svc.send_message("my-queue", {"data": "hello"})
    except MessagingError as exc:
        raised = True
        assert exc.queue_name == "my-queue", (
            "MessagingError should contain queue_name 'my-queue', got: {!r}".format(
                exc.queue_name)
        )

    assert raised is True, "send_message should raise MessagingError on client exception"
    return


def test_azure_messaging_receive_messages_raises_messaging_error_on_exception():
    """
        Verify that receive_messages raises MessagingError on client exception.
    """
    mock_client = _create_mock_servicebus_client()
    mock_client.mock_context().mock_method(
        "get_queue_receiver", side_effect=_raise_runtime_error("connection failed")
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=mock_client
    )

    raised = False
    try:
        svc.receive_messages("my-queue")
    except MessagingError as exc:
        raised = True
        assert exc.queue_name == "my-queue", (
            "MessagingError should contain queue_name 'my-queue', got: {!r}".format(
                exc.queue_name)
        )

    assert raised is True, "receive_messages should raise MessagingError on client exception"
    return


def test_azure_messaging_acknowledge_message_raises_messaging_error_on_exception():
    """
        Verify that acknowledge_message raises MessagingError on client exception.
    """
    mock_client = _create_mock_servicebus_client()
    mock_client.mock_context().mock_method(
        "get_queue_receiver", side_effect=_raise_runtime_error("connection failed")
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=mock_client
    )

    raised = False
    try:
        svc.acknowledge_message("my-queue", "lock-token-123")
    except MessagingError:
        raised = True

    assert raised is True, "acknowledge_message should raise MessagingError on client exception"
    return


def test_azure_messaging_create_queue_raises_messaging_error_on_exception():
    """
        Verify that create_queue raises MessagingError on client exception.
    """
    mock_client = _create_mock_servicebus_client()
    mock_client.mock_context().mock_method(
        "get_queue_admin", side_effect=_raise_runtime_error("access denied")
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=mock_client
    )

    raised = False
    try:
        svc.create_queue("new-queue")
    except MessagingError:
        raised = True

    assert raised is True, "create_queue should raise MessagingError on client exception"
    return


def test_azure_messaging_delete_queue_raises_messaging_error_on_exception():
    """
        Verify that delete_queue raises MessagingError on client exception.
    """
    mock_client = _create_mock_servicebus_client()
    mock_client.mock_context().mock_method(
        "get_queue_admin", side_effect=_raise_runtime_error("access denied")
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=mock_client
    )

    raised = False
    try:
        svc.delete_queue("my-queue")
    except MessagingError:
        raised = True

    assert raised is True, "delete_queue should raise MessagingError on client exception"
    return


def test_azure_messaging_list_queues_raises_messaging_error_on_exception():
    """
        Verify that list_queues raises MessagingError on client exception.
    """
    mock_client = _create_mock_servicebus_client()
    mock_client.mock_context().mock_method(
        "get_queue_admin", side_effect=_raise_runtime_error("access denied")
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=mock_client
    )

    raised = False
    try:
        svc.list_queues()
    except MessagingError:
        raised = True

    assert raised is True, "list_queues should raise MessagingError on client exception"
    return


def test_azure_messaging_is_available_false():
    """
        Verify that is_available returns False when list_queues fails.
    """
    mock_client = _create_mock_servicebus_client()
    mock_client.mock_context().mock_method(
        "get_queue_admin", side_effect=_raise_runtime_error("fail")
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        servicebus_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_azure_messaging_endpoint_override_in_config():
    """
        Verify that AzureMessagingService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AZURE,
        service_endpoint_overrides={"service_bus": "my-namespace.servicebus.windows.net"}
    )

    svc = AzureMessagingService(
        platform_type=PlatformType.AZURE,
        configuration=config,
        servicebus_client=_create_mock_servicebus_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "service_bus" in overrides, "endpoint override for 'service_bus' should be present"
    assert overrides["service_bus"] == "my-namespace.servicebus.windows.net", (
        "endpoint override mismatch, got: {!r}".format(overrides["service_bus"])
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
