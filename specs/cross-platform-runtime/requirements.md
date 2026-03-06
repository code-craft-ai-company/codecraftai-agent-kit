# Requirements Document — Cross-Platform Runtime

## Introduction

The Cross-Platform Runtime feature extends the `automojo-agent-kit` SDK with a platform abstraction layer that enables agents to run across cloud providers (AWS, Azure, GCP) and local environments through a unified API surface. It defines abstract base classes for platform services (compute, storage, messaging), a platform detection and auto-configuration system, platform-specific adapter implementations for each supported provider, and portable deployment descriptors that define how agents are deployed across platforms. The system integrates with the Agent base class so agents can access platform services through a consistent interface, with AgentConfiguration for platform-specific settings, with `automojo-extension` for platform adapter plugin discovery, with `automojo-credentials` for cloud provider authentication, with `automojo-this-app` for environment configuration and settings, and with the Testing & Quality feature whose PlatformTestHarness and SimulatedPlatformService classes simulate the real platform abstractions defined here.

## Glossary

- **PlatformRuntime**: A component that manages the active platform environment for an Agent, providing access to platform services, platform identity, and platform configuration. Each Agent holds a reference to a PlatformRuntime instance.
- **PlatformType**: An enumeration defining the supported platform types: AWS, AZURE, GCP, and LOCAL.
- **PlatformDetector**: A component that inspects the runtime environment to determine which platform the agent is running on, returning a PlatformType value. The PlatformDetector checks environment variables, metadata endpoints, and configuration hints.
- **PlatformConfiguration**: A configuration object that defines platform-specific settings including the platform type, region, credentials references, service endpoint overrides, and platform-specific options. The PlatformConfiguration integrates with AgentConfiguration.
- **PlatformService**: An abstract base class representing a cloud or local service that a platform provides. Concrete subclasses include ComputeService, StorageService, and MessagingService.
- **PlatformServiceRegistry**: A registry that tracks all available PlatformService instances within a PlatformRuntime, providing lookup by service name and service type.
- **ComputeService**: An abstract base class representing a compute service that can invoke functions, manage execution contexts, and report execution status. Concrete implementations wrap AWS Lambda, Azure Functions, GCP Cloud Functions, and local process execution.
- **StorageService**: An abstract base class representing an object storage service that can store, retrieve, list, and delete objects by key. Concrete implementations wrap AWS S3, Azure Blob Storage, GCP Cloud Storage, and local file system storage.
- **MessagingService**: An abstract base class representing a message queuing service that can send messages to queues, receive messages from queues, and manage queue subscriptions. Concrete implementations wrap AWS SQS, Azure Service Bus, GCP Pub/Sub, and local in-memory queuing.
- **PlatformAdapter**: An abstract base class that bundles a complete set of platform service implementations (ComputeService, StorageService, MessagingService) for a specific platform. Concrete implementations provide AwsPlatformAdapter, AzurePlatformAdapter, GcpPlatformAdapter, and LocalPlatformAdapter.
- **AwsPlatformAdapter**: A PlatformAdapter implementation that provides AWS-specific service implementations using AWS SDK clients for Lambda, S3, and SQS.
- **AzurePlatformAdapter**: A PlatformAdapter implementation that provides Azure-specific service implementations using Azure SDK clients for Functions, Blob Storage, and Service Bus.
- **GcpPlatformAdapter**: A PlatformAdapter implementation that provides GCP-specific service implementations using GCP SDK clients for Cloud Functions, Cloud Storage, and Pub/Sub.
- **LocalPlatformAdapter**: A PlatformAdapter implementation that provides local environment service implementations using subprocess execution, file system storage, and in-memory message queuing.
- **DeploymentDescriptor**: A declarative configuration object that defines how an agent is deployed on a specific platform, including the target platform type, compute configuration, storage configuration, messaging configuration, environment variables, and scaling parameters.
- **DeploymentDescriptorParser**: A component that parses DeploymentDescriptor objects from YAML or JSON files, validating the descriptor against a schema and resolving platform-specific defaults.
- **DeploymentDescriptorPrinter**: A component that formats DeploymentDescriptor objects back into valid YAML or JSON files.
- **StorageObject**: An immutable object representing a stored object, containing the object key, content as bytes, content type string, metadata dictionary, size in bytes, and last modified timestamp.
- **QueueMessage**: An immutable object representing a message in a queue, containing a unique identifier, queue name, body as a Python object, attributes dictionary, receipt handle string for acknowledgment, and timestamp.
- **InvocationResult**: An immutable object representing the result of a compute invocation, containing a status string (one of "success", "error", "timeout"), a response payload as a Python object, an optional error message, the execution duration in seconds, and a request identifier.
- **Agent**: The base agent class defined in the Core Agent Framework that holds a reference to a PlatformRuntime for accessing platform services.
- **AgentConfiguration**: The configuration object defined in the Core Agent Framework, extended with PlatformConfiguration for platform-specific settings.
- **ExtensionPoint**: An integration surface provided by `automojo-extension` that allows external plugins to register PlatformAdapter implementations.
- **CredentialReference**: A named reference resolved through `automojo-credentials` that provides secure access to cloud provider credentials (AWS access keys, Azure service principals, GCP service account keys).
- **AppContext**: The application context provided by `automojo-this-app` that supplies settings, environment variables, and directory-based presence for platform detection and configuration loading.
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **PlatformError**: An exception raised when a platform operation fails due to a service error, connectivity issue, or authentication failure, inherited from AgentKitError.
- **PlatformDetectionError**: An exception raised when the PlatformDetector cannot determine the current platform, inherited from PlatformError.
- **StorageError**: An exception raised when a StorageService operation fails, inherited from PlatformError.
- **ComputeError**: An exception raised when a ComputeService operation fails, inherited from PlatformError.
- **MessagingError**: An exception raised when a MessagingService operation fails, inherited from PlatformError.
- **DeploymentDescriptorError**: An exception raised when a DeploymentDescriptor is invalid or cannot be parsed, inherited from PlatformError.

