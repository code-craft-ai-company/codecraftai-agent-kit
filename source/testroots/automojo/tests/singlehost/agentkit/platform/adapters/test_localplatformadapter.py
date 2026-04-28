"""
    Tests for the automojo.agentkit.platform.adapters.localplatformadapter module.

    Contains unit tests for LocalPlatformAdapter, LocalComputeService,
    LocalStorageService, and LocalMessagingService including subprocess
    execution, file system storage, in-memory queuing, and concurrent access.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.adapters.test_localplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for LocalPlatformAdapter and local service implementations.
"""

import os
import shutil
import tempfile
import threading
import time

from automojo.agentkit.platform.adapters.localplatformadapter import LocalComputeService
from automojo.agentkit.platform.adapters.localplatformadapter import LocalMessagingService
from automojo.agentkit.platform.adapters.localplatformadapter import LocalPlatformAdapter
from automojo.agentkit.platform.adapters.localplatformadapter import LocalStorageService
from automojo.agentkit.platform.errors import ComputeError
from automojo.agentkit.platform.errors import MessagingError
from automojo.agentkit.platform.errors import StorageError
from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration
from automojo.agentkit.platform.platformtype import PlatformType


# ---------------------------------------------------------------------------
# LocalPlatformAdapter tests
# ---------------------------------------------------------------------------

def test_local_adapter_platform_type_is_local():
    """
        Verify that LocalPlatformAdapter.platform_type returns LOCAL.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = LocalPlatformAdapter(configuration=config)

    actual = adapter.platform_type

    assert actual is PlatformType.LOCAL, (
        "platform_type should be LOCAL, got: {!r}".format(actual)
    )
    return


def test_local_adapter_get_compute_service_returns_local_compute():
    """
        Verify that get_compute_service returns a LocalComputeService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = LocalPlatformAdapter(configuration=config)

    svc = adapter.get_compute_service()

    assert isinstance(svc, LocalComputeService), (
        "get_compute_service should return LocalComputeService, got: {!r}".format(type(svc))
    )
    return


def test_local_adapter_get_storage_service_returns_local_storage():
    """
        Verify that get_storage_service returns a LocalStorageService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = LocalPlatformAdapter(configuration=config)

    svc = adapter.get_storage_service()

    assert isinstance(svc, LocalStorageService), (
        "get_storage_service should return LocalStorageService, got: {!r}".format(type(svc))
    )
    return


def test_local_adapter_get_messaging_service_returns_local_messaging():
    """
        Verify that get_messaging_service returns a LocalMessagingService.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = LocalPlatformAdapter(configuration=config)

    svc = adapter.get_messaging_service()

    assert isinstance(svc, LocalMessagingService), (
        "get_messaging_service should return LocalMessagingService, got: {!r}".format(type(svc))
    )
    return


