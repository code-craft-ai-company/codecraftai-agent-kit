"""
    Unit tests for WorkflowStep and WorkflowDefinition classes in the
    Workflow & Orchestration feature.

    Tests WorkflowStep SemanticError for missing step_id/name,
    WorkflowDefinition validation (invalid start step, invalid edge
    refs, cycles, unreachable steps), get_step, get_outgoing_edges,
    get_incoming_edges, get_terminal_steps, and ParallelBranch
    validation.

    Requirements: 1.1-1.14, 2.1-2.10, 8.1-8.5
"""

from automojo.agentkit.workflowstep import WorkflowStep
from automojo.agentkit.workflowdefinition import WorkflowDefinition
from automojo.agentkit.workflowedge import WorkflowEdge
from automojo.agentkit.parallelbranch import ParallelBranch
from automojo.agentkit.workflowerrors import WorkflowDefinitionError
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.stepexecutionstatus import StepExecutionStatus
from automojo.agentkit.stepresult import StepResult


# =========================================================================
# Minimal concrete WorkflowStep subclass for testing
# =========================================================================

class ConcreteTestStep(WorkflowStep):
    """
        Minimal concrete WorkflowStep subclass used for unit testing.
    """

    def __init__(self, step_id: str, name: str, step_type: str = "test",
                 **kwargs) -> None:
        super().__init__(step_id=step_id, name=name, step_type=step_type,
                         **kwargs)
        return

    def execute(self, context) -> StepResult:
        rtnval = StepResult(
            step_id=self.step_id,
            step_name=self.name,
            status=StepExecutionStatus.COMPLETED
        )
        return rtnval


def _step(step_id: str, name: str = None) -> ConcreteTestStep:
    """
        Helper to create a ConcreteTestStep with a derived name.
    """
    if name is None:
        name = "Step {}".format(step_id)
    rtnval = ConcreteTestStep(step_id=step_id, name=name)
    return rtnval



# =========================================================================
# WorkflowStep SemanticError tests (Requirements 2.5, 2.6)
# =========================================================================

def test_workflowstep_raises_semantic_error_for_none_step_id():
    """
        Verify that WorkflowStep raises SemanticError when step_id
        is None.
    """
    raised = False
    try:
        ConcreteTestStep(step_id=None, name="valid-name")
    except SemanticError:
        raised = True

    assert raised, \
        "SemanticError should be raised when step_id is None"
    return


def test_workflowstep_raises_semantic_error_for_empty_step_id():
    """
        Verify that WorkflowStep raises SemanticError when step_id
        is an empty string.
    """
    raised = False
    try:
        ConcreteTestStep(step_id="", name="valid-name")
    except SemanticError:
        raised = True

    assert raised, \
        "SemanticError should be raised when step_id is empty"
    return


def test_workflowstep_raises_semantic_error_for_whitespace_step_id():
    """
        Verify that WorkflowStep raises SemanticError when step_id
        is only whitespace.
    """
    raised = False
    try:
        ConcreteTestStep(step_id="   ", name="valid-name")
    except SemanticError:
        raised = True

    assert raised, \
        "SemanticError should be raised when step_id is whitespace"
    return


def test_workflowstep_raises_semantic_error_for_none_name():
    """
        Verify that WorkflowStep raises SemanticError when name
        is None.
    """
    raised = False
    try:
        ConcreteTestStep(step_id="valid-id", name=None)
    except SemanticError:
        raised = True

    assert raised, \
        "SemanticError should be raised when name is None"
    return


def test_workflowstep_raises_semantic_error_for_empty_name():
    """
        Verify that WorkflowStep raises SemanticError when name
        is an empty string.
    """
    raised = False
    try:
        ConcreteTestStep(step_id="valid-id", name="")
    except SemanticError:
        raised = True

    assert raised, \
        "SemanticError should be raised when name is empty"
    return


def test_workflowstep_raises_semantic_error_for_whitespace_name():
    """
        Verify that WorkflowStep raises SemanticError when name
        is only whitespace.
    """
    raised = False
    try:
        ConcreteTestStep(step_id="valid-id", name="   ")
    except SemanticError:
        raised = True

    assert raised, \
        "SemanticError should be raised when name is whitespace"
    return


def test_workflowstep_valid_construction():
    """
        Verify that WorkflowStep constructs successfully with valid
        step_id and name.
    """
    step = ConcreteTestStep(step_id="step-1", name="First Step")

    assert step.step_id == "step-1", \
        "step_id should be 'step-1'"
    assert step.name == "First Step", \
        "name should be 'First Step'"
    assert step.step_type == "test", \
        "step_type should be 'test'"
    return


