"""
    Defines the LLMStep class, a concrete WorkflowStep that executes
    an LLM completion request through the Agent's LLMProviderRegistry
    during workflow execution.

    LLMStep renders a prompt from the WorkflowContext using either a
    prompt template or a static prompt string, constructs an
    LLMConversation, executes the completion request through the
    Agent's complete method, optionally parses the response with an
    OutputParser, and returns a StepResult containing the LLMResponse
    content or a FAILED status on failure.

    .. module:: automojo.agentkit.steps.llmstep
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Built-in workflow step for LLM completion execution.
"""

import logging
import time

from typing import Optional

from automojo.agentkit.stepexecutionstatus import StepExecutionStatus
from automojo.agentkit.stepresult import StepResult
from automojo.agentkit.workflowcontext import WorkflowContext
from automojo.agentkit.workflowstep import WorkflowStep


class _AttributeDict:
    """
        A lightweight wrapper around a dictionary that exposes keys
        as attributes. Used internally by LLMStep to support dotted
        reference resolution in prompt templates via str.format_map.

        For example, given a dictionary {"text": "hello"}, accessing
        .text on this wrapper returns "hello".
    """

    def __init__(self, data: dict) -> None:
        self._data = data
        return

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        if name in self._data:
            value = self._data[name]

            if isinstance(value, dict):
                return _AttributeDict(value)

            return value

        raise AttributeError(
            "_AttributeDict has no attribute {!r}".format(name)
        )

    def __repr__(self) -> str:
        return "_AttributeDict({!r})".format(self._data)


def _build_format_namespace(context) -> dict:
    """
        Builds a format namespace dictionary for prompt template
        rendering from a WorkflowContext.

        Returns a dictionary with "inputs" and "steps" keys, each
        mapped to an _AttributeDict wrapper that supports
        attribute-style access for str.format_map resolution.

        :param context: The WorkflowContext to build the namespace
            from.

        :returns: A dictionary suitable for str.format_map.
    """
    inputs_wrapper = _AttributeDict(context.inputs)

    steps_dict = {}
    for step_id, step_output in context.step_outputs.items():
        if isinstance(step_output, dict):
            steps_dict[step_id] = step_output
        else:
            steps_dict[step_id] = {}

    steps_wrapper = _AttributeDict(steps_dict)

    namespace = {
        "inputs": inputs_wrapper,
        "steps": steps_wrapper
    }
    return namespace


