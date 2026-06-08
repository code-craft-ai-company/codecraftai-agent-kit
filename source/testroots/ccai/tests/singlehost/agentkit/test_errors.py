"""
    Unit tests for the ccai.agentkit.errors module.

    Tests the exception hierarchy: AgentKitError, ConfigurationError,
    SemanticError, and LifecycleError.
"""

from ccai.agentkit.errors import AgentKitError
from ccai.agentkit.errors import ConfigurationError
from ccai.agentkit.errors import LifecycleError
from ccai.agentkit.errors import SemanticError


def test_agentkit_error_inherits_from_exception():
    """
        Verify that AgentKitError inherits from Exception.
    """
    err = AgentKitError("test error")
    is_exception = isinstance(err, Exception)
    assert is_exception is True, "AgentKitError should inherit from Exception"
    return


def test_configuration_error_inherits_from_agentkit_error():
    """
        Verify that ConfigurationError inherits from AgentKitError.
    """
    err = ConfigurationError("config error")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "ConfigurationError should inherit from AgentKitError"
    return


def test_semantic_error_inherits_from_agentkit_error():
    """
        Verify that SemanticError inherits from AgentKitError.
    """
    err = SemanticError("semantic error")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "SemanticError should inherit from AgentKitError"
    return


def test_lifecycle_error_inherits_from_agentkit_error():
    """
        Verify that LifecycleError inherits from AgentKitError.
    """
    err = LifecycleError("lifecycle error")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "LifecycleError should inherit from AgentKitError"
    return


def test_agentkit_error_message_property():
    """
        Verify that AgentKitError stores and exposes the message.
    """
    err = AgentKitError("something went wrong")
    message = err.message
    assert message == "something went wrong", "Message property should return the provided message"
    return


def test_agentkit_error_cause_is_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = AgentKitError("no cause")
    cause = err.cause
    assert cause is None, "Cause should be None when not provided"
    return


def test_agentkit_error_cause_chaining():
    """
        Verify that cause exception is stored and accessible.
    """
    original = ValueError("original error")
    err = AgentKitError("wrapped error", cause=original)
    cause = err.cause
    assert cause is original, "Cause should be the original exception"

    dunder_cause = err.__cause__
    assert dunder_cause is original, "__cause__ should be set for exception chaining"
    return


def test_configuration_error_cause_chaining():
    """
        Verify that ConfigurationError supports cause chaining.
    """
    original = IOError("file not found")
    err = ConfigurationError("config load failed", cause=original)
    cause = err.cause
    assert cause is original, "ConfigurationError cause should be the original exception"
    return


def test_semantic_error_cause_chaining():
    """
        Verify that SemanticError supports cause chaining.
    """
    original = RuntimeError("bad state")
    err = SemanticError("invalid usage", cause=original)
    cause = err.cause
    assert cause is original, "SemanticError cause should be the original exception"
    return


def test_lifecycle_error_cause_chaining():
    """
        Verify that LifecycleError supports cause chaining.
    """
    original = TimeoutError("timed out")
    err = LifecycleError("transition failed", cause=original)
    cause = err.cause
    assert cause is original, "LifecycleError cause should be the original exception"
    return


def test_agentkit_error_repr():
    """
        Verify that __repr__ includes class name and message.
    """
    err = AgentKitError("test repr message")
    repr_str = repr(err)
    has_class_name = "AgentKitError" in repr_str
    has_message = "test repr message" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    assert has_message is True, "repr should contain the message"
    return


def test_configuration_error_repr():
    """
        Verify that ConfigurationError __repr__ includes its own class name.
    """
    err = ConfigurationError("config repr message")
    repr_str = repr(err)
    has_class_name = "ConfigurationError" in repr_str
    has_message = "config repr message" in repr_str
    assert has_class_name is True, "repr should contain ConfigurationError class name"
    assert has_message is True, "repr should contain the message"
    return


def test_semantic_error_repr():
    """
        Verify that SemanticError __repr__ includes its own class name.
    """
    err = SemanticError("semantic repr message")
    repr_str = repr(err)
    has_class_name = "SemanticError" in repr_str
    has_message = "semantic repr message" in repr_str
    assert has_class_name is True, "repr should contain SemanticError class name"
    assert has_message is True, "repr should contain the message"
    return


def test_lifecycle_error_repr():
    """
        Verify that LifecycleError __repr__ includes its own class name.
    """
    err = LifecycleError("lifecycle repr message")
    repr_str = repr(err)
    has_class_name = "LifecycleError" in repr_str
    has_message = "lifecycle repr message" in repr_str
    assert has_class_name is True, "repr should contain LifecycleError class name"
    assert has_message is True, "repr should contain the message"
    return


def test_all_errors_catchable_as_agentkit_error():
    """
        Verify that all framework exceptions can be caught as AgentKitError.
    """
    exceptions = [
        ConfigurationError("config"),
        SemanticError("semantic"),
        LifecycleError("lifecycle"),
    ]

    for exc in exceptions:
        caught = False
        try:
            raise exc
        except AgentKitError:
            caught = True

        assert caught is True, "{} should be catchable as AgentKitError".format(type(exc).__name__)

    return
