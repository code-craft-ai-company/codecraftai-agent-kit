"""
    Tests for the automojo.agentkit.platform.errors module.

    Contains unit tests for the platform exception hierarchy including
    inheritance chains, __repr__ output, and extra fields on specialized
    error subclasses.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.test_errors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for platform error classes.
"""

from automojo.agentkit.errors import AgentKitError
from automojo.agentkit.platform.errors import ComputeError
from automojo.agentkit.platform.errors import DeploymentDescriptorError
from automojo.agentkit.platform.errors import MessagingError
from automojo.agentkit.platform.errors import PlatformDetectionError
from automojo.agentkit.platform.errors import PlatformError
from automojo.agentkit.platform.errors import StorageError
from automojo.agentkit.platform.platformtype import PlatformType


# ---------------------------------------------------------------------------
# Inheritance chain tests
# ---------------------------------------------------------------------------

def test_platform_error_inherits_from_agentkit_error():
    """
        Verify that PlatformError is a subclass of AgentKitError.
    """
    err = PlatformError("test error")

    is_agentkit = isinstance(err, AgentKitError)

    assert is_agentkit is True, (
        "PlatformError should inherit from AgentKitError"
    )
    return


def test_platform_detection_error_inherits_from_platform_error():
    """
        Verify that PlatformDetectionError is a subclass of PlatformError.
    """
    err = PlatformDetectionError("detection failed")

    is_platform = isinstance(err, PlatformError)
    is_agentkit = isinstance(err, AgentKitError)

    assert is_platform is True, (
        "PlatformDetectionError should inherit from PlatformError"
    )
    assert is_agentkit is True, (
        "PlatformDetectionError should also be an AgentKitError"
    )
    return


def test_storage_error_inherits_from_platform_error():
    """
        Verify that StorageError is a subclass of PlatformError.
    """
    err = StorageError("storage failed")

    is_platform = isinstance(err, PlatformError)

    assert is_platform is True, (
        "StorageError should inherit from PlatformError"
    )
    return


def test_compute_error_inherits_from_platform_error():
    """
        Verify that ComputeError is a subclass of PlatformError.
    """
    err = ComputeError("compute failed")

    is_platform = isinstance(err, PlatformError)

    assert is_platform is True, (
        "ComputeError should inherit from PlatformError"
    )
    return


def test_messaging_error_inherits_from_platform_error():
    """
        Verify that MessagingError is a subclass of PlatformError.
    """
    err = MessagingError("messaging failed")

    is_platform = isinstance(err, PlatformError)

    assert is_platform is True, (
        "MessagingError should inherit from PlatformError"
    )
    return


def test_deployment_descriptor_error_inherits_from_platform_error():
    """
        Verify that DeploymentDescriptorError is a subclass of PlatformError.
    """
    err = DeploymentDescriptorError("descriptor invalid")

    is_platform = isinstance(err, PlatformError)

    assert is_platform is True, (
        "DeploymentDescriptorError should inherit from PlatformError"
    )
    return


# ---------------------------------------------------------------------------
# PlatformError construction and properties
# ---------------------------------------------------------------------------

def test_platform_error_message_property():
    """
        Verify that PlatformError exposes the message via the message property.
    """
    err = PlatformError("something went wrong")

    actual = str(err)

    assert "something went wrong" in actual, (
        "PlatformError message should contain the provided text, got: {!r}".format(actual)
    )
    return


def test_platform_error_cause_property():
    """
        Verify that PlatformError stores and exposes the cause exception.
    """
    cause = ValueError("root cause")
    err = PlatformError("wrapper", cause=cause)

    actual_cause = err.cause

    assert actual_cause is cause, (
        "PlatformError cause should be the provided exception"
    )
    return


def test_platform_error_platform_type_property():
    """
        Verify that PlatformError stores and exposes the platform_type.
    """
    err = PlatformError("test", platform_type=PlatformType.AWS)

    actual = err.platform_type

    assert actual is PlatformType.AWS, (
        "platform_type should be PlatformType.AWS, got: {!r}".format(actual)
    )
    return


