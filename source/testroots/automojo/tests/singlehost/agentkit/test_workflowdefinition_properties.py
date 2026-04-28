"""
    Property-based tests for the automojo.agentkit.workflowdefinition module.

    Uses automojo.testbase.properties to verify:
    - Property 10: DAG Acyclicity Validation
    - Property 11: DAG Reachability Validation
    - Property 6: WorkflowDefinition JSON Round-Trip
    - Property 7: WorkflowDefinition YAML Round-Trip

    **Validates: Requirement 1 AC 6-9, Requirement 21 AC 7-8**
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given, assume
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.workflowdefinition import WorkflowDefinition
from automojo.agentkit.workflowstep import WorkflowStep
from automojo.agentkit.workflowedge import WorkflowEdge
from automojo.agentkit.workflowerrors import WorkflowDefinitionError
from automojo.agentkit.stepexecutionstatus import StepExecutionStatus
from automojo.agentkit.stepresult import StepResult
from automojo.agentkit.workflowcontext import WorkflowContext


# ---------------------------------------------------------------------------
# Minimal concrete WorkflowStep subclass for testing
# ---------------------------------------------------------------------------

class _TestStep(WorkflowStep):
    """
        Minimal concrete WorkflowStep for property testing.
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


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _make_step(step_id: str) -> _TestStep:
    """
        Creates a _TestStep with the given identifier and a derived name.
    """
    rtnval = _TestStep(step_id=step_id, name="Step {}".format(step_id))
    return rtnval



# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_step_id_alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"

_step_id = st.text(
    min_size=1,
    max_size=8,
    alphabet=_step_id_alphabet
)

_version_str = st.text(
    min_size=1,
    max_size=5,
    alphabet="0123456789."
)

_name_str = st.text(
    min_size=1,
    max_size=15,
    alphabet="abcdefghijklmnopqrstuvwxyz "
)


@composite
def valid_dag(draw, min_steps=2, max_steps=6):
    """
        Generates a valid DAG: a list of unique step IDs and edges
        forming an acyclic, fully-reachable graph from step 0.

        Steps are assigned indices 0..n-1. Edges only go from lower
        index to higher index, guaranteeing acyclicity. All steps
        are connected via at least one edge from a lower-index step.
    """
    num_steps = draw(st.integers(min_steps, max_steps))

    step_ids = []
    for i in range(num_steps):
        sid = "s{}".format(i)
        step_ids.append(sid)

    edges = []

    # Ensure every step (except start) is reachable: connect each
    # step i (i >= 1) from some step j where j < i.
    for i in range(1, num_steps):
        source_idx = draw(st.integers(0, i - 1))
        edges.append((step_ids[source_idx], step_ids[i]))

    # Add some extra forward edges for variety
    extra_count = draw(st.integers(0, min(num_steps, 4)))
    for _ in range(extra_count):
        src_idx = draw(st.integers(0, num_steps - 2))
        tgt_idx = draw(st.integers(src_idx + 1, num_steps - 1))
        pair = (step_ids[src_idx], step_ids[tgt_idx])
        if pair not in edges:
            edges.append(pair)

    return step_ids, edges


@composite
def dag_with_cycle(draw, min_steps=3, max_steps=6):
    """
        Generates a set of step IDs and edges that contain at least
        one guaranteed cycle. Builds a linear chain s0 -> s1 -> ... -> sN
        then adds a back-edge from the last step to the first step,
        guaranteeing a cycle along the chain. Additional steps may be
        added and connected to ensure all steps are reachable.
    """
    num_steps = draw(st.integers(min_steps, max_steps))

    step_ids = []
    for i in range(num_steps):
        sid = "s{}".format(i)
        step_ids.append(sid)

    edges = []

    # Build a linear chain: s0 -> s1 -> s2 -> ... -> s(n-1)
    for i in range(1, num_steps):
        edges.append((step_ids[i - 1], step_ids[i]))

    # Add a back-edge from the last step to the first step,
    # creating a guaranteed cycle: s0 -> s1 -> ... -> s(n-1) -> s0
    back_edge = (step_ids[num_steps - 1], step_ids[0])
    edges.append(back_edge)

    return step_ids, edges