## Requirements

### Requirement 1: Platform Type Enumeration

**User Story:** As a developer, I want a well-defined enumeration of supported platforms, so that I can reference platform types consistently throughout configuration and code.

#### Acceptance Criteria

1. THE PlatformType enumeration SHALL define the values AWS, AZURE, GCP, and LOCAL.
2. THE PlatformType enumeration SHALL provide a from_string class method that accepts a case-insensitive string value and returns the corresponding PlatformType member.
3. IF an invalid string value is provided to the from_string method, THEN THE PlatformType SHALL raise a SemanticError identifying the invalid value and listing the valid platform type values.
4. THE PlatformType enumeration SHALL provide a to_string method that returns the lowercase string representation of the platform type.

### Requirement 2: Platform Detection

**User Story:** As a developer, I want the runtime to automatically detect which platform my agent is running on, so that the correct platform adapter is selected without manual configuration.

#### Acceptance Criteria

1. THE PlatformDetector SHALL provide a detect method that inspects the runtime environment and returns a PlatformType value.
2. THE PlatformDetector SHALL detect AWS by checking for the presence of AWS-specific environment variables (AWS_LAMBDA_FUNCTION_NAME, AWS_EXECUTION_ENV, AWS_REGION).
3. THE PlatformDetector SHALL detect Azure by checking for the presence of Azure-specific environment variables (AZURE_FUNCTIONS_ENVIRONMENT, WEBSITE_SITE_NAME, AZURE_REGION).
4. THE PlatformDetector SHALL detect GCP by checking for the presence of GCP-specific environment variables (GOOGLE_CLOUD_PROJECT, FUNCTION_NAME, GCP_REGION).
5. WHEN no cloud platform environment variables are detected, THE PlatformDetector SHALL return PlatformType.LOCAL as the default platform.
6. THE PlatformDetector SHALL support an optional PlatformConfiguration hint that overrides environment-based detection, allowing explicit platform selection.
7. IF multiple cloud platform environments are detected simultaneously, THEN THE PlatformDetector SHALL raise a PlatformDetectionError listing the conflicting platform indicators.
8. THE PlatformDetector SHALL log the detection result at INFO level including the detected platform type and the environment indicators that were found.
9. THE PlatformDetector SHALL provide a __repr__ method that includes the class name.
10. THE PlatformDetector SHALL provide a __str__ method that returns a human-readable summary including the last detected platform type.

### Requirement 3: Platform Configuration

**User Story:** As a developer, I want to configure platform-specific settings declaratively, so that I can define platform behavior without modifying code.

#### Acceptance Criteria

1. THE PlatformConfiguration SHALL contain the platform type as a PlatformType value, an optional region string, an optional list of CredentialReference names, an optional service endpoint overrides dictionary mapping service names to endpoint URLs, and a platform-specific options dictionary.
2. THE PlatformConfiguration SHALL support loading configuration from a Python dictionary.
3. THE PlatformConfiguration SHALL support loading configuration from a JSON file path.
4. THE PlatformConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE PlatformConfiguration SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
6. THE PlatformConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. WHEN the PlatformConfiguration contains CredentialReference entries, THE PlatformConfiguration SHALL resolve each CredentialReference through `automojo-credentials` at initialization time.
8. IF a CredentialReference cannot be resolved, THEN THE PlatformConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
9. THE PlatformConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration, excluding resolved credential values.
10. THE PlatformConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration, excluding resolved credential values.
11. THE PlatformConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration, excluding resolved credential values.
12. THE PlatformConfiguration SHALL provide a class method from_dict that constructs a PlatformConfiguration from a dictionary.
13. THE PlatformConfiguration SHALL provide a class method from_json that deserializes a JSON string into a PlatformConfiguration instance.
14. THE PlatformConfiguration SHALL provide a class method from_yaml that deserializes a YAML string into a PlatformConfiguration instance.
15. FOR ALL valid PlatformConfiguration instances, calling to_json and then from_json SHALL produce an equivalent PlatformConfiguration object (round-trip property).
16. FOR ALL valid PlatformConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent PlatformConfiguration object (round-trip property).
17. THE PlatformConfiguration SHALL provide a __repr__ method that includes the class name, platform type, and region.
18. THE PlatformConfiguration SHALL provide a __str__ method that returns a human-readable summary including the platform type, region, and the count of service endpoint overrides.

