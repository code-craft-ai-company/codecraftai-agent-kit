"""
    Provides the register_builtin_agent_metrics function that registers
    the standard set of agent metrics in a MetricsRegistry.

    The 13 built-in metrics cover agent lifecycle transitions, tool
    execution duration and errors, LLM request duration, token usage,
    and errors, memory operations, message counts, workflow step
    duration and errors, and active trace spans.
"""

from ccai.agentkit.metricdefinition import MetricDefinition
from ccai.agentkit.metricsregistry import MetricsRegistry
from ccai.agentkit.metrictype import MetricType


BUILTIN_METRICS = [
    MetricDefinition(
        name="agent.lifecycle.transitions",
        description="Count of agent lifecycle state transitions",
        unit="count",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.tool.execution.duration",
        description="Duration of tool executions",
        unit="seconds",
        metric_type=MetricType.HISTOGRAM
    ),
    MetricDefinition(
        name="agent.tool.execution.errors",
        description="Count of tool execution errors",
        unit="count",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.llm.request.duration",
        description="Duration of LLM completion requests",
        unit="seconds",
        metric_type=MetricType.HISTOGRAM
    ),
    MetricDefinition(
        name="agent.llm.token.usage.prompt",
        description="Count of prompt tokens consumed",
        unit="tokens",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.llm.token.usage.completion",
        description="Count of completion tokens consumed",
        unit="tokens",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.llm.request.errors",
        description="Count of LLM request errors",
        unit="count",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.memory.operations",
        description="Count of memory store operations",
        unit="count",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.message.sent",
        description="Count of messages sent",
        unit="count",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.message.received",
        description="Count of messages received",
        unit="count",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.workflow.step.duration",
        description="Duration of workflow step executions",
        unit="seconds",
        metric_type=MetricType.HISTOGRAM
    ),
    MetricDefinition(
        name="agent.workflow.step.errors",
        description="Count of workflow step execution errors",
        unit="count",
        metric_type=MetricType.COUNTER
    ),
    MetricDefinition(
        name="agent.active.spans",
        description="Count of currently active trace spans",
        unit="count",
        metric_type=MetricType.GAUGE
    ),
]


def register_builtin_agent_metrics(registry: MetricsRegistry) -> None:
    """
        Registers the standard set of agent metrics in the provided
        MetricsRegistry.

        Called automatically when an Agent is initialized with
        observability enabled. Registers 13 metric definitions covering
        lifecycle transitions, tool execution, LLM requests, memory
        operations, messaging, workflow steps, and active spans.

        :param registry: The MetricsRegistry instance to register
            the built-in metrics in.
    """
    for definition in BUILTIN_METRICS:
        registry.register(definition)

    return
