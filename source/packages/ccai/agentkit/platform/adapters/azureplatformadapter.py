"""
    Defines the AzurePlatformAdapter and its Azure service implementations
    for running agents on Microsoft Azure. Provides AzureComputeService
    (Azure Functions), AzureStorageService (Azure Blob Storage), and
    AzureMessagingService (Azure Service Bus).

    .. module:: ccai.agentkit.platform.adapters.azureplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Azure platform adapter with Functions, Blob Storage, and Service Bus services.
"""

import json
import logging
import os
import time
import uuid

from datetime import datetime
from typing import Optional

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
# AzureComputeService
# ---------------------------------------------------------------------------

class AzureComputeService(ComputeService):
    """
        Compute service implementation that wraps Azure Functions invocation
        via the Azure SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be AZURE).
        :param configuration: An optional PlatformConfiguration.
        :param region: The Azure region string.
        :param functions_client: An optional pre-configured Azure Functions client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 functions_client=None) -> None:
        super().__init__(
            service_name="azure-functions",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._functions_client = functions_client
        return

    def _get_client(self):
        """
            Returns the Azure Functions client, creating one if not already
            provided.

            :returns: An Azure Functions client.
            :raises: ComputeError
        """
        if self._functions_client is not None:
            rtnval = self._functions_client
            return rtnval

        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.web import WebSiteManagementClient

            credential = None
            if self._configuration is not None:
                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    credential = first_cred

            if credential is None:
                credential = DefaultAzureCredential()

            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "")

            client_kwargs = {}
            if self._configuration is not None:
                overrides = self._configuration.service_endpoint_overrides
                if "functions" in overrides:
                    client_kwargs["base_url"] = overrides["functions"]

            self._functions_client = WebSiteManagementClient(
                credential=credential,
                subscription_id=subscription_id,
                **client_kwargs
            )
            rtnval = self._functions_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create Azure Functions client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name="client_init",
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def invoke(self, function_name: str, payload: dict,
               timeout: float = None) -> InvocationResult:
        """
            Invokes an Azure Function synchronously via HTTP trigger.

            :param function_name: Name of the Azure Function to invoke.
            :param payload: Dictionary payload serialized as JSON.
            :param timeout: Optional timeout in seconds.

            :returns: An InvocationResult with the execution outcome.
            :raises: ComputeError
        """
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        try:
            client = self._get_client()

            response = client.invoke(
                function_name=function_name,
                payload=payload,
                timeout=timeout
            )

            duration = time.monotonic() - start_time

            if hasattr(response, "status_code"):
                status_code = response.status_code
            else:
                status_code = getattr(response, "status", 200)

            if hasattr(response, "text"):
                response_body = response.text
            elif hasattr(response, "content"):
                response_body = response.content
            else:
                response_body = str(response)

            if status_code >= 400:
                rtnval = InvocationResult(
                    status="error",
                    response=response_body,
                    error_message="HTTP {}".format(status_code),
                    duration=duration,
                    request_id=request_id
                )
            else:
                rtnval = InvocationResult(
                    status="success",
                    response=response_body,
                    duration=duration,
                    request_id=request_id
                )

        except ComputeError:
            raise

        except Exception as exc:
            duration = time.monotonic() - start_time
            err_msg_lines = [
                "Azure Functions invocation failed.",
                "  Function: {!r}".format(function_name),
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name=function_name,
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def invoke_async(self, function_name: str, payload: dict) -> str:
        """
            Invokes an Azure Function asynchronously.

            :param function_name: Name of the Azure Function to invoke.
            :param payload: Dictionary payload serialized as JSON.

            :returns: A request identifier string.
            :raises: ComputeError
        """
        request_id = str(uuid.uuid4())

        try:
            client = self._get_client()
            client.invoke(
                function_name=function_name,
                payload=payload,
                async_mode=True
            )

        except ComputeError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Azure Functions async invocation failed.",
                "  Function: {!r}".format(function_name),
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name=function_name,
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        rtnval = request_id
        return rtnval

    def get_invocation_status(self, request_id: str) -> InvocationResult:
        """
            Returns a status for async invocations.

            :param request_id: The request identifier from invoke_async.

            :returns: An InvocationResult representing the current status.
            :raises: ComputeError
        """
        rtnval = InvocationResult(
            status="success",
            response=None,
            request_id=request_id
        )
        return rtnval

    def list_functions(self) -> list:
        """
            Returns a list of available Azure Function names.

            :returns: List of function name strings.
            :raises: ComputeError
        """
        try:
            client = self._get_client()
            response = client.list_functions()
            functions = getattr(response, "value", response) if response is not None else []
            rtnval = [getattr(f, "name", str(f)) for f in functions]

        except ComputeError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list Azure Functions.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name="list_functions",
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the Azure Functions service is available.

            :returns: True if available, False otherwise.
        """
        try:
            self.list_functions()
            rtnval = True
        except Exception:
            rtnval = False

        return rtnval

    def health_check(self) -> bool:
        """
            Health check for Azure Functions service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# AzureStorageService
# ---------------------------------------------------------------------------

class AzureStorageService(StorageService):
    """
        Storage service implementation that wraps Azure Blob Storage
        operations via the Azure SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be AZURE).
        :param configuration: An optional PlatformConfiguration.
        :param region: The Azure region string.
        :param blob_service_client: An optional pre-configured Azure Blob Service client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 blob_service_client=None) -> None:
        super().__init__(
            service_name="azure-blob-storage",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._blob_service_client = blob_service_client
        return

    def _get_client(self):
        """
            Returns the Azure Blob Service client, creating one if not
            already provided.

            :returns: An Azure BlobServiceClient.
            :raises: StorageError
        """
        if self._blob_service_client is not None:
            rtnval = self._blob_service_client
            return rtnval

        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient

            credential = None
            if self._configuration is not None:
                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    credential = first_cred

            if credential is None:
                credential = DefaultAzureCredential()

            account_url = None
            if self._configuration is not None:
                overrides = self._configuration.service_endpoint_overrides
                if "blob_storage" in overrides:
                    account_url = overrides["blob_storage"]

            if account_url is None:
                account_name = os.environ.get("AZURE_STORAGE_ACCOUNT", "")
                account_url = "https://{}.blob.core.windows.net".format(account_name)

            self._blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )
            rtnval = self._blob_service_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create Azure Blob Storage client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="client_init",
                container_name="",
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def put_object(self, container_name: str, object_key: str,
                   content: bytes, content_type: str = None,
                   metadata: dict = None) -> None:
        """
            Stores an object in an Azure Blob Storage container.

            :param container_name: Name of the blob container.
            :param object_key: Key identifying the blob.
            :param content: Object content as bytes.
            :param content_type: Optional MIME content type string.
            :param metadata: Optional metadata dictionary.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=container_name,
                blob=object_key
            )

            upload_kwargs = {}
            if content_type is not None:
                from azure.storage.blob import ContentSettings
                upload_kwargs["content_settings"] = ContentSettings(
                    content_type=content_type
                )

            if metadata is not None:
                upload_kwargs["metadata"] = metadata

            blob_client.upload_blob(content, overwrite=True, **upload_kwargs)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to put object in Azure Blob Storage.",
                "  Container: {!r}".format(container_name),
                "  Key: {!r}".format(object_key),
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
                platform_type=PlatformType.AZURE
            )

        return

    def get_object(self, container_name: str, object_key: str) -> StorageObject:
        """
            Retrieves an object from an Azure Blob Storage container.

            :param container_name: Name of the blob container.
            :param object_key: Key identifying the blob.

            :returns: A StorageObject instance.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=container_name,
                blob=object_key
            )

            download = blob_client.download_blob()
            content = download.readall()

            properties = blob_client.get_blob_properties()
            content_type = getattr(
                getattr(properties, "content_settings", None),
                "content_type", "application/octet-stream"
            )
            metadata = getattr(properties, "metadata", {}) or {}
            size = getattr(properties, "size", len(content))
            last_modified = getattr(properties, "last_modified", None)

            rtnval = StorageObject(
                key=object_key,
                content=content,
                content_type=content_type if content_type is not None else "application/octet-stream",
                metadata=metadata,
                size=size,
                last_modified=last_modified
            )

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to get object from Azure Blob Storage.",
                "  Container: {!r}".format(container_name),
                "  Key: {!r}".format(object_key),
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
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def delete_object(self, container_name: str, object_key: str) -> None:
        """
            Removes a blob from an Azure Blob Storage container.

            :param container_name: Name of the blob container.
            :param object_key: Key identifying the blob.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=container_name,
                blob=object_key
            )
            blob_client.delete_blob()

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete object from Azure Blob Storage.",
                "  Container: {!r}".format(container_name),
                "  Key: {!r}".format(object_key),
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
                platform_type=PlatformType.AZURE
            )

        return

    def list_objects(self, container_name: str, prefix: str = None) -> list:
        """
            Returns a list of blob names in an Azure container.

            :param container_name: Name of the blob container.
            :param prefix: Optional prefix filter string.

            :returns: List of blob name strings.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            container_client = client.get_container_client(container_name)

            list_kwargs = {}
            if prefix is not None:
                list_kwargs["name_starts_with"] = prefix

            blobs = container_client.list_blobs(**list_kwargs)
            rtnval = [blob.name for blob in blobs]

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list objects in Azure Blob Storage.",
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
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def object_exists(self, container_name: str, object_key: str) -> bool:
        """
            Checks whether a blob exists in an Azure container.

            :param container_name: Name of the blob container.
            :param object_key: Key identifying the blob.

            :returns: True if the blob exists, False otherwise.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            blob_client = client.get_blob_client(
                container=container_name,
                blob=object_key
            )
            blob_client.get_blob_properties()
            rtnval = True

        except StorageError:
            raise

        except Exception as exc:
            error_code = getattr(exc, "error_code", "")
            if error_code == "BlobNotFound" or "BlobNotFound" in str(exc):
                rtnval = False
            else:
                err_msg_lines = [
                    "Failed to check object existence in Azure Blob Storage.",
                    "  Container: {!r}".format(container_name),
                    "  Key: {!r}".format(object_key),
                    "  Error: {}".format(str(exc))
                ]
                err_msg = os.linesep.join(err_msg_lines)
                logger.warning("%s", err_msg)
                raise StorageError(
                    err_msg,
                    operation_name="object_exists",
                    container_name=container_name,
                    object_key=object_key,
                    cause=exc,
                    platform_type=PlatformType.AZURE
                )

        return rtnval

    def create_container(self, container_name: str) -> None:
        """
            Creates an Azure Blob Storage container.

            :param container_name: Name of the container to create.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            client.create_container(container_name)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to create container in Azure Blob Storage.",
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
                platform_type=PlatformType.AZURE
            )

        return

    def delete_container(self, container_name: str) -> None:
        """
            Removes an Azure Blob Storage container.

            :param container_name: Name of the container to remove.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            client.delete_container(container_name)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete container from Azure Blob Storage.",
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
                platform_type=PlatformType.AZURE
            )

        return

    def list_containers(self) -> list:
        """
            Returns a list of Azure Blob Storage container names.

            :returns: List of container name strings.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            containers = client.list_containers()
            rtnval = [c.name for c in containers]

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list containers in Azure Blob Storage.",
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="list_containers",
                container_name="",
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the Azure Blob Storage service is available.

            :returns: True if available, False otherwise.
        """
        try:
            self.list_containers()
            rtnval = True
        except Exception:
            rtnval = False

        return rtnval

    def health_check(self) -> bool:
        """
            Health check for Azure Blob Storage service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# AzureMessagingService