### Requirement 4: Platform Service Abstraction

**User Story:** As a developer, I want abstract base classes for platform services, so that I can write agent code that works across platforms without depending on provider-specific APIs.

#### Acceptance Criteria

1. THE PlatformService base class SHALL define an abstract interface that includes a service_name property, a service_type property (one of "compute", "storage", "messaging"), a platform_type property returning the PlatformType, an is_available method that checks service availability, and a health_check method that returns a boolean indicating service health.
2. THE PlatformService base class SHALL require all subclasses to provide an implementation for the is_available and health_check methods.
3. THE PlatformService base class SHALL accept an optional PlatformConfiguration at construction time for service-specific settings.
4. THE PlatformService base class SHALL provide a __repr__ method that includes the class name, service name, service type, and platform type.
5. THE PlatformService base class SHALL provide a __str__ method that returns a human-readable summary including the service name, service type, and platform type.

### Requirement 5: Compute Service

**User Story:** As a developer, I want a unified compute service interface, so that I can invoke functions and manage execution contexts across AWS Lambda, Azure Functions, GCP Cloud Functions, and local processes through a consistent API.

#### Acceptance Criteria

1. THE ComputeService base class SHALL inherit from PlatformService and SHALL set the service_type to "compute".
2. THE ComputeService base class SHALL define an abstract invoke method that accepts a function name string, a payload as a Python dictionary, and an optional timeout in seconds as a float, and returns an InvocationResult.
3. THE ComputeService base class SHALL define an abstract invoke_async method that accepts a function name string and a payload as a Python dictionary, and returns a request identifier string for tracking the asynchronous invocation.
4. THE ComputeService base class SHALL define an abstract get_invocation_status method that accepts a request identifier string and returns an InvocationResult representing the current status of the asynchronous invocation.
5. THE ComputeService base class SHALL define an abstract list_functions method that returns a list of available function name strings.
6. IF the invoke method exceeds the specified timeout, THEN THE ComputeService SHALL return an InvocationResult with status "timeout" and an error message indicating the timeout duration.
7. IF the invoke method encounters a service error, THEN THE ComputeService SHALL raise a ComputeError that includes the function name, the platform type, and the error detail.
8. THE ComputeService base class SHALL provide a __repr__ method that includes the class name, service name, and platform type.
9. THE ComputeService base class SHALL provide a __str__ method that returns a human-readable summary including the service name and platform type.

### Requirement 6: Storage Service

**User Story:** As a developer, I want a unified storage service interface, so that I can store, retrieve, list, and delete objects across AWS S3, Azure Blob Storage, GCP Cloud Storage, and local file system through a consistent API.

#### Acceptance Criteria

1. THE StorageService base class SHALL inherit from PlatformService and SHALL set the service_type to "storage".
2. THE StorageService base class SHALL define an abstract put_object method that accepts a container name string, an object key string, content as bytes, an optional content type string, and an optional metadata dictionary, and stores the object.
3. THE StorageService base class SHALL define an abstract get_object method that accepts a container name string and an object key string, and returns a StorageObject.
4. THE StorageService base class SHALL define an abstract delete_object method that accepts a container name string and an object key string, and removes the object.
5. THE StorageService base class SHALL define an abstract list_objects method that accepts a container name string and an optional prefix string, and returns a list of object key strings matching the prefix.
6. THE StorageService base class SHALL define an abstract object_exists method that accepts a container name string and an object key string, and returns a boolean indicating whether the object exists.
7. THE StorageService base class SHALL define an abstract create_container method that accepts a container name string and creates the storage container.
8. THE StorageService base class SHALL define an abstract delete_container method that accepts a container name string and removes the storage container.
9. THE StorageService base class SHALL define an abstract list_containers method that returns a list of container name strings.
10. IF a get_object request references a nonexistent object, THEN THE StorageService SHALL raise a StorageError that includes the container name, object key, and platform type.
11. IF a storage operation encounters a service error, THEN THE StorageService SHALL raise a StorageError that includes the operation name, container name, platform type, and error detail.
12. THE StorageService base class SHALL provide a __repr__ method that includes the class name, service name, and platform type.
13. THE StorageService base class SHALL provide a __str__ method that returns a human-readable summary including the service name and platform type.

