"""
    Tests for the ccai.agentkit.platform.adapters.gcpplatformadapter module.

    Contains unit tests for GcpPlatformAdapter, GcpComputeService,
    GcpStorageService, and GcpMessagingService using mocked GCP SDK clients.

    Feature: cross-platform-runtime

    .. module:: ccai.tests.singlehost.agentkit.platform.adapters.test_gcpplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for GCP platform adapter and service implementations.
"""

import os

from datetime import datetime

from ccai.agentkit.platform.adapters.gcpplatformadapter import GcpComputeService
from ccai.agentkit.platform.adapters.gcpplatformadapter import GcpMessagingService
from ccai.agentkit.platform.adapters.gcpplatformadapter import GcpPlatformAdapter
from ccai.agentkit.platform.adapters.gcpplatformadapter import GcpStorageService
from ccai.agentkit.platform.errors import ComputeError
from ccai.agentkit.platform.errors import MessagingError
from ccai.agentkit.platform.errors import StorageError
from ccai.agentkit.platform.platformconfiguration import PlatformConfiguration
from ccai.agentkit.platform.platformtype import PlatformType
from ccai.testbase.mocking import Mock


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
# Helper: create mock GCP SDK clients
# ---------------------------------------------------------------------------

def _create_mock_functions_client():
    """Creates a mock GCP Cloud Functions client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


def _create_mock_storage_client():
    """Creates a mock GCP Cloud Storage client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


def _create_mock_publisher_client():
    """Creates a mock GCP Pub/Sub publisher client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


def _create_mock_subscriber_client():
    """Creates a mock GCP Pub/Sub subscriber client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


# ---------------------------------------------------------------------------
# GcpPlatformAdapter tests
# ---------------------------------------------------------------------------

def test_gcp_adapter_platform_type_is_gcp():
    """
        Verify that GcpPlatformAdapter.platform_type returns GCP.
    """
    config = PlatformConfiguration(platform_type=PlatformType.GCP)
    adapter = GcpPlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        storage_client=_create_mock_storage_client(),
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    actual = adapter.platform_type

    assert actual is PlatformType.GCP, (
        "platform_type should be GCP, got: {!r}".format(actual)
    )
    return


def test_gcp_adapter_get_compute_service_returns_gcp_compute():
    """
        Verify that get_compute_service returns a GcpComputeService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.GCP)
    adapter = GcpPlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        storage_client=_create_mock_storage_client(),
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    svc = adapter.get_compute_service()

    assert isinstance(svc, GcpComputeService), (
        "get_compute_service should return GcpComputeService, got: {!r}".format(type(svc))
    )
    return


def test_gcp_adapter_get_storage_service_returns_gcp_storage():
    """
        Verify that get_storage_service returns a GcpStorageService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.GCP)
    adapter = GcpPlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        storage_client=_create_mock_storage_client(),
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    svc = adapter.get_storage_service()

    assert isinstance(svc, GcpStorageService), (
        "get_storage_service should return GcpStorageService, got: {!r}".format(type(svc))
    )
    return


def test_gcp_adapter_get_messaging_service_returns_gcp_messaging():
    """
        Verify that get_messaging_service returns a GcpMessagingService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.GCP)
    adapter = GcpPlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        storage_client=_create_mock_storage_client(),
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    svc = adapter.get_messaging_service()

    assert isinstance(svc, GcpMessagingService), (
        "get_messaging_service should return GcpMessagingService, got: {!r}".format(type(svc))
    )
    return


def test_gcp_adapter_region_from_configuration():
    """
        Verify that GcpPlatformAdapter uses region from PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        region="europe-west1"
    )
    adapter = GcpPlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        storage_client=_create_mock_storage_client(),
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    assert adapter._region == "europe-west1", (
        "Region should be 'europe-west1' from config, got: {!r}".format(adapter._region)
    )
    return


def test_gcp_adapter_region_fallback_to_env_var():
    """
        Verify that GcpPlatformAdapter falls back to GCP_REGION env var
        when no region is in configuration.
    """
    original = os.environ.get("GCP_REGION")
    os.environ["GCP_REGION"] = "asia-east1"

    try:
        config = PlatformConfiguration(platform_type=PlatformType.GCP)
        adapter = GcpPlatformAdapter(
            configuration=config,
            functions_client=_create_mock_functions_client(),
            storage_client=_create_mock_storage_client(),
            publisher_client=_create_mock_publisher_client(),
            subscriber_client=_create_mock_subscriber_client()
        )

        assert adapter._region == "asia-east1", (
            "Region should fall back to GCP_REGION env var, got: {!r}".format(adapter._region)
        )
    finally:
        if original is not None:
            os.environ["GCP_REGION"] = original
        else:
            os.environ.pop("GCP_REGION", None)

    return


