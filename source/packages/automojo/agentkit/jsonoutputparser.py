"""
    Defines the JsonOutputParser class for parsing LLM response text as JSON.

    JsonOutputParser extends OutputParser to handle JSON-formatted LLM
    responses. It uses json.loads to parse the raw text and raises
    LLMResponseParsingError when the text is not valid JSON.
"""

import json

from automojo.agentkit.llmerrors import LLMResponseParsingError
from automojo.agentkit.outputparser import OutputParser
from automojo.agentkit.outputschema import OutputSchema


class JsonOutputParser(OutputParser):
    """
        Parses LLM response text as JSON.

        Extends OutputParser with JSON-specific parsing logic. Optionally
        validates the parsed result against an OutputSchema if one was
        provided at construction time.

        :param schema: Optional OutputSchema for post-parse validation.
    """

    def __init__(self, schema: OutputSchema = None) -> None:
        super().__init__(schema=schema)
        return

    def _parse_raw(self, raw_text: str) -> object:
        """
            Parses the raw text as JSON.

            :param raw_text: The raw LLM response text.

            :returns: A Python dictionary or list.
            :raises: LLMResponseParsingError if text is not valid JSON.
        """
        try:
            rtnval = json.loads(raw_text)
        except json.JSONDecodeError as jde:
            errmsg = "Failed to parse JSON: {}".format(str(jde))
            raise LLMResponseParsingError(
                parser_name=self.__class__.__name__,
                raw_text=raw_text,
                message=errmsg
            ) from jde

        return rtnval
