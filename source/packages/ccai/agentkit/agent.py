"""
    Defines the Agent abstract base class for the codecraftai-agent-kit framework.

    Agent provides the foundational abstraction for all agents in the SDK,
    including lifecycle management, identity, configuration, hooks,
    sub-agent composition, and structured logging.
"""

import abc
import logging
import os
import time

from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentidentity import AgentIdentity
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.agentstatemachine import AgentStateMachine
from ccai.agentkit.configurationmanager import ConfigurationManager
from ccai.agentkit.contextwindow import ContextWindow
from ccai.agentkit.contextwindowstrategy import ContextWindowStrategy
from ccai.agentkit.costtracker import CostTracker
from ccai.agentkit.debugsession import DebugSession
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.fallbackchain import FallbackChain
from ccai.agentkit.featureflagregistry import FeatureFlagRegistry
from ccai.agentkit.hotreloadmonitor import HotReloadMonitor
from ccai.agentkit.hotreloadpolicy import HotReloadPolicy
from ccai.agentkit.inmemorystore import InMemoryStore
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmerrors import LLMRequestError
from ccai.agentkit.llmprovider import LLMProvider
from ccai.agentkit.llmproviderregistry import LLMProviderRegistry
from ccai.agentkit.llmresponse import LLMResponse
from ccai.agentkit.memoryconfiguration import MemoryConfiguration
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryquery import MemoryQuery
from ccai.agentkit.memoryqueryresult import MemoryQueryResult
from ccai.agentkit.memoryscope import MemoryScope
from ccai.agentkit.memorystore import MemoryStore
from ccai.agentkit.memorystoreregistry import MemoryStoreRegistry
from ccai.agentkit.observabilityconfiguration import ObservabilityConfiguration
from ccai.agentkit.observabilitypipeline import ObservabilityPipeline
from ccai.agentkit.pluginmanager import PluginManager
from ccai.agentkit.resilienceconfiguration import ResilienceConfiguration
from ccai.agentkit.resiliencepipeline import ResiliencePipeline
from ccai.agentkit.retrypolicy import RetryPolicy
from ccai.agentkit.tool import Tool
from ccai.agentkit.toolchain import ToolChain
from ccai.agentkit.toolchainexecutor import ToolChainExecutor
from ccai.agentkit.toolchainresult import ToolChainResult
from ccai.agentkit.toolexecutor import ToolExecutor
from ccai.agentkit.toolregistry import ToolRegistry
from ccai.agentkit.toolresult import ToolResult
from ccai.agentkit.transitionrecord import TransitionRecord
from ccai.agentkit.workflowconfiguration import WorkflowConfiguration
from ccai.agentkit.workflowdefinition import WorkflowDefinition
from ccai.agentkit.workflowexecutor import WorkflowExecutor
from ccai.agentkit.workflowregistry import WorkflowRegistry
from ccai.agentkit.workflowresult import WorkflowResult
from ccai.agentkit.addressresolver import AddressResolver
from ccai.agentkit.jsonmessageserializer import JsonMessageSerializer
from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.approvalgate import ApprovalGate
from ccai.agentkit.checkpointmanager import CheckpointManager
from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.messagepattern import MessagePattern
from ccai.agentkit.messagerouter import MessageRouter
from ccai.agentkit.messageserializerregistry import MessageSerializerRegistry
from ccai.agentkit.messagingconfiguration import MessagingConfiguration
from ccai.agentkit.pubsubbroker import PubSubBroker
from ccai.agentkit.requestresponsehandler import RequestResponseHandler
from ccai.agentkit.subscription import Subscription
from ccai.agentkit.transport import Transport
from ccai.agentkit.transportregistry import TransportRegistry


VALID_TRANSITION_POINTS = [
    "on_initialize",
    "on_start",
    "on_pause",
    "on_resume",
    "on_stop",
    "on_error",
]