# ---------------------------------------------------------------------------

class AzureMessagingService(MessagingService):
    """
        Messaging service implementation that wraps Azure Service Bus
        operations via the Azure SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be AZURE).
        :param configuration: An optional PlatformConfiguration.
        :param region: The Azure region string.
        :param servicebus_client: An optional pre-configured Azure Service Bus client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 servicebus_client=None) -> None:
        super().__init__(
            service_name="azure-service-bus",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._servicebus_client = servicebus_client
        return

    def _get_client(self):
        """
            Returns the Azure Service Bus client, creating one if not
            already provided.

            :returns: An Azure ServiceBusClient.
            :raises: MessagingError
        """
        if self._servicebus_client is not None:
            rtnval = self._servicebus_client
            return rtnval

        try:
            from azure.identity import DefaultAzureCredential
            from azure.servicebus import ServiceBusClient

            credential = None
            if self._configuration is not None:
                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    credential = first_cred

            if credential is None:
                credential = DefaultAzureCredential()

            namespace = None
            if self._configuration is not None:
                overrides = self._configuration.service_endpoint_overrides
                if "service_bus" in overrides:
                    namespace = overrides["service_bus"]

            if namespace is None:
                namespace = os.environ.get(
                    "AZURE_SERVICEBUS_NAMESPACE",
                    ""
                )

            self._servicebus_client = ServiceBusClient(
                fully_qualified_namespace=namespace,
                credential=credential
            )
            rtnval = self._servicebus_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create Azure Service Bus client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name="",
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def send_message(self, queue_name: str, body: object,
                     attributes: dict = None) -> str:
        """
            Sends a message to an Azure Service Bus queue.

            :param queue_name: Name of the target queue.
            :param body: Message body as a Python object (serialized to JSON).
            :param attributes: Optional message attributes dictionary.

            :returns: A message identifier string.
            :raises: MessagingError
        """
        try:
            client = self._get_client()
            from azure.servicebus import ServiceBusMessage

            message_body = json.dumps(body)
            message = ServiceBusMessage(message_body)

            if attributes is not None:
                message.application_properties = attributes

            sender = client.get_queue_sender(queue_name=queue_name)
            sender.send_messages(message)

            message_id = getattr(message, "message_id", str(uuid.uuid4()))
            rtnval = str(message_id)

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to send message to Azure Service Bus.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def receive_messages(self, queue_name: str, max_count: int = 1,
                         wait_time: float = None) -> list:
        """
            Receives messages from an Azure Service Bus queue.

            :param queue_name: Name of the source queue.
            :param max_count: Maximum number of messages to receive.
            :param wait_time: Optional wait time in seconds.

            :returns: A list of QueueMessage objects.
            :raises: MessagingError
        """
        try:
            client = self._get_client()
            receiver = client.get_queue_receiver(queue_name=queue_name)

            receive_kwargs = {
                "max_message_count": max_count
            }
            if wait_time is not None:
                receive_kwargs["max_wait_time"] = wait_time

            sb_messages = receiver.receive_messages(**receive_kwargs)

            messages = []
            for sb_msg in sb_messages:
                msg_body_str = str(sb_msg)
                try:
                    msg_body = json.loads(msg_body_str)
                except (json.JSONDecodeError, TypeError):
                    msg_body = msg_body_str

                msg_attrs = getattr(sb_msg, "application_properties", {}) or {}
                msg_id = str(getattr(sb_msg, "message_id", uuid.uuid4()))
                lock_token = str(getattr(sb_msg, "lock_token", ""))

                message = QueueMessage(
                    identifier=msg_id,
                    queue_name=queue_name,
                    body=msg_body,
                    attributes=msg_attrs,
                    receipt_handle=lock_token,
                    timestamp=datetime.utcnow()
                )
                messages.append(message)

            rtnval = messages

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to receive messages from Azure Service Bus.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def acknowledge_message(self, queue_name: str, receipt_handle: str) -> None:
        """
            Acknowledges a message by completing it in Azure Service Bus.

            :param queue_name: Name of the queue.
            :param receipt_handle: Lock token string for the message.

            :raises: MessagingError
        """
        try:
            client = self._get_client()
            receiver = client.get_queue_receiver(queue_name=queue_name)
            receiver.complete_message(receipt_handle)

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to acknowledge message in Azure Service Bus.",
                "  Queue name: {!r}".format(queue_name),
                "  Receipt handle: {!r}".format(receipt_handle),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return

    def create_queue(self, queue_name: str) -> None:
        """
            Creates an Azure Service Bus queue.

            :param queue_name: Name of the queue to create.

            :raises: MessagingError
        """
        try:
            client = self._get_client()
            admin = client.get_queue_admin()
            admin.create_queue(queue_name)

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to create queue in Azure Service Bus.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return

    def delete_queue(self, queue_name: str) -> None:
        """
            Removes an Azure Service Bus queue.

            :param queue_name: Name of the queue to remove.

            :raises: MessagingError
        """
        try:
            client = self._get_client()
            admin = client.get_queue_admin()
            admin.delete_queue(queue_name)

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete queue from Azure Service Bus.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return

    def list_queues(self) -> list:
        """
            Returns a list of Azure Service Bus queue names.

            :returns: List of queue name strings.
            :raises: MessagingError
        """
        try:
            client = self._get_client()
            admin = client.get_queue_admin()
            queues = admin.list_queues()
            rtnval = [getattr(q, "name", str(q)) for q in queues]

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list queues in Azure Service Bus.",
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name="",
                cause=exc,
                platform_type=PlatformType.AZURE
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the Azure Service Bus service is available.

            :returns: True if available, False otherwise.
        """
        try:
            self.list_queues()
            rtnval = True
        except Exception:
            rtnval = False

        return rtnval

    def health_check(self) -> bool:
        """
            Health check for Azure Service Bus service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# AzurePlatformAdapter
# ---------------------------------------------------------------------------

class AzurePlatformAdapter(PlatformAdapter):
    """
        PlatformAdapter implementation providing Azure-specific service
        implementations using Azure SDK clients for Functions, Blob Storage,
        and Service Bus.

        Resolves Azure credentials through CredentialReference entries in the
        PlatformConfiguration, falling back to the default Azure credential
        chain when no explicit credentials are configured.

        :param configuration: The PlatformConfiguration for the Azure platform.
        :param functions_client: An optional pre-configured Azure Functions client.
        :param blob_service_client: An optional pre-configured Azure Blob Service client.
        :param servicebus_client: An optional pre-configured Azure Service Bus client.
    """

    def __init__(self, configuration: PlatformConfiguration,
                 functions_client=None, blob_service_client=None,
                 servicebus_client=None) -> None:
        super().__init__(configuration=configuration)
        self._region = self._resolve_region()
        self._compute_service = AzureComputeService(
            platform_type=PlatformType.AZURE,
            configuration=configuration,
            region=self._region,
            functions_client=functions_client
        )
        self._storage_service = AzureStorageService(
            platform_type=PlatformType.AZURE,
            configuration=configuration,
            region=self._region,
            blob_service_client=blob_service_client
        )
        self._messaging_service = AzureMessagingService(
            platform_type=PlatformType.AZURE,
            configuration=configuration,
            region=self._region,
            servicebus_client=servicebus_client
        )
        return

    @property
    def platform_type(self) -> PlatformType:
        """
            Returns PlatformType.AZURE.

            :returns: PlatformType.AZURE.
        """
        rtnval = PlatformType.AZURE
        return rtnval

    def get_compute_service(self) -> ComputeService:
        """
            Returns the AzureComputeService instance.

            :returns: The AzureComputeService.
        """
        rtnval = self._compute_service
        return rtnval

    def get_storage_service(self) -> StorageService:
        """
            Returns the AzureStorageService instance.

            :returns: The AzureStorageService.
        """
        rtnval = self._storage_service
        return rtnval

    def get_messaging_service(self) -> MessagingService:
        """
            Returns the AzureMessagingService instance.

            :returns: The AzureMessagingService.
        """
        rtnval = self._messaging_service
        return rtnval

    def _resolve_region(self) -> str:
        """
            Resolves the Azure region from configuration, falling back to
            the AZURE_REGION environment variable, defaulting to eastus.

            :returns: The resolved region string.
        """
        if self._configuration is not None and self._configuration.region is not None:
            rtnval = self._configuration.region
            return rtnval

        rtnval = os.environ.get("AZURE_REGION", "eastus")
        return rtnval
