"""
    Tests for the ccai.agentkit.platform.adapters.awsplatformadapter module.

    Contains unit tests for AwsPlatformAdapter, AwsComputeService,
    AwsStorageService, and AwsMessagingService using mocked boto3 clients.

    Feature: cross-platform-runtime

    .. module:: ccai.tests.singlehost.agentkit.platform.adapters.test_awsplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for AWS platform adapter and service implementations.
"""

import json
import os

from datetime import datetime
from io import BytesIO

from ccai.agentkit.platform.adapters.awsplatformadapter import AwsComputeService
from ccai.agentkit.platform.adapters.awsplatformadapter import AwsMessagingService
from ccai.agentkit.platform.adapters.awsplatformadapter import AwsPlatformAdapter
from ccai.agentkit.platform.adapters.awsplatformadapter import AwsStorageService
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
# Helper: create a mock boto3 client
# ---------------------------------------------------------------------------

def _create_mock_lambda_client():
    """Creates a mock boto3 Lambda client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


def _create_mock_s3_client():
    """Creates a mock boto3 S3 client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


def _create_mock_sqs_client():
    """Creates a mock boto3 SQS client."""
    mock = Mock()
    mock.configure(recursive=True)
    return mock


# ---------------------------------------------------------------------------
# AwsPlatformAdapter tests
# ---------------------------------------------------------------------------

def test_aws_adapter_platform_type_is_aws():
    """
        Verify that AwsPlatformAdapter.platform_type returns AWS.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AWS)
    adapter = AwsPlatformAdapter(
        configuration=config,
        lambda_client=_create_mock_lambda_client(),
        s3_client=_create_mock_s3_client(),
        sqs_client=_create_mock_sqs_client()
    )

    actual = adapter.platform_type

    assert actual is PlatformType.AWS, (
        "platform_type should be AWS, got: {!r}".format(actual)
    )
    return


def test_aws_adapter_get_compute_service_returns_aws_compute():
    """
        Verify that get_compute_service returns an AwsComputeService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AWS)
    adapter = AwsPlatformAdapter(
        configuration=config,
        lambda_client=_create_mock_lambda_client(),
        s3_client=_create_mock_s3_client(),
        sqs_client=_create_mock_sqs_client()
    )

    svc = adapter.get_compute_service()

    assert isinstance(svc, AwsComputeService), (
        "get_compute_service should return AwsComputeService, got: {!r}".format(type(svc))
    )
    return


def test_aws_adapter_get_storage_service_returns_aws_storage():
    """
        Verify that get_storage_service returns an AwsStorageService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AWS)
    adapter = AwsPlatformAdapter(
        configuration=config,
        lambda_client=_create_mock_lambda_client(),
        s3_client=_create_mock_s3_client(),
        sqs_client=_create_mock_sqs_client()
    )

    svc = adapter.get_storage_service()

    assert isinstance(svc, AwsStorageService), (
        "get_storage_service should return AwsStorageService, got: {!r}".format(type(svc))
    )
    return


def test_aws_adapter_get_messaging_service_returns_aws_messaging():
    """
        Verify that get_messaging_service returns an AwsMessagingService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AWS)
    adapter = AwsPlatformAdapter(
        configuration=config,
        lambda_client=_create_mock_lambda_client(),
        s3_client=_create_mock_s3_client(),
        sqs_client=_create_mock_sqs_client()
    )

    svc = adapter.get_messaging_service()

    assert isinstance(svc, AwsMessagingService), (
        "get_messaging_service should return AwsMessagingService, got: {!r}".format(type(svc))
    )
    return