def test_local_adapter_get_all_services_returns_three():
    """
        Verify that get_all_services returns three services.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = LocalPlatformAdapter(configuration=config)

    services = adapter.get_all_services()

    assert len(services) == 3, (
        "get_all_services should return 3 services, got: {}".format(len(services))
    )
    return


def test_local_adapter_uses_storage_base_directory_from_options():
    """
        Verify that LocalPlatformAdapter uses storage_base_directory from
        configuration options.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        config = PlatformConfiguration(
            platform_type=PlatformType.LOCAL,
            options={"storage_base_directory": tmp_dir}
        )
        adapter = LocalPlatformAdapter(configuration=config)
        storage = adapter.get_storage_service()

        assert storage._base_directory == tmp_dir, (
            "storage base_directory should be {!r}, got: {!r}".format(
                tmp_dir, storage._base_directory
            )
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_local_adapter_repr():
    """
        Verify that __repr__ includes the class name and platform type.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)
    adapter = LocalPlatformAdapter(configuration=config)

    repr_str = repr(adapter)

    assert "LocalPlatformAdapter" in repr_str, (
        "repr should contain 'LocalPlatformAdapter', got: {!r}".format(repr_str)
    )
    assert "local" in repr_str, (
        "repr should contain 'local', got: {!r}".format(repr_str)
    )
    return


# ---------------------------------------------------------------------------
# LocalComputeService tests
# ---------------------------------------------------------------------------

def test_compute_invoke_success():
    """
        Verify that invoke returns an InvocationResult with status "success"
        for a simple subprocess that exits 0.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    result = svc.invoke("echo hello", payload={})

    assert result.status == "success", (
        "status should be 'success', got: {!r}".format(result.status)
    )
    assert "hello" in result.response, (
        "response should contain 'hello', got: {!r}".format(result.response)
    )
    assert result.duration > 0, (
        "duration should be positive, got: {}".format(result.duration)
    )
    assert len(result.request_id) > 0, (
        "request_id should be non-empty"
    )
    return


def test_compute_invoke_error_nonzero_exit():
    """
        Verify that invoke returns an InvocationResult with status "error"
        when the subprocess exits with a non-zero code.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    result = svc.invoke("exit 1", payload={})

    assert result.status == "error", (
        "status should be 'error', got: {!r}".format(result.status)
    )
    assert result.error_message is not None, (
        "error_message should not be None for error status"
    )
    return


def test_compute_invoke_timeout():
    """
        Verify that invoke returns an InvocationResult with status "timeout"
        when the subprocess exceeds the timeout.
    """
    svc = LocalComputeService(
        platform_type=PlatformType.LOCAL,
        default_timeout=0.5
    )

    result = svc.invoke("sleep 10", payload={}, timeout=0.5)

    assert result.status == "timeout", (
        "status should be 'timeout', got: {!r}".format(result.status)
    )
    assert result.error_message is not None, (
        "error_message should describe the timeout"
    )
    assert "timed out" in result.error_message.lower() or "timeout" in result.error_message.lower(), (
        "error_message should mention timeout, got: {!r}".format(result.error_message)
    )
    return


def test_compute_invoke_uses_default_timeout():
    """
        Verify that invoke uses the default_timeout when no explicit
        timeout is provided.
    """
    svc = LocalComputeService(
        platform_type=PlatformType.LOCAL,
        default_timeout=0.5
    )

    result = svc.invoke("sleep 10", payload={})

    assert result.status == "timeout", (
        "status should be 'timeout' with default timeout, got: {!r}".format(result.status)
    )
    return


def test_compute_invoke_async_returns_request_id():
    """
        Verify that invoke_async returns a non-empty request identifier.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    request_id = svc.invoke_async("echo async", payload={})

    assert len(request_id) > 0, (
        "invoke_async should return a non-empty request_id"
    )
    return


def test_compute_get_invocation_status_unknown_id_raises():
    """
        Verify that get_invocation_status raises ComputeError for an
        unknown request identifier.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    caught = False
    try:
        svc.get_invocation_status("nonexistent-id")
    except ComputeError:
        caught = True

    assert caught is True, (
        "get_invocation_status should raise ComputeError for unknown request_id"
    )
    return


def test_compute_service_name():
    """
        Verify that the service_name is 'local-compute'.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    assert svc.service_name == "local-compute", (
        "service_name should be 'local-compute', got: {!r}".format(svc.service_name)
    )
    return


def test_compute_service_type():
    """
        Verify that the service_type is 'compute'.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    assert svc.service_type == "compute", (
        "service_type should be 'compute', got: {!r}".format(svc.service_type)
    )
    return


def test_compute_is_available():
    """
        Verify that is_available returns True.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    assert svc.is_available() is True, "is_available should return True"
    return


def test_compute_health_check():
    """
        Verify that health_check returns True on a working system.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    assert svc.health_check() is True, "health_check should return True"
    return


def test_compute_list_functions_returns_empty():
    """
        Verify that list_functions returns an empty list.
    """
    svc = LocalComputeService(platform_type=PlatformType.LOCAL)

    result = svc.list_functions()

    assert result == [], (
        "list_functions should return empty list, got: {!r}".format(result)
    )
    return


# ---------------------------------------------------------------------------
# LocalStorageService tests
# ---------------------------------------------------------------------------

def test_storage_put_and_get_object():
    """
        Verify that put_object stores an object and get_object retrieves it.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")
        svc.put_object(
            container_name="test-bucket",
            object_key="hello.txt",
            content=b"Hello, World!",
            content_type="text/plain",
            metadata={"author": "test"}
        )

        obj = svc.get_object("test-bucket", "hello.txt")

        assert obj.key == "hello.txt", (
            "key should be 'hello.txt', got: {!r}".format(obj.key)
        )
        assert obj.content == b"Hello, World!", (
            "content mismatch, got: {!r}".format(obj.content)
        )
        assert obj.content_type == "text/plain", (
            "content_type should be 'text/plain', got: {!r}".format(obj.content_type)
        )
        assert obj.metadata.get("author") == "test", (
            "metadata should contain author=test, got: {!r}".format(obj.metadata)
        )
        assert obj.size == 13, (
            "size should be 13, got: {}".format(obj.size)
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_get_nonexistent_object_raises():
    """
        Verify that get_object raises StorageError for a nonexistent object.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")

        caught = False
        try:
            svc.get_object("test-bucket", "nonexistent.txt")
        except StorageError:
            caught = True

        assert caught is True, (
            "get_object should raise StorageError for nonexistent object"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_delete_object():
    """
        Verify that delete_object removes the object and its metadata.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")
        svc.put_object("test-bucket", "to-delete.txt", b"data")

        assert svc.object_exists("test-bucket", "to-delete.txt") is True

        svc.delete_object("test-bucket", "to-delete.txt")

        assert svc.object_exists("test-bucket", "to-delete.txt") is False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_list_objects():
    """
        Verify that list_objects returns all object keys in a container.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")
        svc.put_object("test-bucket", "a.txt", b"aaa")
        svc.put_object("test-bucket", "b.txt", b"bbb")
        svc.put_object("test-bucket", "c.txt", b"ccc")

        keys = svc.list_objects("test-bucket")

        assert len(keys) == 3, (
            "list_objects should return 3 keys, got: {}".format(len(keys))
        )
        assert "a.txt" in keys, "keys should contain 'a.txt'"
        assert "b.txt" in keys, "keys should contain 'b.txt'"
        assert "c.txt" in keys, "keys should contain 'c.txt'"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_list_objects_with_prefix():
    """
        Verify that list_objects filters by prefix.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")
        svc.put_object("test-bucket", "data-a.txt", b"aaa")
        svc.put_object("test-bucket", "data-b.txt", b"bbb")
        svc.put_object("test-bucket", "other.txt", b"ccc")

        keys = svc.list_objects("test-bucket", prefix="data-")

        assert len(keys) == 2, (
            "list_objects with prefix should return 2 keys, got: {}".format(len(keys))
        )
        assert "data-a.txt" in keys, "keys should contain 'data-a.txt'"
        assert "data-b.txt" in keys, "keys should contain 'data-b.txt'"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_list_objects_nonexistent_container_returns_empty():
    """
        Verify that list_objects returns an empty list for a nonexistent container.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )

        keys = svc.list_objects("nonexistent-bucket")

        assert keys == [], (
            "list_objects should return empty list for nonexistent container, got: {!r}".format(keys)
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_object_exists_true():
    """
        Verify that object_exists returns True for an existing object.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")
        svc.put_object("test-bucket", "exists.txt", b"data")

        result = svc.object_exists("test-bucket", "exists.txt")

        assert result is True, "object_exists should return True"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_object_exists_false():
    """
        Verify that object_exists returns False for a nonexistent object.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")

        result = svc.object_exists("test-bucket", "nope.txt")

        assert result is False, "object_exists should return False"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_create_container():
    """
        Verify that create_container creates a directory.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("new-bucket")

        container_path = os.path.join(tmp_dir, "new-bucket")
        assert os.path.isdir(container_path), (
            "create_container should create a directory"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_delete_container():
    """
        Verify that delete_container removes the container directory.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("to-delete")
        svc.put_object("to-delete", "file.txt", b"data")

        svc.delete_container("to-delete")

        container_path = os.path.join(tmp_dir, "to-delete")
        assert not os.path.exists(container_path), (
            "delete_container should remove the directory"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_list_containers():
    """
        Verify that list_containers returns all container names.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("alpha")
        svc.create_container("beta")
        svc.create_container("gamma")

        containers = svc.list_containers()

        assert len(containers) == 3, (
            "list_containers should return 3, got: {}".format(len(containers))
        )
        assert "alpha" in containers, "containers should contain 'alpha'"
        assert "beta" in containers, "containers should contain 'beta'"
        assert "gamma" in containers, "containers should contain 'gamma'"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_list_containers_empty():
    """
        Verify that list_containers returns empty list when no containers exist.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )

        containers = svc.list_containers()

        assert containers == [], (
            "list_containers should return empty list, got: {!r}".format(containers)
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_service_name():
    """
        Verify that the service_name is 'local-storage'.
    """
    svc = LocalStorageService(
        platform_type=PlatformType.LOCAL,
        base_directory=tempfile.mkdtemp()
    )

    assert svc.service_name == "local-storage", (
        "service_name should be 'local-storage', got: {!r}".format(svc.service_name)
    )
    return


def test_storage_service_type():
    """
        Verify that the service_type is 'storage'.
    """
    svc = LocalStorageService(
        platform_type=PlatformType.LOCAL,
        base_directory=tempfile.mkdtemp()
    )

    assert svc.service_type == "storage", (
        "service_type should be 'storage', got: {!r}".format(svc.service_type)
    )
    return


def test_storage_is_available():
    """
        Verify that is_available returns True with a valid base directory.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )

        assert svc.is_available() is True, "is_available should return True"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_health_check():
    """
        Verify that health_check returns True with a writable base directory.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )

        assert svc.health_check() is True, "health_check should return True"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


def test_storage_put_object_overwrites_existing():
    """
        Verify that put_object overwrites an existing object.
    """
    tmp_dir = tempfile.mkdtemp()

    try:
        svc = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            base_directory=tmp_dir
        )
        svc.create_container("test-bucket")
        svc.put_object("test-bucket", "file.txt", b"original")
        svc.put_object("test-bucket", "file.txt", b"updated")

        obj = svc.get_object("test-bucket", "file.txt")

        assert obj.content == b"updated", (
            "content should be 'updated' after overwrite, got: {!r}".format(obj.content)
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return


# ---------------------------------------------------------------------------
# LocalMessagingService tests
# ---------------------------------------------------------------------------

def test_messaging_create_and_list_queues():
    """
        Verify that create_queue creates a queue and list_queues returns it.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("test-queue")
    queues = svc.list_queues()

    assert "test-queue" in queues, (
        "list_queues should contain 'test-queue', got: {!r}".format(queues)
    )
    return


def test_messaging_delete_queue():
    """
        Verify that delete_queue removes the queue.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("to-delete")
    svc.delete_queue("to-delete")
    queues = svc.list_queues()

    assert "to-delete" not in queues, (
        "list_queues should not contain 'to-delete' after deletion"
    )
    return


def test_messaging_send_and_receive_message():
    """
        Verify that send_message adds a message and receive_messages retrieves it.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("test-queue")
    msg_id = svc.send_message("test-queue", body={"key": "value"}, attributes={"priority": "high"})

    assert len(msg_id) > 0, "send_message should return a non-empty message_id"

    messages = svc.receive_messages("test-queue", max_count=1)

    assert len(messages) == 1, (
        "receive_messages should return 1 message, got: {}".format(len(messages))
    )
    msg = messages[0]
    assert msg.identifier == msg_id, (
        "message identifier should match, got: {!r}".format(msg.identifier)
    )
    assert msg.body == {"key": "value"}, (
        "message body mismatch, got: {!r}".format(msg.body)
    )
    assert msg.attributes.get("priority") == "high", (
        "message attributes mismatch, got: {!r}".format(msg.attributes)
    )
    assert msg.queue_name == "test-queue", (
        "queue_name should be 'test-queue', got: {!r}".format(msg.queue_name)
    )
    return


def test_messaging_receive_empty_queue():
    """
        Verify that receive_messages returns an empty list for an empty queue.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("empty-queue")
    messages = svc.receive_messages("empty-queue", max_count=5)

    assert messages == [], (
        "receive_messages should return empty list for empty queue, got: {!r}".format(messages)
    )
    return


def test_messaging_receive_multiple_messages():
    """
        Verify that receive_messages returns up to max_count messages.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("multi-queue")
    svc.send_message("multi-queue", body="msg1")
    svc.send_message("multi-queue", body="msg2")
    svc.send_message("multi-queue", body="msg3")

    messages = svc.receive_messages("multi-queue", max_count=2)

    assert len(messages) == 2, (
        "receive_messages should return 2 messages, got: {}".format(len(messages))
    )
    return


def test_messaging_acknowledge_message():
    """
        Verify that acknowledge_message removes the message from pending.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("ack-queue")
    svc.send_message("ack-queue", body="to-ack")

    messages = svc.receive_messages("ack-queue", max_count=1)
    assert len(messages) == 1

    receipt = messages[0].receipt_handle
    svc.acknowledge_message("ack-queue", receipt)

    pending = svc._pending.get("ack-queue", {})
    assert receipt not in pending, (
        "receipt_handle should be removed from pending after acknowledge"
    )
    return


def test_messaging_send_to_nonexistent_queue_raises():
    """
        Verify that send_message raises MessagingError for a nonexistent queue.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    caught = False
    try:
        svc.send_message("nonexistent", body="test")
    except MessagingError:
        caught = True

    assert caught is True, (
        "send_message should raise MessagingError for nonexistent queue"
    )
    return


def test_messaging_receive_from_nonexistent_queue_raises():
    """
        Verify that receive_messages raises MessagingError for a nonexistent queue.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    caught = False
    try:
        svc.receive_messages("nonexistent")
    except MessagingError:
        caught = True

    assert caught is True, (
        "receive_messages should raise MessagingError for nonexistent queue"
    )
    return


def test_messaging_fifo_ordering():
    """
        Verify that messages are received in FIFO order.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("fifo-queue")
    svc.send_message("fifo-queue", body="first")
    svc.send_message("fifo-queue", body="second")
    svc.send_message("fifo-queue", body="third")

    messages = svc.receive_messages("fifo-queue", max_count=3)

    bodies = [m.body for m in messages]
    assert bodies == ["first", "second", "third"], (
        "Messages should be in FIFO order, got: {!r}".format(bodies)
    )
    return


def test_messaging_service_name():
    """
        Verify that the service_name is 'local-messaging'.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    assert svc.service_name == "local-messaging", (
        "service_name should be 'local-messaging', got: {!r}".format(svc.service_name)
    )
    return


def test_messaging_service_type():
    """
        Verify that the service_type is 'messaging'.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    assert svc.service_type == "messaging", (
        "service_type should be 'messaging', got: {!r}".format(svc.service_type)
    )
    return


def test_messaging_is_available():
    """
        Verify that is_available returns True.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    assert svc.is_available() is True, "is_available should return True"
    return


def test_messaging_health_check():
    """
        Verify that health_check returns True.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    assert svc.health_check() is True, "health_check should return True"
    return


def test_messaging_list_queues_empty():
    """
        Verify that list_queues returns empty list when no queues exist.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    queues = svc.list_queues()

    assert queues == [], (
        "list_queues should return empty list, got: {!r}".format(queues)
    )
    return


def test_messaging_create_queue_idempotent():
    """
        Verify that creating the same queue twice does not raise an error.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)

    svc.create_queue("idempotent-queue")
    svc.create_queue("idempotent-queue")

    queues = svc.list_queues()
    assert queues.count("idempotent-queue") == 1, (
        "Queue should appear exactly once, got: {!r}".format(queues)
    )
    return


# ---------------------------------------------------------------------------
# Concurrent access tests
# ---------------------------------------------------------------------------

def test_messaging_concurrent_send_receive():
    """
        Verify that concurrent send and receive operations on
        LocalMessagingService do not corrupt state.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)
    svc.create_queue("concurrent-queue")

    num_messages = 50
    sent_ids = []
    received_messages = []
    errors = []

    def sender():
        for i in range(num_messages):
            try:
                msg_id = svc.send_message("concurrent-queue", body="msg-{}".format(i))
                sent_ids.append(msg_id)
            except Exception as exc:
                errors.append(str(exc))
        return

    def receiver():
        time.sleep(0.05)
        attempts = 0
        while len(received_messages) < num_messages and attempts < 200:
            try:
                msgs = svc.receive_messages("concurrent-queue", max_count=5, wait_time=0.01)
                received_messages.extend(msgs)
            except Exception as exc:
                errors.append(str(exc))
            attempts += 1
        return

    sender_thread = threading.Thread(target=sender)
    receiver_thread = threading.Thread(target=receiver)

    sender_thread.start()
    receiver_thread.start()

    sender_thread.join(timeout=10)
    receiver_thread.join(timeout=10)

    assert len(errors) == 0, (
        "No errors should occur during concurrent access, got: {!r}".format(errors)
    )
    assert len(sent_ids) == num_messages, (
        "All {} messages should be sent, got: {}".format(num_messages, len(sent_ids))
    )
    assert len(received_messages) == num_messages, (
        "All {} messages should be received, got: {}".format(num_messages, len(received_messages))
    )
    return


def test_messaging_concurrent_create_delete_queues():
    """
        Verify that concurrent queue creation and deletion does not
        corrupt the internal state.
    """
    svc = LocalMessagingService(platform_type=PlatformType.LOCAL)
    errors = []

    def creator():
        for i in range(20):
            try:
                svc.create_queue("q-{}".format(i))
            except Exception as exc:
                errors.append(str(exc))
        return

    def deleter():
        time.sleep(0.01)
        for i in range(20):
            try:
                svc.delete_queue("q-{}".format(i))
            except Exception as exc:
                errors.append(str(exc))
        return

    creator_thread = threading.Thread(target=creator)
    deleter_thread = threading.Thread(target=deleter)

    creator_thread.start()
    deleter_thread.start()

    creator_thread.join(timeout=10)
    deleter_thread.join(timeout=10)

    assert len(errors) == 0, (
        "No errors should occur during concurrent queue operations, got: {!r}".format(errors)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
