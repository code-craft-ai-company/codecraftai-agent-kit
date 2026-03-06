"""
    Defines the CostEstimate class for immutable cost records.

    CostEstimate encapsulates the prompt cost, completion cost,
    total cost, and currency for a single LLM request. The total
    must equal the sum of prompt and completion costs within
    floating-point tolerance (1e-9).
"""

from automojo.agentkit.errors import SemanticError


class CostEstimate:
    """
        Immutable record of estimated cost for a single LLM request.

        Provides read-only access to prompt cost, completion cost,
        total cost, and currency. Validates that the total equals
        the sum of prompt and completion costs within floating-point
        tolerance at construction time.

        :param prompt_cost: Cost for prompt tokens.
        :param completion_cost: Cost for completion tokens.
        :param total_cost: Total cost.
        :param currency: Currency string (default "USD").
    """

    def __init__(self, prompt_cost: float, completion_cost: float,
                 total_cost: float, currency: str = "USD") -> None:
        expected_total = prompt_cost + completion_cost

        if abs(total_cost - expected_total) > 1e-9:
            errmsg = "CostEstimate total_cost ({}) does not equal prompt_cost ({}) + completion_cost ({}) = {}.".format(
                total_cost, prompt_cost, completion_cost, expected_total
            )
            raise SemanticError(errmsg)

        self._prompt_cost = prompt_cost
        self._completion_cost = completion_cost
        self._total_cost = total_cost
        self._currency = currency
        return

    @property
    def prompt_cost(self) -> float:
        """
            The cost for prompt tokens.

            :returns: The prompt cost as a float.
        """
        rtnval = self._prompt_cost
        return rtnval

    @property
    def completion_cost(self) -> float:
        """
            The cost for completion tokens.

            :returns: The completion cost as a float.
        """
        rtnval = self._completion_cost
        return rtnval

    @property
    def total_cost(self) -> float:
        """
            The total cost.

            :returns: The total cost as a float.
        """
        rtnval = self._total_cost
        return rtnval

    @property
    def currency(self) -> str:
        """
            The currency string.

            :returns: The currency string.
        """
        rtnval = self._currency
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the cost fields.

            :returns: A dictionary with prompt_cost, completion_cost,
                total_cost, and currency keys.
        """
        rtnval = {
            "prompt_cost": self._prompt_cost,
            "completion_cost": self._completion_cost,
            "total_cost": self._total_cost,
            "currency": self._currency
        }
        return rtnval

    def __eq__(self, other) -> bool:
        """
            Checks equality based on all cost fields within floating-point
            tolerance (1e-9) and exact currency match.

            :param other: The object to compare against.

            :returns: True if all cost fields are equal within tolerance
                and currency matches, False otherwise.
        """
        if not isinstance(other, CostEstimate):
            return False

        rtnval = (abs(self._prompt_cost - other._prompt_cost) < 1e-9 and
                  abs(self._completion_cost - other._completion_cost) < 1e-9 and
                  abs(self._total_cost - other._total_cost) < 1e-9 and
                  self._currency == other._currency)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            total cost, and currency.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(total={}, currency={!r})".format(
            self.__class__.__name__, self._total_cost, self._currency
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the costs.

            :returns: A human-readable string.
        """
        rtnval = "Cost: {} {} (prompt: {}, completion: {})".format(
            self._total_cost, self._currency, self._prompt_cost, self._completion_cost
        )
        return rtnval