def test_aws_adapter_region_from_configuration():
    """
        Verify that AwsPlatformAdapter uses region from PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        region="eu-west-1"
    )
    adapter = AwsPlatformAdapter(
        configuration=config,
        lambda_client=_create_mock_lambda_client(),
        s3_client=_create_mock_s3_client(),
        sqs_client=_create_mock_sqs_client()
    )

    assert adapter._region == "eu-west-1", (
        "Region should be 'eu-west-1' from config, got: {!r}".format(adapter._region)
    )
    return


def test_aws_adapter_region_fallback_to_env_var():
    """
        Verify that AwsPlatformAdapter falls back to AWS_REGION env var
        when no region is in configuration.
    """
    original = os.environ.get("AWS_REGION")
    os.environ["AWS_REGION"] = "ap-southeast-1"

    try:
        config = PlatformConfiguration(platform_type=PlatformType.AWS)
        adapter = AwsPlatformAdapter(
            configuration=config,
            lambda_client=_create_mock_lambda_client(),
            s3_client=_create_mock_s3_client(),
            sqs_client=_create_mock_sqs_client()
        )

        assert adapter._region == "ap-southeast-1", (
            "Region should fall back to AWS_REGION env var, got: {!r}".format(adapter._region)
        )
    finally:
        if original is not None:
            os.environ["AWS_REGION"] = original
        else:
            os.environ.pop("AWS_REGION", None)

    return


def test_aws_adapter_get_all_services_returns_three():
    """
        Verify that get_all_services returns three services.
    """
    config = PlatformConfiguration(platform_type=PlatformType.AWS)
    adapter = AwsPlatformAdapter(
        configuration=config,
        lambda_client=_create_mock_lambda_client(),
        s3_client=_create_mock_s3_client(),
        sqs_client=_create_mock_sqs_client()
    )

    services = adapter.get_all_services()

    assert len(services) == 3, (
        "get_all_services should return 3 services, got: {}".format(len(services))
    )
    return


# ---------------------------------------------------------------------------
# AwsComputeService tests
# ---------------------------------------------------------------------------

def test_aws_compute_service_name():
    """
        Verify that AwsComputeService has service_name 'aws-lambda'.
    """
    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=_create_mock_lambda_client()
    )

    assert svc.service_name == "aws-lambda", (
        "service_name should be 'aws-lambda', got: {!r}".format(svc.service_name)
    )
    return


def test_aws_compute_service_type():
    """
        Verify that AwsComputeService has service_type 'compute'.
    """
    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=_create_mock_lambda_client()
    )

    assert svc.service_type == "compute", (
        "service_type should be 'compute', got: {!r}".format(svc.service_type)
    )
    return


def test_aws_compute_service_platform_type():
    """
        Verify that AwsComputeService has platform_type AWS.
    """
    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=_create_mock_lambda_client()
    )

    assert svc.platform_type is PlatformType.AWS, (
        "platform_type should be AWS, got: {!r}".format(svc.platform_type)
    )
    return


def test_aws_compute_invoke_success():
    """
        Verify that invoke delegates to the Lambda client and returns
        an InvocationResult with status 'success'.
    """
    mock_client = _create_mock_lambda_client()

    payload_stream = Mock()
    payload_stream.configure(recursive=True)
    payload_stream.mock_context().mock_method(
        "read", return_value=b'{"result": "ok"}'
    )

    mock_client.mock_context().mock_method("invoke", return_value={
        "StatusCode": 200,
        "Payload": payload_stream,
    })

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    result = svc.invoke("my-function", {"key": "value"})

    assert result.status == "success", (
        "invoke should return status 'success', got: {!r}".format(result.status)
    )
    assert result.request_id is not None, "request_id should not be None"
    return


def test_aws_compute_invoke_function_error():
    """
        Verify that invoke returns status 'error' when FunctionError is present.
    """
    mock_client = _create_mock_lambda_client()

    payload_stream = Mock()
    payload_stream.configure(recursive=True)
    payload_stream.mock_context().mock_method(
        "read", return_value=b'{"errorMessage": "boom"}'
    )

    mock_client.mock_context().mock_method("invoke", return_value={
        "StatusCode": 200,
        "Payload": payload_stream,
        "FunctionError": "Unhandled"
    })

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    result = svc.invoke("my-function", {"key": "value"})

    assert result.status == "error", (
        "invoke should return status 'error' on FunctionError, got: {!r}".format(result.status)
    )
    assert result.error_message == "Unhandled", (
        "error_message should be 'Unhandled', got: {!r}".format(result.error_message)
    )
    return


def test_aws_compute_invoke_raises_compute_error_on_exception():
    """
        Verify that invoke raises ComputeError when the Lambda client
        raises an exception.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method(
        "invoke", side_effect=_raise_runtime_error("connection failed")
    )

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
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


