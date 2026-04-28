"""
    Defines the GcpPlatformAdapter and its GCP service implementations
    for running agents on Google Cloud Platform. Provides GcpComputeService
    (GCP Cloud Functions), GcpStorageService (GCP Cloud Storage), and
    GcpMessagingService (GCP Pub/Sub).

    .. module:: automojo.agentkit.platform.adapters.gcpplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: GCP platform adapter with Cloud Functions, Cloud Storage, and Pub/Sub services.
"""

import json
import logging
import os
import time
import uuid

from datetime import datetime
from typing import Optional

from automojo.agentkit.platform.adapters.platformadapter import PlatformAdapter
from automojo.agentkit.platform.errors import ComputeError
from automojo.agentkit.platform.errors import MessagingError
from automojo.agentkit.platform.errors import StorageError
from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration
from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.computeservice import ComputeService
from automojo.agentkit.platform.services.invocationresult import InvocationResult
from automojo.agentkit.platform.services.messagingservice import MessagingService
from automojo.agentkit.platform.services.queuemessage import QueueMessage
from automojo.agentkit.platform.services.storageobject import StorageObject
from automojo.agentkit.platform.services.storageservice import StorageService


logger = logging.getLogger("automojo.agentkit.platform.adapters")


# ---------------------------------------------------------------------------
# GcpComputeService
# ---------------------------------------------------------------------------

class GcpComputeService(ComputeService):
    """
        Compute service implementation that wraps GCP Cloud Functions
        invocation via the GCP SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be GCP).
        :param configuration: An optional PlatformConfiguration.
        :param region: The GCP region string.
        :param functions_client: An optional pre-configured GCP Cloud Functions client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 functions_client=None) -> None:
        super().__init__(
            service_name="gcp-cloud-functions",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._functions_client = functions_client
        self._project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        return

    def _get_client(self):
        """
            Returns the GCP Cloud Functions client, creating one if not
            already provided.

            :returns: A GCP Cloud Functions client.
            :raises: ComputeError
        """
        if self._functions_client is not None:
            rtnval = self._functions_client
            return rtnval

        try:
            from google.cloud import functions_v2

            client_kwargs = {}

            if self._configuration is not None:
                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    client_kwargs["credentials"] = first_cred

                overrides = self._configuration.service_endpoint_overrides
                if "functions" in overrides:
                    client_kwargs["client_options"] = {
                        "api_endpoint": overrides["functions"]
                    }

            self._functions_client = functions_v2.FunctionServiceClient(**client_kwargs)
            rtnval = self._functions_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create GCP Cloud Functions client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name="client_init",
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def invoke(self, function_name: str, payload: dict,
               timeout: float = None) -> InvocationResult:
        """
            Invokes a GCP Cloud Function synchronously via HTTP trigger.

            :param function_name: Name of the Cloud Function to invoke.
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
                "GCP Cloud Functions invocation failed.",
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
                platform_type=PlatformType.GCP
            )

        return rtnval

    def invoke_async(self, function_name: str, payload: dict) -> str:
        """
            Invokes a GCP Cloud Function asynchronously.

            :param function_name: Name of the Cloud Function to invoke.
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
                "GCP Cloud Functions async invocation failed.",
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
                platform_type=PlatformType.GCP
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
            Returns a list of available GCP Cloud Function names.

            :returns: List of function name strings.
            :raises: ComputeError
        """
        try:
            client = self._get_client()
            response = client.list_functions(
                parent="projects/{}/locations/{}".format(
                    self._project_id, self._region
                )
            )
            functions = getattr(response, "functions", response) if response is not None else []
            rtnval = [getattr(f, "name", str(f)) for f in functions]

        except ComputeError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list GCP Cloud Functions.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name="list_functions",
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the GCP Cloud Functions service is available.

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
            Health check for GCP Cloud Functions service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# GcpStorageService
# ---------------------------------------------------------------------------