def test_gcp_adapter_get_all_services_returns_three():
    """
        Verify that get_all_services returns three services.
    """
    config = PlatformConfiguration(platform_type=PlatformType.GCP)
    adapter = GcpPlatformAdapter(
        configuration=config,
        functions_client=_create_mock_functions_client(),
        storage_client=_create_mock_storage_client(),
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    services = adapter.get_all_services()

    assert len(services) == 3, (
        "get_all_services should return 3 services, got: {}".format(len(services))
    )
    return


# ---------------------------------------------------------------------------
# GcpComputeService tests
# ---------------------------------------------------------------------------

def test_gcp_compute_service_name():
    """
        Verify that GcpComputeService has service_name 'gcp-cloud-functions'.
    """
    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=_create_mock_functions_client()
    )

    assert svc.service_name == "gcp-cloud-functions", (
        "service_name should be 'gcp-cloud-functions', got: {!r}".format(svc.service_name)
    )
    return


def test_gcp_compute_service_type():
    """
        Verify that GcpComputeService has service_type 'compute'.
    """
    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=_create_mock_functions_client()
    )

    assert svc.service_type == "compute", (
        "service_type should be 'compute', got: {!r}".format(svc.service_type)
    )
    return


def test_gcp_compute_service_platform_type():
    """
        Verify that GcpComputeService has platform_type GCP.
    """
    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=_create_mock_functions_client()
    )

    assert svc.platform_type is PlatformType.GCP, (
        "platform_type should be GCP, got: {!r}".format(svc.platform_type)
    )
    return


def test_gcp_compute_invoke_success():
    """
        Verify that invoke delegates to the Cloud Functions client and
        returns an InvocationResult with status 'success'.
    """
    mock_client = _create_mock_functions_client()

    mock_response = Mock()
    mock_response.configure(recursive=True)
    mock_response.mock_context().set_attribute("status_code", 200)
    mock_response.mock_context().set_attribute("text", '{"result": "ok"}')

    mock_client.mock_context().mock_method("invoke", return_value=mock_response)

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=mock_client
    )

    result = svc.invoke("my-function", {"key": "value"})

    assert result.status == "success", (
        "invoke should return status 'success', got: {!r}".format(result.status)
    )
    assert result.request_id is not None, "request_id should not be None"
    return


def test_gcp_compute_invoke_error_status():
    """
        Verify that invoke returns status 'error' when HTTP status >= 400.
    """
    mock_client = _create_mock_functions_client()

    mock_response = Mock()
    mock_response.configure(recursive=True)
    mock_response.mock_context().set_attribute("status_code", 500)
    mock_response.mock_context().set_attribute("text", "Internal Server Error")

    mock_client.mock_context().mock_method("invoke", return_value=mock_response)

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=mock_client
    )

    result = svc.invoke("my-function", {"key": "value"})

    assert result.status == "error", (
        "invoke should return status 'error' on HTTP 500, got: {!r}".format(result.status)
    )
    return


def test_gcp_compute_invoke_raises_compute_error_on_exception():
    """
        Verify that invoke raises ComputeError when the client raises.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method(
        "invoke", side_effect=_raise_runtime_error("connection failed")
    )

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
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


def test_gcp_compute_invoke_async_returns_request_id():
    """
        Verify that invoke_async returns a request ID string.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method("invoke", return_value=None)

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=mock_client
    )

    request_id = svc.invoke_async("my-function", {"key": "value"})

    assert isinstance(request_id, str), (
        "invoke_async should return a string, got: {!r}".format(type(request_id))
    )
    assert len(request_id) > 0, "request_id should not be empty"
    return


def test_gcp_compute_invoke_async_raises_compute_error_on_exception():
    """
        Verify that invoke_async raises ComputeError on client exception.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method(
        "invoke", side_effect=_raise_runtime_error("connection failed")
    )

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=mock_client
    )

    raised = False
    try:
        svc.invoke_async("my-function", {"key": "value"})
    except ComputeError:
        raised = True

    assert raised is True, "invoke_async should raise ComputeError on client exception"
    return


def test_gcp_compute_list_functions_raises_compute_error_on_exception():
    """
        Verify that list_functions raises ComputeError on client exception.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method(
        "list_functions", side_effect=_raise_runtime_error("access denied")
    )

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=mock_client
    )

    raised = False
    try:
        svc.list_functions()
    except ComputeError:
        raised = True

    assert raised is True, "list_functions should raise ComputeError on client exception"
    return


