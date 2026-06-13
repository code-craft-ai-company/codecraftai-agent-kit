"""
    Defines the ToolExecutor class for validated tool invocation with
    credential resolution and structured logging.

    ToolExecutor validates inputs against a tool's input schema, resolves
    credential references via a credential resolver, invokes the tool's
    execute method, validates outputs against the tool's output schema,
    and returns structured ToolResult objects.
"""

import logging
import os
import time

from ccai.agentkit.errors import ConfigurationError
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.tool import Tool
from ccai.agentkit.toolerrors import ToolValidationError
from ccai.agentkit.toolresult import ToolResult


class ToolExecutor:
    """
        Validates inputs, resolves credentials, invokes tools, validates outputs,
        and returns structured ToolResult objects.

        :param credential_resolver: An optional credential resolver used to resolve
            credential references declared by tools. The resolver must support a
            resolve(name) method that returns the credential value or raises an
            exception on failure.
    """

    def __init__(self, credential_resolver=None) -> None:
        self._credential_resolver = credential_resolver
        self._logger = logging.getLogger("ccai.agentkit.tools")
        return

    def execute(self, tool: Tool, inputs: dict, agent_identifier: str = None) -> ToolResult:
        """
            Executes a tool with validated inputs and credential resolution.

            Validates the input dictionary against the tool's input schema,
            resolves any credential references declared by the tool, invokes
            the tool's execute method, validates the output against the tool's
            output schema, and returns a ToolResult with the execution outcome.

            :param tool: The Tool instance to execute.
            :param inputs: The input dictionary.
            :param agent_identifier: Optional agent identifier for logging.

            :returns: A ToolResult with the execution outcome.
            :raises: ToolValidationError, ConfigurationError
        """

        self._logger.info(
            "Executing tool '%s' for agent '%s'",
            tool.name,
            agent_identifier,
        )

        # Step 1: Validate inputs against the tool's input schema
        input_schema = tool.input_schema
        if input_schema is not None:
            input_errors = input_schema.validate(values=inputs)
            if len(input_errors) > 0:
                self._logger.warning(
                    "Tool '%s' input validation failed: %s",
                    tool.name,
                    input_errors,
                )
                raise ToolValidationError(
                    tool_name=tool.name,
                    direction="input",
                    errors=input_errors,
                )

        # Step 2: Resolve credential references
        credentials = {}
        credential_names = tool.credential_names
        if len(credential_names) > 0:
            if self._credential_resolver is not None:
                for cred_name in credential_names:
                    try:
                        resolved_value = self._credential_resolver.resolve(cred_name)
                        credentials[cred_name] = resolved_value
                    except Exception as resolve_err:
                        errmsg_lines = [
                            "Failed to resolve credential '{}' for tool '{}'.".format(
                                cred_name, tool.name
                            ),
                            "CAUSE: {}".format(str(resolve_err)),
                        ]
                        errmsg = os.linesep.join(errmsg_lines)
                        raise ConfigurationError(errmsg, cause=resolve_err) from resolve_err
            else:
                errmsg_lines = [
                    "Tool '{}' requires credentials {} but no credential resolver is configured.".format(
                        tool.name, credential_names
                    ),
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise ConfigurationError(errmsg)

        # Step 3: Execute the tool and measure duration
        start_time = time.time()

        try:
            output = tool.execute(inputs=inputs, credentials=credentials)
            end_time = time.time()
            duration = end_time - start_time

            # Step 4: Validate output against the tool's output schema
            output_schema = tool.output_schema
            if output_schema is not None:
                output_errors = output_schema.validate(values=output)
                if len(output_errors) > 0:
                    self._logger.warning(
                        "Tool '%s' output validation failed: %s",
                        tool.name,
                        output_errors,
                    )
                    raise ToolValidationError(
                        tool_name=tool.name,
                        direction="output",
                        errors=output_errors,
                    )

            # Step 5: Return success result
            self._logger.info(
                "Tool '%s' executed successfully in %.3f seconds",
                tool.name,
                duration,
            )

            rtnval = ToolResult(
                tool_name=tool.name,
                status=ToolResult.STATUS_SUCCESS,
                output=output,
                duration=duration,
            )
            return rtnval

        except ToolValidationError:
            raise

        except SemanticError:
            # SemanticError signals API misuse and must never be swallowed into
            # a failure ToolResult -- let it bubble to the caller.
            raise

        except Exception as exec_err:
            end_time = time.time()
            duration = end_time - start_time

            self._logger.warning(
                "Tool '%s' execution failed after %.3f seconds: %s",
                tool.name,
                duration,
                str(exec_err),
            )

            rtnval = ToolResult(
                tool_name=tool.name,
                status=ToolResult.STATUS_FAILURE,
                duration=duration,
                error=exec_err,
            )
            return rtnval
