"""
    Defines the WorkflowDefinition class representing an immutable
    directed acyclic graph (DAG) of WorkflowStep nodes connected by
    WorkflowEdge edges in the Workflow & Orchestration feature.

    A WorkflowDefinition contains a name, version, optional description,
    a dictionary of WorkflowStep objects keyed by step identifier, a list
    of WorkflowEdge objects, a designated start step identifier, and an
    optional list of ParallelBranch declarations.

    The WorkflowDefinition validates structural integrity at construction
    time, checking that the start step exists, all edge references are
    valid, the graph contains no cycles, all steps are reachable from
    the start step, and all ParallelBranch fork/join steps are valid
    with converging paths.

    .. module:: automojo.agentkit.workflowdefinition
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable DAG workflow definition with validation.
"""

import json

from collections import deque
from typing import Optional

import yaml

from automojo.agentkit.workflowstep import WorkflowStep
from automojo.agentkit.workflowedge import WorkflowEdge
from automojo.agentkit.parallelbranch import ParallelBranch
from automojo.agentkit.workflowerrors import WorkflowDefinitionError
from automojo.agentkit.stepexecutionstatus import StepExecutionStatus


class _PassthroughStep(WorkflowStep):
    """
        A minimal concrete WorkflowStep subclass used for round-trip
        deserialization when no step_type_registry is provided.

        The _PassthroughStep stores the raw step data dictionary and
        returns a dummy StepResult from execute. This allows
        WorkflowDefinition instances to be reconstructed from
        serialized data without requiring the original step classes.

        :param step_id: The unique identifier for this step.
        :param name: The human-readable name for this step.
        :param step_type: The step type string.
        :param step_data: The raw dictionary of step data from
            deserialization.
        :param input_schema: An optional input schema dictionary.
        :param output_schema: An optional output schema dictionary.
        :param tags: An optional tags dictionary.
        :param retry_policy: An optional retry policy.
    """

    def __init__(self, step_id: str, name: str, step_type: str,
                 step_data: Optional[dict] = None,
                 input_schema: Optional[dict] = None,
                 output_schema: Optional[dict] = None,
                 tags: Optional[dict] = None,
                 retry_policy=None) -> None:
        super().__init__(
            step_id=step_id, name=name, step_type=step_type,
            input_schema=input_schema, output_schema=output_schema,
            tags=tags, retry_policy=retry_policy
        )
        self._step_data = dict(step_data) if step_data is not None else {}
        return

    @property
    def step_data(self) -> dict:
        """
            The raw step data dictionary from deserialization.

            :returns: A dictionary of step data fields.
        """
        return self._step_data

    def execute(self, context) -> "StepResult":
        """
            Returns a dummy StepResult with COMPLETED status.

            This implementation exists only to satisfy the abstract
            interface requirement. _PassthroughStep is not intended
            for actual workflow execution.

            :param context: The WorkflowContext (unused).

            :returns: A StepResult with COMPLETED status.
        """
        from automojo.agentkit.stepresult import StepResult

        rtnval = StepResult(
            step_id=self._step_id,
            step_name=self._name,
            status=StepExecutionStatus.COMPLETED
        )
        return rtnval



