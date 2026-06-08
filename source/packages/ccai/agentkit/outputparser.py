"""
    Defines the OutputParser abstract base class for parsing raw LLM
    response text into structured Python objects.

    OutputParser provides a two-phase parsing pipeline: subclasses implement
    the _parse_raw method for format-specific parsing, and the base class
    optionally validates the parsed result against an OutputSchema.
"""

import abc

from ccai.agentkit.llmerrors import LLMResponseParsingError
from ccai.agentkit.outputschema import OutputSchema


class OutputParser(abc.ABC):
    """
        Abstract base class for parsing raw LLM response text
        into structured Python objects.

        Subclasses must implement the _parse_raw method to handle
        format-specific parsing. The base class provides optional
        post-parse validation against an OutputSchema.

        :param schema: Optional OutputSchema for post-parse validation.
    """

    def __init__(self, schema: OutputSchema = None) -> None:
        self._schema = schema
        return

    @property
    def schema(self) -> OutputSchema:
        """
            The optional OutputSchema used for post-parse validation.

            :returns: The OutputSchema instance or None.
        """
        rtnval = self._schema
        return rtnval

    @abc.abstractmethod
    def _parse_raw(self, raw_text: str) -> object:
        """
            Parses the raw text into a Python object.
            Subclasses implement this method.

            :param raw_text: The raw LLM response text.

            :returns: A parsed Python object.
            :raises: LLMResponseParsingError
        """
        ...

    def parse(self, raw_text: str) -> object:
        """
            Parses raw text and optionally validates against the schema.

            Calls _parse_raw to perform format-specific parsing, then
            validates the result against the OutputSchema if one was
            provided at construction time.

            :param raw_text: The raw LLM response text.

            :returns: A parsed Python object.
            :raises: LLMResponseParsingError if parsing or validation fails.
        """
        parsed = self._parse_raw(raw_text)

        if self._schema is not None:
            validation_errors = self._schema.validate(parsed)
            if len(validation_errors) > 0:
                errmsg = "Output validation failed for {}: {}".format(
                    self.__class__.__name__, "; ".join(validation_errors)
                )
                raise LLMResponseParsingError(
                    parser_name=self.__class__.__name__,
                    raw_text=raw_text,
                    message=errmsg
                )

        rtnval = parsed
        return rtnval
