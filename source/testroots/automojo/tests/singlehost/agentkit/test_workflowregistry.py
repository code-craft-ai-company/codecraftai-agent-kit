"""
    Unit tests for the WorkflowConfiguration and WorkflowRegistry
    classes in the Workflow & Orchestration feature.

    Tests WorkflowConfiguration validation errors, defaults,
    serialization (as_dict, to_json, from_json, to_yaml, from_yaml),
    and __repr__/__str__.

    Tests WorkflowRegistry register, deregister, lookup, latest
    version, duplicate error, list_all, has_workflow, count,
    and __repr__/__str__.

    Requirements: 16.1-16.9, 17.1-17.16
"""

import json

from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.stepexecutionstatus import StepExecutionStatus
from automojo.agentkit.stepresult import StepResult
from automojo.agentkit.workflowconfiguration import WorkflowConfiguration
from automojo.agentkit.workflowdefinition import WorkflowDefinition
from automojo.agentkit.workflowedge import WorkflowEdge
from automojo.agentkit.workflowregistry import WorkflowRegistry
from automojo.agentkit.workflowstep import WorkflowStep


# =========================================================================
# Minimal concrete WorkflowStep subclass for testing
# =========================================================================

class _TestStep(WorkflowStep):
    """
        Minimal concrete WorkflowStep subclass used for unit testing.
    """

    def __init__(self, step_id: str, name: str,
                 step_type: str = "test", **kwargs) -> None:
        super().__init__(step_id=step_id, name=name,
                         step_type=step_type, **kwargs)
        return

    def execute(self, context) -> StepResult:
        rtnval = StepResult(
            step_id=self.step_id,
            step_name=self.name,
            status=StepExecutionStatus.COMPLETED
        )
        return rtnval


def _make_step(step_id: str) -> _TestStep:
    """
        Helper to create a _TestStep with a derived name.
    """
    rtnval = _TestStep(step_id=step_id, name="Step {}".format(step_id))
    return rtnval


def _make_workflow(name: str, version: str) -> WorkflowDefinition:
    """
        Helper to create a minimal valid WorkflowDefinition with
        a single step and no edges.
    """
    step = _make_step("start")
    rtnval = WorkflowDefinition(
        name=name,
        version=version,
        steps={"start": step},
        edges=[],
        start_step_id="start"
    )
    return rtnval


# =========================================================================
# WorkflowConfiguration defaults tests (Requirement 17.1)
# =========================================================================

def test_configuration_defaults():
    """
        Verify that WorkflowConfiguration uses correct default
        values when no arguments are provided.
    """
    config = WorkflowConfiguration()

    assert config.max_parallel_workers == 4, \
        "Default max_parallel_workers should be 4"
    assert config.checkpoint_interval == 1, \
        "Default checkpoint_interval should be 1"
    assert config.default_approval_timeout == 3600.0, \
        "Default default_approval_timeout should be 3600.0"
    assert config.default_retry_policy is None, \
        "Default default_retry_policy should be None"
    return


def test_configuration_custom_values():
    """
        Verify that WorkflowConfiguration stores custom values
        provided at construction time.
    """
    config = WorkflowConfiguration(
        max_parallel_workers=8,
        checkpoint_interval=5,
        default_approval_timeout=7200.0,
        default_retry_policy="some-policy"
    )

    assert config.max_parallel_workers == 8, \
        "max_parallel_workers should be 8"
    assert config.checkpoint_interval == 5, \
        "checkpoint_interval should be 5"
    assert config.default_approval_timeout == 7200.0, \
        "default_approval_timeout should be 7200.0"
    assert config.default_retry_policy == "some-policy", \
        "default_retry_policy should be 'some-policy'"
    return


# =========================================================================
# WorkflowConfiguration validation tests (Requirements 17.7, 17.8)
# =========================================================================

def test_configuration_raises_error_for_zero_workers():
    """
        Verify that WorkflowConfiguration raises ConfigurationError
        when max_parallel_workers is 0.
    """
    caught = False
    try:
        WorkflowConfiguration(max_parallel_workers=0)
    except ConfigurationError:
        caught = True

    assert caught is True, \
        "ConfigurationError should be raised for max_parallel_workers=0"
    return


def test_configuration_raises_error_for_negative_workers():
    """
        Verify that WorkflowConfiguration raises ConfigurationError
        when max_parallel_workers is negative.
    """
    caught = False
    try:
        WorkflowConfiguration(max_parallel_workers=-1)
    except ConfigurationError:
        caught = True

    assert caught is True, \
        "ConfigurationError should be raised for negative max_parallel_workers"
    return


