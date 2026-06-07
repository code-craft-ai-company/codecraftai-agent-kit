"""
    Defines the WorkflowStep abstract base class representing a single
    unit of work within a workflow in the Workflow & Orchestration
    feature.

    A WorkflowStep has a unique step identifier, a human-readable name,
    a step type string, optional input and output schemas, optional tags
    for categorization, and an optional retry policy. Concrete subclasses
    must implement the execute method which accepts a WorkflowContext and
    returns a StepResult.

    The base class validates that a step identifier and name are provided
    at construction time, raising a SemanticError when either is missing
    or empty.
"""

import abc

from typing import Optional

from ccai.agentkit.errors import SemanticError


class WorkflowStep(abc.ABC):
    """
        Abstract base class representing a single unit of work within
        a workflow.

        A WorkflowStep defines the interface for all workflow step
        implementations. Each step has a unique identifier, a
        human-readable name, a step type string identifying the kind
        of step, optional input and output schemas describing the
        expected data shapes, optional tags for categorization and
        discovery, and an optional retry policy for configuring
        step-level retry behavior.

        Concrete subclasses must implement the execute method which
        accepts a WorkflowContext and returns a StepResult.

        :param step_id: The unique identifier for this step within
            the workflow. Must not be None or empty.
        :param name: The human-readable name for this step. Must
            not be None or empty.
        :param step_type: A string identifying the kind of step
            (e.g. "tool", "llm", "agent", "approval", "subworkflow").
        :param input_schema: An optional dictionary describing the
            expected input data shape. Defaults to an empty dictionary.
        :param output_schema: An optional dictionary describing the
            expected output data shape. Defaults to an empty dictionary.
        :param tags: An optional dictionary of tags for categorization
            and discovery. Defaults to an empty dictionary.
        :param retry_policy: An optional retry policy for configuring
            step-level retry behavior. Defaults to None.

        :raises SemanticError: When step_id is None or empty after
            stripping whitespace.
        :raises SemanticError: When name is None or empty after
            stripping whitespace.
    """

    def __init__(self, step_id: str, name: str, step_type: str,
                 input_schema: Optional[dict] = None,
                 output_schema: Optional[dict] = None,
                 tags: Optional[dict] = None,
                 retry_policy=None) -> None:
        self._step_id = step_id
        self._name = name
        self._step_type = step_type
        self._input_schema = dict(input_schema) if input_schema is not None else {}
        self._output_schema = dict(output_schema) if output_schema is not None else {}
        self._tags = dict(tags) if tags is not None else {}
        self._retry_policy = retry_policy

        if self._step_id is None or len(self._step_id.strip()) == 0:
            errmsg = "A step identifier is required."
            raise SemanticError(errmsg)

        if self._name is None or len(self._name.strip()) == 0:
            errmsg = "A step name is required."
            raise SemanticError(errmsg)

        return

    @property
    def step_id(self) -> str:
        """
            The unique identifier for this step within the workflow.

            :returns: The step identifier string.
        """
        return self._step_id

    @property
    def name(self) -> str:
        """
            The human-readable name for this step.

            :returns: The step name string.
        """
        return self._name

    @property
    def step_type(self) -> str:
        """
            A string identifying the kind of step.

            :returns: The step type string.
        """
        return self._step_type

    @property
    def input_schema(self) -> dict:
        """
            The dictionary describing the expected input data shape
            for this step.

            :returns: A dictionary of input schema fields. Empty
                dictionary when no input schema was provided.
        """
        return self._input_schema

    @property
    def output_schema(self) -> dict:
        """
            The dictionary describing the expected output data shape
            for this step.

            :returns: A dictionary of output schema fields. Empty
                dictionary when no output schema was provided.
        """
        return self._output_schema

    @property
    def tags(self) -> dict:
        """
            The dictionary of tags for categorization and discovery.

            :returns: A dictionary of tag key-value pairs. Empty
                dictionary when no tags were provided.
        """
        return self._tags

    @property
    def retry_policy(self):
        """
            The optional retry policy for configuring step-level
            retry behavior.

            :returns: The retry policy object or None when no retry
                policy was configured.
        """
        return self._retry_policy

    @abc.abstractmethod
    def execute(self, context) -> "StepResult":
        """
            Executes this step using the provided workflow context.

            Concrete subclasses must implement this method to perform
            the step's unit of work. The method receives the current
            WorkflowContext containing workflow inputs and prior step
            outputs, and returns a StepResult describing the execution
            outcome.

            :param context: The WorkflowContext with inputs and prior
                step outputs.

            :returns: A StepResult with the execution outcome.
        """
        ...

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, step identifier, step name, and step type.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(step_id={!r}, name={!r}, step_type={!r})".format(
            self.__class__.__name__, self._step_id, self._name,
            self._step_type
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the step name
            and step type.

            :returns: A human-readable string describing the workflow
                step.
        """
        str_val = "WorkflowStep: {} [type: {}]".format(
            self._name, self._step_type
        )
        return str_val
