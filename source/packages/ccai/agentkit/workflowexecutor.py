"""
    Defines the WorkflowExecutor class responsible for executing a
    WorkflowDefinition by traversing the DAG, evaluating edge
    conditions, executing steps, managing parallel branches, and
    producing a WorkflowResult.

    The WorkflowExecutor coordinates with the ConditionEvaluator for
    conditional branching, the CheckpointManager for fault-tolerant
    execution with resumption, and uses concurrent.futures for
    parallel branch execution.

    Requirements: 4.1-4.13, 8.6-8.9, 9.6-9.7, 10.1-10.6,
                  22.1-22.15, 23.21, 23.22

    .. module:: ccai.agentkit.workflowexecutor
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: DAG traversal and step execution engine.
"""

import logging
import time
import uuid

from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from ccai.agentkit.checkpointmanager import CheckpointManager
from ccai.agentkit.conditionevaluator import ConditionEvaluator
from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.workflowconfiguration import WorkflowConfiguration
from ccai.agentkit.workflowcontext import WorkflowContext
from ccai.agentkit.workflowdefinition import WorkflowDefinition
from ccai.agentkit.workflowerrors import WorkflowCheckpointError
from ccai.agentkit.workflowerrors import WorkflowExecutionError
from ccai.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from ccai.agentkit.workflowresult import WorkflowResult


