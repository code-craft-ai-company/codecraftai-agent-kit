# Implementation Plan: Cross-Platform Runtime

## Overview

Incremental implementation of the cross-platform runtime feature for the `automojo-agent-kit` SDK. Each task builds on the previous, starting with the exception hierarchy and PlatformType enum, then data transfer objects, abstract service base classes, platform configuration and detection, the service registry, platform adapters (local first, then cloud), deployment descriptors, the PlatformRuntime entry point, and finally Agent integration. Tests mirror the source hierarchy under `source/testroots/automojo/tests/singlehost/agentkit/platform/`.

## Tasks

- [x] 1. Implement platform exception hierarchy and PlatformType enum
  - [x] 1.1 Create `source/packages/automojo/agentkit/platform/__init__.py` as the platform package init
    - Export public API symbols for the platform sub-package
    - _Requirements: None (structural)_

  - [x] 1.2 Create `source/packages/automojo/agentkit/platform/errors.py` with PlatformError, PlatformDetectionError, StorageError, ComputeError, MessagingError, DeploymentDescriptorError
    - PlatformError inherits from AgentKitError, accepts message, optional cause, optional platform_type
    - PlatformDetectionError inherits from PlatformError
    - StorageError inherits from PlatformError, adds operation_name, container_name, optional object_key
    - ComputeError inherits from PlatformError, adds function_name
    - MessagingError inherits from PlatformError, adds queue_name
    - DeploymentDescriptorError inherits from PlatformError
    - All provide meaningful `__repr__` including class name, message, and platform type
    - Use multi-line error message formation pattern per coding standards
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7, 22.8, 22.9, 22.10, 22.11_

  - [x] 1.3 Create `source/packages/automojo/agentkit/platform/platformtype.py` with PlatformType enum
    - Define AWS, AZURE, GCP, LOCAL values
    - Implement from_string class method (case-insensitive), raises SemanticError for invalid values
    - Implement to_string method returning lowercase string
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.4 Write unit tests for platform errors and PlatformType
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/__init__.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/test_errors.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/test_platformtype.py`
    - Test exception inheritance chain (PlatformError -> AgentKitError, StorageError -> PlatformError, etc.)
    - Test __repr__ output includes class name, message, platform type
    - Test StorageError, ComputeError, MessagingError contain their extra fields
    - Test PlatformType.from_string with valid values (case-insensitive) and invalid values (SemanticError)
    - Test PlatformType.to_string returns lowercase
    - _Requirements: 22.1–22.11, 1.1–1.4_

- [x] 2. Implement data transfer objects (StorageObject, QueueMessage, InvocationResult)
  - [x] 2.1 Create `source/packages/automojo/agentkit/platform/services/__init__.py` as the services sub-package init
    - Export public API symbols for service abstractions and DTOs
    - _Requirements: None (structural)_

  - [x] 2.2 Create `source/packages/automojo/agentkit/platform/services/storageobject.py` with StorageObject
    - Immutable object with key, content (bytes), content_type, metadata, size, last_modified properties
    - All fields exposed as read-only properties
    - Implement as_dict (base64-encode content), to_json, from_dict (base64-decode content), from_json
    - Implement __repr__ and __str__ per design
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

  - [x] 2.3 Create `source/packages/automojo/agentkit/platform/services/queuemessage.py` with QueueMessage
    - Immutable object with identifier, queue_name, body, attributes, receipt_handle, timestamp properties
    - All fields exposed as read-only properties
    - Implement as_dict, to_json, from_dict, from_json
    - Implement __repr__ and __str__ (truncated body preview at 50 chars) per design
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9_

  - [x] 2.4 Create `source/packages/automojo/agentkit/platform/services/invocationresult.py` with InvocationResult
    - Immutable object with status, response, error_message, duration, request_id properties
    - VALID_STATUSES = ("success", "error", "timeout")
    - All fields exposed as read-only properties
    - Implement as_dict, to_json, from_dict, from_json
    - Implement __repr__ and __str__ per design
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

  - [x] 2.5 Write unit tests for StorageObject, QueueMessage, InvocationResult
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/__init__.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/test_storageobject.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/test_queuemessage.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/test_invocationresult.py`
    - Test StorageObject: read-only properties, as_dict base64 encoding, to_json/from_json round-trip, __repr__/__str__
    - Test QueueMessage: read-only properties, as_dict, to_json/from_json round-trip, __repr__/__str__ with body truncation
    - Test InvocationResult: read-only properties, valid statuses, as_dict, to_json/from_json round-trip, __repr__/__str__
    - _Requirements: 7.1–7.9, 9.1–9.9, 10.1–10.9_