### Requirement 7: Storage Object

**User Story:** As a developer, I want a structured object representing stored data, so that I can access object content and metadata through a consistent interface regardless of the storage backend.

#### Acceptance Criteria

1. THE StorageObject SHALL contain the object key as a string, content as bytes, content type as a string, metadata as a dictionary, size in bytes as an integer, and last modified timestamp.
2. THE StorageObject SHALL expose all fields as read-only properties.
3. THE StorageObject SHALL provide an as_dict method that returns a dictionary representation of the object fields, encoding content as base64 for serialization.
4. THE StorageObject SHALL provide a to_json method that returns a JSON string representation of the object fields.
5. THE StorageObject SHALL provide a class method from_dict that constructs a StorageObject from a dictionary, decoding base64 content.
6. THE StorageObject SHALL provide a class method from_json that deserializes a JSON string into a StorageObject instance.
7. FOR ALL valid StorageObject instances, calling to_json and then from_json SHALL produce an equivalent StorageObject object (round-trip property).
8. THE StorageObject SHALL provide a __repr__ method that includes the class name, object key, content type, and size.
9. THE StorageObject SHALL provide a __str__ method that returns a human-readable summary including the object key, content type, and size.

### Requirement 8: Messaging Service

**User Story:** As a developer, I want a unified messaging service interface, so that I can send and receive queue messages across AWS SQS, Azure Service Bus, GCP Pub/Sub, and local in-memory queues through a consistent API.

#### Acceptance Criteria

1. THE MessagingService base class SHALL inherit from PlatformService and SHALL set the service_type to "messaging".
2. THE MessagingService base class SHALL define an abstract send_message method that accepts a queue name string, a body as a Python object, and an optional attributes dictionary, and returns a message identifier string.
3. THE MessagingService base class SHALL define an abstract receive_messages method that accepts a queue name string, an optional max count integer with a default of 1, and an optional wait time in seconds as a float, and returns a list of QueueMessage objects.
4. THE MessagingService base class SHALL define an abstract acknowledge_message method that accepts a queue name string and a receipt handle string, and acknowledges the message for deletion from the queue.
5. THE MessagingService base class SHALL define an abstract create_queue method that accepts a queue name string and creates the message queue.
6. THE MessagingService base class SHALL define an abstract delete_queue method that accepts a queue name string and removes the message queue.
7. THE MessagingService base class SHALL define an abstract list_queues method that returns a list of queue name strings.
8. IF a send_message operation encounters a service error, THEN THE MessagingService SHALL raise a MessagingError that includes the queue name, platform type, and error detail.
9. IF a receive_messages operation encounters a service error, THEN THE MessagingService SHALL raise a MessagingError that includes the queue name, platform type, and error detail.
10. THE MessagingService base class SHALL provide a __repr__ method that includes the class name, service name, and platform type.
11. THE MessagingService base class SHALL provide a __str__ method that returns a human-readable summary including the service name and platform type.

### Requirement 9: Queue Message

**User Story:** As a developer, I want a structured object representing a queue message, so that I can access message content and metadata through a consistent interface regardless of the messaging backend.

#### Acceptance Criteria

1. THE QueueMessage SHALL contain a unique identifier string, a queue name string, a body as a Python object, an attributes dictionary, a receipt handle string for acknowledgment, and a timestamp.
2. THE QueueMessage SHALL expose all fields as read-only properties.
3. THE QueueMessage SHALL provide an as_dict method that returns a dictionary representation of the message fields.
4. THE QueueMessage SHALL provide a to_json method that returns a JSON string representation of the message fields.
5. THE QueueMessage SHALL provide a class method from_dict that constructs a QueueMessage from a dictionary.
6. THE QueueMessage SHALL provide a class method from_json that deserializes a JSON string into a QueueMessage instance.
7. FOR ALL valid QueueMessage instances with JSON-serializable bodies, calling to_json and then from_json SHALL produce an equivalent QueueMessage object (round-trip property).
8. THE QueueMessage SHALL provide a __repr__ method that includes the class name, identifier, and queue name.
9. THE QueueMessage SHALL provide a __str__ method that returns a human-readable summary including the identifier, queue name, and a truncated body preview.

### Requirement 10: Invocation Result

**User Story:** As a developer, I want a structured object representing a compute invocation result, so that I can inspect execution status, response data, and error information through a consistent interface.

#### Acceptance Criteria