class Agent(abc.ABC):
    """
        Abstract base class for all agents in the codecraftai-agent-kit framework.

        Provides lifecycle management, identity, configuration, hooks,
        sub-agent composition with cycle detection, and structured logging.
        Subclasses must implement the abstract lifecycle methods: initialize,
        start, pause, resume, stop, and reset.

        :param configuration: The AgentConfiguration for this agent.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        self._configuration: AgentConfiguration = configuration
        self._identity: AgentIdentity = self._create_identity_from_config(configuration)
        self._state_machine: AgentStateMachine = AgentStateMachine()
        self._parent: Optional["Agent"] = None
        self._sub_agents: List["Agent"] = []
        self._extensions: List = []
        self._hooks: Dict[str, List[Callable]] = {
            "on_initialize": [],
            "on_start": [],
            "on_pause": [],
            "on_resume": [],
            "on_stop": [],
            "on_error": [],
        }

        logger_name = "ccai.agentkit.agent.{}".format(self._identity.identifier)
        self._logger: logging.Logger = logging.getLogger(logger_name)

        self._configuration_manager = ConfigurationManager(
            agent_identifier=self._identity.identifier
        )
        self._feature_flag_registry = FeatureFlagRegistry()
        self._plugin_manager = PluginManager(
            agent_identifier=self._identity.identifier
        )
        self._hot_reload_monitor = None
        self._hot_reload_policy = None
        self._resilience_pipeline = None
        self._observability_pipeline = None
        self._debug_session = None

        self._tool_registry = ToolRegistry()
        self._tool_executor = ToolExecutor()
        self._tool_chain_executor = ToolChainExecutor(tool_executor=self._tool_executor)

        self._llm_provider_registry = LLMProviderRegistry()
        self._cost_tracker = CostTracker()

        self._memory_store: Optional[MemoryStore] = None
        self._memory_store_registry: MemoryStoreRegistry = MemoryStoreRegistry()
        self._context_window: Optional[ContextWindow] = None
        self._memory_configuration: Optional[MemoryConfiguration] = None

        self._workflow_registry: WorkflowRegistry = WorkflowRegistry()
        self._workflow_executor: Optional[WorkflowExecutor] = None
        self._checkpoint_manager: Optional[CheckpointManager] = None
        self._approval_gate: ApprovalGate = ApprovalGate()
        self._workflow_configuration: Optional[WorkflowConfiguration] = None

        self._transport_registry: TransportRegistry = TransportRegistry()
        self._message_serializer_registry: MessageSerializerRegistry = MessageSerializerRegistry()
        self._message_router: MessageRouter = MessageRouter()
        self._pubsub_broker: PubSubBroker = PubSubBroker()
        self._address_resolver: AddressResolver = AddressResolver(agent_registry=AgentRegistry.instance())
        self._request_response_handler: RequestResponseHandler = RequestResponseHandler()
        self._messaging_configuration: Optional[MessagingConfiguration] = None

        self._platform_runtime = None

        platform_config = configuration.get_platform_configuration()
        if platform_config is not None:
            from ccai.agentkit.platform.platformruntime import PlatformRuntime
            self._platform_runtime = PlatformRuntime.create_auto(
                configuration=platform_config
            )

        AgentRegistry.instance().register(self)

        self._initialize_observability()

        return

    @staticmethod
    def _create_identity_from_config(configuration: AgentConfiguration) -> AgentIdentity:
        """
            Creates an AgentIdentity from the configuration identity dictionary.

            :param configuration: The AgentConfiguration containing identity data.

            :returns: An AgentIdentity instance.
        """
        identity_data = configuration.identity
        name = identity_data["name"]
        version = identity_data["version"]
        tags = identity_data.get("tags", None)
        identifier = identity_data.get("identifier", None)

        identity = AgentIdentity(
            name=name,
            version=version,
            tags=tags,
            identifier=identifier
        )
        return identity

    # -----------------------------------------------------------------------
    # Read-only properties
    # -----------------------------------------------------------------------

    @property
    def state(self) -> LifecycleState:
        """
            The current lifecycle state of the agent.

            :returns: The current LifecycleState.
        """
        return self._state_machine.current_state

    @property
    def identity(self) -> AgentIdentity:
        """
            The identity and metadata of the agent.

            :returns: The AgentIdentity instance.
        """
        return self._identity

    @property
    def configuration(self) -> AgentConfiguration:
        """
            The configuration of the agent.

            :returns: The AgentConfiguration instance.
        """
        return self._configuration

    @property
    def parent(self) -> Optional["Agent"]:
        """
            The parent agent, or None if this agent has no parent.

            :returns: The parent Agent instance or None.
        """
        return self._parent

    @property
    def sub_agents(self) -> List["Agent"]:
        """
            A list of sub-agent instances managed by this agent.

            :returns: A list of Agent instances.
        """
        return list(self._sub_agents)

    @property
    def extensions(self) -> List:
        """
            A list of loaded extensions for this agent.

            :returns: A list of extension objects.
        """
        return list(self._extensions)

    @property
    def configuration_manager(self) -> ConfigurationManager:
        """
            The configuration manager for this agent.

            :returns: The ConfigurationManager instance.
        """
        return self._configuration_manager

    @property
    def feature_flags(self) -> FeatureFlagRegistry:
        """
            The feature flag registry for this agent.

            :returns: The FeatureFlagRegistry instance.
        """
        return self._feature_flag_registry

    @property
    def plugin_manager(self) -> PluginManager:
        """
            The plugin manager for this agent.

            :returns: The PluginManager instance.
        """
        return self._plugin_manager

    @property
    def resilience(self):
        """
            The ResiliencePipeline for this agent.

            :returns: The ResiliencePipeline instance or None.
        """
        return self._resilience_pipeline

    @property
    def health_monitor(self):
        """
            The HealthMonitor from the ResiliencePipeline.

            :returns: The HealthMonitor instance or None.
        """
        if self._resilience_pipeline is not None:
            return self._resilience_pipeline.health_monitor
        return None

    @property
    def circuit_breakers(self):
        """
            The CircuitBreakerRegistry from the ResiliencePipeline.

            :returns: The CircuitBreakerRegistry instance or None.
        """
        if self._resilience_pipeline is not None:
            return self._resilience_pipeline.circuit_breaker_registry
        return None

    @property
    def dead_letter_queue(self):
        """
            The DeadLetterQueue from the ResiliencePipeline.

            :returns: The DeadLetterQueue instance or None.
        """
        if self._resilience_pipeline is not None:
            return self._resilience_pipeline.dead_letter_queue
        return None

    @property
    def observability(self) -> ObservabilityPipeline:
        """
            The ObservabilityPipeline instance for this agent.

            :returns: The ObservabilityPipeline instance.
        """
        return self._observability_pipeline

    @property
    def debug_session(self) -> Optional[DebugSession]:
        """
            The DebugSession instance for this agent, or None when
            debug mode is not enabled.

            :returns: A DebugSession instance or None.
        """
        return self._debug_session

    @property
    def tools(self) -> ToolRegistry:
        """
            Returns the Agent's ToolRegistry instance.

            :returns: The ToolRegistry for this agent.
        """
        return self._tool_registry

    @property
    def llm_providers(self) -> LLMProviderRegistry:
        """
            Returns the Agent's LLMProviderRegistry instance.

            :returns: The LLMProviderRegistry for this agent.
        """
        return self._llm_provider_registry

    @property
    def cost_tracker(self) -> CostTracker:
        """
            Returns the Agent's CostTracker instance.

            :returns: The CostTracker for this agent.
        """
        return self._cost_tracker

    @property
    def memory(self) -> Optional[MemoryStore]:
        """
            The Agent's primary MemoryStore instance.

            :returns: The primary MemoryStore or None.
        """
        return self._memory_store

    @property
    def memory_stores(self) -> MemoryStoreRegistry:
        """
            The Agent's MemoryStoreRegistry instance.

            :returns: The MemoryStoreRegistry for this agent.
        """
        return self._memory_store_registry

    @property
    def context_window(self) -> Optional[ContextWindow]:
        """
            The Agent's ContextWindow instance.

            :returns: The ContextWindow or None.
        """
        return self._context_window

    @property
    def workflows(self) -> WorkflowRegistry:
        """
            Returns the Agent's WorkflowRegistry instance.

            :returns: The WorkflowRegistry for this agent.
        """
        return self._workflow_registry

    @property
    def approval_gate(self) -> ApprovalGate:
        """
            Returns the Agent's ApprovalGate instance.

            :returns: The ApprovalGate for this agent.
        """
        return self._approval_gate

    @property
    def transports(self) -> TransportRegistry:
        """
            Returns the Agent's TransportRegistry instance.

            :returns: The TransportRegistry for this agent.
        """
        return self._transport_registry

    @property
    def message_router(self) -> MessageRouter:
        """
            Returns the Agent's MessageRouter instance.

            :returns: The MessageRouter for this agent.
        """
        return self._message_router

    @property
    def pubsub(self) -> PubSubBroker:
        """
            Returns the Agent's PubSubBroker instance.

            :returns: The PubSubBroker for this agent.
        """
        return self._pubsub_broker

    @property
    def address_resolver(self) -> AddressResolver:
        """
            Returns the Agent's AddressResolver instance.

            :returns: The AddressResolver for this agent.
        """
        return self._address_resolver

    @property
    def platform_runtime(self):
        """
            Returns the PlatformRuntime instance, or None when not configured.

            :returns: The PlatformRuntime or None.
        """
        rtnval = self._platform_runtime
        return rtnval

    # -----------------------------------------------------------------------
    # Abstract lifecycle methods
    # -----------------------------------------------------------------------

    @abc.abstractmethod
    def initialize(self) -> None:
        """
            Initializes the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    def start(self) -> None:
        """
            Starts the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    def pause(self) -> None:
        """
            Pauses the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    def resume(self) -> None:
        """
            Resumes the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    def stop(self) -> None:
        """
            Stops the agent. Subclasses must implement this method.
        """

    @abc.abstractmethod
    def reset(self) -> None:
        """
            Resets the agent. Subclasses must implement this method.
        """

    # -----------------------------------------------------------------------
    # Configuration and extensibility convenience methods
    # -----------------------------------------------------------------------

    def get_config(self, field_path: str, default=None):
        """
            Returns the resolved configuration value at the given field path,
            delegating to the ConfigurationManager.

            :param field_path: Dot-separated path string.
            :param default: Value to return when the field path is not found.

            :returns: The resolved configuration value or default.
        """
        value = self._configuration_manager.get(field_path, default=default)
        return value

    def is_feature_enabled(self, flag_name: str) -> bool:
        """
            Returns whether the named feature flag is enabled, delegating
            to the FeatureFlagRegistry.

            :param flag_name: The flag name to evaluate.

            :returns: True if the flag is enabled.
        """
        result = self._feature_flag_registry.is_enabled(flag_name)
        return result

    # -----------------------------------------------------------------------
    # Configuration lifecycle helpers for subclasses
    # -----------------------------------------------------------------------

    def _initialize_configuration(self) -> None:
        """
            Loads configuration from the AgentConfiguration into the
            ConfigurationManager and validates against the schema if defined.

            Subclasses should call this method during their initialize()
            implementation to set up configuration.
        """
        agent_config = self._configuration
        config_dict = agent_config.as_dict()

        self._configuration_manager.load_defaults(config_dict)

        self._logger.info(
            "Configuration initialized for agent '%s'",
            self._identity.identifier
        )
        return

    def _initialize_plugins(self) -> None:
        """
            Discovers and loads plugins through the PluginManager.

            Subclasses should call this method during their initialize()
            implementation to set up plugins.
        """
        self._plugin_manager.discover()

        self._logger.info(
            "Plugins initialized for agent '%s'",
            self._identity.identifier
        )
        return

    def _initialize_feature_flags(self) -> None:
        """
            Loads feature flag definitions from the configuration.

            Subclasses should call this method during their initialize()
            implementation to set up feature flags.
        """
        self._logger.info(
            "Feature flags initialized for agent '%s'",
            self._identity.identifier
        )
        return

    def _start_hot_reload(self, policy: HotReloadPolicy) -> None:
        """
            Starts the HotReloadMonitor with the given policy.

            Subclasses should call this method during their start()
            implementation when a HotReloadPolicy is configured.

            :param policy: The HotReloadPolicy defining monitoring behavior.
        """
        self._hot_reload_policy = policy
        self._hot_reload_monitor = HotReloadMonitor(
            configuration_manager=self._configuration_manager,
            policy=policy
        )
        self._hot_reload_monitor.start()

        self._logger.info(
            "Hot-reload monitor started for agent '%s' with polling interval %.1f",
            self._identity.identifier,
            policy.polling_interval
        )
        return

    def _stop_configuration(self) -> None:
        """
            Stops the HotReloadMonitor if running, deactivates and unloads
            all plugins, and clears runtime configuration overrides.

            Subclasses should call this method during their stop()
            implementation to clean up configuration resources.
        """
        if self._hot_reload_monitor is not None:
            self._hot_reload_monitor.stop()
            self._hot_reload_monitor = None

        plugin_list = self._plugin_manager.list_all()
        for plugin_desc in plugin_list:
            self._plugin_manager.unload_plugin(plugin_desc.name)

        self._logger.info(
            "Configuration stopped for agent '%s'",
            self._identity.identifier
        )
        return

    # -----------------------------------------------------------------------
    # Observability lifecycle helpers
    # -----------------------------------------------------------------------

    def _initialize_observability(self) -> None:
        """
            Initializes the ObservabilityPipeline and optionally a
            DebugSession based on the agent's configuration.

            Reads the "observability" key from the AgentConfiguration's
            settings dictionary. If not present, uses default values:
            log_level="info", log_format="human_readable", tracing/metrics/
            recording/debug disabled, sampling_rate=1.0.

            When debug_mode_enabled is True in the observability config,
            a DebugSession is created for this agent.

            After constructing the pipeline, attempts to discover and
            register exporter plugins from extension points.
        """
        settings = self._configuration.settings
        observability_data = settings.get("observability", None)

        if observability_data is not None:
            obs_config = ObservabilityConfiguration.from_dict(observability_data)
        else:
            obs_config = ObservabilityConfiguration(
                log_level="info",
                log_format="human_readable",
                tracing_enabled=False,
                metrics_enabled=False,
                recording_enabled=False,
                debug_mode_enabled=False,
                sampling_rate=1.0
            )

        self._observability_pipeline = ObservabilityPipeline(
            configuration=obs_config,
            agent_id=self._identity.identifier
        )

        if obs_config.debug_mode_enabled:
            self._debug_session = DebugSession(agent=self)

        self._discover_exporter_plugins()

        return

    def _discover_exporter_plugins(self) -> None:
        """
            Discovers and registers exporter plugins from extension points.

            Queries the following extension points:
            - "ccai.agentkit.log_exporters"
            - "ccai.agentkit.trace_exporters"
            - "ccai.agentkit.metrics_exporters"

            Logs plugin loading failures at WARNING and continues.
            Logs conflicts at WARNING and skips the conflicting plugin.
        """
        if self._observability_pipeline is None:
            return

        extension_point_map = {
            "ccai.agentkit.log_exporters": "register_log_exporter",
            "ccai.agentkit.trace_exporters": "register_trace_exporter",
            "ccai.agentkit.metrics_exporters": "register_metrics_exporter",
        }

        for ext_point_name, register_method_name in extension_point_map.items():
            try:
                extensions = self._extensions
                if extensions is None:
                    continue

                exporters = []
                for ext in extensions:
                    ext_point = getattr(ext, "extension_point", None)
                    if ext_point == ext_point_name:
                        exporters.append(ext)

                register_method = getattr(self._observability_pipeline, register_method_name)

                for exporter in exporters:
                    try:
                        register_method(exporter)
                    except Exception as plugin_err:
                        self._logger.warning(
                            "Failed to register exporter plugin from extension point '%s': %s",
                            ext_point_name,
                            str(plugin_err)
                        )

            except Exception as discovery_err:
                self._logger.warning(
                    "Failed to discover exporter plugins from extension point '%s': %s",
                    ext_point_name,
                    str(discovery_err)
                )

        return

    # -----------------------------------------------------------------------
    # Resilience lifecycle helpers for subclasses
    # -----------------------------------------------------------------------

    def _initialize_resilience(self, resilience_config: ResilienceConfiguration = None) -> None:
        """
            Initializes the ResiliencePipeline from the given configuration.

            Subclasses should call this method during their initialize()
            implementation to set up resilience.

            :param resilience_config: Optional ResilienceConfiguration. If None,
                a default configuration is used.
        """
        if resilience_config is None:
            resilience_config = ResilienceConfiguration()

        self._resilience_pipeline = ResiliencePipeline(
            resilience_config, self._identity.identifier
        )

        self._discover_resilience_plugins()

        self._logger.info(
            "Resilience initialized for agent '%s'",
            self._identity.identifier
        )
        return

    def _discover_resilience_plugins(self) -> None:
        """
            Discovers and registers ResiliencePlugin instances from the
            "ccai.agentkit.resilience" extension point.

            Queries the agent's extensions list for entries with
            extension_point == "ccai.agentkit.resilience" and registers
            discovered HealthCheck, DegradationStrategy, SelfHealingAction,
            and DeadLetterStore instances with the appropriate pipeline
            components.

            Logs plugin loading failures at WARNING and continues.
            Logs name conflicts at WARNING and skips the conflicting component.
        """
        if self._resilience_pipeline is None:
            return

        extensions = self._extensions
        if extensions is None:
            return

        from ccai.agentkit.healthcheck import HealthCheck

        for ext in extensions:
            ext_point = getattr(ext, "extension_point", None)
            if ext_point != "ccai.agentkit.resilience":
                continue

            try:
                if isinstance(ext, HealthCheck):
                    monitor = self._resilience_pipeline.health_monitor
                    if monitor is not None:
                        registry = monitor._health_check_registry
                        check_name = ext.name
                        if registry.has_health_check(check_name):
                            self._logger.warning(
                                "Resilience plugin name conflict: health check '%s' "
                                "is already registered in agent '%s'. Skipping.",
                                check_name,
                                self._identity.identifier,
                            )
                            continue
                        registry.register(ext)

            except Exception as plugin_err:
                try:
                    plugin_name = getattr(ext, "name", "unknown")
                except Exception:
                    plugin_name = "unknown"
                self._logger.warning(
                    "Failed to load resilience plugin '%s' for agent '%s': %s",
                    plugin_name,
                    self._identity.identifier,
                    str(plugin_err),
                )

        return

    def _start_resilience(self) -> None:
        """
            Starts the HealthMonitor if resilience is initialized and
            health monitoring is enabled.

            Subclasses should call this method during their start()
            implementation.
        """
        if self._resilience_pipeline is not None:
            monitor = self._resilience_pipeline.health_monitor
            if monitor is not None:
                monitor.start()
                self._logger.info(
                    "Health monitor started for agent '%s'",
                    self._identity.identifier
                )
        return

    def _stop_resilience(self) -> None:
        """
            Stops the HealthMonitor if running.

            Subclasses should call this method during their stop()
            implementation.
        """
        if self._resilience_pipeline is not None:
            monitor = self._resilience_pipeline.health_monitor
            if monitor is not None and monitor.is_active:
                monitor.stop()
                self._logger.info(
                    "Health monitor stopped for agent '%s'",
                    self._identity.identifier
                )
        return

    def register_tool(self, tool: Tool) -> None:
        """
            Registers a Tool with this Agent's ToolRegistry.

            :param tool: The Tool instance to register.
        """
        self._tool_registry.register(tool=tool)
        return

    def execute_tool(self, tool_name: str, inputs: dict) -> ToolResult:
        """
            Looks up and executes a tool by name.

            :param tool_name: Name of the tool to execute.
            :param inputs: Input dictionary.

            :returns: A ToolResult.
            :raises: SemanticError if tool not found.
        """
        tool = self._tool_registry.lookup(tool_name=tool_name)

        if tool is None:
            err_msg_lines = [
                "Tool '{}' not found in agent '{}'.".format(
                    tool_name, self._identity.identifier
                ),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        rtnval = self._tool_executor.execute(
            tool=tool,
            inputs=inputs,
            agent_identifier=self._identity.identifier,
        )
        return rtnval

    def execute_chain(self, chain: ToolChain, inputs: dict) -> ToolChainResult:
        """
            Executes a ToolChain through the ToolChainExecutor.

            :param chain: The ToolChain to execute.
            :param inputs: Initial input dictionary.

            :returns: A ToolChainResult.
        """
        rtnval = self._tool_chain_executor.execute(
            chain=chain,
            initial_inputs=inputs,
            agent_identifier=self._identity.identifier,
        )
        return rtnval

    def _initialize_tools(self) -> None:
        """
            Discovers and registers ToolPlugin instances from the
            "ccai.agentkit.tools" extension point.

            Subclasses should call this method during their initialize()
            implementation to set up tools.
        """
        try:
            from ccai.extension import ExtensionPoint
            extension_point = ExtensionPoint("ccai.agentkit.tools")
            discovered_tools = extension_point.query()

            for tool_entry in discovered_tools:
                try:
                    tool_instance = tool_entry
                    tool_name = tool_instance.name
                    has_conflict = self._tool_registry.has_tool(tool_name=tool_name)

                    if has_conflict is True:
                        self._logger.warning(
                            "Tool plugin name conflict: tool '%s' is already registered "
                            "in agent '%s'. Skipping plugin tool.",
                            tool_name,
                            self._identity.identifier,
                        )
                        continue

                    self._tool_registry.register(tool=tool_instance)

                except Exception as plugin_err:
                    self._logger.warning(
                        "Failed to load tool plugin for agent '%s': %s",
                        self._identity.identifier,
                        str(plugin_err),
                    )

        except ImportError:
            self._logger.info(
                "codecraftai-extension not available; skipping tool plugin discovery "
                "for agent '%s'",
                self._identity.identifier,
            )
        except Exception as discovery_err:
            self._logger.warning(
                "Tool plugin discovery failed for agent '%s': %s",
                self._identity.identifier,
                str(discovery_err),
            )

        self._logger.info(
            "Tools initialized for agent '%s'",
            self._identity.identifier,
        )
        return

    def _stop_tools(self) -> None:
        """
            Clears the Agent's ToolRegistry.

            Subclasses should call this method during their stop()
            implementation to clean up tools.
        """
        self._tool_registry.clear()
        self._logger.info(
            "Tools cleared for agent '%s'",
            self._identity.identifier,
        )
        return

    # -----------------------------------------------------------------------
    # Messaging lifecycle helpers for subclasses
    # -----------------------------------------------------------------------

    def _initialize_messaging(self, messaging_configuration=None) -> None:
        """
            Initializes the messaging subsystem for this Agent.

            Stores the messaging configuration, configures the
            RequestResponseHandler with the default request timeout,
            registers a default JsonMessageSerializer when no
            MessagingConfiguration is provided, and discovers Transport
            and MessageSerializer plugins from codecraftai-extension
            ExtensionPoint entries.

            Subclasses should call this method during their initialize()
            implementation to set up messaging.

            :param messaging_configuration: Optional MessagingConfiguration.
                If None, defaults to a JsonMessageSerializer and no
                registered transports.
        """
        self._messaging_configuration = messaging_configuration

        if messaging_configuration is not None:
            default_timeout = messaging_configuration.default_request_timeout
            self._request_response_handler = RequestResponseHandler(
                default_timeout=default_timeout
            )

        # Register default JsonMessageSerializer when no configuration is provided
        if messaging_configuration is None:
            default_serializer = JsonMessageSerializer()
            default_format_name = default_serializer.format_name
            has_default = self._message_serializer_registry.has_serializer(default_format_name)

            if has_default is not True:
                self._message_serializer_registry.register(default_serializer)

        # Discover and register Transport plugins
        try:
            from ccai.extension import ExtensionPoint
            transport_extension_point = ExtensionPoint("ccai.agentkit.transports")
            discovered_transports = transport_extension_point.query()

            for transport_entry in discovered_transports:
                try:
                    transport_instance = transport_entry
                    transport_name = transport_instance.name
                    has_conflict = self._transport_registry.has_transport(transport_name)

                    if has_conflict is True:
                        self._logger.warning(
                            "Transport plugin name conflict: transport '%s' is already "
                            "registered in agent '%s'. Skipping plugin transport.",
                            transport_name,
                            self._identity.identifier,
                        )
                        continue

                    self._transport_registry.register(transport=transport_instance)

                except Exception as plugin_err:
                    self._logger.warning(
                        "Failed to load transport plugin for agent '%s': %s",
                        self._identity.identifier,
                        str(plugin_err),
                    )

        except ImportError:
            self._logger.info(
                "codecraftai-extension not available; skipping transport plugin "
                "discovery for agent '%s'",
                self._identity.identifier,
            )
        except Exception as discovery_err:
            self._logger.warning(
                "Transport plugin discovery failed for agent '%s': %s",
                self._identity.identifier,
                str(discovery_err),
            )

        # Discover and register MessageSerializer plugins
        try:
            from ccai.extension import ExtensionPoint
            serializer_extension_point = ExtensionPoint("ccai.agentkit.message_serializers")
            discovered_serializers = serializer_extension_point.query()

            for serializer_entry in discovered_serializers:
                try:
                    serializer_instance = serializer_entry
                    format_name = serializer_instance.format_name
                    has_conflict = self._message_serializer_registry.has_serializer(format_name)

                    if has_conflict is True:
                        self._logger.warning(
                            "MessageSerializer plugin name conflict: format '%s' is "
                            "already registered in agent '%s'. Skipping plugin serializer.",
                            format_name,
                            self._identity.identifier,
                        )
                        continue

                    self._message_serializer_registry.register(serializer_instance)

                except Exception as plugin_err:
                    self._logger.warning(
                        "Failed to load message serializer plugin for agent '%s': %s",
                        self._identity.identifier,
                        str(plugin_err),
                    )

        except ImportError:
            self._logger.info(
                "codecraftai-extension not available; skipping message serializer plugin "
                "discovery for agent '%s'",
                self._identity.identifier,
            )
        except Exception as discovery_err:
            self._logger.warning(
                "Message serializer plugin discovery failed for agent '%s': %s",
                self._identity.identifier,
                str(discovery_err),
            )

        self._logger.info(
            "Messaging initialized for agent '%s'",
            self._identity.identifier,
        )
        return

    def _stop_messaging(self) -> None:
        """
            Disconnects all connected transports, clears the
            TransportRegistry, removes all PubSubBroker subscriptions,
            and resets the messaging configuration.

            Subclasses should call this method during their stop()
            implementation to clean up messaging resources.
        """
        # Disconnect all connected transports
        all_transports = self._transport_registry.list_all()

        for transport in all_transports:
            is_connected = transport.is_connected()

            if is_connected is True:
                try:
                    transport.disconnect()
                except Exception as disconnect_err:
                    self._logger.warning(
                        "Failed to disconnect transport '%s' for agent '%s': %s",
                        transport.name,
                        self._identity.identifier,
                        str(disconnect_err),
                    )

        # Clear the TransportRegistry
        registered_transports = self._transport_registry.list_all()

        for transport in registered_transports:
            self._transport_registry.deregister(transport.name)

        # Remove all PubSubBroker subscriptions
        all_subscriptions = list(self._pubsub_broker._subscriptions)

        for subscription in all_subscriptions:
            self._pubsub_broker.unsubscribe(subscription)

        # Reset messaging configuration
        self._messaging_configuration = None

        self._logger.info(
            "Messaging stopped for agent '%s'",
            self._identity.identifier,
        )
        return

    # -----------------------------------------------------------------------
    # Platform runtime convenience methods
    # -----------------------------------------------------------------------

    def get_compute_service(self):
        """
            Convenience method delegating to the PlatformRuntime.

            :returns: A ComputeService instance.
            :raises: SemanticError
        """
        if self._platform_runtime is None:
            err_msg = "PlatformRuntime must be configured before accessing platform services."
            raise SemanticError(err_msg)
        rtnval = self._platform_runtime.get_compute_service()
        return rtnval

    def get_storage_service(self):
        """
            Convenience method delegating to the PlatformRuntime.

            :returns: A StorageService instance.
            :raises: SemanticError
        """
        if self._platform_runtime is None:
            err_msg = "PlatformRuntime must be configured before accessing platform services."
            raise SemanticError(err_msg)
        rtnval = self._platform_runtime.get_storage_service()
        return rtnval

    def get_messaging_service(self):
        """
            Convenience method delegating to the PlatformRuntime.

            :returns: A MessagingService instance.
            :raises: SemanticError
        """
        if self._platform_runtime is None:
            err_msg = "PlatformRuntime must be configured before accessing platform services."
            raise SemanticError(err_msg)
        rtnval = self._platform_runtime.get_messaging_service()
        return rtnval

    def _stop_platform(self) -> None:
        """
            Logs the platform runtime status at INFO level when the Agent
            transitions to the STOPPED state.

            Subclasses should call this method during their stop()
            implementation to log platform runtime status.
        """
        if self._platform_runtime is not None:
            platform_type = self._platform_runtime.platform_type.to_string()
            try:
                health_results = self._platform_runtime.health_check()
            except Exception as health_err:
                health_results = {"error": str(health_err)}

            self._logger.info(
                "Platform runtime status for agent '%s': platform=%s, health=%s",
                self._identity.identifier,
                platform_type,
                health_results,
            )
        return

    # -----------------------------------------------------------------------
    # LLM provider lifecycle helpers for subclasses
    # -----------------------------------------------------------------------

    def _initialize_llm_providers(self) -> None:
        """
            Discovers and registers LLMProviderPlugin instances from the
            "ccai.agentkit.llm_providers" extension point.

            Subclasses should call this method during their initialize()
            implementation to set up LLM providers.

            Logs WARNING and continues on plugin load failure.
            Logs WARNING and skips on name-model conflict.
        """
        try:
            from ccai.extension import ExtensionPoint
            extension_point = ExtensionPoint("ccai.agentkit.llm_providers")
            discovered_providers = extension_point.query()

            for provider_entry in discovered_providers:
                try:
                    provider_instance = provider_entry
                    provider_name = provider_instance.provider_name
                    model_name = provider_instance.model_name
                    has_conflict = self._llm_provider_registry.has_provider(
                        provider_name, model_name
                    )

                    if has_conflict is True:
                        self._logger.warning(
                            "LLM provider plugin name conflict: provider '%s' model '%s' "
                            "is already registered in agent '%s'. Skipping plugin provider.",
                            provider_name,
                            model_name,
                            self._identity.identifier,
                        )
                        continue

                    self._llm_provider_registry.register(provider_instance)

                except Exception as plugin_err:
                    self._logger.warning(
                        "Failed to load LLM provider plugin for agent '%s': %s",
                        self._identity.identifier,
                        str(plugin_err),
                    )

        except ImportError:
            self._logger.info(
                "codecraftai-extension not available; skipping LLM provider plugin "
                "discovery for agent '%s'",
                self._identity.identifier,
            )
        except Exception as discovery_err:
            self._logger.warning(
                "LLM provider plugin discovery failed for agent '%s': %s",
                self._identity.identifier,
                str(discovery_err),
            )

        self._logger.info(
            "LLM providers initialized for agent '%s'",
            self._identity.identifier,
        )
        return

    def _stop_llm_providers(self) -> None:
        """
            Clears the Agent's LLMProviderRegistry.

            Subclasses should call this method during their stop()
            implementation to clean up LLM providers.
        """
        self._llm_provider_registry.clear()
        self._logger.info(
            "LLM providers cleared for agent '%s'",
            self._identity.identifier,
        )
        return

    # -----------------------------------------------------------------------
    # Memory lifecycle helpers for subclasses
    # -----------------------------------------------------------------------

    def _initialize_memory(self, memory_configuration: MemoryConfiguration = None) -> None:
        """
            Initializes the memory system from the given MemoryConfiguration.

            Constructs the primary MemoryStore and ContextWindow based on
            the configuration. When no configuration is provided, defaults
            to an InMemoryStore with MemoryScope.AGENT and no expiration.

            Discovers and registers MemoryBackendPlugin instances from the
            "ccai.agentkit.memory_backends" extension point.

            Subclasses should call this method during their initialize()
            implementation to set up memory.

            :param memory_configuration: Optional MemoryConfiguration. If None,
                defaults to InMemoryStore with AGENT scope.
        """
        self._memory_configuration = memory_configuration

        if memory_configuration is not None:
            backend_type = memory_configuration.backend_type
            expiration_policy = memory_configuration.expiration_policy

            if backend_type == "inmemory":
                self._memory_store = InMemoryStore(
                    store_name="primary",
                    expiration_policy=expiration_policy,
                )
            elif backend_type == "file":
                from ccai.agentkit.filememorystore import FileMemoryStore
                directory_path = memory_configuration.connection_params.get("directory_path", ".memory")
                self._memory_store = FileMemoryStore(
                    store_name="primary",
                    directory_path=directory_path,
                    expiration_policy=expiration_policy,
                )
            else:
                self._memory_store = InMemoryStore(
                    store_name="primary",
                    expiration_policy=expiration_policy,
                )

            context_settings = memory_configuration.connection_params.get("context_window", {})
            max_tokens = context_settings.get("max_tokens", 4096)
            strategy_str = context_settings.get("strategy", "FIFO")
            strategy = ContextWindowStrategy.from_string(strategy_str)

            self._context_window = ContextWindow(
                max_tokens=max_tokens,
                strategy=strategy,
                token_counter=lambda text: len(text.split()),
            )
        else:
            self._memory_store = InMemoryStore(store_name="primary")

            self._context_window = ContextWindow(
                max_tokens=4096,
                strategy=ContextWindowStrategy.FIFO,
                token_counter=lambda text: len(text.split()),
            )

        self._memory_store_registry = MemoryStoreRegistry()
        self._memory_store_registry.register(store=self._memory_store)

        self._discover_memory_backend_plugins()

        self._logger.info(
            "Memory initialized for agent '%s' with store '%s'",
            self._identity.identifier,
            self._memory_store.store_name,
        )
        return

    def _discover_memory_backend_plugins(self) -> None:
        """
            Discovers and registers MemoryBackendPlugin instances from the
            "ccai.agentkit.memory_backends" extension point.

            Logs WARNING on plugin load failure and continues.
            Logs WARNING on store name conflict and skips.
        """
        try:
            from ccai.extension import ExtensionPoint
            extension_point = ExtensionPoint("ccai.agentkit.memory_backends")
            discovered_stores = extension_point.query()

            for store_entry in discovered_stores:
                try:
                    store_instance = store_entry
                    store_name = store_instance.store_name
                    has_conflict = self._memory_store_registry.has_store(name=store_name)

                    if has_conflict is True:
                        self._logger.warning(
                            "Memory backend plugin name conflict: store '%s' is already "
                            "registered in agent '%s'. Skipping plugin store.",
                            store_name,
                            self._identity.identifier,
                        )
                        continue

                    self._memory_store_registry.register(store=store_instance)

                except Exception as plugin_err:
                    self._logger.warning(
                        "Failed to load memory backend plugin for agent '%s': %s",
                        self._identity.identifier,
                        str(plugin_err),
                    )

        except ImportError:
            self._logger.info(
                "codecraftai-extension not available; skipping memory backend plugin "
                "discovery for agent '%s'",
                self._identity.identifier,
            )
        except Exception as discovery_err:
            self._logger.warning(
                "Memory backend plugin discovery failed for agent '%s': %s",
                self._identity.identifier,
                str(discovery_err),
            )

        return

    def _stop_memory(self) -> None:
        """
            Clears the Agent's MemoryStoreRegistry and resets memory references.

            Subclasses should call this method during their stop()
            implementation to clean up memory resources.
        """
        self._memory_store_registry.clear()
        self._memory_store = None
        self._context_window = None
        self._memory_configuration = None

        self._logger.info(
            "Memory cleared for agent '%s'",
            self._identity.identifier,
        )
        return

    # -----------------------------------------------------------------------
    # Workflow lifecycle methods
    # -----------------------------------------------------------------------

    def _initialize_workflows(self) -> None:
        """
            Initializes the workflow subsystem for this Agent.

            Constructs the WorkflowExecutor and CheckpointManager from the
            WorkflowConfiguration. If no WorkflowConfiguration is provided,
            defaults to a WorkflowConfiguration with default values.

            Queries the "ccai.agentkit.workflow_steps" ExtensionPoint
            and registers all discovered WorkflowStep types.

            Subclasses should call this method during their initialize()
            implementation to set up workflow capabilities.
        """
        if self._workflow_configuration is None:
            self._workflow_configuration = WorkflowConfiguration()

        if self._memory_store is not None:
            self._checkpoint_manager = CheckpointManager(
                memory_store=self._memory_store
            )

        self._workflow_executor = WorkflowExecutor(
            configuration=self._workflow_configuration,
            checkpoint_manager=self._checkpoint_manager
        )

        self._logger.info(
            "Workflow subsystem initialized for agent '%s'.",
            self._identity.identifier,
        )

        # Discover workflow step plugins via ExtensionPoint
        try:
            from ccai.extension import ExtensionPoint
            extension_point = ExtensionPoint("ccai.agentkit.workflow_steps")
            discovered_steps = extension_point.query()

            for step_entry in discovered_steps:
                try:
                    step_type_name = step_entry.step_type if hasattr(step_entry, "step_type") else str(step_entry)

                    self._logger.info(
                        "Discovered workflow step plugin '%s' for agent '%s'.",
                        step_type_name,
                        self._identity.identifier,
                    )

                except Exception as plugin_err:
                    self._logger.warning(
                        "Failed to load workflow step plugin for agent '%s': %s",
                        self._identity.identifier,
                        str(plugin_err),
                    )

        except ImportError:
            self._logger.info(
                "codecraftai-extension not available; skipping workflow step plugin "
                "discovery for agent '%s'.",
                self._identity.identifier,
            )
        except Exception as discovery_err:
            self._logger.warning(
                "Workflow step plugin discovery failed for agent '%s': %s",
                self._identity.identifier,
                str(discovery_err),
            )

        return

    def _stop_workflows(self) -> None:
        """
            Clears the Agent's WorkflowRegistry and cancels all pending
            ApprovalRequests.

            Subclasses should call this method during their stop()
            implementation to clean up workflow resources.
        """
        self._workflow_registry = WorkflowRegistry()
        self._workflow_executor = None
        self._checkpoint_manager = None
        self._workflow_configuration = None

        # Cancel all pending approval requests
        pending_requests = self._approval_gate.list_pending()
        for request in pending_requests:
            try:
                self._approval_gate.reject(
                    request.identifier,
                    reason="Agent stopped."
                )
            except Exception:
                pass

        self._logger.info(
            "Workflow subsystem stopped for agent '%s'.",
            self._identity.identifier,
        )
        return

    # -----------------------------------------------------------------------
    # Memory convenience methods
    # -----------------------------------------------------------------------

    def register_memory_store(self, store: MemoryStore) -> None:
        """
            Registers a MemoryStore with this Agent's MemoryStoreRegistry.

            :param store: The MemoryStore instance to register.
        """
        self._memory_store_registry.register(store=store)
        return

    def store_memory(self, content: str, metadata: dict = None,
                     tags: list = None, scope: MemoryScope = None) -> MemoryEntry:
        """
            Creates a MemoryEntry and stores it in the Agent's primary MemoryStore.

            :param content: The content string for the memory entry.
            :param metadata: Optional metadata dictionary.
            :param tags: Optional list of tag strings.
            :param scope: Optional MemoryScope. Defaults to AGENT.

            :returns: The stored MemoryEntry.
            :raises: SemanticError if no primary MemoryStore is configured.
        """
        if self._memory_store is None:
            errmsg = "No primary MemoryStore is configured for agent '{}'.".format(
                self._identity.identifier
            )
            raise SemanticError(errmsg)

        if scope is None:
            scope = MemoryScope.AGENT

        entry = MemoryEntry(
            content=content,
            scope=scope,
            metadata=metadata,
            tags=tags,
        )

        stored_entry = self._memory_store.store(entry=entry)
        rtnval = stored_entry
        return rtnval

    def search_memory(self, query: MemoryQuery) -> MemoryQueryResult:
        """
            Executes a MemoryQuery against the Agent's primary MemoryStore.

            :param query: The MemoryQuery with filter criteria.

            :returns: A MemoryQueryResult with matching entries.
            :raises: SemanticError if no primary MemoryStore is configured.
        """
        if self._memory_store is None:
            errmsg = "No primary MemoryStore is configured for agent '{}'.".format(
                self._identity.identifier
            )
            raise SemanticError(errmsg)

        rtnval = self._memory_store.search(query=query)
        return rtnval

    def build_context(self, conversation: LLMConversation,
                      memory_query: MemoryQuery = None) -> LLMConversation:
        """
            Builds a trimmed LLMConversation using the Agent's ContextWindow.

            If a memory_query is provided, searches the primary MemoryStore
            and passes the matching entries to the ContextWindow for inclusion.

            :param conversation: The input LLMConversation.
            :param memory_query: Optional MemoryQuery for retrieving relevant memory.

            :returns: A trimmed LLMConversation that fits within the token limit.
            :raises: SemanticError if no ContextWindow is configured.
        """
        if self._context_window is None:
            errmsg = "No ContextWindow is configured for agent '{}'.".format(
                self._identity.identifier
            )
            raise SemanticError(errmsg)

        memory_entries = None
        if memory_query is not None and self._memory_store is not None:
            query_result = self._memory_store.search(query=memory_query)
            memory_entries = query_result.entries

        rtnval = self._context_window.build(
            conversation=conversation,
            memory_entries=memory_entries,
        )
        return rtnval

    # -----------------------------------------------------------------------
    # Workflow methods
    # -----------------------------------------------------------------------

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """
            Registers a WorkflowDefinition with this Agent's WorkflowRegistry.

            :param workflow: The WorkflowDefinition instance to register.
        """
        self._workflow_registry.register(workflow)
        return

    def execute_workflow(self, name: str, inputs: dict,
                         version: str = None) -> WorkflowResult:
        """
            Looks up and executes a workflow by name and optional version.

            Retrieves the WorkflowDefinition from the Agent's WorkflowRegistry
            using the provided name and optional version, then executes the
            workflow through the WorkflowExecutor.

            :param name: The workflow name to look up.
            :param inputs: The initial input dictionary for the workflow.
            :param version: Optional version string. When None, the latest version is used.

            :returns: A WorkflowResult with the execution outcome.
            :raises: SemanticError if the workflow is not found in the registry.
        """
        workflow = self._workflow_registry.lookup(name, version)
        if workflow is None:
            errmsg = "Workflow '{}' not found in the registry.".format(name)
            raise SemanticError(errmsg)

        if self._workflow_executor is None:
            self._workflow_executor = WorkflowExecutor(
                configuration=self._workflow_configuration,
                checkpoint_manager=self._checkpoint_manager
            )

        result = self._workflow_executor.execute(workflow, inputs, agent=self)
        return result

    def resume_workflow(self, execution_id: str,
                        workflow_name: str = None) -> WorkflowResult:
        """
            Resumes a workflow from the last checkpoint.

            Loads the most recent checkpoint for the given execution identifier
            and continues execution from the step following the last completed step.

            :param execution_id: The workflow execution identifier.
            :param workflow_name: Optional workflow name to look up the WorkflowDefinition.

            :returns: A WorkflowResult with the execution outcome.
            :raises: SemanticError if the workflow name is provided but not found.
        """
        if self._workflow_executor is None:
            self._workflow_executor = WorkflowExecutor(
                configuration=self._workflow_configuration,
                checkpoint_manager=self._checkpoint_manager
            )

        workflow = None
        if workflow_name is not None:
            workflow = self._workflow_registry.lookup(workflow_name)
            if workflow is None:
                errmsg = "Workflow '{}' not found in the registry.".format(workflow_name)
                raise SemanticError(errmsg)

        result = self._workflow_executor.resume(execution_id, workflow, agent=self)
        return result

    # -----------------------------------------------------------------------
    # Messaging methods
    # -----------------------------------------------------------------------

    def register_transport(self, transport: Transport) -> None:
        """
            Registers a Transport with this Agent's TransportRegistry.

            :param transport: The Transport instance to register.
        """
        self._transport_registry.register(transport=transport)
        return

    def send_message(self, recipient_id: str, payload: object,
                     transport_name: str = None,
                     serialization_format: str = None,
                     pattern: MessagePattern = MessagePattern.FIRE_AND_FORGET,
                     headers: dict = None) -> MessageEnvelope:
        """
            Constructs and sends a Message to the specified recipient.

            Resolves the default transport name and serialization format
            from the MessagingConfiguration when not provided. Looks up
            the transport from the TransportRegistry, resolves the
            recipient address via the AddressResolver, constructs a
            Message, and sends it through the transport.

            :param recipient_id: The recipient agent identifier.
            :param payload: The message payload.
            :param transport_name: Optional transport name. Defaults to
                the MessagingConfiguration default.
            :param serialization_format: Optional serialization format
                name. Defaults to the MessagingConfiguration default.
            :param pattern: The MessagePattern. Defaults to
                FIRE_AND_FORGET.
            :param headers: Optional headers dictionary.

            :returns: A MessageEnvelope with delivery metadata.

            :raises SemanticError: If the requested transport is not
                found in the TransportRegistry.
        """
        effective_transport_name = transport_name
        if effective_transport_name is None and self._messaging_configuration is not None:
            effective_transport_name = self._messaging_configuration.default_transport

        effective_serialization_format = serialization_format
        if effective_serialization_format is None and self._messaging_configuration is not None:
            effective_serialization_format = self._messaging_configuration.default_serialization_format

        transport = self._transport_registry.lookup(effective_transport_name)

        if transport is None:
            errmsg_lines = [
                "Transport '{}' not found in agent '{}'.".format(
                    effective_transport_name, self._identity.identifier
                ),
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg)

        recipient_address = self._address_resolver.resolve(
            agent_identifier=recipient_id,
            transport_name=effective_transport_name,
        )

        sender_address = AgentAddress(
            agent_identifier=self._identity.identifier,
            transport_name=effective_transport_name,
        )

        message = Message(
            sender=sender_address,
            recipient=recipient_address,
            payload=payload,
            pattern=pattern,
            headers=headers,
        )

        envelope = transport.send(message)

        return envelope

    def request(self, recipient_id: str, payload: object,
                transport_name: str = None,
                serialization_format: str = None,
                timeout: float = None,
                headers: dict = None) -> Message:
        """
            Sends a request and awaits a correlated response.

            Resolves the default transport name and serialization format
            from the MessagingConfiguration when not provided. Constructs
            a REQUEST Message and delegates to the RequestResponseHandler
            for correlated response tracking.

            :param recipient_id: The recipient agent identifier.
            :param payload: The request payload.
            :param transport_name: Optional transport name. Defaults to
                the MessagingConfiguration default.
            :param serialization_format: Optional serialization format
                name. Defaults to the MessagingConfiguration default.
            :param timeout: Optional timeout in seconds.
            :param headers: Optional headers dictionary.

            :returns: The correlated response Message.

            :raises SemanticError: If the requested transport is not
                found in the TransportRegistry.
            :raises MessageTimeoutError: If no response is received
                within the timeout duration.
        """
        effective_transport_name = transport_name
        if effective_transport_name is None and self._messaging_configuration is not None:
            effective_transport_name = self._messaging_configuration.default_transport

        effective_serialization_format = serialization_format
        if effective_serialization_format is None and self._messaging_configuration is not None:
            effective_serialization_format = self._messaging_configuration.default_serialization_format

        transport = self._transport_registry.lookup(effective_transport_name)

        if transport is None:
            errmsg_lines = [
                "Transport '{}' not found in agent '{}'.".format(
                    effective_transport_name, self._identity.identifier
                ),
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg)

        recipient_address = self._address_resolver.resolve(
            agent_identifier=recipient_id,
            transport_name=effective_transport_name,
        )

        sender_address = AgentAddress(
            agent_identifier=self._identity.identifier,
            transport_name=effective_transport_name,
        )

        message = Message(
            sender=sender_address,
            recipient=recipient_address,
            payload=payload,
            pattern=MessagePattern.REQUEST,
            headers=headers,
        )

        response = self._request_response_handler.send_request(
            message=message,
            transport=transport,
            timeout=timeout,
        )

        return response

    def publish(self, topic: str, payload: object) -> None:
        """
            Publishes an event message to a topic.

            Constructs a sender AgentAddress from the agent's identity,
            constructs an EVENT Message with a None recipient, and
            delegates to the PubSubBroker for topic-based delivery.

            :param topic: The topic string.
            :param payload: The event payload.
        """
        sender_address = AgentAddress(
            agent_identifier=self._identity.identifier,
            transport_name="pubsub",
        )

        recipient_address = AgentAddress(
            agent_identifier="",
            transport_name="pubsub",
        )

        message = Message(
            sender=sender_address,
            recipient=recipient_address,
            payload=payload,
            pattern=MessagePattern.EVENT,
        )

        self._pubsub_broker.publish(topic=topic, message=message)

        return

    def subscribe(self, topic: str, handler: callable) -> Subscription:
        """
            Subscribes to a topic with a handler callback.

            Delegates to the PubSubBroker subscribe method using the
            agent's identity identifier as the subscriber agent ID.

            :param topic: The topic string.
            :param handler: The MessageHandler callback.

            :returns: A Subscription object.
        """
        subscription = self._pubsub_broker.subscribe(
            topic=topic,
            subscriber_agent_id=self._identity.identifier,
            handler=handler,
        )

        return subscription

    # -----------------------------------------------------------------------
    # LLM provider methods
    # -----------------------------------------------------------------------

    def register_llm_provider(self, provider: LLMProvider) -> None:
        """
            Registers an LLMProvider with this Agent's LLMProviderRegistry.

            :param provider: The LLMProvider instance to register.
        """
        self._llm_provider_registry.register(provider)
        return

    def complete(self, provider_name: str, model_name: str,
                 conversation: LLMConversation, retry_policy: RetryPolicy = None,
                 fallback_chain: FallbackChain = None, **kwargs) -> LLMResponse:
        """
            Looks up the LLMProvider and executes a completion request.

            Looks up the provider in the Agent's LLMProviderRegistry using
            the provider name and model name. If found, executes the
            completion request and records token usage and cost in the
            Agent's CostTracker. If not found, raises a SemanticError.

            When a RetryPolicy is configured and the completion fails, the
            request is retried according to the policy. When all retries are
            exhausted and a FallbackChain is configured, the next provider
            in the chain is attempted. If all providers fail, an
            LLMRequestError is raised with a summary of all attempted
            providers.

            :param provider_name: The provider name.
            :param model_name: The model name.
            :param conversation: The conversation history.
            :param retry_policy: Optional RetryPolicy for retry behavior.
            :param fallback_chain: Optional FallbackChain for fallback behavior.

            :returns: An LLMResponse.

            :raises: SemanticError if provider not found.
            :raises: LLMRequestError on provider failure after retries and fallbacks.
        """
        llm_logger = logging.getLogger("ccai.agentkit.llm")

        provider = self._llm_provider_registry.lookup(provider_name, model_name)

        if provider is None:
            err_msg_lines = [
                "LLM provider '{}' with model '{}' not found in agent '{}'.".format(
                    provider_name, model_name, self._identity.identifier
                ),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        failed_providers = []

        current_provider_name = provider_name
        current_model_name = model_name
        current_provider = provider

        while True:
            response = self._attempt_completion_with_retries(
                current_provider, current_provider_name, current_model_name,
                conversation, retry_policy, fallback_chain, llm_logger,
                failed_providers, **kwargs
            )

            if response is not None:
                return response

            if fallback_chain is None:
                break

            next_pair = fallback_chain.next_provider(
                current_provider_name, current_model_name
            )

            if next_pair is None:
                break

            fallback_provider_name = next_pair[0]
            fallback_model_name = next_pair[1]

            llm_logger.warning(
                "Falling back from provider '%s/%s' to '%s/%s'",
                current_provider_name, current_model_name,
                fallback_provider_name, fallback_model_name,
            )

            fallback_provider = self._llm_provider_registry.lookup(
                fallback_provider_name, fallback_model_name
            )

            if fallback_provider is None:
                failure_entry = {
                    "provider_name": fallback_provider_name,
                    "model_name": fallback_model_name,
                    "error": "Provider not found in registry",
                }
                failed_providers.append(failure_entry)
                current_provider_name = fallback_provider_name
                current_model_name = fallback_model_name
                continue

            current_provider_name = fallback_provider_name
            current_model_name = fallback_model_name
            current_provider = fallback_provider

        err_msg_lines = [
            "All LLM providers failed for agent '{}'.".format(
                self._identity.identifier
            ),
        ]

        for entry in failed_providers:
            err_msg_lines.append(
                "  Provider '{}' model '{}': {}".format(
                    entry["provider_name"], entry["model_name"], entry["error"]
                )
            )

        err_msg = os.linesep.join(err_msg_lines)

        raise LLMRequestError(
            provider_name=provider_name,
            model_name=model_name,
            category="server_error",
            cause=Exception(err_msg),
        )

    def _attempt_completion_with_retries(
        self, provider: LLMProvider, provider_name: str, model_name: str,
        conversation: LLMConversation, retry_policy: RetryPolicy,
        fallback_chain: FallbackChain,
        llm_logger: logging.Logger, failed_providers: list, **kwargs
    ) -> Optional[LLMResponse]:
        """
            Attempts a completion request with optional retry logic.

            If the completion succeeds, records cost and returns the
            LLMResponse. If it fails and a retry policy is configured,
            retries according to the policy. If all attempts fail and
            a fallback chain or retry policy is configured, appends the
            failure to the failed_providers list and returns None.
            If neither retry_policy nor fallback_chain is configured,
            the exception is re-raised directly.

            :param provider: The LLMProvider instance.
            :param provider_name: The provider name.
            :param model_name: The model name.
            :param conversation: The conversation history.
            :param retry_policy: Optional RetryPolicy for retry behavior.
            :param fallback_chain: Optional FallbackChain for fallback behavior.
            :param llm_logger: The logger for LLM operations.
            :param failed_providers: List to append failure entries to.

            :returns: An LLMResponse on success, or None on failure.
        """
        attempt = 0
        last_exception = None

        while True:
            try:
                llm_logger.info(
                    "Completion request begin: provider '%s', model '%s', agent '%s'",
                    provider_name, model_name, self._identity.identifier,
                )

                response = provider.complete(conversation, **kwargs)

                token_usage = response.token_usage
                cost_estimate = getattr(response, "cost_estimate", None)

                if cost_estimate is not None:
                    self._cost_tracker.record(provider_name, token_usage, cost_estimate)

                llm_logger.info(
                    "Completion request success: provider '%s', model '%s', "
                    "tokens=%d, duration=%.2fs",
                    provider_name, model_name,
                    token_usage.total_tokens, response.duration,
                )

                return response

            except Exception as exc:
                last_exception = exc

                llm_logger.warning(
                    "Completion request failure: provider '%s', model '%s', "
                    "error_type='%s', detail='%s'",
                    provider_name, model_name,
                    type(exc).__name__, str(exc),
                )

                if retry_policy is not None:
                    should_retry = retry_policy.should_retry(exc, attempt)

                    if should_retry is True:
                        delay = retry_policy.get_delay(attempt)

                        llm_logger.info(
                            "Retrying provider '%s/%s', attempt %d, delay %.2fs",
                            provider_name, model_name, attempt + 1, delay,
                        )

                        time.sleep(delay)
                        attempt = attempt + 1
                        continue

                    failure_entry = {
                        "provider_name": provider_name,
                        "model_name": model_name,
                        "error": str(last_exception),
                    }
                    failed_providers.append(failure_entry)

                    return None

                if fallback_chain is not None:
                    failure_entry = {
                        "provider_name": provider_name,
                        "model_name": model_name,
                        "error": str(last_exception),
                    }
                    failed_providers.append(failure_entry)

                    return None

                raise

    def execute_resilient(self, callable_op, operation_name: str = None,
                          retry_policy=None, circuit_breaker_name: str = None):
        """
            Executes the callable with resilience protection, delegating to
            the ResiliencePipeline execute_with_resilience method.

            :param callable_op: The callable to execute.
            :param operation_name: Optional name for the operation.
            :param retry_policy: Optional RetryPolicy override.
            :param circuit_breaker_name: Optional circuit breaker name.

            :returns: The operation result.
            :raises SemanticError: If resilience is not initialized.
        """
        if self._resilience_pipeline is None:
            raise SemanticError("Resilience pipeline is not initialized")

        result = self._resilience_pipeline.execute_with_resilience(
            callable_op,
            operation_name=operation_name,
            retry_policy=retry_policy,
            circuit_breaker_name=circuit_breaker_name
        )
        return result

    # -----------------------------------------------------------------------
    # Hook registration and invocation
    # -----------------------------------------------------------------------

    def register_hook(self, transition_point: str, callback: Callable) -> None:
        """
            Registers a lifecycle hook callback for a transition point.

            :param transition_point: One of on_initialize, on_start, on_pause,
                on_resume, on_stop, on_error.
            :param callback: A callable that accepts (agent, record) arguments.

            :raises: SemanticError
        """
        is_valid_point = transition_point in self._hooks

        if is_valid_point is not True:
            err_msg_lines = [
                "Invalid transition point for hook registration."
            ]
            err_msg_lines.append("  Transition point: {!r}".format(transition_point))
            err_msg_lines.append("  Valid transition points: {}".format(VALID_TRANSITION_POINTS))
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        self._hooks[transition_point].append(callback)

        return

    def deregister_hook(self, transition_point: str, callback: Callable) -> None:
        """
            Deregisters a previously registered lifecycle hook callback.

            :param transition_point: The transition point the hook was registered for.
            :param callback: The callback to remove.

            :raises: SemanticError
        """
        is_valid_point = transition_point in self._hooks

        if is_valid_point is not True:
            err_msg_lines = [
                "Invalid transition point for hook deregistration."
            ]
            err_msg_lines.append("  Transition point: {!r}".format(transition_point))
            err_msg_lines.append("  Valid transition points: {}".format(VALID_TRANSITION_POINTS))
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        hook_list = self._hooks[transition_point]
        is_present = callback in hook_list

        if is_present is True:
            hook_list.remove(callback)

        return

    def _invoke_hooks(self, transition_point: str, record: TransitionRecord) -> None:
        """
            Invokes all registered hooks for a transition point in registration order.

            If a hook raises an exception, the exception is logged at WARNING level
            and invocation continues with the remaining hooks.

            :param transition_point: The transition point to invoke hooks for.
            :param record: The TransitionRecord to pass to each hook.
        """
        hook_list = list(self._hooks.get(transition_point, []))

        for callback in hook_list:
            try:
                callback(self, record)
            except Exception as exc:
                self._logger.warning(
                    "Hook exception in agent %s at transition point %s: %s",
                    self._identity.identifier,
                    transition_point,
                    str(exc)
                )

        return

    # -----------------------------------------------------------------------
    # Lifecycle transition helper
    # -----------------------------------------------------------------------

    def _perform_transition(self, target_state: LifecycleState, transition_point: str,
                            metadata: Optional[dict] = None) -> TransitionRecord:
        """
            Performs a lifecycle state transition, logs it, and invokes hooks.

            If the target state is ERROR and this agent has a parent, the parent
            on_error hooks are invoked with the child identity in metadata.

            :param target_state: The target LifecycleState.
            :param transition_point: The hook transition point to invoke.
            :param metadata: Optional metadata for the transition.

            :returns: The TransitionRecord for the transition.
        """
        record = self._state_machine.transition_to(target_state, metadata=metadata)

        self._logger.info(
            "Agent %s transitioned from %s to %s",
            self._identity.identifier,
            record.previous_state.value,
            record.new_state.value
        )

        self._invoke_hooks(transition_point, record)

        if target_state is LifecycleState.ERROR and self._parent is not None:
            error_metadata = {
                "child_identifier": self._identity.identifier,
                "child_name": self._identity.name,
            }
            parent_record = TransitionRecord(
                previous_state=record.previous_state,
                new_state=record.new_state,
                timestamp=record.timestamp,
                metadata=error_metadata
            )
            self._parent._invoke_hooks("on_error", parent_record)

        return record

    # -----------------------------------------------------------------------
    # Sub-agent management
    # -----------------------------------------------------------------------

    def add_sub_agent(self, agent: "Agent") -> None:
        """
            Adds a child agent as a sub-agent of this agent.

            Performs cycle detection by walking up the ancestor chain.
            Sets the parent reference on the child agent.

            :param agent: The agent to add as a sub-agent.

            :raises: SemanticError
        """
        if agent is self:
            err_msg_lines = [
                "Cannot add an agent as a sub-agent of itself."
            ]
            err_msg_lines.append("  Agent identifier: {!r}".format(self._identity.identifier))
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        current = self
        while current is not None:
            if current is agent:
                err_msg_lines = [
                    "Circular parent-child relationship detected."
                ]
                err_msg_lines.append("  Agent causing cycle: {!r}".format(agent.identity.identifier))
                err_msg_lines.append("  Attempted parent: {!r}".format(self._identity.identifier))
                err_msg = os.linesep.join(err_msg_lines)
                raise SemanticError(err_msg)
            current = current._parent

        agent._parent = self
        self._sub_agents.append(agent)

        return

    def remove_sub_agent(self, identifier: str) -> None:
        """
            Removes a sub-agent by its unique identifier.

            Clears the parent reference on the removed child agent.

            :param identifier: The unique identifier of the sub-agent to remove.
        """
        agent_to_remove = None

        for sub_agent in self._sub_agents:
            if sub_agent.identity.identifier == identifier:
                agent_to_remove = sub_agent
                break

        if agent_to_remove is not None:
            agent_to_remove._parent = None
            self._sub_agents.remove(agent_to_remove)

        return

    # -----------------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------------

    def get_logger(self) -> logging.Logger:
        """
            Returns a logger scoped to this agent's identity.

            The logger name follows the pattern:
            ccai.agentkit.agent.<agent_identifier>

            :returns: A logging.Logger instance.
        """
        return self._logger

    # -----------------------------------------------------------------------
    # String representations
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            agent identifier, agent name, and current lifecycle state.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(identifier={!r}, name={!r}, state={!r})".format(
            self.__class__.__name__,
            self._identity.identifier,
            self._identity.name,
            self._state_machine.current_state
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent name
            and current lifecycle state.

            :returns: A human-readable string.
        """
        str_val = "{}: {} [{}]".format(
            self.__class__.__name__,
            self._identity.name,
            self._state_machine.current_state.value
        )
        return str_val
