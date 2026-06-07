"""
    Defines the AwsPlatformAdapter and its AWS service implementations
    for running agents on Amazon Web Services. Provides AwsComputeService
    (AWS Lambda), AwsStorageService (AWS S3), and AwsMessagingService
    (AWS SQS).

    .. module:: ccai.agentkit.platform.adapters.awsplatformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: AWS platform adapter with Lambda, S3, and SQS services.
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
# AwsComputeService
# ---------------------------------------------------------------------------

class AwsComputeService(ComputeService):
    """
        Compute service implementation that wraps AWS Lambda invocation
        via the boto3 SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be AWS).
        :param configuration: An optional PlatformConfiguration.
        :param region: The AWS region string.
        :param lambda_client: An optional pre-configured boto3 Lambda client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 lambda_client=None) -> None:
        super().__init__(
            service_name="aws-lambda",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._lambda_client = lambda_client
        return

    def _get_client(self):
        """
            Returns the boto3 Lambda client, creating one if not already
            provided.

            :returns: A boto3 Lambda client.
            :raises: ComputeError
        """
        if self._lambda_client is not None:
            rtnval = self._lambda_client
            return rtnval

        try:
            import boto3

            client_kwargs = {
                "service_name": "lambda",
                "region_name": self._region
            }

            if self._configuration is not None:
                overrides = self._configuration.service_endpoint_overrides
                if "lambda" in overrides:
                    client_kwargs["endpoint_url"] = overrides["lambda"]

                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    if hasattr(first_cred, "access_key_id"):
                        client_kwargs["aws_access_key_id"] = first_cred.access_key_id
                        client_kwargs["aws_secret_access_key"] = first_cred.secret_access_key

            self._lambda_client = boto3.client(**client_kwargs)
            rtnval = self._lambda_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create AWS Lambda client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name="client_init",
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def invoke(self, function_name: str, payload: dict,
               timeout: float = None) -> InvocationResult:
        """
            Invokes an AWS Lambda function synchronously.

            :param function_name: Name of the Lambda function to invoke.
            :param payload: Dictionary payload serialized as JSON.
            :param timeout: Optional timeout in seconds (not directly enforced
                by Lambda, but recorded in the result).

            :returns: An InvocationResult with the execution outcome.
            :raises: ComputeError
        """
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        try:
            client = self._get_client()
            payload_bytes = json.dumps(payload).encode("utf-8")

            response = client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=payload_bytes
            )

            duration = time.monotonic() - start_time
            status_code = response.get("StatusCode", 0)
            response_payload = response.get("Payload")

            if response_payload is not None:
                response_body = response_payload.read().decode("utf-8")
            else:
                response_body = None

            function_error = response.get("FunctionError")

            if function_error is not None:
                rtnval = InvocationResult(
                    status="error",
                    response=response_body,
                    error_message=function_error,
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
                "AWS Lambda invocation failed.",
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
                platform_type=PlatformType.AWS
            )

        return rtnval

    def invoke_async(self, function_name: str, payload: dict) -> str:
        """
            Invokes an AWS Lambda function asynchronously using the
            Event invocation type.

            :param function_name: Name of the Lambda function to invoke.
            :param payload: Dictionary payload serialized as JSON.

            :returns: A request identifier string.
            :raises: ComputeError
        """
        request_id = str(uuid.uuid4())

        try:
            client = self._get_client()
            payload_bytes = json.dumps(payload).encode("utf-8")

            client.invoke(
                FunctionName=function_name,
                InvocationType="Event",
                Payload=payload_bytes
            )

        except ComputeError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "AWS Lambda async invocation failed.",
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
                platform_type=PlatformType.AWS
            )

        rtnval = request_id
        return rtnval

    def get_invocation_status(self, request_id: str) -> InvocationResult:
        """
            Returns a pending status for async invocations. AWS Lambda
            Event invocations do not provide status tracking.

            :param request_id: The request identifier from invoke_async.

            :returns: An InvocationResult with status "success" (fire-and-forget).
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
            Returns a list of available Lambda function names.

            :returns: List of function name strings.
            :raises: ComputeError
        """
        try:
            client = self._get_client()
            response = client.list_functions()
            functions = response.get("Functions", [])
            rtnval = [f["FunctionName"] for f in functions]

        except ComputeError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list AWS Lambda functions.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise ComputeError(
                err_msg,
                function_name="list_functions",
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the AWS Lambda service is available by
            attempting to list functions.

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
            Health check for AWS Lambda service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# AwsStorageService
# ---------------------------------------------------------------------------

class AwsStorageService(StorageService):
    """
        Storage service implementation that wraps AWS S3 operations via
        the boto3 SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be AWS).
        :param configuration: An optional PlatformConfiguration.
        :param region: The AWS region string.
        :param s3_client: An optional pre-configured boto3 S3 client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 s3_client=None) -> None:
        super().__init__(
            service_name="aws-s3",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._s3_client = s3_client
        return

    def _get_client(self):
        """
            Returns the boto3 S3 client, creating one if not already
            provided.

            :returns: A boto3 S3 client.
            :raises: StorageError
        """
        if self._s3_client is not None:
            rtnval = self._s3_client
            return rtnval

        try:
            import boto3

            client_kwargs = {
                "service_name": "s3",
                "region_name": self._region
            }

            if self._configuration is not None:
                overrides = self._configuration.service_endpoint_overrides
                if "s3" in overrides:
                    client_kwargs["endpoint_url"] = overrides["s3"]

                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    if hasattr(first_cred, "access_key_id"):
                        client_kwargs["aws_access_key_id"] = first_cred.access_key_id
                        client_kwargs["aws_secret_access_key"] = first_cred.secret_access_key

            self._s3_client = boto3.client(**client_kwargs)
            rtnval = self._s3_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create AWS S3 client.",
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
                platform_type=PlatformType.AWS
            )

        return rtnval

    def put_object(self, container_name: str, object_key: str,
                   content: bytes, content_type: str = None,
                   metadata: dict = None) -> None:
        """
            Stores an object in an S3 bucket.

            :param container_name: Name of the S3 bucket.
            :param object_key: Key identifying the object.
            :param content: Object content as bytes.
            :param content_type: Optional MIME content type string.
            :param metadata: Optional metadata dictionary.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            put_kwargs = {
                "Bucket": container_name,
                "Key": object_key,
                "Body": content
            }

            if content_type is not None:
                put_kwargs["ContentType"] = content_type

            if metadata is not None:
                put_kwargs["Metadata"] = metadata

            client.put_object(**put_kwargs)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to put object in AWS S3.",
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
                platform_type=PlatformType.AWS
            )

        return

    def get_object(self, container_name: str, object_key: str) -> StorageObject:
        """
            Retrieves an object from an S3 bucket.

            :param container_name: Name of the S3 bucket.
            :param object_key: Key identifying the object.

            :returns: A StorageObject instance.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            response = client.get_object(
                Bucket=container_name,
                Key=object_key
            )

            content = response["Body"].read()
            content_type = response.get("ContentType", "application/octet-stream")
            metadata = response.get("Metadata", {})
            content_length = response.get("ContentLength", len(content))
            last_modified = response.get("LastModified")

            if last_modified is not None and not isinstance(last_modified, datetime):
                last_modified = datetime.fromisoformat(str(last_modified))

            rtnval = StorageObject(
                key=object_key,
                content=content,
                content_type=content_type,
                metadata=metadata,
                size=content_length,
                last_modified=last_modified
            )

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to get object from AWS S3.",
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
                platform_type=PlatformType.AWS
            )

        return rtnval

    def delete_object(self, container_name: str, object_key: str) -> None:
        """
            Removes an object from an S3 bucket.

            :param container_name: Name of the S3 bucket.
            :param object_key: Key identifying the object.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            client.delete_object(
                Bucket=container_name,
                Key=object_key
            )

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete object from AWS S3.",
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
                platform_type=PlatformType.AWS
            )

        return

    def list_objects(self, container_name: str, prefix: str = None) -> list:
        """
            Returns a list of object key strings in an S3 bucket,
            optionally filtered by prefix.

            :param container_name: Name of the S3 bucket.
            :param prefix: Optional prefix filter string.

            :returns: List of object key strings.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            list_kwargs = {
                "Bucket": container_name
            }

            if prefix is not None:
                list_kwargs["Prefix"] = prefix

            response = client.list_objects_v2(**list_kwargs)
            contents = response.get("Contents", [])
            rtnval = [obj["Key"] for obj in contents]

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list objects in AWS S3.",
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
                platform_type=PlatformType.AWS
            )

        return rtnval

    def object_exists(self, container_name: str, object_key: str) -> bool:
        """
            Checks whether an object exists in an S3 bucket.

            :param container_name: Name of the S3 bucket.
            :param object_key: Key identifying the object.

            :returns: True if the object exists, False otherwise.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            client.head_object(
                Bucket=container_name,
                Key=object_key
            )
            rtnval = True

        except StorageError:
            raise

        except Exception as exc:
            error_code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "404":
                rtnval = False
            else:
                err_msg_lines = [
                    "Failed to check object existence in AWS S3.",
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
                    platform_type=PlatformType.AWS
                )

        return rtnval

    def create_container(self, container_name: str) -> None:
        """
            Creates an S3 bucket.

            :param container_name: Name of the bucket to create.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            create_kwargs = {
                "Bucket": container_name
            }

            if self._region is not None and self._region != "us-east-1":
                create_kwargs["CreateBucketConfiguration"] = {
                    "LocationConstraint": self._region
                }

            client.create_bucket(**create_kwargs)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to create bucket in AWS S3.",
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
                platform_type=PlatformType.AWS
            )

        return

    def delete_container(self, container_name: str) -> None:
        """
            Removes an S3 bucket.

            :param container_name: Name of the bucket to remove.

            :raises: StorageError
        """
        try:
            client = self._get_client()
            client.delete_bucket(Bucket=container_name)

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete bucket from AWS S3.",
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
                platform_type=PlatformType.AWS
            )

        return

    def list_containers(self) -> list:
        """
            Returns a list of S3 bucket names.

            :returns: List of bucket name strings.
            :raises: StorageError
        """
        try:
            client = self._get_client()
            response = client.list_buckets()
            buckets = response.get("Buckets", [])
            rtnval = [b["Name"] for b in buckets]

        except StorageError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list buckets in AWS S3.",
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise StorageError(
                err_msg,
                operation_name="list_containers",
                container_name="",
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the AWS S3 service is available.

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
            Health check for AWS S3 service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# AwsMessagingService
# ---------------------------------------------------------------------------

class AwsMessagingService(MessagingService):
    """
        Messaging service implementation that wraps AWS SQS operations via
        the boto3 SDK. Supports credential resolution from
        PlatformConfiguration and service endpoint overrides.

        :param platform_type: The PlatformType (expected to be AWS).
        :param configuration: An optional PlatformConfiguration.
        :param region: The AWS region string.
        :param sqs_client: An optional pre-configured boto3 SQS client.
    """

    def __init__(self, platform_type: PlatformType,
                 configuration: PlatformConfiguration = None,
                 region: str = None,
                 sqs_client=None) -> None:
        super().__init__(
            service_name="aws-sqs",
            platform_type=platform_type,
            configuration=configuration
        )
        self._region = region
        self._sqs_client = sqs_client
        self._queue_url_cache = {}
        return

    def _get_client(self):
        """
            Returns the boto3 SQS client, creating one if not already
            provided.

            :returns: A boto3 SQS client.
            :raises: MessagingError
        """
        if self._sqs_client is not None:
            rtnval = self._sqs_client
            return rtnval

        try:
            import boto3

            client_kwargs = {
                "service_name": "sqs",
                "region_name": self._region
            }

            if self._configuration is not None:
                overrides = self._configuration.service_endpoint_overrides
                if "sqs" in overrides:
                    client_kwargs["endpoint_url"] = overrides["sqs"]

                resolved = self._configuration.resolved_credentials
                if len(resolved) > 0:
                    first_cred = list(resolved.values())[0]
                    if hasattr(first_cred, "access_key_id"):
                        client_kwargs["aws_access_key_id"] = first_cred.access_key_id
                        client_kwargs["aws_secret_access_key"] = first_cred.secret_access_key

            self._sqs_client = boto3.client(**client_kwargs)
            rtnval = self._sqs_client

        except Exception as exc:
            err_msg_lines = [
                "Failed to create AWS SQS client.",
                "  Region: {!r}".format(self._region),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name="",
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def _get_queue_url(self, queue_name: str) -> str:
        """
            Resolves the SQS queue URL for a given queue name, using
            a local cache to avoid repeated lookups.

            :param queue_name: Name of the queue.

            :returns: The queue URL string.
            :raises: MessagingError
        """
        if queue_name in self._queue_url_cache:
            rtnval = self._queue_url_cache[queue_name]
            return rtnval

        try:
            client = self._get_client()
            response = client.get_queue_url(QueueName=queue_name)
            queue_url = response["QueueUrl"]
            self._queue_url_cache[queue_name] = queue_url
            rtnval = queue_url

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to resolve SQS queue URL.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def send_message(self, queue_name: str, body: object,
                     attributes: dict = None) -> str:
        """
            Sends a message to an SQS queue.

            :param queue_name: Name of the target queue.
            :param body: Message body as a Python object (serialized to JSON).
            :param attributes: Optional message attributes dictionary.

            :returns: A message identifier string.
            :raises: MessagingError
        """
        try:
            client = self._get_client()
            queue_url = self._get_queue_url(queue_name)

            send_kwargs = {
                "QueueUrl": queue_url,
                "MessageBody": json.dumps(body)
            }

            if attributes is not None:
                sqs_attrs = {}
                for attr_key, attr_val in attributes.items():
                    sqs_attrs[attr_key] = {
                        "DataType": "String",
                        "StringValue": str(attr_val)
                    }
                send_kwargs["MessageAttributes"] = sqs_attrs

            response = client.send_message(**send_kwargs)
            rtnval = response["MessageId"]

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to send message to AWS SQS.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def receive_messages(self, queue_name: str, max_count: int = 1,
                         wait_time: float = None) -> list:
        """
            Receives messages from an SQS queue.

            :param queue_name: Name of the source queue.
            :param max_count: Maximum number of messages to receive.
            :param wait_time: Optional wait time in seconds for long polling.

            :returns: A list of QueueMessage objects.
            :raises: MessagingError
        """
        try:
            client = self._get_client()
            queue_url = self._get_queue_url(queue_name)

            receive_kwargs = {
                "QueueUrl": queue_url,
                "MaxNumberOfMessages": min(max_count, 10),
                "MessageAttributeNames": ["All"]
            }

            if wait_time is not None:
                receive_kwargs["WaitTimeSeconds"] = int(wait_time)

            response = client.receive_message(**receive_kwargs)
            sqs_messages = response.get("Messages", [])

            messages = []
            for sqs_msg in sqs_messages:
                msg_attrs = {}
                raw_attrs = sqs_msg.get("MessageAttributes", {})
                for attr_key, attr_val in raw_attrs.items():
                    msg_attrs[attr_key] = attr_val.get("StringValue", "")

                body_str = sqs_msg.get("Body", "")
                try:
                    body = json.loads(body_str)
                except (json.JSONDecodeError, TypeError):
                    body = body_str

                message = QueueMessage(
                    identifier=sqs_msg["MessageId"],
                    queue_name=queue_name,
                    body=body,
                    attributes=msg_attrs,
                    receipt_handle=sqs_msg["ReceiptHandle"],
                    timestamp=datetime.utcnow()
                )
                messages.append(message)

            rtnval = messages

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to receive messages from AWS SQS.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def acknowledge_message(self, queue_name: str, receipt_handle: str) -> None:
        """
            Acknowledges a message by deleting it from the SQS queue.

            :param queue_name: Name of the queue.
            :param receipt_handle: Receipt handle string for the message.

            :raises: MessagingError
        """
        try:
            client = self._get_client()
            queue_url = self._get_queue_url(queue_name)

            client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to acknowledge message in AWS SQS.",
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
                platform_type=PlatformType.AWS
            )

        return

    def create_queue(self, queue_name: str) -> None:
        """
            Creates an SQS queue.

            :param queue_name: Name of the queue to create.

            :raises: MessagingError
        """
        try:
            client = self._get_client()
            response = client.create_queue(QueueName=queue_name)
            queue_url = response["QueueUrl"]
            self._queue_url_cache[queue_name] = queue_url

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to create queue in AWS SQS.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return

    def delete_queue(self, queue_name: str) -> None:
        """
            Removes an SQS queue.

            :param queue_name: Name of the queue to remove.

            :raises: MessagingError
        """
        try:
            client = self._get_client()
            queue_url = self._get_queue_url(queue_name)
            client.delete_queue(QueueUrl=queue_url)

            if queue_name in self._queue_url_cache:
                del self._queue_url_cache[queue_name]

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to delete queue from AWS SQS.",
                "  Queue name: {!r}".format(queue_name),
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name=queue_name,
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return

    def list_queues(self) -> list:
        """
            Returns a list of SQS queue names.

            :returns: List of queue name strings.
            :raises: MessagingError
        """
        try:
            client = self._get_client()
            response = client.list_queues()
            queue_urls = response.get("QueueUrls", [])
            rtnval = [url.split("/")[-1] for url in queue_urls]

        except MessagingError:
            raise

        except Exception as exc:
            err_msg_lines = [
                "Failed to list queues in AWS SQS.",
                "  Error: {}".format(str(exc))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            logger.warning("%s", err_msg)
            raise MessagingError(
                err_msg,
                queue_name="",
                cause=exc,
                platform_type=PlatformType.AWS
            )

        return rtnval

    def is_available(self) -> bool:
        """
            Checks whether the AWS SQS service is available.

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
            Health check for AWS SQS service.

            :returns: True if the service is healthy.
        """
        rtnval = self.is_available()
        return rtnval


# ---------------------------------------------------------------------------
# AwsPlatformAdapter
# ---------------------------------------------------------------------------

class AwsPlatformAdapter(PlatformAdapter):
    """
        PlatformAdapter implementation providing AWS-specific service
        implementations using AWS SDK clients for Lambda, S3, and SQS.

        Resolves AWS credentials through CredentialReference entries in the
        PlatformConfiguration, falling back to the default AWS credential
        chain when no explicit credentials are configured.

        :param configuration: The PlatformConfiguration for the AWS platform.
        :param lambda_client: An optional pre-configured boto3 Lambda client.
        :param s3_client: An optional pre-configured boto3 S3 client.
        :param sqs_client: An optional pre-configured boto3 SQS client.
    """

    def __init__(self, configuration: PlatformConfiguration,
                 lambda_client=None, s3_client=None,
                 sqs_client=None) -> None:
        super().__init__(configuration=configuration)
        self._region = self._resolve_region()
        self._compute_service = AwsComputeService(
            platform_type=PlatformType.AWS,
            configuration=configuration,
            region=self._region,
            lambda_client=lambda_client
        )
        self._storage_service = AwsStorageService(
            platform_type=PlatformType.AWS,
            configuration=configuration,
            region=self._region,
            s3_client=s3_client
        )
        self._messaging_service = AwsMessagingService(
            platform_type=PlatformType.AWS,
            configuration=configuration,
            region=self._region,
            sqs_client=sqs_client
        )
        return

    @property
    def platform_type(self) -> PlatformType:
        """
            Returns PlatformType.AWS.

            :returns: PlatformType.AWS.
        """
        rtnval = PlatformType.AWS
        return rtnval

    def get_compute_service(self) -> ComputeService:
        """
            Returns the AwsComputeService instance.

            :returns: The AwsComputeService.
        """
        rtnval = self._compute_service
        return rtnval

    def get_storage_service(self) -> StorageService:
        """
            Returns the AwsStorageService instance.

            :returns: The AwsStorageService.
        """
        rtnval = self._storage_service
        return rtnval

    def get_messaging_service(self) -> MessagingService:
        """
            Returns the AwsMessagingService instance.

            :returns: The AwsMessagingService.
        """
        rtnval = self._messaging_service
        return rtnval

    def _resolve_region(self) -> str:
        """
            Resolves the AWS region from configuration, falling back to
            the AWS_REGION environment variable, defaulting to us-east-1.

            :returns: The resolved region string.
        """
        if self._configuration is not None and self._configuration.region is not None:
            rtnval = self._configuration.region
            return rtnval

        rtnval = os.environ.get("AWS_REGION", "us-east-1")
        return rtnval