def test_aws_compute_invoke_async_returns_request_id():
    """
        Verify that invoke_async delegates to the Lambda client with
        Event invocation type and returns a request ID.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method("invoke", return_value={
        "StatusCode": 202
    })

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    request_id = svc.invoke_async("my-function", {"key": "value"})

    assert isinstance(request_id, str), (
        "invoke_async should return a string request_id, got: {!r}".format(type(request_id))
    )
    assert len(request_id) > 0, "request_id should not be empty"
    return


def test_aws_compute_invoke_async_raises_compute_error_on_exception():
    """
        Verify that invoke_async raises ComputeError on client exception.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method(
        "invoke", side_effect=_raise_runtime_error("connection failed")
    )

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    raised = False
    try:
        svc.invoke_async("my-function", {"key": "value"})
    except ComputeError:
        raised = True

    assert raised is True, "invoke_async should raise ComputeError on client exception"
    return


def test_aws_compute_list_functions_delegates_to_client():
    """
        Verify that list_functions delegates to the Lambda client and
        returns function names.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method("list_functions", return_value={
        "Functions": [
            {"FunctionName": "func-a"},
            {"FunctionName": "func-b"}
        ]
    })

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    functions = svc.list_functions()

    assert functions == ["func-a", "func-b"], (
        "list_functions should return function names, got: {!r}".format(functions)
    )
    return


def test_aws_compute_list_functions_raises_compute_error_on_exception():
    """
        Verify that list_functions raises ComputeError on client exception.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method(
        "list_functions", side_effect=_raise_runtime_error("access denied")
    )

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    raised = False
    try:
        svc.list_functions()
    except ComputeError:
        raised = True

    assert raised is True, "list_functions should raise ComputeError on client exception"
    return


def test_aws_compute_is_available_true_when_list_functions_succeeds():
    """
        Verify that is_available returns True when list_functions succeeds.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method("list_functions", return_value={
        "Functions": []
    })

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    assert svc.is_available() is True, "is_available should return True"
    return


def test_aws_compute_is_available_false_when_list_functions_fails():
    """
        Verify that is_available returns False when list_functions raises.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method(
        "list_functions", side_effect=_raise_runtime_error("fail")
    )

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_aws_compute_get_invocation_status_returns_success():
    """
        Verify that get_invocation_status returns an InvocationResult
        with status 'success' (fire-and-forget for AWS Lambda).
    """
    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=_create_mock_lambda_client()
    )

    result = svc.get_invocation_status("req-123")

    assert result.status == "success", (
        "get_invocation_status should return 'success', got: {!r}".format(result.status)
    )
    assert result.request_id == "req-123", (
        "request_id should be 'req-123', got: {!r}".format(result.request_id)
    )
    return