1. THE InvocationResult SHALL contain a status string (one of "success", "error", "timeout"), a response payload as a Python object, an optional error message string, the execution duration in seconds as a float, and a request identifier string.
2. THE InvocationResult SHALL expose all fields as read-only properties.
3. THE InvocationResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
4. THE InvocationResult SHALL provide a to_json method that returns a JSON string representation of the result fields.
5. THE InvocationResult SHALL provide a class method from_dict that constructs an InvocationResult from a dictionary.
6. THE InvocationResult SHALL provide a class method from_json that deserializes a JSON string into an InvocationResult instance.
7. FOR ALL valid InvocationResult instances with JSON-serializable payloads, calling to_json and then from_json SHALL produce an equivalent InvocationResult object (round-trip property).
8. THE InvocationResult SHALL provide a __repr__ method that includes the class name, status, and request identifier.
9. THE InvocationResult SHALL provide a __str__ method that returns a human-readable summary including the status, request identifier, and execution duration.

### Requirement 11: Platform Adapter

**User Story:** As a developer, I want a platform adapter that bundles all service implementations for a specific platform, so that I can switch between platforms by swapping a single adapter without reconfiguring individual services.

#### Acceptance Criteria

1. THE PlatformAdapter base class SHALL define an abstract interface that includes a platform_type property returning a PlatformType, a get_compute_service method returning a ComputeService, a get_storage_service method returning a StorageService, a get_messaging_service method returning a MessagingService, and a get_all_services method returning a list of all PlatformService instances.
2. THE PlatformAdapter base class SHALL require all subclasses to provide an implementation for the get_compute_service, get_storage_service, and get_messaging_service methods.
3. THE PlatformAdapter base class SHALL accept a PlatformConfiguration at construction time for initializing platform-specific service clients.
4. THE PlatformAdapter base class SHALL provide a health_check method that invokes health_check on each service and returns a dictionary mapping service names to boolean health status values.
5. IF a service health check fails, THEN THE PlatformAdapter SHALL log the failure at WARNING level including the service name, platform type, and error detail, and report the service as unhealthy in the health check result.
6. THE PlatformAdapter base class SHALL provide a __repr__ method that includes the class name and platform type.
7. THE PlatformAdapter base class SHALL provide a __str__ method that returns a human-readable summary including the platform type and the list of available service names.

### Requirement 12: AWS Platform Adapter

**User Story:** As a developer, I want an AWS platform adapter, so that my agents can use AWS Lambda for compute, S3 for storage, and SQS for messaging through the unified platform service interfaces.

#### Acceptance Criteria

1. THE AwsPlatformAdapter SHALL inherit from PlatformAdapter and SHALL set the platform_type to PlatformType.AWS.
2. THE AwsPlatformAdapter SHALL provide an AwsComputeService that implements ComputeService using AWS Lambda invocation through the AWS SDK.
3. THE AwsPlatformAdapter SHALL provide an AwsStorageService that implements StorageService using AWS S3 operations through the AWS SDK.
4. THE AwsPlatformAdapter SHALL provide an AwsMessagingService that implements MessagingService using AWS SQS operations through the AWS SDK.
5. THE AwsPlatformAdapter SHALL resolve AWS credentials through CredentialReference entries in the PlatformConfiguration, falling back to the default AWS credential chain when no explicit credentials are configured.
6. THE AwsPlatformAdapter SHALL use the region from PlatformConfiguration, falling back to the AWS_REGION environment variable when no explicit region is configured.
7. WHEN a service endpoint override is configured in PlatformConfiguration for an AWS service, THE AwsPlatformAdapter SHALL use the override endpoint URL instead of the default AWS endpoint.

### Requirement 13: Azure Platform Adapter

**User Story:** As a developer, I want an Azure platform adapter, so that my agents can use Azure Functions for compute, Blob Storage for storage, and Service Bus for messaging through the unified platform service interfaces.

#### Acceptance Criteria

1. THE AzurePlatformAdapter SHALL inherit from PlatformAdapter and SHALL set the platform_type to PlatformType.AZURE.
2. THE AzurePlatformAdapter SHALL provide an AzureComputeService that implements ComputeService using Azure Functions invocation through the Azure SDK.
3. THE AzurePlatformAdapter SHALL provide an AzureStorageService that implements StorageService using Azure Blob Storage operations through the Azure SDK.
4. THE AzurePlatformAdapter SHALL provide an AzureMessagingService that implements MessagingService using Azure Service Bus operations through the Azure SDK.
5. THE AzurePlatformAdapter SHALL resolve Azure credentials through CredentialReference entries in the PlatformConfiguration, falling back to the default Azure credential chain when no explicit credentials are configured.
6. THE AzurePlatformAdapter SHALL use the region from PlatformConfiguration, falling back to the AZURE_REGION environment variable when no explicit region is configured.
7. WHEN a service endpoint override is configured in PlatformConfiguration for an Azure service, THE AzurePlatformAdapter SHALL use the override endpoint URL instead of the default Azure endpoint.

### Requirement 14: GCP Platform Adapter