def test_platform_error_platform_type_defaults_to_none():
    """
        Verify that PlatformError platform_type defaults to None.
    """
    err = PlatformError("test")

    actual = err.platform_type

    assert actual is None, (
        "platform_type should default to None, got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# __repr__ tests
# ---------------------------------------------------------------------------

def test_platform_error_repr_includes_class_name_and_message():
    """
        Verify that PlatformError __repr__ includes the class name and message.
    """
    err = PlatformError("test error", platform_type=PlatformType.GCP)

    repr_str = repr(err)

    has_class = "PlatformError" in repr_str
    has_message = "test error" in repr_str
    has_platform = "gcp" in repr_str

    assert has_class is True, "repr should contain 'PlatformError'"
    assert has_message is True, "repr should contain the message"
    assert has_platform is True, "repr should contain the platform type"
    return


def test_platform_error_repr_unknown_when_no_platform_type():
    """
        Verify that PlatformError __repr__ shows 'unknown' when no platform_type.
    """
    err = PlatformError("test error")

    repr_str = repr(err)

    has_unknown = "unknown" in repr_str

    assert has_unknown is True, (
        "repr should contain 'unknown' when platform_type is None, got: {!r}".format(repr_str)
    )
    return


# ---------------------------------------------------------------------------
# StorageError extra fields
# ---------------------------------------------------------------------------

def test_storage_error_operation_name_property():
    """
        Verify that StorageError exposes the operation_name property.
    """
    err = StorageError(
        "put failed",
        operation_name="put_object",
        container_name="my-bucket",
        object_key="data.bin",
        platform_type=PlatformType.AWS
    )

    assert err.operation_name == "put_object", (
        "operation_name should be 'put_object', got: {!r}".format(err.operation_name)
    )
    return


def test_storage_error_container_name_property():
    """
        Verify that StorageError exposes the container_name property.
    """
    err = StorageError(
        "get failed",
        operation_name="get_object",
        container_name="my-bucket"
    )

    assert err.container_name == "my-bucket", (
        "container_name should be 'my-bucket', got: {!r}".format(err.container_name)
    )
    return


def test_storage_error_object_key_property():
    """
        Verify that StorageError exposes the object_key property.
    """
    err = StorageError(
        "delete failed",
        operation_name="delete_object",
        container_name="bucket",
        object_key="path/to/file.txt"
    )

    assert err.object_key == "path/to/file.txt", (
        "object_key should be 'path/to/file.txt', got: {!r}".format(err.object_key)
    )
    return


def test_storage_error_repr_includes_operation_and_container():
    """
        Verify that StorageError __repr__ includes operation and container info.
    """
    err = StorageError(
        "failed",
        operation_name="put_object",
        container_name="test-bucket",
        platform_type=PlatformType.AZURE
    )

    repr_str = repr(err)

    has_class = "StorageError" in repr_str
    has_operation = "put_object" in repr_str
    has_container = "test-bucket" in repr_str
    has_platform = "azure" in repr_str

    assert has_class is True, "repr should contain 'StorageError'"
    assert has_operation is True, "repr should contain the operation name"
    assert has_container is True, "repr should contain the container name"
    assert has_platform is True, "repr should contain the platform type"
    return


# ---------------------------------------------------------------------------
# ComputeError extra fields
# ---------------------------------------------------------------------------

def test_compute_error_function_name_property():
    """
        Verify that ComputeError exposes the function_name property.
    """
    err = ComputeError(
        "invoke failed",
        function_name="my-lambda",
        platform_type=PlatformType.AWS
    )

    assert err.function_name == "my-lambda", (
        "function_name should be 'my-lambda', got: {!r}".format(err.function_name)
    )
    return


def test_compute_error_repr_includes_function_name():
    """
        Verify that ComputeError __repr__ includes the function name.
    """
    err = ComputeError(
        "timeout",
        function_name="process-data",
        platform_type=PlatformType.GCP
    )

    repr_str = repr(err)

    has_class = "ComputeError" in repr_str
    has_function = "process-data" in repr_str
    has_platform = "gcp" in repr_str

    assert has_class is True, "repr should contain 'ComputeError'"
    assert has_function is True, "repr should contain the function name"
    assert has_platform is True, "repr should contain the platform type"
    return


# ---------------------------------------------------------------------------
# MessagingError extra fields
# ---------------------------------------------------------------------------

def test_messaging_error_queue_name_property():
    """
        Verify that MessagingError exposes the queue_name property.
    """
    err = MessagingError(
        "send failed",
        queue_name="task-queue",
        platform_type=PlatformType.AZURE
    )

    assert err.queue_name == "task-queue", (
        "queue_name should be 'task-queue', got: {!r}".format(err.queue_name)
    )
    return


def test_messaging_error_repr_includes_queue_name():
    """
        Verify that MessagingError __repr__ includes the queue name.
    """
    err = MessagingError(
        "receive failed",
        queue_name="events",
        platform_type=PlatformType.LOCAL
    )

    repr_str = repr(err)

    has_class = "MessagingError" in repr_str
    has_queue = "events" in repr_str
    has_platform = "local" in repr_str

    assert has_class is True, "repr should contain 'MessagingError'"
    assert has_queue is True, "repr should contain the queue name"
    assert has_platform is True, "repr should contain the platform type"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