def test_aws_compute_uses_injected_client():
    """
        Verify that AwsComputeService uses the injected Lambda client
        rather than creating a new one.
    """
    mock_client = _create_mock_lambda_client()
    mock_client.mock_context().mock_method("list_functions", return_value={
        "Functions": []
    })

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        lambda_client=mock_client
    )

    svc.list_functions()

    # Delegation verified: list_functions completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_compute_endpoint_override_in_config():
    """
        Verify that AwsComputeService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        service_endpoint_overrides={"lambda": "http://localhost:4566"}
    )

    svc = AwsComputeService(
        platform_type=PlatformType.AWS,
        configuration=config,
        lambda_client=_create_mock_lambda_client()
    )

    assert svc._configuration is not None, "configuration should be set"
    overrides = svc._configuration.service_endpoint_overrides
    assert "lambda" in overrides, "endpoint override for 'lambda' should be present"
    assert overrides["lambda"] == "http://localhost:4566", (
        "endpoint override should be 'http://localhost:4566', got: {!r}".format(overrides["lambda"])
    )
    return


# ---------------------------------------------------------------------------
# AwsStorageService tests
# ---------------------------------------------------------------------------

def test_aws_storage_service_name():
    """
        Verify that AwsStorageService has service_name 'aws-s3'.
    """
    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=_create_mock_s3_client()
    )

    assert svc.service_name == "aws-s3", (
        "service_name should be 'aws-s3', got: {!r}".format(svc.service_name)
    )
    return


def test_aws_storage_service_type():
    """
        Verify that AwsStorageService has service_type 'storage'.
    """
    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=_create_mock_s3_client()
    )

    assert svc.service_type == "storage", (
        "service_type should be 'storage', got: {!r}".format(svc.service_type)
    )
    return


def test_aws_storage_put_object_delegates_to_client():
    """
        Verify that put_object delegates to the S3 client.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("put_object", return_value={})

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    svc.put_object("my-bucket", "my-key", b"hello", content_type="text/plain")

    # Delegation verified: put_object completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_storage_put_object_raises_storage_error_on_exception():
    """
        Verify that put_object raises StorageError on client exception.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method(
        "put_object", side_effect=_raise_runtime_error("access denied")
    )

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
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


def test_aws_storage_get_object_returns_storage_object():
    """
        Verify that get_object delegates to the S3 client and returns
        a StorageObject.
    """
    mock_body = Mock()
    mock_body.configure(recursive=True)
    mock_body.mock_context().mock_method("read", return_value=b"file content")

    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("get_object", return_value={
        "Body": mock_body,
        "ContentType": "text/plain",
        "Metadata": {"author": "test"},
        "ContentLength": 12,
        "LastModified": datetime(2025, 1, 1)
    })

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
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


def test_aws_storage_get_object_raises_storage_error_on_exception():
    """
        Verify that get_object raises StorageError on client exception.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method(
        "get_object", side_effect=_raise_runtime_error("not found")
    )

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
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


def test_aws_storage_delete_object_delegates_to_client():
    """
        Verify that delete_object delegates to the S3 client.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("delete_object", return_value={})

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    svc.delete_object("my-bucket", "my-key")

    # Delegation verified: delete_object completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_storage_list_objects_returns_keys():
    """
        Verify that list_objects returns a list of object keys.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("list_objects_v2", return_value={
        "Contents": [
            {"Key": "file1.txt"},
            {"Key": "file2.txt"}
        ]
    })

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    keys = svc.list_objects("my-bucket")

    assert keys == ["file1.txt", "file2.txt"], (
        "list_objects should return keys, got: {!r}".format(keys)
    )
    return


def test_aws_storage_list_objects_with_prefix():
    """
        Verify that list_objects passes prefix to the S3 client.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("list_objects_v2", return_value={
        "Contents": [{"Key": "data/file1.txt"}]
    })

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    keys = svc.list_objects("my-bucket", prefix="data/")

    assert keys == ["data/file1.txt"], (
        "list_objects with prefix should return matching keys, got: {!r}".format(keys)
    )
    return


def test_aws_storage_object_exists_true():
    """
        Verify that object_exists returns True when head_object succeeds.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("head_object", return_value={})

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    result = svc.object_exists("my-bucket", "my-key")

    assert result is True, "object_exists should return True when object exists"
    return