@composite
def dag_with_unreachable(draw, min_steps=3, max_steps=6):
    """
        Generates a set of step IDs and edges where at least one
        step is unreachable from the start step. Creates a valid
        DAG for a subset of steps, then adds an isolated step with
        no incoming edges from the reachable set.
    """
    num_steps = draw(st.integers(min_steps, max_steps))

    step_ids = []
    for i in range(num_steps):
        sid = "s{}".format(i)
        step_ids.append(sid)

    # Connect steps 0..n-2 as a valid DAG
    edges = []
    for i in range(1, num_steps - 1):
        source_idx = draw(st.integers(0, i - 1))
        edges.append((step_ids[source_idx], step_ids[i]))

    # step n-1 is unreachable: no edges point to it from the
    # reachable set. We do NOT add any edge targeting step_ids[-1].

    return step_ids, edges


# ---------------------------------------------------------------------------
# Property 10: DAG Acyclicity Validation
# ---------------------------------------------------------------------------

@given(
    dag_data=valid_dag(min_steps=2, max_steps=6),
    wf_name=_name_str,
    wf_version=_version_str,
    constraints={"max_examples": 80},
)
def test_valid_dag_accepted(dag_data, wf_name, wf_version) -> None:
    """
        **Validates: Requirement 1 AC 6**

        For all sets of steps and edges that form a valid DAG (no
        cycles, all reachable), the WorkflowDefinition constructor
        shall succeed without raising.
    """
    step_ids, edge_tuples = dag_data

    steps = {}
    for sid in step_ids:
        steps[sid] = _make_step(sid)

    edges = []
    for src, tgt in edge_tuples:
        edges.append(WorkflowEdge(source_step_id=src, target_step_id=tgt))

    start_step_id = step_ids[0]

    wf = WorkflowDefinition(
        name=wf_name,
        version=wf_version,
        steps=steps,
        edges=edges,
        start_step_id=start_step_id
    )

    testbase.assert_equal(wf.name, wf_name,
        "WorkflowDefinition name should match: {!r} != {!r}".format(
            wf.name, wf_name))

    testbase.assert_equal(wf.start_step_id, start_step_id,
        "start_step_id should match: {!r} != {!r}".format(
            wf.start_step_id, start_step_id))

    return


@given(
    dag_data=dag_with_cycle(min_steps=3, max_steps=6),
    wf_name=_name_str,
    wf_version=_version_str,
    constraints={"max_examples": 80},
)
def test_cyclic_graph_rejected(dag_data, wf_name, wf_version) -> None:
    """
        **Validates: Requirement 1 AC 7**

        For all sets of steps and edges that form a cycle, the
        WorkflowDefinition constructor shall raise a
        WorkflowDefinitionError.
    """
    step_ids, edge_tuples = dag_data

    steps = {}
    for sid in step_ids:
        steps[sid] = _make_step(sid)

    edges = []
    for src, tgt in edge_tuples:
        edges.append(WorkflowEdge(source_step_id=src, target_step_id=tgt))

    start_step_id = step_ids[0]

    raised = False
    try:
        WorkflowDefinition(
            name=wf_name,
            version=wf_version,
            steps=steps,
            edges=edges,
            start_step_id=start_step_id
        )
    except WorkflowDefinitionError:
        raised = True

    testbase.assert_true(raised,
        "WorkflowDefinitionError should be raised for cyclic graph "
        "with edges: {}".format(edge_tuples))

    return


# ---------------------------------------------------------------------------
# Property 11: DAG Reachability Validation
# ---------------------------------------------------------------------------

