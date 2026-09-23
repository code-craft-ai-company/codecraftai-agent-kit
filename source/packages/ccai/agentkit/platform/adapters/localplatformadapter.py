"""
    Defines the LocalPlatformAdapter and its local service implementations
    for running agents in a local environment. Provides LocalComputeService
    (subprocess execution), LocalStorageService (file system storage), and
    LocalMessagingService (in-memory queuing).

    .. module:: ccai.agentkit.platform.adapters.localplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Local platform adapter with subprocess, filesystem, and in-memory services.
"""

import collections
import json
import logging
import os
import subprocess
import threading
import time
import uuid

from datetime import datetime

from ccai.agentkit.platform.adapters.platformadapter import PlatformAdapter
from ccai.agentkit.platform.errors import ComputeError
from ccai.agentkit.platform.errors import MessagingError
from ccai.agentkit.platform.errors import StorageError
from ccai.agentkit.platform.platformconfiguration import PlatformConfiguration
from ccai.agentkit.platform.platformtype import PlatformType
from ccai.agentkit.platform.services.computeservice import ComputeService
from ccai.agentkit.platform.services.invocationresult import InvocationResult
from ccai.agentkit.platform.services.messagingservice import MessagingService
from ccai.agentkit.platform.services.queuemessage import QueueMessage
from ccai.agentkit.platform.services.storageobject import StorageObject
from ccai.agentkit.platform.services.storageservice import StorageService


logger = logging.getLogger("ccai.agentkit.platform.adapters")


# ---------------------------------------------------------------------------
# LocalComputeService
# ---------------------------------------------------------------------------