**User Story:** As a developer, I want a GCP platform adapter, so that my agents can use Cloud Functions for compute, Cloud Storage for storage, and Pub/Sub for messaging through the unified platform service interfaces.

#### Acceptance Criteria

1. THE GcpPlatformAdapter SHALL inherit from PlatformAdapter and SHALL set the platform_type to PlatformType.GCP.
2. THE GcpPlatformAdapter SHALL provide a GcpComputeService that implements ComputeService using GCP Cloud Functions invocation through the GCP SDK.
3. THE GcpPlatformAdapter SHALL provide a GcpStorageService that implements StorageService using GCP Cloud Storage operations through the GCP SDK.
4. THE GcpPlatformAdapter SHALL provide a GcpMessagingService that implements MessagingService using GCP Pub/Sub operations through the GCP SDK.
5. THE GcpPlatformAdapter SHALL resolve GCP credentials through CredentialReference entries in the PlatformConfiguration, falling back to the default GCP application default credentials when no explicit credentials are configured.
6. THE GcpPlatformAdapter SHALL use the region from PlatformConfiguration, falling back to the GCP_REGION environment variable when no explicit region is configured.
7. WHEN a service endpoint override is configured in PlatformConfiguration for a GCP service, THE GcpPlatformAdapter SHALL use the override endpoint URL instead of the default GCP endpoint.

### Requirement 15: Local Platform Adapter

**User Story:** As a developer, I want a local platform adapter, so that my agents can run on a developer workstation using subprocess execution, file system storage, and in-memory queuing without cloud dependencies.

#### Acceptance Criteria

1. THE LocalPlatformAdapter SHALL inherit from PlatformAdapter and SHALL set the platform_type to PlatformType.LOCAL.
2. THE LocalPlatformAdapter SHALL provide a LocalComputeService that implements ComputeService using subprocess execution for function invocation.
3. THE LocalPlatformAdapter SHALL provide a LocalStorageService that implements StorageService using the local file system for object storage, storing objects under a configurable base directory.
4. THE LocalPlatformAdapter SHALL provide a LocalMessagingService that implements MessagingService using in-memory queues for message exchange.
5. WHEN the LocalStorageService base directory is not configured, THE LocalStorageService SHALL use a directory under the AppContext directory provided by `automojo-this-app`.
6. THE LocalMessagingService SHALL support concurrent access to in-memory queues using appropriate synchronization primitives.
7. THE LocalComputeService SHALL support configuring a timeout in seconds for subprocess execution, defaulting to 30 seconds.

### Requirement 16: Platform Service Registry

**User Story:** As a developer, I want a registry that tracks available platform services within a runtime, so that I can discover and look up services by name or type.

#### Acceptance Criteria

1. THE PlatformServiceRegistry SHALL support registration of a PlatformService instance using the service name as the registration key.
2. IF a PlatformService with a duplicate name is registered, THEN THE PlatformServiceRegistry SHALL raise a SemanticError that includes the duplicate service name.
3. THE PlatformServiceRegistry SHALL support deregistration of a PlatformService by name.
4. THE PlatformServiceRegistry SHALL support lookup of a registered PlatformService by name, returning the PlatformService instance or None when the name is not found.
5. THE PlatformServiceRegistry SHALL support lookup of registered PlatformService instances by service type, returning a list of PlatformService instances matching the provided service type.
6. THE PlatformServiceRegistry SHALL support enumeration of all registered PlatformService instances as a list.
7. THE PlatformServiceRegistry SHALL expose a read-only property for the count of currently registered services.
8. THE PlatformServiceRegistry SHALL provide a has_service method that accepts a service name and returns a boolean indicating whether a PlatformService with the given name is registered.
9. THE PlatformServiceRegistry SHALL provide a __repr__ method that includes the class name and the count of registered services.
10. THE PlatformServiceRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered service names and service types.

### Requirement 17: Platform Runtime

**User Story:** As a developer, I want a platform runtime component that manages the active platform environment for an agent, so that agents can access platform services through a single entry point.

#### Acceptance Criteria

1. THE PlatformRuntime SHALL accept a PlatformConfiguration and a PlatformAdapter at construction time.
2. THE PlatformRuntime SHALL expose a read-only property for the PlatformType of the active platform.
3. THE PlatformRuntime SHALL expose a read-only property for the PlatformConfiguration.
4. THE PlatformRuntime SHALL expose a read-only property for the PlatformAdapter.
5. THE PlatformRuntime SHALL provide a get_compute_service method that returns the ComputeService from the active PlatformAdapter.
6. THE PlatformRuntime SHALL provide a get_storage_service method that returns the StorageService from the active PlatformAdapter.
7. THE PlatformRuntime SHALL provide a get_messaging_service method that returns the MessagingService from the active PlatformAdapter.
8. THE PlatformRuntime SHALL provide a get_service method that accepts a service name and returns the PlatformService from the PlatformServiceRegistry.
9. THE PlatformRuntime SHALL maintain a PlatformServiceRegistry and register all services from the PlatformAdapter during initialization.
10. THE PlatformRuntime SHALL provide a health_check method that delegates to the PlatformAdapter health_check and returns the result.
11. THE PlatformRuntime SHALL provide a __repr__ method that includes the class name and platform type.
12. THE PlatformRuntime SHALL provide a __str__ method that returns a human-readable summary including the platform type, region, and the count of available services.