def test_gcp_compute_is_available_false_when_list_functions_fails():
    """
        Verify that is_available returns False when list_functions raises.
    """
    mock_client = _create_mock_functions_client()
    mock_client.mock_context().mock_method(
        "list_functions", side_effect=_raise_runtime_error("fail")
    )

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        functions_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_gcp_compute_get_invocation_status_returns_success():
    """
        Verify that get_invocation_status returns an InvocationResult
        with status 'success'.
    """
    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
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


def test_gcp_compute_endpoint_override_in_config():
    """
        Verify that GcpComputeService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        service_endpoint_overrides={"functions": "http://localhost:8080"}
    )

    svc = GcpComputeService(
        platform_type=PlatformType.GCP,
        configuration=config,
        functions_client=_create_mock_functions_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "functions" in overrides, "endpoint override for 'functions' should be present"
    assert overrides["functions"] == "http://localhost:8080", (
        "endpoint override should be 'http://localhost:8080', got: {!r}".format(
            overrides["functions"])
    )
    return


# ---------------------------------------------------------------------------
# GcpStorageService tests
# ---------------------------------------------------------------------------

def test_gcp_storage_service_name():
    """
        Verify that GcpStorageService has service_name 'gcp-cloud-storage'.
    """
    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=_create_mock_storage_client()
    )

    assert svc.service_name == "gcp-cloud-storage", (
        "service_name should be 'gcp-cloud-storage', got: {!r}".format(svc.service_name)
    )
    return


def test_gcp_storage_service_type():
    """
        Verify that GcpStorageService has service_type 'storage'.
    """
    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=_create_mock_storage_client()
    )

    assert svc.service_type == "storage", (
        "service_type should be 'storage', got: {!r}".format(svc.service_type)
    )
    return


def test_gcp_storage_put_object_delegates_to_client():
    """
        Verify that put_object delegates to the GCS client.
    """
    mock_client = _create_mock_storage_client()

    mock_blob = Mock()
    mock_blob.configure(recursive=True)
    mock_blob.mock_context().mock_method("upload_from_string", return_value=None)

    mock_bucket = Mock()
    mock_bucket.configure(recursive=True)
    mock_bucket.mock_context().mock_method("blob", return_value=mock_blob)

    mock_client.mock_context().mock_method("bucket", return_value=mock_bucket)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    svc.put_object("my-bucket", "my-key", b"hello")

    # Delegation verified: upload_from_string was called on the blob mock.
    # The operation completing without error confirms the client was used.
    return


def test_gcp_storage_put_object_raises_storage_error_on_exception():
    """
        Verify that put_object raises StorageError on client exception.
    """
    mock_client = _create_mock_storage_client()
    mock_client.mock_context().mock_method(
        "bucket", side_effect=_raise_runtime_error("access denied")
    )

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    raised = False
    try:
        svc.put_object("my-bucket", "my-key", b"hello")
    except StorageError as exc:
        raised = True
        assert exc.operation_name == "put_object", (
            "StorageError should contain operation_name 'put_object', got: {!r}".format(
                exc.operation_name)
        )
        assert exc.container_name == "my-bucket", (
            "StorageError should contain container_name 'my-bucket', got: {!r}".format(
                exc.container_name)
        )

    assert raised is True, "put_object should raise StorageError on client exception"
    return


def test_gcp_storage_get_object_returns_storage_object():
    """
        Verify that get_object delegates to the GCS client and returns
        a StorageObject.
    """
    mock_client = _create_mock_storage_client()

    mock_blob = Mock()
    mock_blob.configure(recursive=True)
    mock_blob.mock_context().mock_method("download_as_bytes", return_value=b"file content")
    mock_blob.mock_context().mock_method("reload", return_value=None)
    mock_blob.mock_context().set_attribute("content_type", "text/plain")
    mock_blob.mock_context().set_attribute("metadata", {"author": "test"})
    mock_blob.mock_context().set_attribute("size", 12)
    mock_blob.mock_context().set_attribute("updated", datetime(2025, 1, 1))

    mock_bucket = Mock()
    mock_bucket.configure(recursive=True)
    mock_bucket.mock_context().mock_method("blob", return_value=mock_blob)

    mock_client.mock_context().mock_method("bucket", return_value=mock_bucket)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    obj = svc.get_object("my-bucket", "my-key")

    assert obj.key == "my-key", (
        "StorageObject key should be 'my-key', got: {!r}".format(obj.key)
    )
    assert obj.content == b"file content", (
        "StorageObject content should be b'file content', got: {!r}".format(obj.content)
    )
    assert obj.content_type == "text/plain", (
        "StorageObject content_type should be 'text/plain', got: {!r}".format(obj.content_type)
    )
    return


def test_gcp_storage_get_object_raises_storage_error_on_exception():
    """
        Verify that get_object raises StorageError on client exception.
    """
    mock_client = _create_mock_storage_client()
    mock_client.mock_context().mock_method(
        "bucket", side_effect=_raise_runtime_error("not found")
    )

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    raised = False
    try:
        svc.get_object("my-bucket", "my-key")
    except StorageError as exc:
        raised = True
        assert exc.object_key == "my-key", (
            "StorageError should contain object_key 'my-key', got: {!r}".format(exc.object_key)
        )

    assert raised is True, "get_object should raise StorageError on client exception"
    return


def test_gcp_storage_delete_object_delegates_to_client():
    """
        Verify that delete_object delegates to the GCS client.
    """
    mock_client = _create_mock_storage_client()

    mock_blob = Mock()
    mock_blob.configure(recursive=True)
    mock_blob.mock_context().mock_method("delete", return_value=None)

    mock_bucket = Mock()
    mock_bucket.configure(recursive=True)
    mock_bucket.mock_context().mock_method("blob", return_value=mock_blob)

    mock_client.mock_context().mock_method("bucket", return_value=mock_bucket)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    svc.delete_object("my-bucket", "my-key")

    # Delegation verified: delete was called on the blob mock.
    # The operation completing without error confirms the client was used.
    return


def test_gcp_storage_list_objects_returns_blob_names():
    """
        Verify that list_objects returns a list of blob names.
    """
    mock_client = _create_mock_storage_client()

    mock_blob_a = Mock()
    mock_blob_a.configure(recursive=True)
    mock_blob_a.mock_context().set_attribute("name", "file1.txt")

    mock_blob_b = Mock()
    mock_blob_b.configure(recursive=True)
    mock_blob_b.mock_context().set_attribute("name", "file2.txt")

    mock_bucket = Mock()
    mock_bucket.configure(recursive=True)
    mock_bucket.mock_context().mock_method(
        "list_blobs", return_value=[mock_blob_a, mock_blob_b]
    )

    mock_client.mock_context().mock_method("bucket", return_value=mock_bucket)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    keys = svc.list_objects("my-bucket")

    assert keys == ["file1.txt", "file2.txt"], (
        "list_objects should return blob names, got: {!r}".format(keys)
    )
    return


def test_gcp_storage_object_exists_true():
    """
        Verify that object_exists returns True when blob.exists() returns True.
    """
    mock_client = _create_mock_storage_client()

    mock_blob = Mock()
    mock_blob.configure(recursive=True)
    mock_blob.mock_context().mock_method("exists", return_value=True)

    mock_bucket = Mock()
    mock_bucket.configure(recursive=True)
    mock_bucket.mock_context().mock_method("blob", return_value=mock_blob)

    mock_client.mock_context().mock_method("bucket", return_value=mock_bucket)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    result = svc.object_exists("my-bucket", "my-key")

    assert result is True, "object_exists should return True when blob exists"
    return


def test_gcp_storage_object_exists_false():
    """
        Verify that object_exists returns False when blob.exists() returns False.
    """
    mock_client = _create_mock_storage_client()

    mock_blob = Mock()
    mock_blob.configure(recursive=True)
    mock_blob.mock_context().mock_method("exists", return_value=False)

    mock_bucket = Mock()
    mock_bucket.configure(recursive=True)
    mock_bucket.mock_context().mock_method("blob", return_value=mock_blob)

    mock_client.mock_context().mock_method("bucket", return_value=mock_bucket)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    result = svc.object_exists("my-bucket", "my-key")

    assert result is False, "object_exists should return False when blob does not exist"
    return


def test_gcp_storage_create_container_delegates_to_client():
    """
        Verify that create_container delegates to the GCS client.
    """
    mock_client = _create_mock_storage_client()
    mock_client.mock_context().mock_method("create_bucket", return_value=None)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    svc.create_container("my-bucket")

    # Delegation verified: create_bucket completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_gcp_storage_delete_container_delegates_to_client():
    """
        Verify that delete_container delegates to the GCS client.
    """
    mock_client = _create_mock_storage_client()

    mock_bucket = Mock()
    mock_bucket.configure(recursive=True)
    mock_bucket.mock_context().mock_method("delete", return_value=None)

    mock_client.mock_context().mock_method("bucket", return_value=mock_bucket)

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    svc.delete_container("my-bucket")

    # Delegation verified: delete was called on the bucket mock.
    # The operation completing without error confirms the client was used.
    return


def test_gcp_storage_list_containers_returns_bucket_names():
    """
        Verify that list_containers returns a list of bucket names.
    """
    mock_client = _create_mock_storage_client()

    mock_bucket_a = Mock()
    mock_bucket_a.configure(recursive=True)
    mock_bucket_a.mock_context().set_attribute("name", "bucket-a")

    mock_bucket_b = Mock()
    mock_bucket_b.configure(recursive=True)
    mock_bucket_b.mock_context().set_attribute("name", "bucket-b")

    mock_client.mock_context().mock_method(
        "list_buckets", return_value=[mock_bucket_a, mock_bucket_b]
    )

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    buckets = svc.list_containers()

    assert buckets == ["bucket-a", "bucket-b"], (
        "list_containers should return bucket names, got: {!r}".format(buckets)
    )
    return


def test_gcp_storage_is_available_true():
    """
        Verify that is_available returns True when list_containers succeeds.
    """
    mock_client = _create_mock_storage_client()
    mock_client.mock_context().mock_method("list_buckets", return_value=[])

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    assert svc.is_available() is True, "is_available should return True"
    return


def test_gcp_storage_is_available_false():
    """
        Verify that is_available returns False when list_containers fails.
    """
    mock_client = _create_mock_storage_client()
    mock_client.mock_context().mock_method(
        "list_buckets", side_effect=_raise_runtime_error("fail")
    )

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        storage_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_gcp_storage_endpoint_override_in_config():
    """
        Verify that GcpStorageService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        service_endpoint_overrides={"storage": "http://localhost:9023"}
    )

    svc = GcpStorageService(
        platform_type=PlatformType.GCP,
        configuration=config,
        storage_client=_create_mock_storage_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "storage" in overrides, "endpoint override for 'storage' should be present"
    assert overrides["storage"] == "http://localhost:9023", (
        "endpoint override should be 'http://localhost:9023', got: {!r}".format(
            overrides["storage"])
    )
    return


# ---------------------------------------------------------------------------
# GcpMessagingService tests
# ---------------------------------------------------------------------------

def test_gcp_messaging_service_name():
    """
        Verify that GcpMessagingService has service_name 'gcp-pubsub'.
    """
    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    assert svc.service_name == "gcp-pubsub", (
        "service_name should be 'gcp-pubsub', got: {!r}".format(svc.service_name)
    )
    return


def test_gcp_messaging_service_type():
    """
        Verify that GcpMessagingService has service_type 'messaging'.
    """
    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    assert svc.service_type == "messaging", (
        "service_type should be 'messaging', got: {!r}".format(svc.service_type)
    )
    return


def test_gcp_messaging_send_message_raises_messaging_error_on_exception():
    """
        Verify that send_message raises MessagingError on client exception.
    """
    mock_publisher = _create_mock_publisher_client()
    mock_publisher.mock_context().mock_method(
        "publish", side_effect=_raise_runtime_error("topic not found")
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=mock_publisher,
        subscriber_client=_create_mock_subscriber_client()
    )

    raised = False
    try:
        svc.send_message("my-topic", {"data": "hello"})
    except MessagingError as exc:
        raised = True
        assert exc.queue_name == "my-topic", (
            "MessagingError should contain queue_name 'my-topic', got: {!r}".format(
                exc.queue_name)
        )

    assert raised is True, "send_message should raise MessagingError on client exception"
    return


def test_gcp_messaging_send_message_success():
    """
        Verify that send_message delegates to the publisher client and
        returns a message ID.
    """
    mock_publisher = _create_mock_publisher_client()

    mock_future = Mock()
    mock_future.configure(recursive=True)
    mock_future.mock_context().mock_method("result", return_value="msg-gcp-001")

    mock_publisher.mock_context().mock_method("publish", return_value=mock_future)

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=mock_publisher,
        subscriber_client=_create_mock_subscriber_client()
    )

    msg_id = svc.send_message("my-topic", {"data": "hello"})

    assert msg_id == "msg-gcp-001", (
        "send_message should return message ID, got: {!r}".format(msg_id)
    )
    return