@given(
    dag_data=valid_dag(min_steps=2, max_steps=6),
    wf_name=_name_str,
    wf_version=_version_str,
    constraints={"max_examples": 80},
)
def test_all_steps_reachable_accepted(dag_data, wf_name, wf_version) -> None:
    """
        **Validates: Requirement 1 AC 8**

        For all valid WorkflowDefinition instances, every step in the
        steps dictionary shall be reachable from the start step via
        the edges.
    """
    step_ids, edge_tuples = dag_data

    steps = {}
    for sid in step_ids:
        steps[sid] = _make_step(sid)

    edges = []
    for src, tgt in edge_tuples:
        edges.append(WorkflowEdge(source_step_id=src, target_step_id=tgt))

    start_step_id = step_ids[0]

    wf = WorkflowDefinition(
        name=wf_name,
        version=wf_version,
        steps=steps,
        edges=edges,
        start_step_id=start_step_id
    )

    testbase.assert_equal(len(wf.steps), len(step_ids),
        "All {} steps should be present in the definition".format(
            len(step_ids)))

    return


@given(
    dag_data=dag_with_unreachable(min_steps=3, max_steps=6),
    wf_name=_name_str,
    wf_version=_version_str,
    constraints={"max_examples": 80},
)
def test_unreachable_steps_rejected(dag_data, wf_name, wf_version) -> None:
    """
        **Validates: Requirement 1 AC 9**

        If any step is unreachable from the start step, the
        WorkflowDefinition constructor shall raise a
        WorkflowDefinitionError.
    """
    step_ids, edge_tuples = dag_data

    steps = {}
    for sid in step_ids:
        steps[sid] = _make_step(sid)

    edges = []
    for src, tgt in edge_tuples:
        edges.append(WorkflowEdge(source_step_id=src, target_step_id=tgt))

    start_step_id = step_ids[0]

    raised = False
    try:
        WorkflowDefinition(
            name=wf_name,
            version=wf_version,
            steps=steps,
            edges=edges,
            start_step_id=start_step_id
        )
    except WorkflowDefinitionError:
        raised = True

    testbase.assert_true(raised,
        "WorkflowDefinitionError should be raised for unreachable "
        "steps with edges: {}".format(edge_tuples))

    return