class GcpStorageService(StorageService):
    """
        Storage service implementation that wraps GCP Cloud Storage
        operations via the GCP SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be GCP).
        :param configuration: An optional PlatformConfiguration.
        :param region: The GCP region string.
        :param storage_client: An optional pre-configured GCP Storage client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 storage_client=None) -> None:
        super().__init__(
            service_name="gcp-cloud-storage",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._storage_client = storage_client
        return

    def _get_client(self):
        """
            Returns the GCP Cloud Storage client, creating one if not
            already provided.

            :returns: A GCP Storage client.
            :raises: StorageError
        """
        if self._storage_client is not None:
            rtnval = self._storage_client
            return rtnval

        try:
            from google.cloud import storage

            client_kwargs = {}

            if self._configuration is not None:
                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    client_kwargs["credentials"] = first_cred

                overrides = self._configuration.service_endpoint_overrides
                if "storage" in overrides:
                    client_kwargs["client_options"] = {
                        "api_endpoint": overrides["storage"]
                    }

            self._storage_client = storage.Client(**client_kwargs)
            rtnval = self._storage_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create GCP Cloud Storage client.",
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
                platform_type=PlatformType.GCP
            )

        return rtnval

    def put_object(self, container_name: str, object_key: str,
                   content: bytes, content_type: str = None,
                   metadata: dict = None) -> None:
        """
            Stores an object in a GCP Cloud Storage bucket.

            :param container_name: Name of the GCS bucket.
            :param object_key: Key identifying the object.
            :param content: Object content as bytes.
            :param content_type: Optional MIME content type string.
            :param metadata: Optional metadata dictionary.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            bucket = client.bucket(container_name)
            blob = bucket.blob(object_key)

            if content_type is not None:
                blob.content_type = content_type

            if metadata is not None:
                blob.metadata = metadata

            blob.upload_from_string(content)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to put object in GCP Cloud Storage.",
                "  Bucket: {!r}".format(container_name),
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
                platform_type=PlatformType.GCP
            )

        return

    def get_object(self, container_name: str, object_key: str) -> StorageObject:
        """
            Retrieves an object from a GCP Cloud Storage bucket.

            :param container_name: Name of the GCS bucket.
            :param object_key: Key identifying the object.

            :returns: A StorageObject instance.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            bucket = client.bucket(container_name)
            blob = bucket.blob(object_key)

            content = blob.download_as_bytes()
            blob.reload()

            content_type = blob.content_type if blob.content_type is not None else "application/octet-stream"
            metadata = blob.metadata if blob.metadata is not None else {}
            size = blob.size if blob.size is not None else len(content)
            last_modified = blob.updated

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
                "Failed to get object from GCP Cloud Storage.",
                "  Bucket: {!r}".format(container_name),
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
                platform_type=PlatformType.GCP
            )

        return rtnval

    def delete_object(self, container_name: str, object_key: str) -> None:
        """
            Removes an object from a GCP Cloud Storage bucket.

            :param container_name: Name of the GCS bucket.
            :param object_key: Key identifying the object.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            bucket = client.bucket(container_name)
            blob = bucket.blob(object_key)
            blob.delete()

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete object from GCP Cloud Storage.",
                "  Bucket: {!r}".format(container_name),
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
                platform_type=PlatformType.GCP
            )

        return

    def list_objects(self, container_name: str, prefix: str = None) -> list:
        """
            Returns a list of object key strings in a GCS bucket.

            :param container_name: Name of the GCS bucket.
            :param prefix: Optional prefix filter string.

            :returns: List of object key strings.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            bucket = client.bucket(container_name)

            list_kwargs = {}
            if prefix is not None:
                list_kwargs["prefix"] = prefix

            blobs = bucket.list_blobs(**list_kwargs)
            rtnval = [blob.name for blob in blobs]

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list objects in GCP Cloud Storage.",
                "  Bucket: {!r}".format(container_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="list_objects",
                container_name=container_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def object_exists(self, container_name: str, object_key: str) -> bool:
        """
            Checks whether an object exists in a GCS bucket.

            :param container_name: Name of the GCS bucket.
            :param object_key: Key identifying the object.

            :returns: True if the object exists, False otherwise.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            bucket = client.bucket(container_name)
            blob = bucket.blob(object_key)
            rtnval = blob.exists()

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to check object existence in GCP Cloud Storage.",
                "  Bucket: {!r}".format(container_name),
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
                platform_type=PlatformType.GCP
            )

        return rtnval

    def create_container(self, container_name: str) -> None:
        """
            Creates a GCP Cloud Storage bucket.

            :param container_name: Name of the bucket to create.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            client.create_bucket(container_name, location=self._region)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to create bucket in GCP Cloud Storage.",
                "  Bucket: {!r}".format(container_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="create_container",
                container_name=container_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return

    def delete_container(self, container_name: str) -> None:
        """
            Removes a GCP Cloud Storage bucket.

            :param container_name: Name of the bucket to remove.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            bucket = client.bucket(container_name)
            bucket.delete()

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete bucket from GCP Cloud Storage.",
                "  Bucket: {!r}".format(container_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="delete_container",
                container_name=container_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return

    def list_containers(self) -> list:
        """
            Returns a list of GCP Cloud Storage bucket names.

            :returns: List of bucket name strings.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            buckets = client.list_buckets()
            rtnval = [b.name for b in buckets]

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list buckets in GCP Cloud Storage.",
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="list_containers",
                container_name="",
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the GCP Cloud Storage service is available.

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
            Health check for GCP Cloud Storage service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# GcpMessagingService
# ---------------------------------------------------------------------------

class GcpMessagingService(MessagingService):
    """
        Messaging service implementation that wraps GCP Pub/Sub operations
        via the GCP SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be GCP).
        :param configuration: An optional PlatformConfiguration.
        :param region: The GCP region string.
        :param publisher_client: An optional pre-configured GCP Pub/Sub publisher client.
        :param subscriber_client: An optional pre-configured GCP Pub/Sub subscriber client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 publisher_client=None,
                 subscriber_client=None) -> None:
        super().__init__(
            service_name="gcp-pubsub",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._publisher_client = publisher_client
        self._subscriber_client = subscriber_client
        self._project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        return

    def _get_publisher(self):
        """
            Returns the GCP Pub/Sub publisher client, creating one if not
            already provided.

            :returns: A GCP PublisherClient.
            :raises: MessagingError
        """
        if self._publisher_client is not None:
            rtnval = self._publisher_client
            return rtnval

        try:
            from google.cloud import pubsub_v1

            client_kwargs = {}

            if self._configuration is not None:
                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    client_kwargs["credentials"] = first_cred

                overrides = self._configuration.service_endpoint_overrides
                if "pubsub" in overrides:
                    client_kwargs["client_options"] = {
                        "api_endpoint": overrides["pubsub"]
                    }

            self._publisher_client = pubsub_v1.PublisherClient(**client_kwargs)
            rtnval = self._publisher_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create GCP Pub/Sub publisher client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name="",
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def _get_subscriber(self):
        """
            Returns the GCP Pub/Sub subscriber client, creating one if not
            already provided.

            :returns: A GCP SubscriberClient.
            :raises: MessagingError
        """
        if self._subscriber_client is not None:
            rtnval = self._subscriber_client
            return rtnval

        try:
            from google.cloud import pubsub_v1

            client_kwargs = {}

            if self._configuration is not None:
                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    client_kwargs["credentials"] = first_cred

                overrides = self._configuration.service_endpoint_overrides
                if "pubsub" in overrides:
                    client_kwargs["client_options"] = {
                        "api_endpoint": overrides["pubsub"]
                    }

            self._subscriber_client = pubsub_v1.SubscriberClient(**client_kwargs)
            rtnval = self._subscriber_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create GCP Pub/Sub subscriber client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name="",
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def send_message(self, queue_name: str, body: object,
                     attributes: dict = None) -> str:
        """
            Publishes a message to a GCP Pub/Sub topic.

            :param queue_name: Name of the Pub/Sub topic.
            :param body: Message body as a Python object (serialized to JSON).
            :param attributes: Optional message attributes dictionary.

            :returns: A message identifier string.
            :raises: MessagingError
        """
        try:
            publisher = self._get_publisher()
            topic_path = "projects/{}/topics/{}".format(
                self._project_id, queue_name
            )

            message_data = json.dumps(body).encode("utf-8")

            publish_kwargs = {
                "topic": topic_path,
                "data": message_data
            }

            if attributes is not None:
                str_attrs = {}
                for attr_key, attr_val in attributes.items():
                    str_attrs[str(attr_key)] = str(attr_val)
                publish_kwargs["attributes"] = str_attrs

            future = publisher.publish(**publish_kwargs)
            message_id = future.result()
            rtnval = str(message_id)

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to send message to GCP Pub/Sub.",
                "  Topic: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def receive_messages(self, queue_name: str, max_count: int = 1,
                         wait_time: float = None) -> list:
        """
            Pulls messages from a GCP Pub/Sub subscription.

            :param queue_name: Name of the Pub/Sub subscription.
            :param max_count: Maximum number of messages to receive.
            :param wait_time: Optional wait time in seconds (not directly
                used by pull, but recorded for consistency).

            :returns: A list of QueueMessage objects.
            :raises: MessagingError
        """
        try:
            subscriber = self._get_subscriber()
            subscription_path = "projects/{}/subscriptions/{}".format(
                self._project_id, queue_name
            )

            response = subscriber.pull(
                subscription=subscription_path,
                max_messages=max_count
            )

            received_messages = getattr(response, "received_messages", [])
            messages = []

            for received in received_messages:
                pubsub_msg = received.message
                msg_data = pubsub_msg.data.decode("utf-8") if pubsub_msg.data is not None else ""

                try:
                    msg_body = json.loads(msg_data)
                except (json.JSONDecodeError, TypeError):
                    msg_body = msg_data

                msg_attrs = dict(pubsub_msg.attributes) if pubsub_msg.attributes is not None else {}
                msg_id = str(pubsub_msg.message_id) if hasattr(pubsub_msg, "message_id") else str(uuid.uuid4())
                ack_id = received.ack_id if hasattr(received, "ack_id") else ""

                message = QueueMessage(
                    identifier=msg_id,
                    queue_name=queue_name,
                    body=msg_body,
                    attributes=msg_attrs,
                    receipt_handle=ack_id,
                    timestamp=datetime.utcnow()
                )
                messages.append(message)

            rtnval = messages

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to receive messages from GCP Pub/Sub.",
                "  Subscription: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def acknowledge_message(self, queue_name: str, receipt_handle: str) -> None:
        """
            Acknowledges a message in a GCP Pub/Sub subscription.

            :param queue_name: Name of the subscription.
            :param receipt_handle: Ack ID string for the message.

            :raises: MessagingError
        """
        try:
            subscriber = self._get_subscriber()
            subscription_path = "projects/{}/subscriptions/{}".format(
                self._project_id, queue_name
            )

            subscriber.acknowledge(
                subscription=subscription_path,
                ack_ids=[receipt_handle]
            )

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to acknowledge message in GCP Pub/Sub.",
                "  Subscription: {!r}".format(queue_name),
                "  Ack ID: {!r}".format(receipt_handle),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return

    def create_queue(self, queue_name: str) -> None:
        """
            Creates a GCP Pub/Sub topic.

            :param queue_name: Name of the topic to create.

            :raises: MessagingError
        """
        try:
            publisher = self._get_publisher()
            topic_path = "projects/{}/topics/{}".format(
                self._project_id, queue_name
            )
            publisher.create_topic(name=topic_path)

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to create topic in GCP Pub/Sub.",
                "  Topic: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return

    def delete_queue(self, queue_name: str) -> None:
        """
            Removes a GCP Pub/Sub topic.

            :param queue_name: Name of the topic to remove.

            :raises: MessagingError
        """
        try:
            publisher = self._get_publisher()
            topic_path = "projects/{}/topics/{}".format(
                self._project_id, queue_name
            )
            publisher.delete_topic(topic=topic_path)

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete topic from GCP Pub/Sub.",
                "  Topic: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return

    def list_queues(self) -> list:
        """
            Returns a list of GCP Pub/Sub topic names.

            :returns: List of topic name strings.
            :raises: MessagingError
        """
        try:
            publisher = self._get_publisher()
            project_path = "projects/{}".format(self._project_id)
            topics = publisher.list_topics(project=project_path)
            rtnval = [t.name.split("/")[-1] for t in topics]

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list topics in GCP Pub/Sub.",
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name="",
                cause=exc,
                platform_type=PlatformType.GCP
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the GCP Pub/Sub service is available.

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
            Health check for GCP Pub/Sub service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# GcpPlatformAdapter