def test_configuration_raises_error_for_zero_timeout():
    """
        Verify that WorkflowConfiguration raises ConfigurationError
        when default_approval_timeout is 0.
    """
    caught = False
    try:
        WorkflowConfiguration(default_approval_timeout=0)
    except ConfigurationError:
        caught = True

    assert caught is True, \
        "ConfigurationError should be raised for default_approval_timeout=0"
    return


def test_configuration_raises_error_for_negative_timeout():
    """
        Verify that WorkflowConfiguration raises ConfigurationError
        when default_approval_timeout is negative.
    """
    caught = False
    try:
        WorkflowConfiguration(default_approval_timeout=-100.0)
    except ConfigurationError:
        caught = True

    assert caught is True, \
        "ConfigurationError should be raised for negative default_approval_timeout"
    return


# =========================================================================
# WorkflowConfiguration serialization tests (Requirements 17.9-17.14)
# =========================================================================

def test_configuration_as_dict():
    """
        Verify that as_dict returns a dictionary with all
        configuration fields.
    """
    config = WorkflowConfiguration(
        max_parallel_workers=2,
        checkpoint_interval=3,
        default_approval_timeout=1800.0
    )

    result = config.as_dict()

    assert result["max_parallel_workers"] == 2, \
        "as_dict max_parallel_workers should be 2"
    assert result["checkpoint_interval"] == 3, \
        "as_dict checkpoint_interval should be 3"
    assert result["default_approval_timeout"] == 1800.0, \
        "as_dict default_approval_timeout should be 1800.0"
    assert "default_retry_policy" not in result, \
        "as_dict should not include default_retry_policy when None"
    return


def test_configuration_to_json_produces_valid_json():
    """
        Verify that to_json produces a valid JSON string.
    """
    config = WorkflowConfiguration(
        max_parallel_workers=6,
        checkpoint_interval=2,
        default_approval_timeout=900.0
    )

    json_str = config.to_json()
    parsed = json.loads(json_str)

    assert parsed["max_parallel_workers"] == 6, \
        "JSON max_parallel_workers should be 6"
    assert parsed["checkpoint_interval"] == 2, \
        "JSON checkpoint_interval should be 2"
    return


def test_configuration_from_json_reconstructs():
    """
        Verify that from_json reconstructs an equivalent
        WorkflowConfiguration.
    """
    original = WorkflowConfiguration(
        max_parallel_workers=10,
        checkpoint_interval=4,
        default_approval_timeout=600.0
    )

    json_str = original.to_json()
    restored = WorkflowConfiguration.from_json(json_str)

    assert restored.max_parallel_workers == 10, \
        "Restored max_parallel_workers should be 10"
    assert restored.checkpoint_interval == 4, \
        "Restored checkpoint_interval should be 4"
    assert restored.default_approval_timeout == 600.0, \
        "Restored default_approval_timeout should be 600.0"
    return


def test_configuration_to_yaml_and_from_yaml():
    """
        Verify that to_yaml and from_yaml produce an equivalent
        WorkflowConfiguration.
    """
    original = WorkflowConfiguration(
        max_parallel_workers=3,
        checkpoint_interval=7,
        default_approval_timeout=1200.0
    )

    yaml_str = original.to_yaml()
    restored = WorkflowConfiguration.from_yaml(yaml_str)

    assert restored.max_parallel_workers == 3, \
        "Restored max_parallel_workers should be 3"
    assert restored.checkpoint_interval == 7, \
        "Restored checkpoint_interval should be 7"
    assert restored.default_approval_timeout == 1200.0, \
        "Restored default_approval_timeout should be 1200.0"
    return


def test_configuration_from_dict():
    """
        Verify that from_dict constructs a WorkflowConfiguration
        from a dictionary.
    """
    data = {
        "max_parallel_workers": 16,
        "checkpoint_interval": 10,
        "default_approval_timeout": 500.0
    }

    config = WorkflowConfiguration.from_dict(data)

    assert config.max_parallel_workers == 16, \
        "from_dict max_parallel_workers should be 16"
    assert config.checkpoint_interval == 10, \
        "from_dict checkpoint_interval should be 10"
    assert config.default_approval_timeout == 500.0, \
        "from_dict default_approval_timeout should be 500.0"
    return