def test_workflowstep_repr_includes_class_step_id_name_type():
    """
        Verify that __repr__ includes the class name, step_id, name,
        and step_type.
    """
    step = ConcreteTestStep(step_id="s1", name="My Step", step_type="custom")
    repr_str = repr(step)

    assert "ConcreteTestStep" in repr_str, \
        "__repr__ should include the class name"
    assert "s1" in repr_str, \
        "__repr__ should include the step_id"
    assert "My Step" in repr_str, \
        "__repr__ should include the name"
    assert "custom" in repr_str, \
        "__repr__ should include the step_type"
    return


def test_workflowstep_str_includes_name_and_type():
    """
        Verify that __str__ includes the step name and step type.
    """
    step = ConcreteTestStep(step_id="s1", name="My Step", step_type="custom")
    str_val = str(step)

    assert "My Step" in str_val, \
        "__str__ should include the step name"
    assert "custom" in str_val, \
        "__str__ should include the step type"
    return



# =========================================================================
# WorkflowDefinition validation tests (Requirements 1.2-1.9)
# =========================================================================

def test_invalid_start_step_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when the start step identifier does not reference a valid step.
    """
    steps = {"a": _step("a"), "b": _step("b")}
    edges = [WorkflowEdge(source_step_id="a", target_step_id="b")]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="nonexistent"
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for invalid start step"
    assert "nonexistent" in detail_msg, \
        "Error detail should identify the invalid start step"
    return


def test_invalid_edge_source_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when an edge source references a nonexistent step.
    """
    steps = {"a": _step("a"), "b": _step("b")}
    edges = [WorkflowEdge(source_step_id="missing", target_step_id="b")]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="a"
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for invalid edge source"
    assert "missing" in detail_msg, \
        "Error detail should identify the invalid step reference"
    return


def test_invalid_edge_target_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when an edge target references a nonexistent step.
    """
    steps = {"a": _step("a"), "b": _step("b")}
    edges = [WorkflowEdge(source_step_id="a", target_step_id="ghost")]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="a"
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for invalid edge target"
    assert "ghost" in detail_msg, \
        "Error detail should identify the invalid step reference"
    return


def test_cycle_detection_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when the graph contains a cycle.
    """
    steps = {
        "a": _step("a"),
        "b": _step("b"),
        "c": _step("c"),
    }
    edges = [
        WorkflowEdge(source_step_id="a", target_step_id="b"),
        WorkflowEdge(source_step_id="b", target_step_id="c"),
        WorkflowEdge(source_step_id="c", target_step_id="a"),
    ]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="a"
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for cyclic graph"
    assert "ycle" in detail_msg, \
        "Error detail should mention cycle detection"
    return