- [x] 3. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement abstract platform service base classes
  - [x] 4.1 Create `source/packages/automojo/agentkit/platform/services/platformservice.py` with PlatformService ABC
    - Abstract base class with service_name, service_type, platform_type properties
    - Accept optional PlatformConfiguration at construction
    - Define abstract is_available and health_check methods
    - Implement __repr__ and __str__ per design
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 4.2 Create `source/packages/automojo/agentkit/platform/services/computeservice.py` with ComputeService ABC
    - Inherit from PlatformService, set service_type to "compute"
    - Define abstract invoke, invoke_async, get_invocation_status, list_functions methods
    - Implement __repr__ and __str__ per design
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

  - [x] 4.3 Create `source/packages/automojo/agentkit/platform/services/storageservice.py` with StorageService ABC
    - Inherit from PlatformService, set service_type to "storage"
    - Define abstract put_object, get_object, delete_object, list_objects, object_exists, create_container, delete_container, list_containers methods
    - Implement __repr__ and __str__ per design
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13_

  - [x] 4.4 Create `source/packages/automojo/agentkit/platform/services/messagingservice.py` with MessagingService ABC
    - Inherit from PlatformService, set service_type to "messaging"
    - Define abstract send_message, receive_messages, acknowledge_message, create_queue, delete_queue, list_queues methods
    - Implement __repr__ and __str__ per design
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11_

  - [x] 4.5 Write unit tests for abstract service base classes
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/test_platformservice.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/test_computeservice.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/test_storageservice.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/services/test_messagingservice.py`
    - Test that PlatformService, ComputeService, StorageService, MessagingService cannot be instantiated directly (ABC enforcement)
    - Test that concrete subclasses must implement all abstract methods
    - Test service_name, service_type, platform_type properties via a minimal concrete subclass
    - Test __repr__ and __str__ output format
    - _Requirements: 4.1–4.5, 5.1–5.9, 6.1–6.13, 8.1–8.11_

- [x] 5. Implement PlatformConfiguration and PlatformDetector
  - [x] 5.1 Create `source/packages/automojo/agentkit/platform/platformconfiguration.py` with PlatformConfiguration
    - Constructor accepts platform_type, optional region, credential_references, service_endpoint_overrides, options
    - Read-only properties for all fields
    - Implement resolve_credentials method (resolves CredentialReference via automojo-credentials, raises ConfigurationError)
    - Implement as_dict (excludes resolved credentials), to_json, to_yaml
    - Implement from_dict, from_json, from_yaml class methods (validate required fields, raise ConfigurationError)
    - Implement from_json_file, from_yaml_file class methods (resolve path via AppContext, raise ConfigurationError)
    - Implement __repr__ and __str__ per design
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 3.16, 3.17, 3.18_

  - [x] 5.2 Create `source/packages/automojo/agentkit/platform/platformdetector.py` with PlatformDetector
    - Check AWS env vars (AWS_LAMBDA_FUNCTION_NAME, AWS_EXECUTION_ENV, AWS_REGION)
    - Check Azure env vars (AZURE_FUNCTIONS_ENVIRONMENT, WEBSITE_SITE_NAME, AZURE_REGION)
    - Check GCP env vars (GOOGLE_CLOUD_PROJECT, FUNCTION_NAME, GCP_REGION)
    - Default to LOCAL when no cloud vars detected
    - Support optional PlatformConfiguration hint that overrides detection
    - Raise PlatformDetectionError when multiple cloud platforms detected simultaneously
    - Log detection result at INFO level
    - Implement __repr__ and __str__ per design
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 5.3 Write unit tests for PlatformConfiguration
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/test_platformconfiguration.py`
    - Test construction with all fields, read-only properties
    - Test from_dict with valid data and missing required fields (ConfigurationError)
    - Test to_json/from_json round-trip, to_yaml/from_yaml round-trip
    - Test as_dict excludes resolved credential values
    - Test resolve_credentials with mock credential resolver, test unresolvable credential raises ConfigurationError
    - Test from_json_file and from_yaml_file with mock AppContext
    - Test __repr__ and __str__ output
    - _Requirements: 3.1–3.18_

  - [x] 5.4 Write unit tests for PlatformDetector
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/test_platformdetector.py`
    - Use automojo.testbase.mocking to patch os.environ for each platform detection scenario
    - Test AWS detection with AWS env vars set
    - Test Azure detection with Azure env vars set
    - Test GCP detection with GCP env vars set
    - Test LOCAL default when no cloud vars present
    - Test configuration hint overrides environment detection
    - Test PlatformDetectionError when multiple cloud platforms detected
    - Test __repr__ and __str__ output
    - _Requirements: 2.1–2.10_

- [x] 6. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement PlatformServiceRegistry
  - [x] 7.1 Create `source/packages/automojo/agentkit/platform/platformserviceregistry.py` with PlatformServiceRegistry
    - Dictionary-based registry keyed by service name
    - Implement register (raises SemanticError on duplicate), deregister, lookup_by_name, lookup_by_type, list_all, count property, has_service
    - Implement __repr__ and __str__ per design
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10_

  - [x] 7.2 Write unit tests for PlatformServiceRegistry
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/test_platformserviceregistry.py`
    - Test register and lookup_by_name with mock PlatformService instances
    - Test duplicate registration raises SemanticError
    - Test deregister removes service
    - Test lookup_by_type filters correctly
    - Test list_all returns all registered services
    - Test count property
    - Test has_service returns correct boolean
    - Test lookup_by_name returns None for unknown name
    - Test __repr__ and __str__ output
    - _Requirements: 16.1–16.10_