# ---------------------------------------------------------------------------

class GcpPlatformAdapter(PlatformAdapter):
    """
        PlatformAdapter implementation providing GCP-specific service
        implementations using GCP SDK clients for Cloud Functions, Cloud
        Storage, and Pub/Sub.

        Resolves GCP credentials through CredentialReference entries in the
        PlatformConfiguration, falling back to GCP application default
        credentials when no explicit credentials are configured.

        :param configuration: The PlatformConfiguration for the GCP platform.
        :param functions_client: An optional pre-configured GCP Cloud Functions client.
        :param storage_client: An optional pre-configured GCP Storage client.
        :param publisher_client: An optional pre-configured GCP Pub/Sub publisher client.
        :param subscriber_client: An optional pre-configured GCP Pub/Sub subscriber client.
    """

    def __init__(self, configuration: PlatformConfiguration,
                 functions_client=None, storage_client=None,
                 publisher_client=None, subscriber_client=None) -> None:
        super().__init__(configuration=configuration)
        self._region = self._resolve_region()
        self._compute_service = GcpComputeService(
            platform_type=PlatformType.GCP,
            configuration=configuration,
            region=self._region,
            functions_client=functions_client
        )
        self._storage_service = GcpStorageService(
            platform_type=PlatformType.GCP,
            configuration=configuration,
            region=self._region,
            storage_client=storage_client
        )
        self._messaging_service = GcpMessagingService(
            platform_type=PlatformType.GCP,
            configuration=configuration,
            region=self._region,
            publisher_client=publisher_client,
            subscriber_client=subscriber_client
        )
        return

    @property
    def platform_type(self) -> PlatformType:
        """
            Returns PlatformType.GCP.

            :returns: PlatformType.GCP.
        """
        rtnval = PlatformType.GCP
        return rtnval

    def get_compute_service(self) -> ComputeService:
        """
            Returns the GcpComputeService instance.

            :returns: The GcpComputeService.
        """
        rtnval = self._compute_service
        return rtnval

    def get_storage_service(self) -> StorageService:
        """
            Returns the GcpStorageService instance.

            :returns: The GcpStorageService.
        """
        rtnval = self._storage_service
        return rtnval

    def get_messaging_service(self) -> MessagingService:
        """
            Returns the GcpMessagingService instance.

            :returns: The GcpMessagingService.
        """
        rtnval = self._messaging_service
        return rtnval

    def _resolve_region(self) -> str:
        """
            Resolves the GCP region from configuration, falling back to
            the GCP_REGION environment variable, defaulting to us-central1.

            :returns: The resolved region string.
        """
        if self._configuration is not None and self._configuration.region is not None:
            rtnval = self._configuration.region
            return rtnval

        rtnval = os.environ.get("GCP_REGION", "us-central1")
        return rtnval