def test_unreachable_steps_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when steps are unreachable from the start step.
    """
    steps = {
        "a": _step("a"),
        "b": _step("b"),
        "c": _step("c"),
    }
    # Only a -> b edge; c is unreachable
    edges = [WorkflowEdge(source_step_id="a", target_step_id="b")]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="a"
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for unreachable steps"
    assert "c" in detail_msg, \
        "Error detail should identify the unreachable step 'c'"
    return


# =========================================================================
# WorkflowDefinition query methods (Requirements 1.11-1.14)
# =========================================================================

def _make_linear_workflow():
    """
        Creates a simple linear workflow: a -> b -> c
    """
    steps = {
        "a": _step("a"),
        "b": _step("b"),
        "c": _step("c"),
    }
    edges = [
        WorkflowEdge(source_step_id="a", target_step_id="b"),
        WorkflowEdge(source_step_id="b", target_step_id="c"),
    ]
    wf = WorkflowDefinition(
        name="linear", version="1.0", steps=steps,
        edges=edges, start_step_id="a"
    )
    return wf


def test_get_step_returns_step_for_valid_id():
    """
        Verify that get_step returns the WorkflowStep for a valid
        step identifier.
    """
    wf = _make_linear_workflow()

    step = wf.get_step("b")

    assert step is not None, \
        "get_step should return a step for valid id 'b'"
    assert step.step_id == "b", \
        "Returned step should have step_id 'b'"
    return


def test_get_step_returns_none_for_invalid_id():
    """
        Verify that get_step returns None when the step identifier
        is not found.
    """
    wf = _make_linear_workflow()

    step = wf.get_step("nonexistent")

    assert step is None, \
        "get_step should return None for invalid id"
    return


def test_get_outgoing_edges_returns_edges_from_step():
    """
        Verify that get_outgoing_edges returns edges originating
        from the given step.
    """
    wf = _make_linear_workflow()

    edges = wf.get_outgoing_edges("a")

    assert len(edges) == 1, \
        "Step 'a' should have 1 outgoing edge"
    assert edges[0].target_step_id == "b", \
        "Outgoing edge from 'a' should target 'b'"
    return


def test_get_outgoing_edges_ordered_by_priority():
    """
        Verify that get_outgoing_edges returns edges ordered by
        priority in ascending order.
    """
    steps = {
        "a": _step("a"),
        "b": _step("b"),
        "c": _step("c"),
    }
    edges = [
        WorkflowEdge(source_step_id="a", target_step_id="c", priority=10),
        WorkflowEdge(source_step_id="a", target_step_id="b", priority=1),
    ]
    wf = WorkflowDefinition(
        name="branching", version="1.0", steps=steps,
        edges=edges, start_step_id="a"
    )

    outgoing = wf.get_outgoing_edges("a")

    assert len(outgoing) == 2, \
        "Step 'a' should have 2 outgoing edges"
    assert outgoing[0].target_step_id == "b", \
        "First edge (priority 1) should target 'b'"
    assert outgoing[1].target_step_id == "c", \
        "Second edge (priority 10) should target 'c'"
    return


def test_get_outgoing_edges_empty_for_terminal_step():
    """
        Verify that get_outgoing_edges returns an empty list for
        a terminal step with no outgoing edges.
    """
    wf = _make_linear_workflow()

    edges = wf.get_outgoing_edges("c")

    assert len(edges) == 0, \
        "Terminal step 'c' should have no outgoing edges"
    return


def test_get_incoming_edges_returns_edges_targeting_step():
    """
        Verify that get_incoming_edges returns edges targeting
        the given step.
    """
    wf = _make_linear_workflow()

    edges = wf.get_incoming_edges("c")

    assert len(edges) == 1, \
        "Step 'c' should have 1 incoming edge"
    assert edges[0].source_step_id == "b", \
        "Incoming edge to 'c' should originate from 'b'"
    return


def test_get_incoming_edges_empty_for_start_step():
    """
        Verify that get_incoming_edges returns an empty list for
        the start step.
    """
    wf = _make_linear_workflow()

    edges = wf.get_incoming_edges("a")

    assert len(edges) == 0, \
        "Start step 'a' should have no incoming edges"
    return


def test_get_terminal_steps_returns_steps_with_no_outgoing():
    """
        Verify that get_terminal_steps returns step identifiers
        that have no outgoing edges.
    """
    wf = _make_linear_workflow()

    terminals = wf.get_terminal_steps()

    assert "c" in terminals, \
        "Step 'c' should be a terminal step"
    assert len(terminals) == 1, \
        "There should be exactly 1 terminal step"
    return


def test_get_terminal_steps_multiple_terminals():
    """
        Verify that get_terminal_steps returns multiple terminal
        steps when the workflow branches without converging.
    """
    steps = {
        "a": _step("a"),
        "b": _step("b"),
        "c": _step("c"),
    }
    edges = [
        WorkflowEdge(source_step_id="a", target_step_id="b"),
        WorkflowEdge(source_step_id="a", target_step_id="c"),
    ]
    wf = WorkflowDefinition(
        name="fan-out", version="1.0", steps=steps,
        edges=edges, start_step_id="a"
    )

    terminals = wf.get_terminal_steps()

    assert "b" in terminals, \
        "Step 'b' should be a terminal step"
    assert "c" in terminals, \
        "Step 'c' should be a terminal step"
    assert len(terminals) == 2, \
        "There should be exactly 2 terminal steps"
    return



# =========================================================================
# ParallelBranch validation tests (Requirements 8.1-8.5)
# =========================================================================

def test_parallel_branch_invalid_fork_step_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when a ParallelBranch references an invalid fork step.
    """
    steps = {
        "a": _step("a"),
        "b": _step("b"),
        "c": _step("c"),
        "d": _step("d"),
    }
    edges = [
        WorkflowEdge(source_step_id="a", target_step_id="b"),
        WorkflowEdge(source_step_id="a", target_step_id="c"),
        WorkflowEdge(source_step_id="b", target_step_id="d"),
        WorkflowEdge(source_step_id="c", target_step_id="d"),
    ]
    branches = [ParallelBranch(fork_step_id="nonexistent", join_step_id="d")]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="a",
            parallel_branches=branches
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for invalid fork step"
    assert "nonexistent" in detail_msg, \
        "Error detail should identify the invalid fork step"
    return


