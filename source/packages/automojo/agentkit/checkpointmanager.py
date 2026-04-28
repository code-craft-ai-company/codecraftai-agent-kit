"""
    Defines the CheckpointManager class responsible for persisting
    and restoring WorkflowExecution state at configurable checkpoint
    boundaries using a MemoryStore backend.

    The CheckpointManager serializes WorkflowCheckpoint objects to
    JSON and stores them as MemoryEntry objects in the MemoryStore.
    It provides save, load, list, and delete operations for
    checkpoint management.
"""

import logging

from automojo.agentkit.memoryentry import MemoryEntry
from automojo.agentkit.memoryquery import MemoryQuery
from automojo.agentkit.memoryscope import MemoryScope
from automojo.agentkit.workflowcheckpoint import WorkflowCheckpoint
from automojo.agentkit.workflowcontext import WorkflowContext
from automojo.agentkit.workflowerrors import WorkflowCheckpointError


class CheckpointManager:
    """
        Persists and restores WorkflowExecution state at configurable
        checkpoint boundaries using a MemoryStore backend.

        The CheckpointManager uses a MemoryStore to persist
        WorkflowCheckpoint objects as MemoryEntry instances. Each
        checkpoint is serialized to JSON and stored with the
        execution identifier as the entry identifier. Checkpoints
        are tagged with the workflow name for efficient lookup.

        :param memory_store: The MemoryStore instance used for
            persisting checkpoint data.
    """

    def __init__(self, memory_store) -> None:
        self._memory_store = memory_store
        self._logger = logging.getLogger("automojo.agentkit.workflow.checkpoint")
        return

    def save_checkpoint(self, execution_id: str, context: WorkflowContext,
                        completed_step_ids: set, current_step_id: str) -> None:
        """
            Persists a WorkflowCheckpoint to the MemoryStore.

            Creates a WorkflowCheckpoint from the provided execution
            state, serializes it to JSON, and stores it as a
            MemoryEntry in the MemoryStore. The execution identifier
            is used as the MemoryEntry identifier for direct
            retrieval.

            :param execution_id: The unique identifier of the
                workflow execution.
            :param context: The current WorkflowContext containing
                inputs, step outputs, and metadata.
            :param completed_step_ids: The set of step identifiers
                that have completed execution.
            :param current_step_id: The identifier of the step
                that is currently executing or about to execute.

            :raises: WorkflowCheckpointError when the save
                operation fails.
        """
        try:
            context_state = context.as_dict()
            workflow_name = context.get_metadata("workflow_name", "unknown")

            checkpoint = WorkflowCheckpoint(
                workflow_name=workflow_name,
                execution_id=execution_id,
                completed_step_ids=completed_step_ids,
                context_state=context_state,
                current_step_id=current_step_id
            )

            checkpoint_json = checkpoint.to_json()

            entry = MemoryEntry(
                content=checkpoint_json,
                scope=MemoryScope.AGENT,
                identifier=execution_id,
                metadata={
                    "type": "workflow_checkpoint",
                    "workflow_name": workflow_name,
                    "execution_id": execution_id
                },
                tags=["workflow_checkpoint", workflow_name]
            )

            if self._memory_store.contains(execution_id):
                self._memory_store.update(execution_id, entry)
            else:
                self._memory_store.store(entry)

            completed_count = len(completed_step_ids)
            self._logger.info(
                "Checkpoint saved for workflow '%s', execution '%s', "
                "%d completed steps.",
                workflow_name, execution_id, completed_count
            )

        except WorkflowCheckpointError:
            raise
        except Exception as ex:
            raise WorkflowCheckpointError(
                execution_id=execution_id,
                operation="save",
                cause=ex
            )

        return

    def load_checkpoint(self, execution_id: str) -> WorkflowCheckpoint:
        """
            Returns the most recent WorkflowCheckpoint for the
            execution, or None when no checkpoint exists.

            Retrieves the MemoryEntry by execution identifier and
            deserializes the checkpoint JSON content back into a
            WorkflowCheckpoint instance.

            :param execution_id: The unique identifier of the
                workflow execution.

            :returns: A WorkflowCheckpoint instance or None when
                no checkpoint exists for the execution.

            :raises: WorkflowCheckpointError when the load
                operation fails.
        """
        try:
            entry = self._memory_store.retrieve(execution_id)

            if entry is None:
                rtnval = None
                return rtnval

            rtnval = WorkflowCheckpoint.from_json(entry.content)
            return rtnval

        except WorkflowCheckpointError:
            raise
        except Exception as ex:
            raise WorkflowCheckpointError(
                execution_id=execution_id,
                operation="load",
                cause=ex
            )

    def list_checkpoints(self, workflow_name: str) -> list:
        """
            Returns checkpoints for the workflow, ordered by
            timestamp descending.

            Searches the MemoryStore for entries tagged with the
            workflow name and the workflow_checkpoint tag, then
            deserializes each entry into a WorkflowCheckpoint and
            sorts by timestamp descending.

            :param workflow_name: The name of the workflow whose
                checkpoints to list.

            :returns: A list of WorkflowCheckpoint objects ordered
                by timestamp descending.
        """
        query = MemoryQuery(
            tags=["workflow_checkpoint", workflow_name]
        )

        result = self._memory_store.search(query)

        checkpoints = []
        for entry in result.entries:
            checkpoint = WorkflowCheckpoint.from_json(entry.content)
            checkpoints.append(checkpoint)

        checkpoints.sort(key=lambda cp: cp.timestamp, reverse=True)

        rtnval = checkpoints
        return rtnval

    def delete_checkpoint(self, execution_id: str) -> None:
        """
            Removes all checkpoints for the execution from the
            MemoryStore.

            :param execution_id: The unique identifier of the
                workflow execution whose checkpoints to remove.
        """
        if self._memory_store.contains(execution_id):
            self._memory_store.delete(execution_id)

        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the MemoryStore name.

            :returns: A repr string for debugging.
        """
        store_name = getattr(self._memory_store, "store_name", "unknown")
        repr_str = "{}(memory_store={!r})".format(
            self.__class__.__name__, store_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the
            MemoryStore name.

            :returns: A human-readable string describing the
                checkpoint manager.
        """
        store_name = getattr(self._memory_store, "store_name", "unknown")
        str_val = "CheckpointManager: store={}".format(store_name)
        return str_val
