"""
    Defines the ConfigurationValidationResult class encapsulating the outcome
    of validating a configuration dictionary against a ConfigurationSchema
    in the automojo-agent-kit framework.

    A ConfigurationValidationResult contains a valid flag, a list of
    validation error strings, and a list of validation warning strings.
"""


class ConfigurationValidationResult:
    """
        Immutable object encapsulating the outcome of validating a configuration
        dictionary against a ConfigurationSchema.

        :param valid: A boolean flag indicating whether the configuration passed validation.
        :param errors: An optional list of validation error strings.
        :param warnings: An optional list of validation warning strings.
    """

    def __init__(self, valid: bool, errors: list = None, warnings: list = None) -> None:
        self._valid = valid

        if errors is not None:
            self._errors = list(errors)
        else:
            self._errors = []

        if warnings is not None:
            self._warnings = list(warnings)
        else:
            self._warnings = []

        return

    @property
    def valid(self) -> bool:
        """
            The boolean flag indicating whether the configuration passed validation.

            :returns: True if the configuration was marked as valid.
        """
        return self._valid

    @property
    def errors(self) -> list:
        """
            A defensive copy of the list of validation error strings.

            :returns: A list of validation error strings.
        """
        return list(self._errors)

    @property
    def warnings(self) -> list:
        """
            A defensive copy of the list of validation warning strings.

            :returns: A list of validation warning strings.
        """
        return list(self._warnings)

    @property
    def is_valid(self) -> bool:
        """
            Returns True when the valid flag is True and the error list is empty.

            :returns: True if the result is considered valid.
        """
        has_no_errors = len(self._errors) == 0
        result = self._valid is True and has_no_errors is True
        return result

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the result fields.

            :returns: A dictionary with valid, errors, and warnings.
        """
        result = {
            "valid": self._valid,
            "errors": list(self._errors),
            "warnings": list(self._warnings),
        }
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            valid flag, error count, and warning count.

            :returns: A repr string for debugging.
        """
        repr_str = "ConfigurationValidationResult(valid={}, error_count={}, warning_count={})".format(
            self._valid, len(self._errors), len(self._warnings)
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the valid flag,
            error count, warning count, and the first error message
            when errors are present.

            :returns: A human-readable string.
        """
        error_count = len(self._errors)
        warning_count = len(self._warnings)

        str_val = "ConfigurationValidationResult valid={}, errors={}, warnings={}".format(
            self._valid, error_count, warning_count
        )

        if error_count > 0:
            first_error = self._errors[0]
            str_val = "{}, first_error={!r}".format(str_val, first_error)

        return str_val
