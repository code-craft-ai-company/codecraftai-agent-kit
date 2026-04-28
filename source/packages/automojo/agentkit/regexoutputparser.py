"""
    Defines the RegexOutputParser class for extracting structured data
    from LLM response text using regular expressions.

    RegexOutputParser extends OutputParser to handle regex-based extraction
    of named capture groups from LLM responses. It compiles the pattern
    at construction time and raises LLMResponseParsingError when the
    pattern does not match the response text.
"""

import re

from automojo.agentkit.llmerrors import LLMResponseParsingError
from automojo.agentkit.outputparser import OutputParser
from automojo.agentkit.outputschema import OutputSchema


class RegexOutputParser(OutputParser):
    """
        Extracts structured data from LLM response text using a regular
        expression pattern with named capture groups.

        The pattern is compiled at construction time. The _parse_raw method
        searches the raw text for a match and returns the named group
        dictionary. Optionally validates the parsed result against an
        OutputSchema if one was provided at construction time.

        :param pattern: A regex pattern string with named capture groups.
        :param schema: Optional OutputSchema for post-parse validation.
    """

    def __init__(self, pattern: str, schema: OutputSchema = None) -> None:
        super().__init__(schema=schema)
        self._pattern = pattern
        self._compiled = re.compile(pattern)
        return

    @property
    def pattern(self) -> str:
        """
            The regex pattern string.

            :returns: The pattern string.
        """
        rtnval = self._pattern
        return rtnval

    def _parse_raw(self, raw_text: str) -> object:
        """
            Matches the pattern against the raw text and returns named groups.

            :param raw_text: The raw LLM response text.

            :returns: A dictionary of named capture group matches.
            :raises: LLMResponseParsingError if pattern does not match.
        """
        match = self._compiled.search(raw_text)

        if match is None:
            errmsg = "Regex pattern {!r} did not match the response text.".format(self._pattern)
            raise LLMResponseParsingError(
                parser_name=self.__class__.__name__,
                raw_text=raw_text,
                message=errmsg
            )

        rtnval = match.groupdict()
        return rtnval