class WorkflowDefinition:
    """
        Immutable DAG of WorkflowStep nodes connected by WorkflowEdge
        edges. Validates structural integrity at construction time.

        A WorkflowDefinition represents a complete workflow as a directed
        acyclic graph. It contains a name, version, optional description,
        a dictionary of WorkflowStep objects keyed by step identifier,
        a list of WorkflowEdge objects defining the connections between
        steps, a designated start step identifier, and an optional list
        of ParallelBranch declarations for concurrent execution
        boundaries.

        At construction time the definition validates that:

        1. The start step identifier references a step in the steps
           dictionary.
        2. All edge source and target step identifiers reference valid
           steps.
        3. The graph contains no cycles (DFS-based cycle detection).
        4. All steps are reachable from the start step (BFS from start).
        5. All ParallelBranch fork/join steps are valid and paths
           converge at the join step.

        :param name: The workflow name string.
        :param version: The workflow version string.
        :param steps: A dictionary of WorkflowStep objects keyed by
            step identifier.
        :param edges: A list of WorkflowEdge objects defining the
            connections between steps.
        :param start_step_id: The identifier of the step where
            execution begins.
        :param parallel_branches: An optional list of ParallelBranch
            declarations. Defaults to an empty list.
        :param description: An optional description string for the
            workflow.

        :raises WorkflowDefinitionError: When any structural validation
            fails.
    """

    def __init__(self, name: str, version: str, steps: dict,
                 edges: list, start_step_id: str,
                 parallel_branches: Optional[list] = None,
                 description: Optional[str] = None) -> None:
        self._name = name
        self._version = version
        self._description = description
        self._steps = dict(steps)
        self._edges = list(edges)
        self._start_step_id = start_step_id
        self._parallel_branches = list(parallel_branches) if parallel_branches is not None else []

        self._validate()

        return

    def _validate(self) -> None:
        """
            Validates the workflow DAG structural integrity.

            Checks are performed in the following order:

            1. Start step exists in the steps dictionary.
            2. All edge source and target step identifiers reference
               valid steps.
            3. No cycles exist in the graph (DFS with WHITE/GRAY/BLACK
               coloring).
            4. All steps are reachable from the start step (BFS from
               start).
            5. ParallelBranch fork/join steps are valid and all paths
               from fork converge at join.

            :raises WorkflowDefinitionError: When any validation check
                fails.
        """
        self._validate_start_step()
        self._validate_edge_references()
        self._validate_no_cycles()
        self._validate_reachability()
        self._validate_parallel_branches()

        return

    def _validate_start_step(self) -> None:
        """
            Validates that the start step identifier references a step
            present in the steps dictionary.

            :raises WorkflowDefinitionError: When the start step
                identifier is not found in the steps dictionary.
        """
        if self._start_step_id not in self._steps:
            detail = "Start step '{}' not found in steps dictionary".format(
                self._start_step_id
            )
            raise WorkflowDefinitionError(self._name, detail)

        return

    def _validate_edge_references(self) -> None:
        """
            Validates that all edge source and target step identifiers
            reference steps present in the steps dictionary.

            :raises WorkflowDefinitionError: When an edge references
                a step identifier not in the steps dictionary.
        """
        for edge in self._edges:
            if edge.source_step_id not in self._steps:
                detail = "Edge references invalid step '{}'".format(
                    edge.source_step_id
                )
                raise WorkflowDefinitionError(self._name, detail)

            if edge.target_step_id not in self._steps:
                detail = "Edge references invalid step '{}'".format(
                    edge.target_step_id
                )
                raise WorkflowDefinitionError(self._name, detail)

        return

    def _validate_no_cycles(self) -> None:
        """
            Validates that the graph contains no cycles using DFS
            with WHITE/GRAY/BLACK coloring.

            WHITE = not visited, GRAY = in current DFS path,
            BLACK = fully processed.

            :raises WorkflowDefinitionError: When a cycle is detected,
                identifying the steps involved.
        """
        WHITE = 0
        GRAY = 1
        BLACK = 2

        color = {}
        for step_id in self._steps:
            color[step_id] = WHITE

        adjacency = {}
        for step_id in self._steps:
            adjacency[step_id] = []

        for edge in self._edges:
            adjacency[edge.source_step_id].append(edge.target_step_id)

        cycle_steps = []

        def dfs(node: str) -> bool:
            """
                Performs depth-first search from the given node to
                detect cycles.

                :param node: The step identifier to visit.

                :returns: True if a cycle is detected, False otherwise.
            """
            color[node] = GRAY

            for neighbor in adjacency[node]:
                if color[neighbor] == GRAY:
                    cycle_steps.append(neighbor)
                    cycle_steps.append(node)
                    return True

                if color[neighbor] == WHITE:
                    found_cycle = dfs(neighbor)
                    if found_cycle:
                        cycle_steps.append(node)
                        return True

            color[node] = BLACK
            return False

        for step_id in self._steps:
            if color[step_id] == WHITE:
                found_cycle = dfs(step_id)
                if found_cycle:
                    unique_cycle_steps = []
                    seen = set()
                    for sid in cycle_steps:
                        if sid not in seen:
                            unique_cycle_steps.append(sid)
                            seen.add(sid)

                    step_list = ", ".join(unique_cycle_steps)
                    detail = "Cycle detected involving steps: {}".format(
                        step_list
                    )
                    raise WorkflowDefinitionError(self._name, detail)

        return

    def _validate_reachability(self) -> None:
        """
            Validates that all steps are reachable from the start step
            using breadth-first search.

            :raises WorkflowDefinitionError: When unreachable steps
                are detected, identifying the unreachable step
                identifiers.
        """
        adjacency = {}
        for step_id in self._steps:
            adjacency[step_id] = []

        for edge in self._edges:
            adjacency[edge.source_step_id].append(edge.target_step_id)

        visited = set()
        queue = deque()
        queue.append(self._start_step_id)
        visited.add(self._start_step_id)

        while len(queue) > 0:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        all_step_ids = set(self._steps.keys())
        unreachable = all_step_ids - visited

        if len(unreachable) > 0:
            unreachable_list = ", ".join(sorted(unreachable))
            detail = "Unreachable steps: {}".format(unreachable_list)
            raise WorkflowDefinitionError(self._name, detail)

        return

    def _validate_parallel_branches(self) -> None:
        """
            Validates that all ParallelBranch declarations have valid
            fork and join step identifiers and that all paths from the
            fork step converge at the join step.

            :raises WorkflowDefinitionError: When a ParallelBranch
                references an invalid step or paths do not converge.
        """
        for branch in self._parallel_branches:
            fork_id = branch.fork_step_id
            join_id = branch.join_step_id

            if fork_id not in self._steps:
                detail = "ParallelBranch references invalid fork step '{}'".format(
                    fork_id
                )
                raise WorkflowDefinitionError(self._name, detail)

            if join_id not in self._steps:
                detail = "ParallelBranch references invalid join step '{}'".format(
                    join_id
                )
                raise WorkflowDefinitionError(self._name, detail)

            self._validate_paths_converge(fork_id, join_id)

        return

    def _validate_paths_converge(self, fork_id: str, join_id: str) -> None:
        """
            Validates that all paths from the fork step converge at
            the join step using BFS. Every path from the fork must
            reach the join step.

            :param fork_id: The fork step identifier.
            :param join_id: The join step identifier.

            :raises WorkflowDefinitionError: When paths from the fork
                do not all converge at the join step.
        """
        adjacency = {}
        for step_id in self._steps:
            adjacency[step_id] = []

        for edge in self._edges:
            adjacency[edge.source_step_id].append(edge.target_step_id)

        outgoing_from_fork = adjacency.get(fork_id, [])

        if len(outgoing_from_fork) == 0:
            detail = "ParallelBranch fork step '{}' has no outgoing edges".format(
                fork_id
            )
            raise WorkflowDefinitionError(self._name, detail)

        for branch_start in outgoing_from_fork:
            reached_join = self._can_reach(branch_start, join_id, adjacency)

            if not reached_join:
                detail = ("ParallelBranch paths from fork '{}' do not all "
                          "converge at join '{}'".format(fork_id, join_id))
                raise WorkflowDefinitionError(self._name, detail)

        return

    def _can_reach(self, start_id: str, target_id: str, adjacency: dict) -> bool:
        """
            Determines whether the target step is reachable from the
            start step using BFS.

            :param start_id: The step identifier to start from.
            :param target_id: The step identifier to reach.
            :param adjacency: The adjacency list dictionary.

            :returns: True if the target is reachable from start,
                False otherwise.
        """
        if start_id == target_id:
            return True

        visited = set()
        queue = deque()
        queue.append(start_id)
        visited.add(start_id)

        while len(queue) > 0:
            current = queue.popleft()

            for neighbor in adjacency.get(current, []):
                if neighbor == target_id:
                    return True

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    @property
    def name(self) -> str:
        """
            The workflow name string.

            :returns: The workflow name.
        """
        return self._name

    @property
    def version(self) -> str:
        """
            The workflow version string.

            :returns: The workflow version.
        """
        return self._version

    @property
    def description(self) -> Optional[str]:
        """
            The optional description string for the workflow.

            :returns: The description string or None.
        """
        return self._description

    @property
    def steps(self) -> dict:
        """
            The dictionary of WorkflowStep objects keyed by step
            identifier.

            :returns: A dictionary of step identifier to WorkflowStep
                mappings.
        """
        return self._steps

    @property
    def edges(self) -> list:
        """
            The list of WorkflowEdge objects defining the connections
            between steps.

            :returns: A list of WorkflowEdge objects.
        """
        return self._edges

    @property
    def start_step_id(self) -> str:
        """
            The identifier of the step where execution begins.

            :returns: The start step identifier string.
        """
        return self._start_step_id

    @property
    def parallel_branches(self) -> list:
        """
            The list of ParallelBranch declarations for concurrent
            execution boundaries.

            :returns: A list of ParallelBranch objects.
        """
        return self._parallel_branches

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """
            Returns the WorkflowStep for the given step identifier,
            or None when the identifier is not found.

            :param step_id: The step identifier to look up.

            :returns: The WorkflowStep instance or None.
        """
        rtnval = self._steps.get(step_id, None)
        return rtnval

    def get_outgoing_edges(self, step_id: str) -> list:
        """
            Returns the list of WorkflowEdge objects originating from
            the given step, ordered by edge priority in ascending order.

            :param step_id: The step identifier to get outgoing edges
                for.

            :returns: A list of WorkflowEdge objects sorted by priority
                ascending.
        """
        matching_edges = []

        for edge in self._edges:
            if edge.source_step_id == step_id:
                matching_edges.append(edge)

        matching_edges.sort(key=lambda e: e.priority)

        return matching_edges

    def get_incoming_edges(self, step_id: str) -> list:
        """
            Returns the list of WorkflowEdge objects targeting the
            given step.

            :param step_id: The step identifier to get incoming edges
                for.

            :returns: A list of WorkflowEdge objects.
        """
        matching_edges = []

        for edge in self._edges:
            if edge.target_step_id == step_id:
                matching_edges.append(edge)

        return matching_edges

    def get_terminal_steps(self) -> list:
        """
            Returns the list of step identifiers that have no outgoing
            edges.

            :returns: A list of step identifier strings.
        """
        steps_with_outgoing = set()

        for edge in self._edges:
            steps_with_outgoing.add(edge.source_step_id)

        terminal_steps = []

        for step_id in self._steps:
            if step_id not in steps_with_outgoing:
                terminal_steps.append(step_id)

        return terminal_steps

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the workflow
            definition including steps, edges, and parallel branches.

            Steps are serialized as a dictionary of step identifier
            to step data dictionaries. Edges are serialized as a list
            of edge dictionaries. Parallel branches are serialized as
            a list of branch dictionaries.

            :returns: A dictionary containing name, version, description,
                steps, edges, start_step_id, and parallel_branches.
        """
        steps_dict = {}

        for step_id, step in self._steps.items():
            step_entry = {
                "step_type": step.step_type,
                "name": step.name,
                "input_schema": step.input_schema,
                "output_schema": step.output_schema,
                "tags": step.tags
            }

            if isinstance(step, _PassthroughStep) and len(step.step_data) > 0:
                step_entry["step_data"] = step.step_data

            steps_dict[step_id] = step_entry

        edges_list = []
        for edge in self._edges:
            edges_list.append(edge.as_dict())

        branches_list = []
        for branch in self._parallel_branches:
            branches_list.append(branch.as_dict())

        rtnval = {
            "name": self._name,
            "version": self._version,
            "description": self._description,
            "steps": steps_dict,
            "edges": edges_list,
            "start_step_id": self._start_step_id,
            "parallel_branches": branches_list
        }

        return rtnval

    def to_json(self) -> str:
        """
            Serializes the workflow definition to a JSON string.

            :returns: A JSON string representation of the workflow
                definition.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    def to_yaml(self) -> str:
        """
            Serializes the workflow definition to a YAML string.

            :returns: A YAML string representation of the workflow
                definition.
        """
        data = self.as_dict()
        rtnval = yaml.safe_dump(data, default_flow_style=False)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict,
                  step_type_registry: Optional[dict] = None) -> "WorkflowDefinition":
        """
            Constructs a WorkflowDefinition from a dictionary
            representation.

            When a step_type_registry is provided, it is used to
            reconstruct WorkflowStep subclasses by looking up the
            step_type string in the registry. When no registry is
            provided, a _PassthroughStep is created for each step
            to enable round-trip serialization.

            :param data: A dictionary containing the workflow
                definition fields.
            :param step_type_registry: An optional dictionary mapping
                step type strings to WorkflowStep subclass factories.

            :returns: A WorkflowDefinition instance.
        """
        name = data["name"]
        version = data["version"]
        description = data.get("description")
        start_step_id = data["start_step_id"]

        steps = {}
        steps_data = data.get("steps", {})

        for step_id, step_info in steps_data.items():
            step_type = step_info.get("step_type", "passthrough")
            step_name = step_info.get("name", step_id)

            if step_type_registry is not None and step_type in step_type_registry:
                factory = step_type_registry[step_type]
                step = factory(step_id=step_id, step_info=step_info)
            else:
                step = _PassthroughStep(
                    step_id=step_id,
                    name=step_name,
                    step_type=step_type,
                    step_data=step_info,
                    input_schema=step_info.get("input_schema"),
                    output_schema=step_info.get("output_schema"),
                    tags=step_info.get("tags")
                )

            steps[step_id] = step

        edges = []
        edges_data = data.get("edges", [])

        for edge_info in edges_data:
            edge = WorkflowEdge(
                source_step_id=edge_info["source_step_id"],
                target_step_id=edge_info["target_step_id"],
                condition=edge_info.get("condition"),
                priority=edge_info.get("priority", 0)
            )
            edges.append(edge)

        parallel_branches = []
        branches_data = data.get("parallel_branches", [])

        for branch_info in branches_data:
            branch = ParallelBranch(
                fork_step_id=branch_info["fork_step_id"],
                join_step_id=branch_info["join_step_id"]
            )
            parallel_branches.append(branch)

        rtnval = cls(
            name=name,
            version=version,
            steps=steps,
            edges=edges,
            start_step_id=start_step_id,
            parallel_branches=parallel_branches,
            description=description
        )

        return rtnval

    @classmethod
    def from_json(cls, json_str: str,
                  step_type_registry: Optional[dict] = None) -> "WorkflowDefinition":
        """
            Deserializes a JSON string into a WorkflowDefinition
            instance.

            :param json_str: A JSON string containing the workflow
                definition fields.
            :param step_type_registry: An optional dictionary mapping
                step type strings to WorkflowStep subclass factories.

            :returns: A WorkflowDefinition instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data, step_type_registry=step_type_registry)
        return rtnval

    @classmethod
    def from_yaml(cls, yaml_str: str,
                  step_type_registry: Optional[dict] = None) -> "WorkflowDefinition":
        """
            Deserializes a YAML string into a WorkflowDefinition
            instance.

            :param yaml_str: A YAML string containing the workflow
                definition fields.
            :param step_type_registry: An optional dictionary mapping
                step type strings to WorkflowStep subclass factories.

            :returns: A WorkflowDefinition instance.
        """
        data = yaml.safe_load(yaml_str)
        rtnval = cls.from_dict(data, step_type_registry=step_type_registry)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, workflow name, version, and step count.

            :returns: A repr string for debugging.
        """
        step_count = len(self._steps)
        repr_str = "{}(name={!r}, version={!r}, steps={})".format(
            self.__class__.__name__, self._name, self._version,
            step_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the workflow
            name, version, step count, and edge count.

            :returns: A human-readable string describing the workflow
                definition.
        """
        step_count = len(self._steps)
        edge_count = len(self._edges)
        str_val = "WorkflowDefinition: {} v{} [{} steps, {} edges]".format(
            self._name, self._version, step_count, edge_count
        )
        return str_val