### Requirement 18: Platform Runtime Auto-Configuration

**User Story:** As a developer, I want the platform runtime to auto-configure itself based on the detected environment, so that agents can start with minimal configuration on any supported platform.

#### Acceptance Criteria

1. THE PlatformRuntime SHALL provide a class method create_auto that uses the PlatformDetector to detect the current platform and creates a PlatformRuntime with the appropriate PlatformAdapter.
2. WHEN create_auto is called without a PlatformConfiguration, THE PlatformRuntime SHALL construct a default PlatformConfiguration using the detected PlatformType and environment-derived settings (region from environment variables, default credential chain).
3. WHEN create_auto is called with a partial PlatformConfiguration, THE PlatformRuntime SHALL merge the provided configuration with environment-derived defaults, with explicit configuration values taking precedence.
4. THE PlatformRuntime SHALL log the auto-configuration result at INFO level including the detected platform type, region, and the list of initialized service names.
5. IF auto-configuration fails due to missing credentials or unavailable services, THEN THE PlatformRuntime SHALL raise a PlatformError with a descriptive message identifying the failure reason and the platform type.

### Requirement 19: Deployment Descriptor

**User Story:** As a developer, I want a declarative deployment descriptor that defines how an agent is deployed on a specific platform, so that I can describe deployment configuration portably across platforms.

#### Acceptance Criteria

1. THE DeploymentDescriptor SHALL contain a descriptor name string, a target PlatformType, a compute configuration dictionary, a storage configuration dictionary, a messaging configuration dictionary, an environment variables dictionary, and a scaling parameters dictionary.
2. THE DeploymentDescriptor SHALL expose all fields as read-only properties.
3. THE DeploymentDescriptor SHALL provide an as_dict method that returns a dictionary representation of the descriptor fields.
4. THE DeploymentDescriptor SHALL provide a to_json method that returns a JSON string representation of the descriptor fields.
5. THE DeploymentDescriptor SHALL provide a to_yaml method that returns a YAML string representation of the descriptor fields.
6. THE DeploymentDescriptor SHALL provide a class method from_dict that constructs a DeploymentDescriptor from a dictionary.
7. THE DeploymentDescriptor SHALL provide a class method from_json that deserializes a JSON string into a DeploymentDescriptor instance.
8. THE DeploymentDescriptor SHALL provide a class method from_yaml that deserializes a YAML string into a DeploymentDescriptor instance.
9. FOR ALL valid DeploymentDescriptor instances, calling to_json and then from_json SHALL produce an equivalent DeploymentDescriptor object (round-trip property).
10. FOR ALL valid DeploymentDescriptor instances, calling to_yaml and then from_yaml SHALL produce an equivalent DeploymentDescriptor object (round-trip property).
11. THE DeploymentDescriptor SHALL provide a __repr__ method that includes the class name, descriptor name, and target platform type.
12. THE DeploymentDescriptor SHALL provide a __str__ method that returns a human-readable summary including the descriptor name, target platform type, and the scaling parameters.

### Requirement 20: Deployment Descriptor Parsing and Printing

**User Story:** As a developer, I want to parse deployment descriptors from files and print them back to files, so that deployment configurations can be stored, versioned, and shared.

#### Acceptance Criteria

1. THE DeploymentDescriptorParser SHALL provide a parse_json method that accepts a JSON string and returns a DeploymentDescriptor instance.
2. THE DeploymentDescriptorParser SHALL provide a parse_yaml method that accepts a YAML string and returns a DeploymentDescriptor instance.
3. THE DeploymentDescriptorParser SHALL provide a parse_file method that accepts a file path string, detects the format from the file extension (.json or .yaml/.yml), and returns a DeploymentDescriptor instance.
4. WHEN a deployment descriptor file path is provided, THE DeploymentDescriptorParser SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
5. THE DeploymentDescriptorParser SHALL validate the parsed descriptor against a schema, raising a DeploymentDescriptorError when required fields are missing or field values are invalid.
6. IF the file extension is not recognized, THEN THE DeploymentDescriptorParser SHALL raise a DeploymentDescriptorError identifying the unrecognized extension and listing the supported extensions.
7. THE DeploymentDescriptorPrinter SHALL provide a print_json method that accepts a DeploymentDescriptor and returns a JSON string.
8. THE DeploymentDescriptorPrinter SHALL provide a print_yaml method that accepts a DeploymentDescriptor and returns a YAML string.
9. THE DeploymentDescriptorPrinter SHALL provide a print_file method that accepts a DeploymentDescriptor and a file path string, writing the descriptor in the format determined by the file extension.
10. FOR ALL valid DeploymentDescriptor instances, parsing a printed JSON representation SHALL produce an equivalent DeploymentDescriptor object (round-trip property).
11. FOR ALL valid DeploymentDescriptor instances, parsing a printed YAML representation SHALL produce an equivalent DeploymentDescriptor object (round-trip property).
12. THE DeploymentDescriptorParser SHALL provide a __repr__ method that includes the class name.
13. THE DeploymentDescriptorPrinter SHALL provide a __repr__ method that includes the class name.