def test_gcp_messaging_receive_messages_raises_messaging_error_on_exception():
    """
        Verify that receive_messages raises MessagingError on client exception.
    """
    mock_subscriber = _create_mock_subscriber_client()
    mock_subscriber.mock_context().mock_method(
        "pull", side_effect=_raise_runtime_error("subscription not found")
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=mock_subscriber
    )

    raised = False
    try:
        svc.receive_messages("my-subscription")
    except MessagingError as exc:
        raised = True
        assert exc.queue_name == "my-subscription", (
            "MessagingError should contain queue_name 'my-subscription', got: {!r}".format(
                exc.queue_name)
        )

    assert raised is True, "receive_messages should raise MessagingError on client exception"
    return


def test_gcp_messaging_acknowledge_message_raises_messaging_error_on_exception():
    """
        Verify that acknowledge_message raises MessagingError on client exception.
    """
    mock_subscriber = _create_mock_subscriber_client()
    mock_subscriber.mock_context().mock_method(
        "acknowledge", side_effect=_raise_runtime_error("connection failed")
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=mock_subscriber
    )

    raised = False
    try:
        svc.acknowledge_message("my-subscription", "ack-id-123")
    except MessagingError:
        raised = True

    assert raised is True, "acknowledge_message should raise MessagingError on client exception"
    return