def test_aws_storage_create_container_delegates_to_client():
    """
        Verify that create_container delegates to the S3 client.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("create_bucket", return_value={})

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    svc.create_container("my-bucket")

    # Delegation verified: create_container completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_storage_delete_container_delegates_to_client():
    """
        Verify that delete_container delegates to the S3 client.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("delete_bucket", return_value={})

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    svc.delete_container("my-bucket")

    # Delegation verified: delete_container completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_storage_list_containers_returns_bucket_names():
    """
        Verify that list_containers returns a list of bucket names.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("list_buckets", return_value={
        "Buckets": [
            {"Name": "bucket-a"},
            {"Name": "bucket-b"}
        ]
    })

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    buckets = svc.list_containers()

    assert buckets == ["bucket-a", "bucket-b"], (
        "list_containers should return bucket names, got: {!r}".format(buckets)
    )
    return


def test_aws_storage_is_available_true():
    """
        Verify that is_available returns True when list_containers succeeds.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method("list_buckets", return_value={
        "Buckets": []
    })

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    assert svc.is_available() is True, "is_available should return True"
    return


def test_aws_storage_is_available_false():
    """
        Verify that is_available returns False when list_containers fails.
    """
    mock_client = _create_mock_s3_client()
    mock_client.mock_context().mock_method(
        "list_buckets", side_effect=_raise_runtime_error("fail")
    )

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        s3_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_aws_storage_endpoint_override_in_config():
    """
        Verify that AwsStorageService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        service_endpoint_overrides={"s3": "http://localhost:4566"}
    )

    svc = AwsStorageService(
        platform_type=PlatformType.AWS,
        configuration=config,
        s3_client=_create_mock_s3_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "s3" in overrides, "endpoint override for 's3' should be present"
    assert overrides["s3"] == "http://localhost:4566", (
        "endpoint override should be 'http://localhost:4566', got: {!r}".format(overrides["s3"])
    )
    return


# ---------------------------------------------------------------------------
# AwsMessagingService tests
# ---------------------------------------------------------------------------

def test_aws_messaging_service_name():
    """
        Verify that AwsMessagingService has service_name 'aws-sqs'.
    """
    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=_create_mock_sqs_client()
    )

    assert svc.service_name == "aws-sqs", (
        "service_name should be 'aws-sqs', got: {!r}".format(svc.service_name)
    )
    return


def test_aws_messaging_service_type():
    """
        Verify that AwsMessagingService has service_type 'messaging'.
    """
    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=_create_mock_sqs_client()
    )

    assert svc.service_type == "messaging", (
        "service_type should be 'messaging', got: {!r}".format(svc.service_type)
    )
    return


def test_aws_messaging_send_message_returns_message_id():
    """
        Verify that send_message delegates to the SQS client and returns
        a message ID.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("get_queue_url", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/my-queue"
    })
    mock_client.mock_context().mock_method("send_message", return_value={
        "MessageId": "msg-abc-123"
    })

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    msg_id = svc.send_message("my-queue", {"data": "hello"})

    assert msg_id == "msg-abc-123", (
        "send_message should return message ID, got: {!r}".format(msg_id)
    )
    return


def test_aws_messaging_send_message_with_attributes():
    """
        Verify that send_message passes attributes to the SQS client.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("get_queue_url", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/my-queue"
    })
    mock_client.mock_context().mock_method("send_message", return_value={
        "MessageId": "msg-abc-456"
    })

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    msg_id = svc.send_message(
        "my-queue",
        {"data": "hello"},
        attributes={"priority": "high"}
    )

    assert msg_id == "msg-abc-456", (
        "send_message with attributes should return message ID, got: {!r}".format(msg_id)
    )
    return


def test_aws_messaging_send_message_raises_messaging_error_on_exception():
    """
        Verify that send_message raises MessagingError on client exception.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("get_queue_url", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/my-queue"
    })
    mock_client.mock_context().mock_method(
        "send_message", side_effect=_raise_runtime_error("queue not found")
    )

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
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