- [x] 8. Implement PlatformAdapter base class and LocalPlatformAdapter
  - [x] 8.1 Create `source/packages/automojo/agentkit/platform/adapters/__init__.py` as the adapters sub-package init
    - Export public API symbols for adapter classes
    - _Requirements: None (structural)_

  - [x] 8.2 Create `source/packages/automojo/agentkit/platform/adapters/platformadapter.py` with PlatformAdapter ABC
    - Accept PlatformConfiguration at construction
    - Define abstract platform_type property, get_compute_service, get_storage_service, get_messaging_service methods
    - Implement get_all_services returning list of all three services
    - Implement health_check that invokes health_check on each service, logs failures at WARNING, returns dict of service name to boolean
    - Implement __repr__ and __str__ per design
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [x] 8.3 Create `source/packages/automojo/agentkit/platform/adapters/localplatformadapter.py` with LocalPlatformAdapter, LocalComputeService, LocalStorageService, LocalMessagingService
    - LocalPlatformAdapter inherits PlatformAdapter, sets platform_type to LOCAL
    - LocalComputeService: subprocess execution with configurable timeout (default 30s), returns InvocationResult with status "timeout" on timeout
    - LocalStorageService: file system storage under configurable base directory (fallback to AppContext dir), companion .meta.json for metadata
    - LocalMessagingService: in-memory queues using collections.deque with threading.Lock for concurrent access
    - All three services implement is_available and health_check
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [x] 8.4 Write unit tests for PlatformAdapter ABC and LocalPlatformAdapter
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/adapters/__init__.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/adapters/test_platformadapter.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/adapters/test_localplatformadapter.py`
    - Test PlatformAdapter cannot be instantiated directly (ABC enforcement)
    - Test PlatformAdapter health_check logs failures and returns unhealthy for failing services (use mocks)
    - Test LocalComputeService invoke with a simple subprocess, test timeout returns InvocationResult with status "timeout"
    - Test LocalStorageService put_object/get_object/delete_object/list_objects/object_exists/create_container/delete_container/list_containers using a temporary directory
    - Test LocalMessagingService send_message/receive_messages/acknowledge_message/create_queue/delete_queue/list_queues with in-memory queues
    - Test concurrent access to LocalMessagingService queues
    - _Requirements: 11.1–11.7, 15.1–15.7_

- [x] 9. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement cloud platform adapters (AWS, Azure, GCP)
  - [x] 10.1 Create `source/packages/automojo/agentkit/platform/adapters/awsplatformadapter.py` with AwsPlatformAdapter, AwsComputeService, AwsStorageService, AwsMessagingService
    - AwsPlatformAdapter inherits PlatformAdapter, sets platform_type to AWS
    - Resolve AWS credentials via CredentialReference, fallback to default AWS credential chain
    - Resolve region from PlatformConfiguration, fallback to AWS_REGION env var
    - Support service endpoint overrides from PlatformConfiguration
    - AwsComputeService wraps AWS Lambda invocation via boto3
    - AwsStorageService wraps AWS S3 operations via boto3
    - AwsMessagingService wraps AWS SQS operations via boto3
    - Raise ComputeError, StorageError, MessagingError on service failures
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

  - [x] 10.2 Create `source/packages/automojo/agentkit/platform/adapters/azureplatformadapter.py` with AzurePlatformAdapter, AzureComputeService, AzureStorageService, AzureMessagingService
    - AzurePlatformAdapter inherits PlatformAdapter, sets platform_type to AZURE
    - Resolve Azure credentials via CredentialReference, fallback to default Azure credential chain
    - Resolve region from PlatformConfiguration, fallback to AZURE_REGION env var
    - Support service endpoint overrides from PlatformConfiguration
    - AzureComputeService wraps Azure Functions invocation via Azure SDK
    - AzureStorageService wraps Azure Blob Storage operations via Azure SDK
    - AzureMessagingService wraps Azure Service Bus operations via Azure SDK
    - Raise ComputeError, StorageError, MessagingError on service failures
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [x] 10.3 Create `source/packages/automojo/agentkit/platform/adapters/gcpplatformadapter.py` with GcpPlatformAdapter, GcpComputeService, GcpStorageService, GcpMessagingService
    - GcpPlatformAdapter inherits PlatformAdapter, sets platform_type to GCP
    - Resolve GCP credentials via CredentialReference, fallback to GCP application default credentials
    - Resolve region from PlatformConfiguration, fallback to GCP_REGION env var
    - Support service endpoint overrides from PlatformConfiguration
    - GcpComputeService wraps GCP Cloud Functions invocation via GCP SDK
    - GcpStorageService wraps GCP Cloud Storage operations via GCP SDK
    - GcpMessagingService wraps GCP Pub/Sub operations via GCP SDK
    - Raise ComputeError, StorageError, MessagingError on service failures
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [x] 10.4 Write unit tests for cloud platform adapters
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/adapters/test_awsplatformadapter.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/adapters/test_azureplatformadapter.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/adapters/test_gcpplatformadapter.py`
    - Use automojo.testbase.mocking.Mock to simulate SDK clients (boto3, Azure SDK, GCP SDK)
    - Test each adapter sets correct platform_type
    - Test credential resolution from PlatformConfiguration and fallback to default chains
    - Test region resolution from PlatformConfiguration and fallback to env vars
    - Test service endpoint overrides are applied
    - Test service methods delegate to mocked SDK clients correctly
    - Test error conditions raise ComputeError, StorageError, MessagingError with correct fields
    - _Requirements: 12.1–12.7, 13.1–13.7, 14.1–14.7_