def test_configuration_from_dict_uses_defaults():
    """
        Verify that from_dict uses default values for missing keys.
    """
    config = WorkflowConfiguration.from_dict({})

    assert config.max_parallel_workers == 4, \
        "from_dict should default max_parallel_workers to 4"
    assert config.checkpoint_interval == 1, \
        "from_dict should default checkpoint_interval to 1"
    assert config.default_approval_timeout == 3600.0, \
        "from_dict should default default_approval_timeout to 3600.0"
    return


# =========================================================================
# WorkflowConfiguration __repr__ / __str__ tests (Req 23.23, 23.24)
# =========================================================================

def test_configuration_repr():
    """
        Verify that __repr__ includes the class name, max parallel
        workers, and checkpoint interval.
    """
    config = WorkflowConfiguration(
        max_parallel_workers=5,
        checkpoint_interval=2
    )

    repr_str = repr(config)

    assert "WorkflowConfiguration" in repr_str, \
        "__repr__ should include the class name"
    assert "5" in repr_str, \
        "__repr__ should include max_parallel_workers"
    assert "2" in repr_str, \
        "__repr__ should include checkpoint_interval"
    return


def test_configuration_str():
    """
        Verify that __str__ includes max parallel workers,
        checkpoint interval, and default approval timeout.
    """
    config = WorkflowConfiguration(
        max_parallel_workers=4,
        checkpoint_interval=1,
        default_approval_timeout=3600.0
    )

    str_val = str(config)

    assert "4" in str_val, \
        "__str__ should include max_parallel_workers"
    assert "1" in str_val, \
        "__str__ should include checkpoint_interval"
    assert "3600" in str_val, \
        "__str__ should include default_approval_timeout"
    return


# =========================================================================
# WorkflowRegistry register tests (Requirements 16.1, 16.2)
# =========================================================================

def test_registry_register_and_lookup():
    """
        Verify that a registered workflow can be looked up by
        name and version.
    """
    registry = WorkflowRegistry()
    wf = _make_workflow("data-pipeline", "1.0.0")

    registry.register(wf)

    result = registry.lookup("data-pipeline", "1.0.0")

    assert result is not None, \
        "lookup should return the registered workflow"
    assert result.name == "data-pipeline", \
        "Looked up workflow name should match"
    assert result.version == "1.0.0", \
        "Looked up workflow version should match"
    return


def test_registry_register_duplicate_raises_semantic_error():
    """
        Verify that registering a duplicate name+version raises
        SemanticError.
    """
    registry = WorkflowRegistry()
    wf1 = _make_workflow("pipeline", "1.0.0")
    wf2 = _make_workflow("pipeline", "1.0.0")

    registry.register(wf1)

    caught = False
    try:
        registry.register(wf2)
    except SemanticError:
        caught = True

    assert caught is True, \
        "SemanticError should be raised for duplicate name+version"
    return


def test_registry_register_different_versions():
    """
        Verify that the same workflow name with different versions
        can be registered.
    """
    registry = WorkflowRegistry()
    wf1 = _make_workflow("pipeline", "1.0.0")
    wf2 = _make_workflow("pipeline", "2.0.0")

    registry.register(wf1)
    registry.register(wf2)

    assert registry.count == 2, \
        "Registry should contain 2 workflows"
    return


# =========================================================================
# WorkflowRegistry deregister tests (Requirement 16.3)
# =========================================================================

def test_registry_deregister():
    """
        Verify that deregister removes a workflow by name and
        version.
    """
    registry = WorkflowRegistry()
    wf = _make_workflow("pipeline", "1.0.0")

    registry.register(wf)
    registry.deregister("pipeline", "1.0.0")

    assert registry.count == 0, \
        "Registry should be empty after deregister"
    assert registry.lookup("pipeline", "1.0.0") is None, \
        "lookup should return None after deregister"
    return


def test_registry_deregister_nonexistent_is_noop():
    """
        Verify that deregistering a nonexistent workflow does not
        raise an error.
    """
    registry = WorkflowRegistry()

    registry.deregister("nonexistent", "1.0.0")

    assert registry.count == 0, \
        "Registry should remain empty"
    return


# =========================================================================
# WorkflowRegistry lookup tests (Requirement 16.4)
# =========================================================================

def test_registry_lookup_returns_none_for_missing():
    """
        Verify that lookup returns None when no matching workflow
        is found.
    """
    registry = WorkflowRegistry()

    result = registry.lookup("missing", "1.0.0")

    assert result is None, \
        "lookup should return None for missing workflow"
    return