class LocalComputeService(ComputeService):
    """
        Compute service implementation that executes functions as local
        subprocesses. Supports configurable timeout with a default of 30
        seconds. Returns InvocationResult with status "timeout" when the
        subprocess exceeds the configured timeout.

        :param platform_type: The PlatformType (expected to be LOCAL).
        :param configuration: An optional PlatformConfiguration.
        :param default_timeout: Default timeout in seconds for subprocess execution.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 default_timeout: float = 30.0) -> None:
        super().__init__(
            service_name="local-compute",
            platform_type=platform_type,
            configuration=configuration
        )
        self._default_timeout = default_timeout
        self._async_results = {}
        return

    def invoke(self, function_name: str, payload: dict,
               timeout: float = None) -> InvocationResult:
        """
            Invokes a function as a local subprocess.

            The function_name is treated as a shell command. The payload is
            serialized to JSON and passed as stdin to the subprocess.

            :param function_name: The command to execute.
            :param payload: Dictionary payload serialized as JSON stdin.
            :param timeout: Optional timeout in seconds, defaults to default_timeout.

            :returns: An InvocationResult with the execution outcome.
            :raises: ComputeError
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout
        request_id = str(uuid.uuid4())
        payload_json = json.dumps(payload)
        start_time = time.monotonic()

        try:
            completed = subprocess.run(
                function_name,
                input=payload_json,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                shell=True
            )
            duration = time.monotonic() - start_time

            if completed.returncode == 0:
                response = completed.stdout
                rtnval = InvocationResult(
                    status="success",
                    response=response,
                    duration=duration,
                    request_id=request_id
                )
            else:
                err_detail = completed.stderr if completed.stderr else "exit code {}".format(completed.returncode)
                rtnval = InvocationResult(
                    status="error",
                    response=completed.stdout,
                    error_message=err_detail,
                    duration=duration,
                    request_id=request_id
                )

        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start_time
            err_msg = "Subprocess timed out after {:.1f} seconds.".format(effective_timeout)
            rtnval = InvocationResult(
                status="timeout",
                error_message=err_msg,
                duration=duration,
                request_id=request_id
            )

        except Exception as exc:
            err_msg_lines = [
                "Local compute invocation failed.",
                "  Function: {!r}".format(function_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name=function_name,
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return rtnval

    def invoke_async(self, function_name: str, payload: dict) -> str:
        """
            Invokes a function asynchronously by spawning a thread that
            runs the subprocess. Returns a request identifier for tracking.

            :param function_name: The command to execute.
            :param payload: Dictionary payload serialized as JSON stdin.

            :returns: A request identifier string.
            :raises: ComputeError
        """
        request_id = str(uuid.uuid4())
        self._async_results[request_id] = None

        def _run():
            result = self.invoke(function_name, payload)
            self._async_results[request_id] = result
            return

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        rtnval = request_id
        return rtnval

    def get_invocation_status(self, request_id: str) -> InvocationResult:
        """
            Returns the current status of an asynchronous invocation.

            :param request_id: The request identifier from invoke_async.

            :returns: An InvocationResult or a pending result.
            :raises: ComputeError
        """
        if request_id not in self._async_results:
            err_msg_lines = [
                "Unknown async invocation request identifier.",
                "  Request ID: {!r}".format(request_id)
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name="unknown",
                platform_type=PlatformType.LOCAL
            )

        result = self._async_results[request_id]
        if result is None:
            rtnval = InvocationResult(
                status="pending",
                request_id=request_id
            )
        else:
            rtnval = result

        return rtnval

    def list_functions(self) -> list:
        """
            Returns an empty list since local compute does not maintain
            a function registry.

            :returns: An empty list.
        """
        rtnval = []
        return rtnval

    def is_available(self) -> bool:
        """
            Local compute is always available.

            :returns: True.
        """
        rtnval = True
        return rtnval

    def health_check(self) -> bool:
        """
            Local compute health check verifies subprocess execution works.

            :returns: True if a simple subprocess can be executed.
        """
        try:
            completed = subprocess.run(
                "echo ok",
                capture_output=True,
                text=True,
                timeout=5.0,
                shell=True
            )
            rtnval = completed.returncode == 0
        except Exception:
            rtnval = False

        return rtnval


# ---------------------------------------------------------------------------
# LocalStorageService
# ---------------------------------------------------------------------------

class LocalStorageService(StorageService):
    """
        Storage service implementation that stores objects as files on the
        local file system. Objects are stored under
        {base_directory}/{container_name}/{object_key} with companion
        .meta.json files for metadata.

        :param platform_type: The PlatformType (expected to be LOCAL).
        :param configuration: An optional PlatformConfiguration.
        :param base_directory: The base directory for file storage.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 base_directory: str = None) -> None:
        super().__init__(
            service_name="local-storage",
            platform_type=platform_type,
            configuration=configuration
        )
        self._base_directory = base_directory if base_directory is not None else os.path.join(os.getcwd(), ".local-storage")
        return

    def _container_path(self, container_name: str) -> str:
        """
            Returns the file system path for a container.

            :param container_name: Name of the container.

            :returns: The absolute path string.
        """
        rtnval = os.path.join(self._base_directory, container_name)
        return rtnval

    def _object_path(self, container_name: str, object_key: str) -> str:
        """
            Returns the file system path for an object within a container.

            :param container_name: Name of the container.
            :param object_key: Key identifying the object.

            :returns: The absolute path string.
        """
        rtnval = os.path.join(self._base_directory, container_name, object_key)
        return rtnval

    def _meta_path(self, container_name: str, object_key: str) -> str:
        """
            Returns the file system path for the metadata companion file.

            :param container_name: Name of the container.
            :param object_key: Key identifying the object.

            :returns: The absolute path string for the .meta.json file.
        """
        rtnval = os.path.join(self._base_directory, container_name, object_key + ".meta.json")
        return rtnval

    def put_object(self, container_name: str, object_key: str,
                   content: bytes, content_type: str = None,
                   metadata: dict = None) -> None:
        """
            Stores an object as a file in the specified container directory.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.
            :param content: Object content as bytes.
            :param content_type: Optional MIME content type string.
            :param metadata: Optional metadata dictionary.

            :raises: StorageError
        """
        obj_path = self._object_path(container_name, object_key)
        meta_path = self._meta_path(container_name, object_key)

        try:
            obj_dir = os.path.dirname(obj_path)
            if not os.path.exists(obj_dir):
                os.makedirs(obj_dir, exist_ok=True)

            with open(obj_path, "wb") as fh:
                fh.write(content)

            meta = {
                "content_type": content_type if content_type is not None else "application/octet-stream",
                "metadata": dict(metadata) if metadata is not None else {},
                "size": len(content),
                "last_modified": datetime.utcnow().isoformat()
            }
            with open(meta_path, "w") as fh:
                json.dump(meta, fh)

        except Exception as exc:
            err_msg_lines = [
                "Failed to store object in local storage.",
                "  Container: {!r}".format(container_name),
                "  Object key: {!r}".format(object_key),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="put_object",
                container_name=container_name,
                object_key=object_key,
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return

    def get_object(self, container_name: str, object_key: str) -> StorageObject:
        """
            Retrieves an object from the specified container directory.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.

            :returns: A StorageObject instance.
            :raises: StorageError
        """
        obj_path = self._object_path(container_name, object_key)
        meta_path = self._meta_path(container_name, object_key)

        if not os.path.exists(obj_path):
            err_msg_lines = [
                "Object not found in local storage.",
                "  Container: {!r}".format(container_name),
                "  Object key: {!r}".format(object_key)
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="get_object",
                container_name=container_name,
                object_key=object_key,
                platform_type=PlatformType.LOCAL
            )

        try:
            with open(obj_path, "rb") as fh:
                content = fh.read()

            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, "r") as fh:
                    meta = json.load(fh)

            content_type = meta.get("content_type", "application/octet-stream")
            metadata = meta.get("metadata", {})
            size = meta.get("size", len(content))
            last_modified_str = meta.get("last_modified")
            last_modified = datetime.fromisoformat(last_modified_str) if last_modified_str is not None else None

            rtnval = StorageObject(
                key=object_key,
                content=content,
                content_type=content_type,
                metadata=metadata,
                size=size,
                last_modified=last_modified
            )

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to retrieve object from local storage.",
                "  Container: {!r}".format(container_name),
                "  Object key: {!r}".format(object_key),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="get_object",
                container_name=container_name,
                object_key=object_key,
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return rtnval

    def delete_object(self, container_name: str, object_key: str) -> None:
        """
            Removes an object file and its metadata companion from the
            specified container directory.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.

            :raises: StorageError
        """
        obj_path = self._object_path(container_name, object_key)
        meta_path = self._meta_path(container_name, object_key)

        try:
            if os.path.exists(obj_path):
                os.remove(obj_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
        except Exception as exc:
            err_msg_lines = [
                "Failed to delete object from local storage.",
                "  Container: {!r}".format(container_name),
                "  Object key: {!r}".format(object_key),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="delete_object",
                container_name=container_name,
                object_key=object_key,
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return

    def list_objects(self, container_name: str, prefix: str = None) -> list:
        """
            Returns a list of object key strings in the specified container,
            optionally filtered by prefix. Excludes .meta.json companion files.

            :param container_name: Name of the storage container.
            :param prefix: Optional prefix filter string.

            :returns: List of object key strings.
            :raises: StorageError
        """
        container_path = self._container_path(container_name)

        if not os.path.exists(container_path):
            rtnval = []
            return rtnval

        try:
            keys = []
            for root, dirs, files in os.walk(container_path):
                for file_name in files:
                    if file_name.endswith(".meta.json"):
                        continue
                    full_path = os.path.join(root, file_name)
                    relative_key = os.path.relpath(full_path, container_path)
                    if prefix is not None and not relative_key.startswith(prefix):
                        continue
                    keys.append(relative_key)

            rtnval = sorted(keys)

        except Exception as exc:
            err_msg_lines = [
                "Failed to list objects in local storage.",
                "  Container: {!r}".format(container_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="list_objects",
                container_name=container_name,
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return rtnval

    def object_exists(self, container_name: str, object_key: str) -> bool:
        """
            Checks whether an object file exists in the specified container.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.

            :returns: True if the object exists, False otherwise.
            :raises: StorageError
        """
        obj_path = self._object_path(container_name, object_key)
        rtnval = os.path.exists(obj_path)
        return rtnval

    def create_container(self, container_name: str) -> None:
        """
            Creates a container directory.

            :param container_name: Name of the container to create.

            :raises: StorageError
        """
        container_path = self._container_path(container_name)

        try:
            os.makedirs(container_path, exist_ok=True)
        except Exception as exc:
            err_msg_lines = [
                "Failed to create container in local storage.",
                "  Container: {!r}".format(container_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="create_container",
                container_name=container_name,
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return

    def delete_container(self, container_name: str) -> None:
        """
            Removes a container directory and all its contents.

            :param container_name: Name of the container to remove.

            :raises: StorageError
        """
        container_path = self._container_path(container_name)

        try:
            if os.path.exists(container_path):
                import shutil
                shutil.rmtree(container_path)
        except Exception as exc:
            err_msg_lines = [
                "Failed to delete container from local storage.",
                "  Container: {!r}".format(container_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="delete_container",
                container_name=container_name,
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return

    def list_containers(self) -> list:
        """
            Returns a list of container name strings (subdirectories under
            the base directory).

            :returns: List of container name strings.
            :raises: StorageError
        """
        if not os.path.exists(self._base_directory):
            rtnval = []
            return rtnval

        try:
            containers = []
            for entry in os.listdir(self._base_directory):
                entry_path = os.path.join(self._base_directory, entry)
                if os.path.isdir(entry_path):
                    containers.append(entry)

            rtnval = sorted(containers)

        except Exception as exc:
            err_msg_lines = [
                "Failed to list containers in local storage.",
                "  Base directory: {!r}".format(self._base_directory),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="list_containers",
                container_name="",
                cause=exc,
                platform_type=PlatformType.LOCAL
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Local storage is available when the base directory exists or
            can be created.

            :returns: True if available.
        """
        try:
            os.makedirs(self._base_directory, exist_ok=True)
            rtnval = True
        except Exception:
            rtnval = False

        return rtnval

    def health_check(self) -> bool:
        """
            Local storage health check verifies the base directory is
            accessible.

            :returns: True if the base directory is writable.
        """
        try:
            os.makedirs(self._base_directory, exist_ok=True)
            test_path = os.path.join(self._base_directory, ".health_check")
            with open(test_path, "w") as fh:
                fh.write("ok")
            os.remove(test_path)
            rtnval = True
        except Exception:
            rtnval = False

        return rtnval


# ---------------------------------------------------------------------------
# LocalMessagingService
# ---------------------------------------------------------------------------

class LocalMessagingService(MessagingService):
    """
        Messaging service implementation that uses in-memory queues backed
        by collections.deque with threading.Lock for concurrent access.

        Messages are QueueMessage instances stored in per-queue deques.
        Acknowledged messages are removed from the pending set.

        :param platform_type: The PlatformType (expected to be LOCAL).
        :param configuration: An optional PlatformConfiguration.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None) -> None:
        super().__init__(
            service_name="local-messaging",
            platform_type=platform_type,
            configuration=configuration
        )
        self._queues = {}
        self._pending = {}
        self._lock = threading.Lock()
        return

    def send_message(self, queue_name: str, body: object,
                     attributes: dict = None) -> str:
        """
            Sends a message to the specified in-memory queue.

            :param queue_name: Name of the target queue.
            :param body: Message body as a Python object.
            :param attributes: Optional message attributes dictionary.

            :returns: A message identifier string.
            :raises: MessagingError
        """
        with self._lock:
            if queue_name not in self._queues:
                err_msg_lines = [
                    "Queue does not exist.",
                    "  Queue name: {!r}".format(queue_name)
                ]
                err_msg = os.linesep.join(err_msg_lines)
                logger.warning("%s", err_msg)
                raise MessagingError(
                    err_msg,
                    queue_name=queue_name,
                    platform_type=PlatformType.LOCAL
                )

            message_id = str(uuid.uuid4())
            receipt_handle = str(uuid.uuid4())
            message = QueueMessage(
                identifier=message_id,
                queue_name=queue_name,
                body=body,
                attributes=attributes,
                receipt_handle=receipt_handle,
                timestamp=datetime.utcnow()
            )
            self._queues[queue_name].append(message)

        rtnval = message_id
        return rtnval

    def receive_messages(self, queue_name: str, max_count: int = 1,
                         wait_time: float = None) -> list:
        """
            Receives messages from the specified in-memory queue.

            Messages are moved from the queue to a pending set until
            acknowledged. If wait_time is specified and the queue is empty,
            this method will poll briefly before returning.

            :param queue_name: Name of the source queue.
            :param max_count: Maximum number of messages to receive.
            :param wait_time: Optional wait time in seconds.

            :returns: A list of QueueMessage objects.
            :raises: MessagingError
        """
        with self._lock:
            if queue_name not in self._queues:
                err_msg_lines = [
                    "Queue does not exist.",
                    "  Queue name: {!r}".format(queue_name)
                ]
                err_msg = os.linesep.join(err_msg_lines)
                logger.warning("%s", err_msg)
                raise MessagingError(
                    err_msg,
                    queue_name=queue_name,
                    platform_type=PlatformType.LOCAL
                )

        messages = []
        deadline = time.monotonic() + (wait_time if wait_time is not None else 0)

        while True:
            with self._lock:
                queue = self._queues.get(queue_name)
                if queue is None:
                    break

                while len(messages) < max_count and len(queue) > 0:
                    msg = queue.popleft()
                    messages.append(msg)
                    if queue_name not in self._pending:
                        self._pending[queue_name] = {}
                    self._pending[queue_name][msg.receipt_handle] = msg

            if len(messages) >= max_count:
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(0.01)

        rtnval = messages
        return rtnval

    def acknowledge_message(self, queue_name: str, receipt_handle: str) -> None:
        """
            Acknowledges a message for deletion from the pending set.

            :param queue_name: Name of the queue.
            :param receipt_handle: Receipt handle string for the message.

            :raises: MessagingError
        """
        with self._lock:
            pending_for_queue = self._pending.get(queue_name, {})
            if receipt_handle in pending_for_queue:
                del pending_for_queue[receipt_handle]

        return

    def create_queue(self, queue_name: str) -> None:
        """
            Creates an in-memory queue.

            :param queue_name: Name of the queue to create.

            :raises: MessagingError
        """
        with self._lock:
            if queue_name not in self._queues:
                self._queues[queue_name] = collections.deque()
                self._pending[queue_name] = {}

        return

    def delete_queue(self, queue_name: str) -> None:
        """
            Removes an in-memory queue and its pending messages.

            :param queue_name: Name of the queue to remove.

            :raises: MessagingError
        """
        with self._lock:
            if queue_name in self._queues:
                del self._queues[queue_name]
            if queue_name in self._pending:
                del self._pending[queue_name]

        return

    def list_queues(self) -> list:
        """
            Returns a list of queue name strings.

            :returns: List of queue name strings.
        """
        with self._lock:
            rtnval = sorted(list(self._queues.keys()))

        return rtnval

    def is_available(self) -> bool:
        """
            Local messaging is always available.

            :returns: True.
        """
        rtnval = True
        return rtnval

    def health_check(self) -> bool:
        """
            Local messaging health check always returns True.

            :returns: True.
        """
        rtnval = True
        return rtnval


# ---------------------------------------------------------------------------
# LocalPlatformAdapter
# ---------------------------------------------------------------------------

class LocalPlatformAdapter(PlatformAdapter):
    """
        PlatformAdapter implementation providing local environment service
        implementations using subprocess execution, file system storage,
        and in-memory message queuing.

        :param configuration: The PlatformConfiguration for the local platform.
    """

    def __init__(self, configuration: PlatformConfiguration) -> None:
        super().__init__(configuration=configuration)
        base_dir = self._resolve_base_directory()
        self._compute_service = LocalComputeService(
            platform_type=PlatformType.LOCAL,
            configuration=configuration,
            default_timeout=30.0
        )
        self._storage_service = LocalStorageService(
            platform_type=PlatformType.LOCAL,
            configuration=configuration,
            base_directory=base_dir
        )
        self._messaging_service = LocalMessagingService(
            platform_type=PlatformType.LOCAL,
            configuration=configuration
        )
        return

    @property
    def platform_type(self) -> PlatformType:
        """
            Returns PlatformType.LOCAL.

            :returns: PlatformType.LOCAL.
        """
        rtnval = PlatformType.LOCAL
        return rtnval

    def get_compute_service(self) -> ComputeService:
        """
            Returns the LocalComputeService instance.

            :returns: The LocalComputeService.
        """
        rtnval = self._compute_service
        return rtnval

    def get_storage_service(self) -> StorageService:
        """
            Returns the LocalStorageService instance.

            :returns: The LocalStorageService.
        """
        rtnval = self._storage_service
        return rtnval

    def get_messaging_service(self) -> MessagingService:
        """
            Returns the LocalMessagingService instance.

            :returns: The LocalMessagingService.
        """
        rtnval = self._messaging_service
        return rtnval

    def _resolve_base_directory(self) -> str:
        """
            Resolves the base directory for local storage from configuration
            options, falling back to a .local-storage directory under the
            current working directory.

            :returns: The resolved base directory path string.
        """
        if self._configuration is not None:
            options = self._configuration.options
            if "storage_base_directory" in options:
                rtnval = options["storage_base_directory"]
                return rtnval

        rtnval = os.path.join(os.getcwd(), ".local-storage")
        return rtnval