class LLMStep(WorkflowStep):
    """
        Executes an LLM completion request through the Agent's
        LLMProviderRegistry.

        LLMStep is a concrete WorkflowStep subclass that integrates
        with the LLM Integration system. At execution time, it
        renders a prompt from the WorkflowContext, constructs an
        LLMConversation with a single user message, executes the
        completion request through the Agent's complete method, and
        wraps the result in a StepResult.

        The prompt can be provided as either a prompt_template or a
        static prompt_string. When a prompt_template is provided, it
        is rendered using the WorkflowContext inputs and step outputs
        via Python string formatting. When a prompt_string is
        provided, it is used directly without rendering.

        An optional output_parser can be provided to parse the LLM
        response content into structured output. The output_parser
        must be a callable that accepts a string and returns a
        dictionary.

        :param step_id: The unique identifier for this step within
            the workflow. Must not be None or empty.
        :param name: The human-readable name for this step. Must
            not be None or empty.
        :param provider_name: The name of the LLMProvider to use
            for the completion request.
        :param model_name: The name of the model to use for the
            completion request.
        :param prompt_template: An optional prompt template string
            that supports {inputs.<field>} and
            {steps.<step_id>.<field>} references for rendering
            against the WorkflowContext. Defaults to None.
        :param prompt_string: An optional static prompt string
            used directly without rendering. Defaults to None.
        :param output_parser: An optional callable that accepts
            the LLM response content string and returns a
            dictionary of parsed output. Defaults to None.
        :param kwargs: Additional keyword arguments passed to the
            WorkflowStep base class constructor (e.g. input_schema,
            output_schema, tags, retry_policy).
    """

    def __init__(self, step_id: str, name: str, provider_name: str,
                 model_name: str, prompt_template: Optional[str] = None,
                 prompt_string: Optional[str] = None,
                 output_parser=None, **kwargs) -> None:
        super().__init__(step_id=step_id, name=name, step_type="llm", **kwargs)
        self._provider_name = provider_name
        self._model_name = model_name
        self._prompt_template = prompt_template
        self._prompt_string = prompt_string
        self._output_parser = output_parser
        self._logger = logging.getLogger("automojo.agentkit.workflow.steps.llm")
        return

    @property
    def provider_name(self) -> str:
        """
            The name of the LLMProvider to use for the completion
            request.

            :returns: The provider name string.
        """
        return self._provider_name

    @property
    def model_name(self) -> str:
        """
            The name of the model to use for the completion request.

            :returns: The model name string.
        """
        return self._model_name

    @property
    def prompt_template(self) -> Optional[str]:
        """
            The prompt template string for rendering against the
            WorkflowContext, or None when no template is configured.

            :returns: The prompt template string or None.
        """
        return self._prompt_template

    @property
    def prompt_string(self) -> Optional[str]:
        """
            The static prompt string used directly without rendering,
            or None when no static prompt is configured.

            :returns: The prompt string or None.
        """
        return self._prompt_string

    @property
    def output_parser(self):
        """
            The optional output parser callable for parsing the LLM
            response content into structured output, or None when
            no parser is configured.

            :returns: The output parser callable or None.
        """
        return self._output_parser

    def _render_prompt(self, context: WorkflowContext) -> str:
        """
            Renders the prompt from the WorkflowContext.

            When a prompt_template is configured, builds a namespace
            dictionary from the context inputs and step outputs and
            renders the template using Python string formatting.
            Template references use the form {inputs.<field>} and
            {steps.<step_id>.<field>}. The namespace objects support
            attribute-style access so that Python's str.format_map
            can resolve dotted references.

            When a prompt_string is configured, returns it directly
            without rendering.

            When neither is configured, returns an empty string.

            :param context: The WorkflowContext to render the prompt
                against.

            :returns: The rendered prompt string.
        """
        if self._prompt_template is not None:
            format_dict = _build_format_namespace(context)
            rendered_prompt = self._prompt_template.format_map(format_dict)
            return rendered_prompt

        if self._prompt_string is not None:
            return self._prompt_string

        return ""

    def execute(self, context: WorkflowContext) -> StepResult:
        """
            Executes this LLMStep using the provided workflow context.

            Renders the prompt from the WorkflowContext, retrieves the
            Agent from the context, constructs an LLMConversation with
            a single user message containing the rendered prompt,
            executes the completion request through the Agent's
            complete method, optionally parses the response with the
            output_parser, and returns a StepResult with the execution
            outcome.

            If the Agent is None, a StepResult with FAILED status is
            returned. If the LLM completion request fails, a StepResult
            with FAILED status and the error information is returned.
            If the output_parser fails to parse the response, a
            StepResult with FAILED status and the parsing error
            information is returned.

            :param context: The WorkflowContext with inputs and prior
                step outputs.

            :returns: A StepResult with the execution outcome.
        """
        start_time = time.monotonic()

        agent = context.agent

        if agent is None:
            duration = time.monotonic() - start_time
            errmsg = "LLMStep '{}' failed: no agent available in the workflow context.".format(
                self._name
            )
            self._logger.warning(errmsg)

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.FAILED,
                duration=duration,
                error=errmsg
            )
            return result

        # Render the prompt from the WorkflowContext
        try:
            rendered_prompt = self._render_prompt(context)
        except Exception as render_err:
            duration = time.monotonic() - start_time
            errmsg = "LLMStep '{}' failed during prompt rendering: {}".format(
                self._name, str(render_err)
            )
            self._logger.warning(errmsg)

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.FAILED,
                duration=duration,
                error=errmsg
            )
            return result

        # Construct an LLMConversation with a single user message
        from automojo.agentkit.llmconversation import LLMConversation
        from automojo.agentkit.llmmessage import LLMMessage

        user_message = LLMMessage(role="user", content=rendered_prompt)
        conversation = LLMConversation(messages=[user_message])

        # Execute the completion request through the Agent
        try:
            llm_response = agent.complete(
                provider_name=self._provider_name,
                model_name=self._model_name,
                conversation=conversation
            )
        except Exception as llm_err:
            duration = time.monotonic() - start_time
            errmsg = "LLMStep '{}' failed during LLM completion with provider '{}' model '{}': {}".format(
                self._name, self._provider_name, self._model_name, str(llm_err)
            )
            self._logger.warning(errmsg)

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.FAILED,
                duration=duration,
                error=errmsg
            )
            return result

        # Extract the response content
        response_content = llm_response.message.content

        # If an output_parser is provided, parse the response content
        if self._output_parser is not None:
            try:
                parsed_output = self._output_parser(response_content)

                if not isinstance(parsed_output, dict):
                    parsed_output = {"content": parsed_output}

                duration = time.monotonic() - start_time

                result = StepResult(
                    step_id=self._step_id,
                    step_name=self._name,
                    status=StepExecutionStatus.COMPLETED,
                    output=parsed_output,
                    duration=duration
                )
                return result

            except Exception as parse_err:
                duration = time.monotonic() - start_time
                errmsg = "LLMStep '{}' failed during output parsing: {}".format(
                    self._name, str(parse_err)
                )
                self._logger.warning(errmsg)

                result = StepResult(
                    step_id=self._step_id,
                    step_name=self._name,
                    status=StepExecutionStatus.FAILED,
                    duration=duration,
                    error=errmsg
                )
                return result

        # No output_parser: return the raw response content
        duration = time.monotonic() - start_time
        output = {"content": response_content}

        result = StepResult(
            step_id=self._step_id,
            step_name=self._name,
            status=StepExecutionStatus.COMPLETED,
            output=output,
            duration=duration
        )
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, step identifier, step name, provider name,
            and model name.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(step_id={!r}, name={!r}, provider_name={!r}, model_name={!r})".format(
            self.__class__.__name__, self._step_id, self._name,
            self._provider_name, self._model_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the step name,
            provider name, and model name.

            :returns: A human-readable string describing the LLM step.
        """
        rtnval = "LLMStep: {} [provider: {}, model: {}]".format(
            self._name, self._provider_name, self._model_name
        )
        return rtnval