def test_registry_lookup_latest_version():
    """
        Verify that lookup without a version returns the latest
        version (lexicographic ordering).
    """
    registry = WorkflowRegistry()
    wf1 = _make_workflow("pipeline", "1.0.0")
    wf2 = _make_workflow("pipeline", "2.0.0")
    wf3 = _make_workflow("pipeline", "1.5.0")

    registry.register(wf1)
    registry.register(wf2)
    registry.register(wf3)

    result = registry.lookup("pipeline")

    assert result is not None, \
        "lookup should return a workflow"
    assert result.version == "2.0.0", \
        "lookup without version should return the latest version"
    return


def test_registry_lookup_latest_returns_none_when_no_match():
    """
        Verify that lookup without version returns None when no
        workflows match the name.
    """
    registry = WorkflowRegistry()
    wf = _make_workflow("other", "1.0.0")
    registry.register(wf)

    result = registry.lookup("missing")

    assert result is None, \
        "lookup should return None when no workflows match"
    return


# =========================================================================
# WorkflowRegistry list_all tests (Requirement 16.5)
# =========================================================================

def test_registry_list_all():
    """
        Verify that list_all returns all registered workflows.
    """
    registry = WorkflowRegistry()
    wf1 = _make_workflow("alpha", "1.0.0")
    wf2 = _make_workflow("beta", "1.0.0")

    registry.register(wf1)
    registry.register(wf2)

    result = registry.list_all()

    assert len(result) == 2, \
        "list_all should return 2 workflows"
    return


def test_registry_list_all_empty():
    """
        Verify that list_all returns an empty list when no
        workflows are registered.
    """
    registry = WorkflowRegistry()

    result = registry.list_all()

    assert result == [], \
        "list_all should return an empty list"
    return


# =========================================================================
# WorkflowRegistry has_workflow tests (Requirement 16.7)
# =========================================================================

def test_registry_has_workflow_with_version():
    """
        Verify that has_workflow returns True for a registered
        name+version.
    """
    registry = WorkflowRegistry()
    wf = _make_workflow("pipeline", "1.0.0")
    registry.register(wf)

    assert registry.has_workflow("pipeline", "1.0.0") is True, \
        "has_workflow should return True for registered workflow"
    assert registry.has_workflow("pipeline", "2.0.0") is False, \
        "has_workflow should return False for unregistered version"
    return


def test_registry_has_workflow_without_version():
    """
        Verify that has_workflow without version returns True if
        any version of the named workflow is registered.
    """
    registry = WorkflowRegistry()
    wf = _make_workflow("pipeline", "1.0.0")
    registry.register(wf)

    assert registry.has_workflow("pipeline") is True, \
        "has_workflow should return True when any version exists"
    assert registry.has_workflow("missing") is False, \
        "has_workflow should return False when no version exists"
    return


# =========================================================================
# WorkflowRegistry count tests (Requirement 16.6)
# =========================================================================

def test_registry_count():
    """
        Verify that count returns the number of registered
        workflows.
    """
    registry = WorkflowRegistry()

    assert registry.count == 0, \
        "count should be 0 for empty registry"

    wf1 = _make_workflow("a", "1.0.0")
    wf2 = _make_workflow("b", "1.0.0")
    registry.register(wf1)
    registry.register(wf2)

    assert registry.count == 2, \
        "count should be 2 after registering 2 workflows"
    return


# =========================================================================
# WorkflowRegistry __repr__ / __str__ tests (Req 23.19, 23.20)
# =========================================================================

def test_registry_repr():
    """
        Verify that __repr__ includes the class name and count.
    """
    registry = WorkflowRegistry()
    wf = _make_workflow("pipeline", "1.0.0")
    registry.register(wf)

    repr_str = repr(registry)

    assert "WorkflowRegistry" in repr_str, \
        "__repr__ should include the class name"
    assert "1" in repr_str, \
        "__repr__ should include the count"
    return


def test_registry_str_empty():
    """
        Verify that __str__ for an empty registry indicates 0
        workflows.
    """
    registry = WorkflowRegistry()

    str_val = str(registry)

    assert "0" in str_val, \
        "__str__ should indicate 0 workflows"
    return


def test_registry_str_with_workflows():
    """
        Verify that __str__ lists registered workflow names and
        versions.
    """
    registry = WorkflowRegistry()
    wf1 = _make_workflow("alpha", "1.0.0")
    wf2 = _make_workflow("beta", "2.0.0")
    registry.register(wf1)
    registry.register(wf2)

    str_val = str(registry)

    assert "alpha@1.0.0" in str_val, \
        "__str__ should list alpha@1.0.0"
    assert "beta@2.0.0" in str_val, \
        "__str__ should list beta@2.0.0"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
