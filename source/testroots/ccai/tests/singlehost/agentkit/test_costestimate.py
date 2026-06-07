"""
    Unit tests for the ccai.agentkit.costestimate module.

    Tests CostEstimate construction, validation, properties, equality,
    and string representations.

    Feature: llm-integration, Task 1.5
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 19.11, 19.12**
"""

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.costestimate import CostEstimate


# ---------------------------------------------------------------------------
# Construction and validation
# ---------------------------------------------------------------------------


def test_cost_estimate_valid_construction():
    """
        CostEstimate accepts valid costs where total equals the sum.

        **Validates: Requirements 5.1, 5.3**
    """
    cost = CostEstimate(
        prompt_cost=0.01,
        completion_cost=0.02,
        total_cost=0.03
    )

    assert abs(cost.prompt_cost - 0.01) < 1e-9, (
        "prompt_cost mismatch: {}".format(cost.prompt_cost)
    )
    assert abs(cost.completion_cost - 0.02) < 1e-9, (
        "completion_cost mismatch: {}".format(cost.completion_cost)
    )
    assert abs(cost.total_cost - 0.03) < 1e-9, (
        "total_cost mismatch: {}".format(cost.total_cost)
    )

    return


def test_cost_estimate_default_currency():
    """
        CostEstimate defaults to USD currency.

        **Validates: Requirements 5.1**
    """
    cost = CostEstimate(
        prompt_cost=0.0,
        completion_cost=0.0,
        total_cost=0.0
    )

    assert cost.currency == "USD", (
        "Default currency should be USD, got: {!r}".format(cost.currency)
    )

    return


def test_cost_estimate_custom_currency():
    """
        CostEstimate accepts a custom currency string.

        **Validates: Requirements 5.1**
    """
    cost = CostEstimate(
        prompt_cost=1.0,
        completion_cost=2.0,
        total_cost=3.0,
        currency="EUR"
    )

    assert cost.currency == "EUR", (
        "Currency should be EUR, got: {!r}".format(cost.currency)
    )

    return


def test_cost_estimate_zero_values():
    """
        CostEstimate accepts all-zero cost values.

        **Validates: Requirements 5.1, 5.3**
    """
    cost = CostEstimate(
        prompt_cost=0.0,
        completion_cost=0.0,
        total_cost=0.0
    )

    assert abs(cost.total_cost) < 1e-9, "total_cost should be 0.0"

    return


def test_cost_estimate_invalid_total_raises_semantic_error():
    """
        CostEstimate raises SemanticError when total does not equal the sum.

        **Validates: Requirements 5.4**
    """
    caught = False

    try:
        CostEstimate(
            prompt_cost=0.01,
            completion_cost=0.02,
            total_cost=0.99
        )
    except SemanticError:
        caught = True

    assert caught is True, (
        "CostEstimate should raise SemanticError for mismatched total"
    )

    return


# ---------------------------------------------------------------------------
# Read-only properties
# ---------------------------------------------------------------------------


def test_cost_estimate_properties_are_read_only():
    """
        CostEstimate properties return the correct values.

        **Validates: Requirements 5.2**
    """
    cost = CostEstimate(
        prompt_cost=0.05,
        completion_cost=0.10,
        total_cost=0.15,
        currency="GBP"
    )

    assert abs(cost.prompt_cost - 0.05) < 1e-9, "prompt_cost property mismatch"
    assert abs(cost.completion_cost - 0.10) < 1e-9, "completion_cost property mismatch"
    assert abs(cost.total_cost - 0.15) < 1e-9, "total_cost property mismatch"
    assert cost.currency == "GBP", "currency property mismatch"

    return


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------


def test_cost_estimate_as_dict():
    """
        CostEstimate as_dict returns a dictionary with all cost fields.

        **Validates: Requirements 5.5**
    """
    cost = CostEstimate(
        prompt_cost=0.01,
        completion_cost=0.02,
        total_cost=0.03,
        currency="USD"
    )
    result = cost.as_dict()

    assert abs(result["prompt_cost"] - 0.01) < 1e-9, "as_dict prompt_cost mismatch"
    assert abs(result["completion_cost"] - 0.02) < 1e-9, "as_dict completion_cost mismatch"
    assert abs(result["total_cost"] - 0.03) < 1e-9, "as_dict total_cost mismatch"
    assert result["currency"] == "USD", "as_dict currency mismatch"

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__
# ---------------------------------------------------------------------------


def test_cost_estimate_repr():
    """
        CostEstimate __repr__ includes class name, total cost, and currency.

        **Validates: Requirements 5.6, 19.11**
    """
    cost = CostEstimate(
        prompt_cost=0.01,
        completion_cost=0.02,
        total_cost=0.03,
        currency="USD"
    )
    repr_str = repr(cost)

    assert "CostEstimate" in repr_str, (
        "repr should contain class name, got: {!r}".format(repr_str)
    )
    assert "0.03" in repr_str, (
        "repr should contain total cost, got: {!r}".format(repr_str)
    )
    assert "USD" in repr_str, (
        "repr should contain currency, got: {!r}".format(repr_str)
    )

    return


def test_cost_estimate_str():
    """
        CostEstimate __str__ returns a human-readable summary of costs.

        **Validates: Requirements 5.7, 19.12**
    """
    cost = CostEstimate(
        prompt_cost=0.01,
        completion_cost=0.02,
        total_cost=0.03,
        currency="USD"
    )
    str_val = str(cost)

    assert "0.03" in str_val, "str should contain total cost"
    assert "USD" in str_val, "str should contain currency"
    assert "0.01" in str_val, "str should contain prompt cost"
    assert "0.02" in str_val, "str should contain completion cost"

    return


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_cost_estimate_eq_same_values():
    """
        CostEstimate __eq__ returns True for equal cost values.

        **Validates: Requirements 5.1**
    """
    a = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    b = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)

    assert a == b, "CostEstimate with same values should be equal"

    return


def test_cost_estimate_eq_different_values():
    """
        CostEstimate __eq__ returns False for different cost values.

        **Validates: Requirements 5.1**
    """
    a = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    b = CostEstimate(prompt_cost=0.05, completion_cost=0.10, total_cost=0.15)

    assert (a == b) is False, "CostEstimate with different values should not be equal"

    return


def test_cost_estimate_eq_different_currency():
    """
        CostEstimate __eq__ returns False when currencies differ.

        **Validates: Requirements 5.1**
    """
    a = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03, currency="USD")
    b = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03, currency="EUR")

    assert (a == b) is False, "CostEstimate with different currencies should not be equal"

    return


def test_cost_estimate_eq_non_cost_estimate():
    """
        CostEstimate __eq__ returns False when compared to a non-CostEstimate object.

        **Validates: Requirements 5.1**
    """
    cost = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)

    assert (cost == "not a cost estimate") is False, (
        "CostEstimate should not be equal to a string"
    )

    return