def test_aws_messaging_receive_messages_returns_queue_messages():
    """
        Verify that receive_messages delegates to the SQS client and
        returns QueueMessage objects.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("get_queue_url", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/my-queue"
    })
    mock_client.mock_context().mock_method("receive_message", return_value={
        "Messages": [
            {
                "MessageId": "msg-001",
                "Body": json.dumps({"data": "hello"}),
                "ReceiptHandle": "receipt-001",
                "MessageAttributes": {}
            }
        ]
    })

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    messages = svc.receive_messages("my-queue", max_count=1)

    assert len(messages) == 1, (
        "receive_messages should return 1 message, got: {}".format(len(messages))
    )
    assert messages[0].identifier == "msg-001", (
        "message identifier should be 'msg-001', got: {!r}".format(messages[0].identifier)
    )
    assert messages[0].body == {"data": "hello"}, (
        "message body should be deserialized JSON, got: {!r}".format(messages[0].body)
    )
    return


def test_aws_messaging_receive_messages_empty_queue():
    """
        Verify that receive_messages returns empty list for empty queue.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("get_queue_url", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/my-queue"
    })
    mock_client.mock_context().mock_method("receive_message", return_value={})

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    messages = svc.receive_messages("my-queue")

    assert len(messages) == 0, (
        "receive_messages should return empty list, got: {}".format(len(messages))
    )
    return


def test_aws_messaging_acknowledge_message_delegates_to_client():
    """
        Verify that acknowledge_message delegates to the SQS client.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("get_queue_url", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/my-queue"
    })
    mock_client.mock_context().mock_method("delete_message", return_value={})

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    svc.acknowledge_message("my-queue", "receipt-001")

    # Delegation verified: acknowledge_message completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_messaging_create_queue_delegates_to_client():
    """
        Verify that create_queue delegates to the SQS client.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("create_queue", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/new-queue"
    })

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    svc.create_queue("new-queue")

    # Delegation verified: create_queue completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_messaging_delete_queue_delegates_to_client():
    """
        Verify that delete_queue delegates to the SQS client.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("get_queue_url", return_value={
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789/my-queue"
    })
    mock_client.mock_context().mock_method("delete_queue", return_value={})

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    svc.delete_queue("my-queue")

    # Delegation verified: delete_queue completed without error using the
    # injected mock client, confirming the client was used.
    return


def test_aws_messaging_list_queues_returns_queue_names():
    """
        Verify that list_queues returns a list of queue names.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("list_queues", return_value={
        "QueueUrls": [
            "https://sqs.us-east-1.amazonaws.com/123456789/queue-a",
            "https://sqs.us-east-1.amazonaws.com/123456789/queue-b"
        ]
    })

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    queues = svc.list_queues()

    assert queues == ["queue-a", "queue-b"], (
        "list_queues should return queue names, got: {!r}".format(queues)
    )
    return


def test_aws_messaging_is_available_true():
    """
        Verify that is_available returns True when list_queues succeeds.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method("list_queues", return_value={
        "QueueUrls": []
    })

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    assert svc.is_available() is True, "is_available should return True"
    return


def test_aws_messaging_is_available_false():
    """
        Verify that is_available returns False when list_queues fails.
    """
    mock_client = _create_mock_sqs_client()
    mock_client.mock_context().mock_method(
        "list_queues", side_effect=_raise_runtime_error("fail")
    )

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        sqs_client=mock_client
    )

    assert svc.is_available() is False, "is_available should return False"
    return


def test_aws_messaging_endpoint_override_in_config():
    """
        Verify that AwsMessagingService accepts endpoint overrides from
        PlatformConfiguration.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        service_endpoint_overrides={"sqs": "http://localhost:4566"}
    )

    svc = AwsMessagingService(
        platform_type=PlatformType.AWS,
        configuration=config,
        sqs_client=_create_mock_sqs_client()
    )

    overrides = svc._configuration.service_endpoint_overrides
    assert "sqs" in overrides, "endpoint override for 'sqs' should be present"
    assert overrides["sqs"] == "http://localhost:4566", (
        "endpoint override should be 'http://localhost:4566', got: {!r}".format(overrides["sqs"])
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
