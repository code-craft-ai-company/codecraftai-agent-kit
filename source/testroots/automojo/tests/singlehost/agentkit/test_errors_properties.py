"""
    Property-based tests for the automojo.agentkit.errors module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 24: Exception hierarchy fields and chaining

    **Validates: Requirements 14.5, 14.6, 14.7**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.errors import AgentKitError
from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.errors import LifecycleError
from automojo.agentkit.errors import SemanticError


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_message_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789 _-.",
)

_exception_classes = st.sampled_from([
    AgentKitError,
    ConfigurationError,
    SemanticError,
    LifecycleError,
])


# ---------------------------------------------------------------------------
# Property 24: Exception hierarchy fields and chaining (with cause)
# ---------------------------------------------------------------------------

@given(
    exc_class=_exception_classes,
    message=_message_strategy,
    cause_message=_message_strategy,
    constraints={"max_examples": 30},
)
def test_exception_fields_and_chaining_with_cause(
    exc_class,
    message: str,
    cause_message: str,
) -> None:
    """
        **Validates: Requirements 14.5, 14.6, 14.7**

        For any exception class constructed with a message and a cause,
        the message property matches the constructor arg, the cause property
        returns the cause, __cause__ is set, and __repr__ contains the
        class name and message.
    """
    cause = RuntimeError(cause_message)
    exc = exc_class(message, cause=cause)

    assert exc.message == message, (
        "message property mismatch for {}: expected {!r}, got {!r}".format(
            exc_class.__name__, message, exc.message)
    )

    assert exc.cause is cause, (
        "cause property should be the provided cause for {}: "
        "expected {!r}, got {!r}".format(
            exc_class.__name__, cause, exc.cause)
    )

    assert exc.__cause__ is cause, (
        "__cause__ should be set to the provided cause for {}: "
        "expected {!r}, got {!r}".format(
            exc_class.__name__, cause, exc.__cause__)
    )

    repr_str = repr(exc)

    assert exc_class.__name__ in repr_str, (
        "__repr__ should contain class name {!r}: got {!r}".format(
            exc_class.__name__, repr_str)
    )

    assert message in repr_str, (
        "__repr__ should contain message {!r}: got {!r}".format(
            message, repr_str)
    )

    return


# ---------------------------------------------------------------------------
# Property 24: Exception hierarchy fields and chaining (without cause)
# ---------------------------------------------------------------------------

@given(
    exc_class=_exception_classes,
    message=_message_strategy,
    constraints={"max_examples": 30},
)
def test_exception_fields_and_chaining_without_cause(
    exc_class,
    message: str,
) -> None:
    """
        **Validates: Requirements 14.5, 14.6, 14.7**

        For any exception class constructed with a message and no cause,
        the message property matches the constructor arg, the cause property
        is None, __cause__ is None, and __repr__ contains the class name
        and message.
    """
    exc = exc_class(message)

    assert exc.message == message, (
        "message property mismatch for {}: expected {!r}, got {!r}".format(
            exc_class.__name__, message, exc.message)
    )

    assert exc.cause is None, (
        "cause property should be None when no cause provided for {}: "
        "got {!r}".format(exc_class.__name__, exc.cause)
    )

    assert exc.__cause__ is None, (
        "__cause__ should be None when no cause provided for {}: "
        "got {!r}".format(exc_class.__name__, exc.__cause__)
    )

    repr_str = repr(exc)

    assert exc_class.__name__ in repr_str, (
        "__repr__ should contain class name {!r}: got {!r}".format(
            exc_class.__name__, repr_str)
    )

    assert message in repr_str, (
        "__repr__ should contain message {!r}: got {!r}".format(
            message, repr_str)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