### Requirement 21: Agent Platform Integration

**User Story:** As a developer, I want the Agent base class to integrate with the PlatformRuntime, so that agents can access platform services directly through the agent instance.

#### Acceptance Criteria

1. THE Agent base class SHALL accept an optional PlatformRuntime at construction time or through the AgentConfiguration.
2. THE Agent base class SHALL expose a read-only property for the PlatformRuntime instance, returning None when no platform runtime is configured.
3. WHEN an Agent is initialized with a PlatformConfiguration in the AgentConfiguration, THE Agent SHALL create a PlatformRuntime using the create_auto method when no explicit PlatformAdapter is provided.
4. THE Agent base class SHALL provide convenience methods get_compute_service, get_storage_service, and get_messaging_service that delegate to the PlatformRuntime.
5. IF platform service convenience methods are called when no PlatformRuntime is configured, THEN THE Agent SHALL raise a SemanticError indicating that a PlatformRuntime must be configured before accessing platform services.
6. WHEN the Agent transitions to the STOPPED state, THE Agent SHALL log the platform runtime status at INFO level including the platform type and service health.

### Requirement 22: Exception Hierarchy

**User Story:** As a developer, I want well-defined exception types for platform operations, so that I can diagnose and handle platform-specific errors precisely.

#### Acceptance Criteria

1. THE PlatformError SHALL inherit from AgentKitError and SHALL be raised for general platform operation failures.
2. THE PlatformError SHALL accept a descriptive message string, an optional cause exception, and an optional platform type.
3. THE PlatformDetectionError SHALL inherit from PlatformError and SHALL be raised when platform detection fails or produces ambiguous results.
4. THE StorageError SHALL inherit from PlatformError and SHALL be raised when a storage operation fails.
5. THE StorageError SHALL contain the operation name, container name, and optional object key in addition to the base PlatformError fields.
6. THE ComputeError SHALL inherit from PlatformError and SHALL be raised when a compute operation fails.
7. THE ComputeError SHALL contain the function name in addition to the base PlatformError fields.
8. THE MessagingError SHALL inherit from PlatformError and SHALL be raised when a messaging operation fails.
9. THE MessagingError SHALL contain the queue name in addition to the base PlatformError fields.
10. THE DeploymentDescriptorError SHALL inherit from PlatformError and SHALL be raised when a deployment descriptor is invalid or cannot be parsed.
11. ALL platform-related exceptions SHALL provide a meaningful __repr__ that includes the exception class name, descriptive message, and platform type.

### Requirement 23: Extension Point Integration

**User Story:** As a developer, I want the platform runtime to support extensibility through `automojo-extension`, so that plugins can register custom platform adapters for additional platforms.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.platform.adapters" through `automojo-extension` for registering PlatformAdapter implementations.
2. WHEN the PlatformRuntime create_auto method is called, THE PlatformRuntime SHALL discover and load all registered PlatformAdapter implementations from the "automojo.agentkit.platform.adapters" ExtensionPoint.
3. WHEN a registered plugin provides a PlatformAdapter for a PlatformType that matches the detected platform, THE PlatformRuntime SHALL use the plugin-provided adapter.
4. IF a platform adapter plugin fails to load, THEN THE framework SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.

### Requirement 24: Structured Logging

**User Story:** As a developer, I want platform runtime operations to produce structured log entries, so that I can monitor and debug platform interactions using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy rooted at `automojo.agentkit.platform`.
2. WHEN a PlatformDetector detects the platform, THE framework SHALL log at INFO level including the detected platform type and the environment indicators.
3. WHEN a PlatformRuntime is initialized, THE framework SHALL log at INFO level including the platform type, region, and the list of initialized service names.
4. WHEN a platform service operation fails, THE framework SHALL log at WARNING level including the service name, operation name, platform type, and error detail.
5. WHEN a PlatformAdapter health check completes, THE framework SHALL log at INFO level including the platform type and the health status of each service.
6. WHEN a DeploymentDescriptor is parsed, THE framework SHALL log at DEBUG level including the descriptor name and target platform type.