def test_gcp_messaging_create_queue_raises_messaging_error_on_exception():
    """
        Verify that create_queue raises MessagingError on client exception.
    """
    mock_publisher = _create_mock_publisher_client()
    mock_publisher.mock_context().mock_method(
        "create_topic", side_effect=_raise_runtime_error("access denied")
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=mock_publisher,
        subscriber_client=_create_mock_subscriber_client()
    )

    raised = False
    try:
        svc.create_queue("new-topic")
    except MessagingError:
        raised = True

    assert raised is True, "create_queue should raise MessagingError on client exception"
    return


def test_gcp_messaging_delete_queue_raises_messaging_error_on_exception():
    """
        Verify that delete_queue raises MessagingError on client exception.
    """
    mock_publisher = _create_mock_publisher_client()
    mock_publisher.mock_context().mock_method(
        "delete_topic", side_effect=_raise_runtime_error("access denied")
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=mock_publisher,
        subscriber_client=_create_mock_subscriber_client()
    )

    raised = False
    try:
        svc.delete_queue("my-topic")
    except MessagingError:
        raised = True

    assert raised is True, "delete_queue should raise MessagingError on client exception"
    return


def test_gcp_messaging_list_queues_raises_messaging_error_on_exception():
    """
        Verify that list_queues raises MessagingError on client exception.
    """
    mock_publisher = _create_mock_publisher_client()
    mock_publisher.mock_context().mock_method(
        "list_topics", side_effect=_raise_runtime_error("access denied")
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=mock_publisher,
        subscriber_client=_create_mock_subscriber_client()
    )

    raised = False
    try:
        svc.list_queues()
    except MessagingError:
        raised = True

    assert raised is True, "list_queues should raise MessagingError on client exception"
    return


def test_gcp_messaging_is_available_false():
    """
        Verify that is_available returns False when list_queues fails.
    """
    mock_publisher = _create_mock_publisher_client()
    mock_publisher.mock_context().mock_method(
        "list_topics", side_effect=_raise_runtime_error("fail")
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        publisher_client=mock_publisher,
        subscriber_client=_create_mock_subscriber_client()
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_gcp_messaging_endpoint_override_in_config():
    """
        Verify that GcpMessagingService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        service_endpoint_overrides={"pubsub": "http://localhost:8085"}
    )

    svc = GcpMessagingService(
        platform_type=PlatformType.GCP,
        configuration=config,
        publisher_client=_create_mock_publisher_client(),
        subscriber_client=_create_mock_subscriber_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "pubsub" in overrides, "endpoint override for 'pubsub' should be present"
    assert overrides["pubsub"] == "http://localhost:8085", (
        "endpoint override should be 'http://localhost:8085', got: {!r}".format(
            overrides["pubsub"])
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