def test_parallel_branch_invalid_join_step_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when a ParallelBranch references an invalid join step.
    """
    steps = {
        "a": _step("a"),
        "b": _step("b"),
        "c": _step("c"),
        "d": _step("d"),
    }
    edges = [
        WorkflowEdge(source_step_id="a", target_step_id="b"),
        WorkflowEdge(source_step_id="a", target_step_id="c"),
        WorkflowEdge(source_step_id="b", target_step_id="d"),
        WorkflowEdge(source_step_id="c", target_step_id="d"),
    ]
    branches = [ParallelBranch(fork_step_id="a", join_step_id="nonexistent")]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="a",
            parallel_branches=branches
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for invalid join step"
    assert "nonexistent" in detail_msg, \
        "Error detail should identify the invalid join step"
    return


def test_parallel_branch_non_converging_paths_raises_error():
    """
        Verify that WorkflowDefinition raises WorkflowDefinitionError
        when parallel paths from a fork do not all converge at the
        declared join step.
    """
    steps = {
        "fork": _step("fork"),
        "b1": _step("b1"),
        "b2": _step("b2"),
        "join": _step("join"),
        "dead": _step("dead"),
    }
    edges = [
        WorkflowEdge(source_step_id="fork", target_step_id="b1"),
        WorkflowEdge(source_step_id="fork", target_step_id="b2"),
        WorkflowEdge(source_step_id="b1", target_step_id="join"),
        # b2 goes to 'dead' instead of 'join'
        WorkflowEdge(source_step_id="b2", target_step_id="dead"),
    ]
    branches = [ParallelBranch(fork_step_id="fork", join_step_id="join")]

    raised = False
    detail_msg = ""
    try:
        WorkflowDefinition(
            name="wf", version="1.0", steps=steps,
            edges=edges, start_step_id="fork",
            parallel_branches=branches
        )
    except WorkflowDefinitionError as err:
        raised = True
        detail_msg = err.detail

    assert raised, \
        "WorkflowDefinitionError should be raised for non-converging paths"
    assert "converge" in detail_msg.lower() or "fork" in detail_msg, \
        "Error detail should mention non-converging paths"
    return


def test_parallel_branch_valid_converging_paths():
    """
        Verify that WorkflowDefinition accepts a valid ParallelBranch
        where all paths from fork converge at join.
    """
    steps = {
        "fork": _step("fork"),
        "b1": _step("b1"),
        "b2": _step("b2"),
        "join": _step("join"),
    }
    edges = [
        WorkflowEdge(source_step_id="fork", target_step_id="b1"),
        WorkflowEdge(source_step_id="fork", target_step_id="b2"),
        WorkflowEdge(source_step_id="b1", target_step_id="join"),
        WorkflowEdge(source_step_id="b2", target_step_id="join"),
    ]
    branches = [ParallelBranch(fork_step_id="fork", join_step_id="join")]

    wf = WorkflowDefinition(
        name="wf", version="1.0", steps=steps,
        edges=edges, start_step_id="fork",
        parallel_branches=branches
    )

    assert len(wf.parallel_branches) == 1, \
        "WorkflowDefinition should have 1 parallel branch"
    assert wf.parallel_branches[0].fork_step_id == "fork", \
        "ParallelBranch fork should be 'fork'"
    assert wf.parallel_branches[0].join_step_id == "join", \
        "ParallelBranch join should be 'join'"
    return


# =========================================================================
# WorkflowDefinition properties and repr/str (Requirements 1.1, 1.10)
# =========================================================================

def test_workflowdefinition_properties():
    """
        Verify that WorkflowDefinition exposes all fields as
        read-only properties.
    """
    wf = _make_linear_workflow()

    assert wf.name == "linear", \
        "name should be 'linear'"
    assert wf.version == "1.0", \
        "version should be '1.0'"
    assert wf.start_step_id == "a", \
        "start_step_id should be 'a'"
    assert len(wf.steps) == 3, \
        "steps should contain 3 entries"
    assert len(wf.edges) == 2, \
        "edges should contain 2 entries"
    assert len(wf.parallel_branches) == 0, \
        "parallel_branches should be empty"
    return


def test_workflowdefinition_repr():
    """
        Verify that __repr__ includes the class name, workflow name,
        version, and step count.
    """
    wf = _make_linear_workflow()
    repr_str = repr(wf)

    assert "WorkflowDefinition" in repr_str, \
        "__repr__ should include the class name"
    assert "linear" in repr_str, \
        "__repr__ should include the workflow name"
    assert "1.0" in repr_str, \
        "__repr__ should include the version"
    return


def test_workflowdefinition_str():
    """
        Verify that __str__ includes the workflow name, version,
        step count, and edge count.
    """
    wf = _make_linear_workflow()
    str_val = str(wf)

    assert "linear" in str_val, \
        "__str__ should include the workflow name"
    assert "1.0" in str_val, \
        "__str__ should include the version"
    assert "3" in str_val, \
        "__str__ should include the step count"
    assert "2" in str_val, \
        "__str__ should include the edge count"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