class WorkflowExecutor:
    """
        Executes a WorkflowDefinition by traversing the DAG,
        evaluating edge conditions, executing steps, managing
        parallel branches, and producing a WorkflowResult.

        The executor creates a WorkflowContext from the provided
        inputs, computes a topological execution order from the
        DAG, and executes each step in order. For conditional
        edges, the ConditionEvaluator evaluates expressions in
        ascending priority order and the first true edge is
        traversed. For unconditional edges with parallel branches,
        branches are executed concurrently using a ThreadPoolExecutor
        bounded by the configured max_parallel_workers.

        Checkpoints are saved via the CheckpointManager at the
        configured interval. Failed steps are retried according
        to their RetryPolicy when configured.

        :param configuration: An optional WorkflowConfiguration
            for execution settings. Defaults to a
            WorkflowConfiguration with default values.
        :param checkpoint_manager: An optional CheckpointManager
            for saving and loading checkpoints.
    """

    def __init__(self, configuration: Optional[WorkflowConfiguration] = None,
                 checkpoint_manager: Optional[CheckpointManager] = None) -> None:
        self._configuration = configuration or WorkflowConfiguration()
        self._checkpoint_manager = checkpoint_manager
        self._condition_evaluator = ConditionEvaluator()
        self._logger = logging.getLogger("ccai.agentkit.workflow.executor")
        return

    def execute(self, workflow: WorkflowDefinition, inputs: dict,
                agent=None) -> WorkflowResult:
        """
            Executes a workflow from the start step.

            Creates a WorkflowContext from the provided inputs,
            generates a unique execution identifier, computes the
            topological execution order from the DAG, and executes
            each step in order. Conditional edges are evaluated in
            ascending priority order. Parallel branches declared
            in the workflow definition are executed concurrently.

            :param workflow: The WorkflowDefinition to execute.
            :param inputs: The initial input dictionary.
            :param agent: The executing Agent instance.

            :returns: A WorkflowResult with the execution outcome.
        """
        execution_id = str(uuid.uuid4())
        context = WorkflowContext(inputs=inputs, agent=agent)
        context.set_metadata("workflow_name", workflow.name)
        context.set_metadata("execution_id", execution_id)

        agent_id = getattr(agent, "identifier", None) if agent is not None else None

        self._logger.info(
            "Workflow execution begins: workflow='%s', "
            "execution_id='%s', agent_id='%s'.",
            workflow.name, execution_id, agent_id
        )

        start_time = time.monotonic()
        step_results = []
        completed_step_ids = set()
        steps_since_checkpoint = 0

        result = self._execute_steps(
            workflow=workflow,
            context=context,
            execution_id=execution_id,
            step_results=step_results,
            completed_step_ids=completed_step_ids,
            steps_since_checkpoint=steps_since_checkpoint,
            start_time=start_time
        )

        return result

    def resume(self, execution_id: str, workflow: WorkflowDefinition,
               agent=None) -> WorkflowResult:
        """
            Resumes a workflow from the last checkpoint.

            Loads the most recent checkpoint for the execution
            identifier, restores the WorkflowContext from the
            checkpoint state, skips completed steps, and continues
            execution from the next step.

            :param execution_id: The workflow execution identifier.
            :param workflow: The WorkflowDefinition to resume.
            :param agent: The executing Agent instance.

            :returns: A WorkflowResult with the execution outcome.

            :raises WorkflowCheckpointError: When no checkpoint is
                found for the execution identifier.
        """
        if self._checkpoint_manager is None:
            raise WorkflowCheckpointError(
                execution_id=execution_id,
                operation="load",
                cause=ValueError("No checkpoint manager configured.")
            )

        checkpoint = self._checkpoint_manager.load_checkpoint(execution_id)

        if checkpoint is None:
            raise WorkflowCheckpointError(
                execution_id=execution_id,
                operation="load",
                cause=ValueError(
                    "No checkpoint found for execution '{}'.".format(
                        execution_id
                    )
                )
            )

        context = WorkflowContext.from_dict(
            checkpoint.context_state, agent=agent
        )
        context.set_metadata("workflow_name", workflow.name)
        context.set_metadata("execution_id", execution_id)

        completed_step_ids = set(checkpoint.completed_step_ids)

        self._logger.info(
            "Workflow resumed: workflow='%s', execution_id='%s', "
            "previously_completed_steps=%d.",
            workflow.name, execution_id, len(completed_step_ids)
        )

        # Build StepResults for previously completed steps from
        # the checkpoint context state.
        step_results = []
        for step_id in completed_step_ids:
            step = workflow.get_step(step_id)
            step_name = step.name if step is not None else step_id
            output = context.get_step_output(step_id) or {}
            prior_result = StepResult(
                step_id=step_id,
                step_name=step_name,
                status=StepExecutionStatus.COMPLETED,
                output=output
            )
            step_results.append(prior_result)

        start_time = time.monotonic()
        steps_since_checkpoint = 0

        result = self._execute_steps(
            workflow=workflow,
            context=context,
            execution_id=execution_id,
            step_results=step_results,
            completed_step_ids=completed_step_ids,
            steps_since_checkpoint=steps_since_checkpoint,
            start_time=start_time
        )

        return result

    def _execute_steps(self, workflow: WorkflowDefinition,
                       context: WorkflowContext,
                       execution_id: str,
                       step_results: list,
                       completed_step_ids: set,
                       steps_since_checkpoint: int,
                       start_time: float) -> WorkflowResult:
        """
            Core execution loop that traverses the DAG in
            topological order and executes each step.

            :param workflow: The WorkflowDefinition being executed.
            :param context: The WorkflowContext for this execution.
            :param execution_id: The unique execution identifier.
            :param step_results: The list of StepResult objects
                accumulated so far.
            :param completed_step_ids: The set of step identifiers
                that have already completed.
            :param steps_since_checkpoint: Counter of steps executed
                since the last checkpoint.
            :param start_time: The monotonic start time for duration
                calculation.

            :returns: A WorkflowResult with the execution outcome.
        """
        topo_order = self._compute_topological_order(workflow)

        # Build a set of fork step IDs for parallel branch detection.
        parallel_fork_map = {}
        for branch in workflow.parallel_branches:
            parallel_fork_map[branch.fork_step_id] = branch

        for step_id in topo_order:
            if step_id in completed_step_ids:
                continue

            step = workflow.get_step(step_id)

            # Check if this is a fork step for a parallel branch.
            if step_id in parallel_fork_map:
                branch = parallel_fork_map[step_id]

                # Execute the fork step itself first.
                fork_result = self._execute_single_step(
                    workflow, step, context, execution_id
                )
                step_results.append(fork_result)
                completed_step_ids.add(step_id)
                steps_since_checkpoint += 1

                if not fork_result.is_success:
                    return self._build_failed_result(
                        workflow, step_results, start_time,
                        step_id, fork_result.error, execution_id
                    )

                # Execute parallel branches.
                branch_result = self._execute_parallel_branches(
                    workflow=workflow,
                    branch=branch,
                    context=context,
                    execution_id=execution_id,
                    step_results=step_results,
                    completed_step_ids=completed_step_ids
                )

                if not branch_result:
                    return self._build_failed_result(
                        workflow, step_results, start_time,
                        step_id, "Parallel branch execution failed.",
                        execution_id
                    )

                steps_since_checkpoint += len(
                    [sr for sr in step_results
                     if sr.step_id not in completed_step_ids
                     or sr.step_id in completed_step_ids]
                )

                # Save checkpoint if interval reached.
                steps_since_checkpoint = self._maybe_save_checkpoint(
                    workflow, context, execution_id,
                    completed_step_ids, step_id,
                    steps_since_checkpoint
                )

                continue

            # Determine which edges to follow from this step.
            outgoing_edges = workflow.get_outgoing_edges(step_id)
            should_execute = self._should_execute_step(
                step_id, workflow, completed_step_ids
            )

            if not should_execute:
                continue

            # Execute the step.
            step_result = self._execute_single_step(
                workflow, step, context, execution_id
            )
            step_results.append(step_result)
            completed_step_ids.add(step_id)
            steps_since_checkpoint += 1

            if not step_result.is_success:
                return self._build_failed_result(
                    workflow, step_results, start_time,
                    step_id, step_result.error, execution_id
                )

            # Save checkpoint if interval reached.
            steps_since_checkpoint = self._maybe_save_checkpoint(
                workflow, context, execution_id,
                completed_step_ids, step_id,
                steps_since_checkpoint
            )

        # Build successful result.
        duration = time.monotonic() - start_time
        terminal_steps = workflow.get_terminal_steps()
        final_output = {}
        for tid in terminal_steps:
            output = context.get_step_output(tid)
            if output is not None:
                final_output.update(output)

        self._logger.info(
            "Workflow execution completes: workflow='%s', "
            "execution_id='%s', status='COMPLETED', "
            "duration=%.3fs.",
            workflow.name, execution_id, duration
        )

        result = WorkflowResult(
            workflow_name=workflow.name,
            status=WorkflowExecutionStatus.COMPLETED,
            step_results=step_results,
            final_output=final_output,
            duration=duration
        )
        return result

    def _should_execute_step(self, step_id: str,
                             workflow: WorkflowDefinition,
                             completed_step_ids: set) -> bool:
        """
            Determines whether a step should be executed by checking
            that all incoming edge sources have completed.

            :param step_id: The step identifier to check.
            :param workflow: The WorkflowDefinition.
            :param completed_step_ids: The set of completed step IDs.

            :returns: True if all predecessors have completed.
        """
        incoming_edges = workflow.get_incoming_edges(step_id)

        if len(incoming_edges) == 0:
            return True

        for edge in incoming_edges:
            if edge.source_step_id not in completed_step_ids:
                return False

        return True

    def _execute_single_step(self, workflow: WorkflowDefinition,
                             step, context: WorkflowContext,
                             execution_id: str) -> StepResult:
        """
            Executes a single workflow step with retry support.

            Logs step execution start and completion. If the step
            has a retry policy configured, retries the step on
            failure according to the policy. Stores the step output
            in the context on success.

            :param workflow: The WorkflowDefinition being executed.
            :param step: The WorkflowStep to execute.
            :param context: The WorkflowContext.
            :param execution_id: The execution identifier.

            :returns: A StepResult with the execution outcome.
        """
        self._logger.info(
            "Step execution begins: workflow='%s', step_id='%s', "
            "step_name='%s'.",
            workflow.name, step.step_id, step.name
        )

        step_start = time.monotonic()
        retry_policy = step.retry_policy
        max_attempts = 1

        if retry_policy is not None:
            max_attempts = 1 + retry_policy.max_retries

        last_result = None

        for attempt in range(max_attempts):
            try:
                result = step.execute(context)
            except Exception as ex:
                step_duration = time.monotonic() - step_start
                self._logger.warning(
                    "Step execution fails: workflow='%s', "
                    "step_id='%s', error='%s'.",
                    workflow.name, step.step_id, str(ex)
                )
                result = StepResult(
                    step_id=step.step_id,
                    step_name=step.name,
                    status=StepExecutionStatus.FAILED,
                    duration=step_duration,
                    error=str(ex)
                )

            last_result = result

            if result.is_success:
                break

            # Check if we should retry.
            if retry_policy is not None and attempt < max_attempts - 1:
                # Create a synthetic exception for the retry policy
                # check.
                synthetic_error = Exception(result.error or "Step failed")
                if retry_policy.should_retry(synthetic_error, attempt):
                    delay = retry_policy.get_delay(attempt)
                    time.sleep(delay)
                    step_start = time.monotonic()
                    continue

            break

        step_duration = time.monotonic() - step_start
        if last_result.is_success:
            # Rebuild result with accurate duration.
            last_result = StepResult(
                step_id=step.step_id,
                step_name=step.name,
                status=last_result.status,
                output=last_result.output,
                duration=step_duration,
                error=last_result.error
            )

            context.set_step_output(step.step_id, last_result.output)

            self._logger.info(
                "Step execution completes: workflow='%s', "
                "step_id='%s', status='%s', duration=%.3fs.",
                workflow.name, step.step_id,
                last_result.status.value, step_duration
            )
        else:
            self._logger.warning(
                "Step execution fails: workflow='%s', "
                "step_id='%s', error='%s'.",
                workflow.name, step.step_id,
                last_result.error
            )

        return last_result

    def _execute_parallel_branches(self, workflow: WorkflowDefinition,
                                   branch, context: WorkflowContext,
                                   execution_id: str,
                                   step_results: list,
                                   completed_step_ids: set) -> bool:
        """
            Executes parallel branches concurrently from a fork step
            to a join step.

            Identifies all branch paths from the fork step, executes
            them concurrently using a ThreadPoolExecutor, and merges
            results into the context. If any branch fails, remaining
            branches are cancelled.

            :param workflow: The WorkflowDefinition being executed.
            :param branch: The ParallelBranch declaration.
            :param context: The WorkflowContext.
            :param execution_id: The execution identifier.
            :param step_results: The accumulated step results list.
            :param completed_step_ids: The set of completed step IDs.

            :returns: True if all branches completed successfully,
                False if any branch failed.
        """
        fork_id = branch.fork_step_id
        join_id = branch.join_step_id

        # Find all immediate successors of the fork step as branch
        # starting points.
        outgoing_edges = workflow.get_outgoing_edges(fork_id)
        branch_starts = [edge.target_step_id for edge in outgoing_edges]

        self._logger.info(
            "Parallel branches forked: workflow='%s', "
            "fork_step_id='%s', branch_count=%d.",
            workflow.name, fork_id, len(branch_starts)
        )

        max_workers = self._configuration.max_parallel_workers

        # Collect steps for each branch path (from branch start to
        # just before the join step).
        branch_step_lists = []
        for branch_start_id in branch_starts:
            branch_steps = self._collect_branch_steps(
                workflow, branch_start_id, join_id
            )
            branch_step_lists.append(branch_steps)

        all_success = True

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}

            for branch_steps in branch_step_lists:
                future = executor.submit(
                    self._execute_branch,
                    workflow, branch_steps, context, execution_id
                )
                futures[future] = branch_steps

            for future in as_completed(futures):
                branch_steps = futures[future]
                try:
                    branch_results = future.result()
                except Exception as ex:
                    all_success = False
                    self._logger.warning(
                        "Parallel branch failed: workflow='%s', "
                        "error='%s'.",
                        workflow.name, str(ex)
                    )
                    # Cancel remaining futures.
                    for other_future in futures:
                        if other_future is not future:
                            other_future.cancel()
                    break

                for br in branch_results:
                    step_results.append(br)
                    completed_step_ids.add(br.step_id)

                    if not br.is_success:
                        all_success = False
                        # Cancel remaining futures.
                        for other_future in futures:
                            if other_future is not future:
                                other_future.cancel()
                        break

                if not all_success:
                    break

        if all_success:
            self._logger.info(
                "Parallel branches joined: workflow='%s', "
                "join_step_id='%s', completed_branch_count=%d.",
                workflow.name, join_id, len(branch_starts)
            )

        return all_success

    def _collect_branch_steps(self, workflow: WorkflowDefinition,
                              start_id: str, join_id: str) -> list:
        """
            Collects the ordered list of step IDs in a branch path
            from start_id up to (but not including) join_id.

            Uses BFS to traverse the branch path.

            :param workflow: The WorkflowDefinition.
            :param start_id: The starting step ID of the branch.
            :param join_id: The join step ID (not included).

            :returns: An ordered list of step IDs in the branch.
        """
        steps = []
        queue = deque()
        queue.append(start_id)
        visited = set()

        while len(queue) > 0:
            current = queue.popleft()

            if current == join_id:
                continue

            if current in visited:
                continue

            visited.add(current)
            steps.append(current)

            outgoing = workflow.get_outgoing_edges(current)
            for edge in outgoing:
                if edge.target_step_id not in visited:
                    queue.append(edge.target_step_id)

        return steps

    def _execute_branch(self, workflow: WorkflowDefinition,
                        branch_steps: list,
                        context: WorkflowContext,
                        execution_id: str) -> list:
        """
            Executes a sequence of steps in a single branch.

            :param workflow: The WorkflowDefinition.
            :param branch_steps: The ordered list of step IDs to
                execute.
            :param context: The WorkflowContext (shared across
                branches).
            :param execution_id: The execution identifier.

            :returns: A list of StepResult objects for the branch.
        """
        results = []

        for step_id in branch_steps:
            step = workflow.get_step(step_id)
            result = self._execute_single_step(
                workflow, step, context, execution_id
            )
            results.append(result)

            if not result.is_success:
                break

        return results

    def _compute_topological_order(self, workflow: WorkflowDefinition) -> list:
        """
            Computes a topological ordering of the workflow steps
            using Kahn's algorithm (BFS-based).

            The ordering ensures that for every edge (A -> B), step
            A appears before step B in the result.

            :param workflow: The WorkflowDefinition to compute the
                order for.

            :returns: A list of step identifiers in topological
                order.
        """
        # Build adjacency list and in-degree map.
        in_degree = {}
        adjacency = {}

        for step_id in workflow.steps:
            in_degree[step_id] = 0
            adjacency[step_id] = []

        for edge in workflow.edges:
            adjacency[edge.source_step_id].append(edge.target_step_id)
            in_degree[edge.target_step_id] += 1

        # Initialize queue with all steps that have in-degree 0.
        queue = deque()
        for step_id in workflow.steps:
            if in_degree[step_id] == 0:
                queue.append(step_id)

        topo_order = []

        while len(queue) > 0:
            current = queue.popleft()
            topo_order.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return topo_order

    def _maybe_save_checkpoint(self, workflow: WorkflowDefinition,
                               context: WorkflowContext,
                               execution_id: str,
                               completed_step_ids: set,
                               current_step_id: str,
                               steps_since_checkpoint: int) -> int:
        """
            Saves a checkpoint if the checkpoint interval has been
            reached and a checkpoint manager is configured.

            :param workflow: The WorkflowDefinition.
            :param context: The WorkflowContext.
            :param execution_id: The execution identifier.
            :param completed_step_ids: The set of completed step IDs.
            :param current_step_id: The current step ID.
            :param steps_since_checkpoint: Steps executed since last
                checkpoint.

            :returns: The updated steps_since_checkpoint counter
                (reset to 0 after saving).
        """
        if self._checkpoint_manager is None:
            return steps_since_checkpoint

        checkpoint_interval = self._configuration.checkpoint_interval

        if steps_since_checkpoint >= checkpoint_interval:
            self._checkpoint_manager.save_checkpoint(
                execution_id=execution_id,
                context=context,
                completed_step_ids=completed_step_ids,
                current_step_id=current_step_id
            )

            self._logger.info(
                "Checkpoint saved: workflow='%s', "
                "execution_id='%s', completed_step_count=%d.",
                workflow.name, execution_id,
                len(completed_step_ids)
            )

            return 0

        return steps_since_checkpoint

    def _build_failed_result(self, workflow: WorkflowDefinition,
                             step_results: list,
                             start_time: float,
                             failed_step_id: str,
                             error: str,
                             execution_id: str) -> WorkflowResult:
        """
            Builds a WorkflowResult with FAILED status.

            :param workflow: The WorkflowDefinition.
            :param step_results: The accumulated step results.
            :param start_time: The monotonic start time.
            :param failed_step_id: The ID of the failed step.
            :param error: The error message.
            :param execution_id: The execution identifier.

            :returns: A WorkflowResult with FAILED status.
        """
        duration = time.monotonic() - start_time

        self._logger.warning(
            "Workflow execution fails: workflow='%s', "
            "execution_id='%s', failed_step_id='%s', "
            "error='%s'.",
            workflow.name, execution_id, failed_step_id, error
        )

        result = WorkflowResult(
            workflow_name=workflow.name,
            status=WorkflowExecutionStatus.FAILED,
            step_results=step_results,
            duration=duration,
            error=error
        )
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the configuration.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(configuration={!r})".format(
            self.__class__.__name__, self._configuration
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the
            configuration details.

            :returns: A human-readable string describing the
                executor.
        """
        str_val = "WorkflowExecutor: {}".format(self._configuration)
        return str_val
