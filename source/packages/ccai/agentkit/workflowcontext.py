"""
    Defines the WorkflowContext class representing a mutable object
    that carries shared state across workflow steps during execution
    in the Workflow & Orchestration feature.

    A WorkflowContext contains the workflow input dictionary,
    accumulated step outputs keyed by step identifier, workflow-level
    metadata, and a reference to the executing Agent. The class
    provides JSON serialization and dictionary-based deserialization
    for checkpoint persistence and state reconstruction.
"""

import json

from typing import Optional


class WorkflowContext:
    """
        Mutable object carrying shared state across workflow steps
        during execution.

        A WorkflowContext holds the workflow input dictionary,
        accumulated step outputs keyed by step identifier,
        workflow-level metadata, and a reference to the executing
        Agent. Steps read inputs and prior step outputs from the
        context and write their own outputs back into it. The
        context is scoped to a single workflow execution and is
        not shared across executions.

        :param inputs: A dictionary of workflow input values. When
            None is provided, defaults to an empty dictionary.
        :param agent: An optional reference to the executing Agent
            instance. Defaults to None.
        :param metadata: An optional dictionary of workflow-level
            metadata. When None is provided, defaults to an empty
            dictionary.
    """

    def __init__(self, inputs: dict, agent=None,
                 metadata: Optional[dict] = None) -> None:
        self._inputs = dict(inputs) if inputs is not None else {}
        self._agent = agent
        self._metadata = dict(metadata) if metadata is not None else {}
        self._step_outputs = {}
        return

    @property
    def inputs(self) -> dict:
        """
            The workflow input dictionary.

            :returns: A dictionary of workflow input values.
        """
        return self._inputs

    @property
    def agent(self):
        """
            The reference to the executing Agent instance.

            :returns: The Agent instance or None when no agent
                is associated with this context.
        """
        return self._agent

    @property
    def step_outputs(self) -> dict:
        """
            The dictionary of completed step outputs keyed by
            step identifier.

            :returns: A dictionary mapping step identifiers to
                their output dictionaries.
        """
        return self._step_outputs

    @property
    def metadata(self) -> dict:
        """
            The workflow-level metadata dictionary.

            :returns: A dictionary of metadata key-value pairs.
        """
        return self._metadata

    def get_input(self, field_name: str, default=None):
        """
            Returns the value from the workflow input dictionary
            for the given field name, or the default value when
            the field is not present.

            :param field_name: The name of the input field to
                retrieve.
            :param default: The value to return when the field
                is not present. Defaults to None.

            :returns: The input field value or the default value.
        """
        rtnval = self._inputs.get(field_name, default)
        return rtnval

    def get_step_output(self, step_id: str) -> Optional[dict]:
        """
            Returns the output dictionary for the completed step
            with the given identifier, or None when the step has
            not completed.

            :param step_id: The unique identifier of the step
                whose output to retrieve.

            :returns: The step output dictionary or None when the
                step has not completed.
        """
        rtnval = self._step_outputs.get(step_id, None)
        return rtnval

    def set_step_output(self, step_id: str, output: dict) -> None:
        """
            Stores the output dictionary for a completed step in
            the context, keyed by the step identifier.

            :param step_id: The unique identifier of the step.
            :param output: The output dictionary produced by the
                step execution.
        """
        self._step_outputs[step_id] = output
        return

    def get_metadata(self, key: str, default=None):
        """
            Returns the metadata value for the given key, or the
            default value when the key is not present.

            :param key: The metadata key string to retrieve.
            :param default: The value to return when the key is
                not present. Defaults to None.

            :returns: The metadata value or the default value.
        """
        rtnval = self._metadata.get(key, default)
        return rtnval

    def set_metadata(self, key: str, value) -> None:
        """
            Stores a metadata value in the context under the given
            key.

            :param key: The metadata key string.
            :param value: The metadata value to store.
        """
        self._metadata[key] = value
        return

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the context state
            including inputs, step_outputs, and metadata.

            The agent reference is not included in the dictionary
            representation because it is not serializable and must
            be provided separately when reconstructing a context
            from a dictionary.

            :returns: A dictionary containing inputs, step_outputs,
                and metadata.
        """
        rtnval = {
            "inputs": self._inputs,
            "step_outputs": self._step_outputs,
            "metadata": self._metadata
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the context
            state.

            Serializes the as_dict output to a JSON string. The
            agent reference is not included in the serialized
            output.

            :returns: A JSON string containing inputs, step_outputs,
                and metadata.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict, agent=None) -> "WorkflowContext":
        """
            Constructs a WorkflowContext from a dictionary
            representation.

            Reconstructs the context from a dictionary containing
            inputs, step_outputs, and metadata fields. The agent
            reference is accepted as a separate parameter because
            it is not included in the serialized representation.

            :param data: A dictionary containing inputs, step_outputs,
                and metadata fields.
            :param agent: An optional reference to the executing Agent
                instance. Defaults to None.

            :returns: A WorkflowContext instance reconstructed from
                the dictionary data.
        """
        inputs = data.get("inputs", {})
        metadata = data.get("metadata", {})

        context = cls(inputs=inputs, agent=agent, metadata=metadata)

        step_outputs = data.get("step_outputs", {})
        for step_id, output in step_outputs.items():
            context.set_step_output(step_id, output)

        return context

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, the count of completed steps, and the count
            of input fields.

            :returns: A repr string for debugging.
        """
        completed_count = len(self._step_outputs)
        input_count = len(self._inputs)
        repr_str = "{}(completed_steps={}, input_fields={})".format(
            self.__class__.__name__, completed_count, input_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count of
            completed steps and input field names.

            :returns: A human-readable string describing the workflow
                context.
        """
        completed_count = len(self._step_outputs)
        input_names = list(self._inputs.keys())
        str_val = "WorkflowContext: {} completed steps, inputs: {}".format(
            completed_count, input_names
        )
        return str_val
