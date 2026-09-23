"""
    Defines the StorageService abstract base class representing an object
    storage service that can store, retrieve, list, and delete objects by
    key. Concrete implementations wrap AWS S3, Azure Blob Storage, GCP
    Cloud Storage, and local file system storage.

    .. module:: ccai.agentkit.platform.services.storageservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract storage service interface for platform storage services.
"""

import abc

from ccai.agentkit.platform.platformtype import PlatformType
from ccai.agentkit.platform.services.platformservice import PlatformService


class StorageService(PlatformService, abc.ABC):
    """
        Abstract base class representing an object storage service that can
        store, retrieve, list, and delete objects by key.

        Inherits from PlatformService with service_type fixed to "storage".
        Subclasses must implement put_object, get_object, delete_object,
        list_objects, object_exists, create_container, delete_container,
        and list_containers in addition to is_available and health_check.

        :param service_name: A string identifying this storage service instance.
        :param platform_type: The PlatformType this service targets.
        :param configuration: An optional PlatformConfiguration for service-specific settings.
    """

    def __init__(self, service_name: str, platform_type: PlatformType,
                 configuration: "PlatformConfiguration" = None) -> None:
        super().__init__(
            service_name=service_name,
            service_type="storage",
            platform_type=platform_type,
            configuration=configuration
        )
        return

    @abc.abstractmethod
    def put_object(self, container_name: str, object_key: str,
                   content: bytes, content_type: str = None,
                   metadata: dict = None) -> None:
        """
            Stores an object in the specified container.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.
            :param content: Object content as bytes.
            :param content_type: Optional MIME content type string.
            :param metadata: Optional metadata dictionary.

            :raises: StorageError
        """

    @abc.abstractmethod
    def get_object(self, container_name: str, object_key: str) -> "StorageObject":
        """
            Retrieves an object from the specified container.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.

            :returns: A StorageObject instance.
            :raises: StorageError
        """

    @abc.abstractmethod
    def delete_object(self, container_name: str, object_key: str) -> None:
        """
            Removes an object from the specified container.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.

            :raises: StorageError
        """

    @abc.abstractmethod
    def list_objects(self, container_name: str, prefix: str = None) -> list:
        """
            Returns a list of object key strings matching the optional prefix.

            :param container_name: Name of the storage container.
            :param prefix: Optional prefix filter string.

            :returns: List of object key strings.
            :raises: StorageError
        """

    @abc.abstractmethod
    def object_exists(self, container_name: str, object_key: str) -> bool:
        """
            Checks whether an object exists in the specified container.

            :param container_name: Name of the storage container.
            :param object_key: Key identifying the object.

            :returns: True if the object exists, False otherwise.
            :raises: StorageError
        """

    @abc.abstractmethod
    def create_container(self, container_name: str) -> None:
        """
            Creates a storage container.

            :param container_name: Name of the container to create.

            :raises: StorageError
        """

    @abc.abstractmethod
    def delete_container(self, container_name: str) -> None:
        """
            Removes a storage container.

            :param container_name: Name of the container to remove.

            :raises: StorageError
        """

    @abc.abstractmethod
    def list_containers(self) -> list:
        """
            Returns a list of container name strings.

            :returns: List of container name strings.
            :raises: StorageError
        """

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            service name, and platform type.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(service_name={}, platform_type={})".format(
            self.__class__.__name__, self._service_name,
            self._platform_type.to_string()
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the service name
            and platform type.

            :returns: A human-readable string.
        """
        rtnval = "{}: name={}, platform={}".format(
            self.__class__.__name__, self._service_name,
            self._platform_type.to_string()
        )
        return rtnval