# ---------------------------------------------------------------------------
# Property 6: WorkflowDefinition JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    dag_data=valid_dag(min_steps=2, max_steps=5),
    wf_name=_name_str,
    wf_version=_version_str,
    description=st.one_of(st.none(), st.text(min_size=1, max_size=20,
        alphabet="abcdefghijklmnopqrstuvwxyz ")),
    constraints={"max_examples": 80},
)
def test_workflowdefinition_json_roundtrip(
    dag_data, wf_name, wf_version, description
) -> None:
    """
        **Validates: Requirement 21 AC 7**

        For all valid WorkflowDefinition instances, calling to_json
        and then from_json shall produce an equivalent
        WorkflowDefinition object with the same name, version,
        description, steps, edges, start step identifier, and
        parallel branches.
    """
    step_ids, edge_tuples = dag_data

    steps = {}
    for sid in step_ids:
        steps[sid] = _make_step(sid)

    edges = []
    for src, tgt in edge_tuples:
        edges.append(WorkflowEdge(source_step_id=src, target_step_id=tgt))

    start_step_id = step_ids[0]

    original = WorkflowDefinition(
        name=wf_name,
        version=wf_version,
        steps=steps,
        edges=edges,
        start_step_id=start_step_id,
        description=description
    )

    json_str = original.to_json()
    restored = WorkflowDefinition.from_json(json_str)

    testbase.assert_equal(restored.name, original.name,
        "name mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.name, original.name))

    testbase.assert_equal(restored.version, original.version,
        "version mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.version, original.version))

    testbase.assert_equal(restored.description, original.description,
        "description mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.description, original.description))

    testbase.assert_equal(restored.start_step_id, original.start_step_id,
        "start_step_id mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.start_step_id, original.start_step_id))

    testbase.assert_equal(
        set(restored.steps.keys()), set(original.steps.keys()),
        "step keys mismatch after JSON round-trip: {!r} != {!r}".format(
            set(restored.steps.keys()), set(original.steps.keys())))

    testbase.assert_equal(len(restored.edges), len(original.edges),
        "edge count mismatch after JSON round-trip: {} != {}".format(
            len(restored.edges), len(original.edges)))

    for i in range(len(original.edges)):
        orig_edge = original.edges[i]
        rest_edge = restored.edges[i]
        testbase.assert_equal(
            rest_edge.source_step_id, orig_edge.source_step_id,
            "edge {} source mismatch: {!r} != {!r}".format(
                i, rest_edge.source_step_id, orig_edge.source_step_id))
        testbase.assert_equal(
            rest_edge.target_step_id, orig_edge.target_step_id,
            "edge {} target mismatch: {!r} != {!r}".format(
                i, rest_edge.target_step_id, orig_edge.target_step_id))

    testbase.assert_equal(
        len(restored.parallel_branches), len(original.parallel_branches),
        "parallel_branches count mismatch after JSON round-trip")

    return


# ---------------------------------------------------------------------------
# Property 7: WorkflowDefinition YAML Round-Trip
# ---------------------------------------------------------------------------

@given(
    dag_data=valid_dag(min_steps=2, max_steps=5),
    wf_name=_name_str,
    wf_version=_version_str,
    description=st.one_of(st.none(), st.text(min_size=1, max_size=20,
        alphabet="abcdefghijklmnopqrstuvwxyz ")),
    constraints={"max_examples": 80},
)
def test_workflowdefinition_yaml_roundtrip(
    dag_data, wf_name, wf_version, description
) -> None:
    """
        **Validates: Requirement 21 AC 8**

        For all valid WorkflowDefinition instances, calling to_yaml
        and then from_yaml shall produce an equivalent
        WorkflowDefinition object.
    """
    step_ids, edge_tuples = dag_data

    steps = {}
    for sid in step_ids:
        steps[sid] = _make_step(sid)

    edges = []
    for src, tgt in edge_tuples:
        edges.append(WorkflowEdge(source_step_id=src, target_step_id=tgt))

    start_step_id = step_ids[0]

    original = WorkflowDefinition(
        name=wf_name,
        version=wf_version,
        steps=steps,
        edges=edges,
        start_step_id=start_step_id,
        description=description
    )

    yaml_str = original.to_yaml()
    restored = WorkflowDefinition.from_yaml(yaml_str)

    testbase.assert_equal(restored.name, original.name,
        "name mismatch after YAML round-trip: {!r} != {!r}".format(
            restored.name, original.name))

    testbase.assert_equal(restored.version, original.version,
        "version mismatch after YAML round-trip: {!r} != {!r}".format(
            restored.version, original.version))

    testbase.assert_equal(restored.description, original.description,
        "description mismatch after YAML round-trip: {!r} != {!r}".format(
            restored.description, original.description))

    testbase.assert_equal(restored.start_step_id, original.start_step_id,
        "start_step_id mismatch after YAML round-trip: {!r} != {!r}".format(
            restored.start_step_id, original.start_step_id))

    testbase.assert_equal(
        set(restored.steps.keys()), set(original.steps.keys()),
        "step keys mismatch after YAML round-trip: {!r} != {!r}".format(
            set(restored.steps.keys()), set(original.steps.keys())))

    testbase.assert_equal(len(restored.edges), len(original.edges),
        "edge count mismatch after YAML round-trip: {} != {}".format(
            len(restored.edges), len(original.edges)))

    for i in range(len(original.edges)):
        orig_edge = original.edges[i]
        rest_edge = restored.edges[i]
        testbase.assert_equal(
            rest_edge.source_step_id, orig_edge.source_step_id,
            "edge {} source mismatch: {!r} != {!r}".format(
                i, rest_edge.source_step_id, orig_edge.source_step_id))
        testbase.assert_equal(
            rest_edge.target_step_id, orig_edge.target_step_id,
            "edge {} target mismatch: {!r} != {!r}".format(
                i, rest_edge.target_step_id, orig_edge.target_step_id))

    testbase.assert_equal(
        len(restored.parallel_branches), len(original.parallel_branches),
        "parallel_branches count mismatch after YAML round-trip")

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