- [x] 11. Implement DeploymentDescriptor, DeploymentDescriptorParser, DeploymentDescriptorPrinter
  - [x] 11.1 Create `source/packages/automojo/agentkit/platform/deployment/__init__.py` as the deployment sub-package init
    - Export public API symbols for deployment classes
    - _Requirements: None (structural)_

  - [x] 11.2 Create `source/packages/automojo/agentkit/platform/deployment/deploymentdescriptor.py` with DeploymentDescriptor
    - Immutable object with name, target_platform, compute_config, storage_config, messaging_config, environment_variables, scaling_parameters
    - All fields exposed as read-only properties
    - Implement as_dict, to_json, to_yaml, from_dict, from_json, from_yaml
    - Implement __repr__ and __str__ per design
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10, 19.11, 19.12_

  - [x] 11.3 Create `source/packages/automojo/agentkit/platform/deployment/deploymentdescriptorparser.py` with DeploymentDescriptorParser
    - Implement parse_json, parse_yaml, parse_file methods
    - Validate required fields (name, target_platform), raise DeploymentDescriptorError on missing fields
    - Detect file format from extension (.json, .yaml, .yml), raise DeploymentDescriptorError for unrecognized extensions
    - Resolve file path relative to AppContext directory
    - Log parsed descriptor at DEBUG level
    - Implement __repr__ per design
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.10, 20.11, 20.12_

  - [x] 11.4 Create `source/packages/automojo/agentkit/platform/deployment/deploymentdescriptorprinter.py` with DeploymentDescriptorPrinter
    - Implement print_json, print_yaml, print_file methods
    - Detect output format from file extension, raise DeploymentDescriptorError for unrecognized extensions
    - Log written descriptor at DEBUG level
    - Implement __repr__ per design
    - _Requirements: 20.7, 20.8, 20.9, 20.10, 20.11, 20.13_

  - [x] 11.5 Write unit tests for DeploymentDescriptor, DeploymentDescriptorParser, DeploymentDescriptorPrinter
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/deployment/__init__.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/deployment/test_deploymentdescriptor.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/deployment/test_deploymentdescriptorparser.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/deployment/test_deploymentdescriptorprinter.py`
    - Test DeploymentDescriptor: read-only properties, as_dict, to_json/from_json round-trip, to_yaml/from_yaml round-trip, __repr__/__str__
    - Test DeploymentDescriptorParser: parse_json/parse_yaml with valid data, missing required fields raises DeploymentDescriptorError, parse_file with .json/.yaml/.yml extensions, unrecognized extension raises DeploymentDescriptorError
    - Test DeploymentDescriptorPrinter: print_json/print_yaml output, print_file writes correct format, unrecognized extension raises DeploymentDescriptorError
    - Test round-trip: parser.parse_json(printer.print_json(descriptor)) produces equivalent descriptor
    - _Requirements: 19.1–19.12, 20.1–20.13_

- [x] 12. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [-] 13. Implement PlatformRuntime with auto-configuration and extension point integration
  - [x] 13.1 Create `source/packages/automojo/agentkit/platform/platformruntime.py` with PlatformRuntime
    - Accept PlatformConfiguration and PlatformAdapter at construction
    - Maintain PlatformServiceRegistry, register all adapter services during initialization
    - Expose read-only properties: platform_type, configuration, adapter
    - Implement get_compute_service, get_storage_service, get_messaging_service delegating to adapter
    - Implement get_service delegating to registry lookup_by_name
    - Implement health_check delegating to adapter, log results at INFO level
    - Implement create_auto class method: use PlatformDetector, build default config from env if needed, merge partial config, check extension point for plugin adapters, fallback to built-in adapters
    - Implement _load_adapter_from_extensions (discover from "automojo.agentkit.platform.adapters" ExtensionPoint, log plugin failures at WARNING)
    - Implement _create_builtin_adapter (map PlatformType to adapter class, raise PlatformError for unknown type)
    - Log initialization at INFO level with platform type, region, service names
    - Implement __repr__ and __str__ per design
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 17.10, 17.11, 17.12, 18.1, 18.2, 18.3, 18.4, 18.5, 23.1, 23.2, 23.3, 23.4, 24.2, 24.3, 24.4, 24.5_

  - [x] 13.2 Write unit tests for PlatformRuntime
    - Create `source/testroots/automojo/tests/singlehost/agentkit/platform/test_platformruntime.py`
    - Test construction with mock PlatformConfiguration and mock PlatformAdapter
    - Test services are registered in PlatformServiceRegistry during init
    - Test get_compute_service, get_storage_service, get_messaging_service delegate to adapter
    - Test get_service delegates to registry
    - Test health_check delegates to adapter
    - Test create_auto with no config (detects LOCAL, creates LocalPlatformAdapter)
    - Test create_auto with full config (uses provided platform type)
    - Test create_auto with partial config (merges with env defaults)
    - Test create_auto raises PlatformError on failure
    - Test extension point integration with mock ExtensionPoint (plugin adapter used when available)
    - Test plugin load failure is logged at WARNING and remaining plugins continue
    - Test __repr__ and __str__ output
    - _Requirements: 17.1–17.12, 18.1–18.5, 23.1–23.4_

- [x] 14. Implement Agent platform integration
  - [x] 14.1 Extend Agent base class with PlatformRuntime support
    - Add optional PlatformRuntime at construction or via AgentConfiguration
    - Add platform_runtime read-only property (returns None when not configured)
    - Auto-create PlatformRuntime via create_auto when AgentConfiguration contains PlatformConfiguration
    - Add get_compute_service, get_storage_service, get_messaging_service convenience methods delegating to PlatformRuntime
    - Raise SemanticError when convenience methods called without configured PlatformRuntime
    - Log platform runtime status at INFO level when Agent transitions to STOPPED state
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6_

  - [x] 14.2 Write unit tests for Agent platform integration
    - Create or extend `source/testroots/automojo/tests/singlehost/agentkit/platform/test_agentplatformintegration.py`
    - Test Agent with PlatformRuntime configured: convenience methods return correct services
    - Test Agent without PlatformRuntime: convenience methods raise SemanticError
    - Test Agent auto-creates PlatformRuntime from AgentConfiguration with PlatformConfiguration
    - Test platform_runtime property returns None when not configured
    - Use automojo.testbase.mocking.Mock for PlatformRuntime, PlatformAdapter, and services
    - _Requirements: 21.1–21.6_

- [-] 15. Wire platform package exports and structured logging
  - [x] 15.1 Update `source/packages/automojo/agentkit/platform/__init__.py` with complete public API exports
    - Export all public classes: PlatformType, PlatformDetector, PlatformConfiguration, PlatformRuntime, PlatformServiceRegistry, PlatformService, ComputeService, StorageService, MessagingService, StorageObject, QueueMessage, InvocationResult, PlatformAdapter, AwsPlatformAdapter, AzurePlatformAdapter, GcpPlatformAdapter, LocalPlatformAdapter, DeploymentDescriptor, DeploymentDescriptorParser, DeploymentDescriptorPrinter, and all error classes
    - _Requirements: None (structural wiring)_

  - [x] 15.2 Configure structured logging hierarchy for all platform components
    - Ensure all platform modules use loggers under `automojo.agentkit.platform` hierarchy
    - Verify PlatformDetector logs at INFO, PlatformRuntime logs at INFO, service failures log at WARNING, deployment parsing logs at DEBUG
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6_

- [x] 16. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Source files go under `source/packages/automojo/agentkit/platform/` with all-lowercase filenames (no underscores)
- Tests go under `source/testroots/automojo/tests/singlehost/agentkit/platform/` mirroring the source hierarchy
- Tests use the `testbase` framework and `automojo.testbase.mocking` for mocks
- Cloud adapter tests mock SDK clients; LocalPlatformAdapter tests use real file system and in-memory queues
