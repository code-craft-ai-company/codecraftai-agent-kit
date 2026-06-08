"""
    Unit tests for the ccai.agentkit.observabilityerror module.

    Tests the ObservabilityError class: construction, properties,
    inheritance, cause chaining, and __repr__.
"""

from ccai.agentkit.errors import AgentKitError
from ccai.agentkit.observabilityerror import ObservabilityError


def test_observability_error_inherits_from_agentkit_error():
    """
        Verify that ObservabilityError inherits from AgentKitError.
    """
    err = ObservabilityError("TestExporter", "export", "export failed")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "ObservabilityError should inherit from AgentKitError"
    return


def test_observability_error_inherits_from_exception():
    """
        Verify that ObservabilityError inherits from Exception.
    """
    err = ObservabilityError("TestExporter", "export", "export failed")
    is_exception = isinstance(err, Exception)
    assert is_exception is True, "ObservabilityError should inherit from Exception"
    return


def test_observability_error_component_name_property():
    """
        Verify that the component_name property returns the provided component name.
    """
    err = ObservabilityError("ConsoleLogExporter", "export", "write failed")
    component_name = err.component_name
    assert component_name == "ConsoleLogExporter", "component_name should return the provided value"
    return


def test_observability_error_operation_name_property():
    """
        Verify that the operation_name property returns the provided operation name.
    """
    err = ObservabilityError("FileTraceExporter", "flush", "flush failed")
    operation_name = err.operation_name
    assert operation_name == "flush", "operation_name should return the provided value"
    return


def test_observability_error_message_property():
    """
        Verify that the message property returns the provided message.
    """
    err = ObservabilityError("MetricsExporter", "shutdown", "shutdown timeout")
    message = err.message
    assert message == "shutdown timeout", "message should return the provided value"
    return


def test_observability_error_cause_is_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = ObservabilityError("Recorder", "record", "record failed")
    cause = err.cause
    assert cause is None, "Cause should be None when not provided"
    return


def test_observability_error_cause_chaining():
    """
        Verify that cause exception is stored and accessible when provided.
    """
    original = IOError("disk full")
    err = ObservabilityError("FileLogExporter", "export", "write failed", cause=original)

    cause = err.cause
    assert cause is original, "Cause should be the original exception"

    dunder_cause = err.__cause__
    assert dunder_cause is original, "__cause__ should be set for exception chaining"
    return


def test_observability_error_catchable_as_agentkit_error():
    """
        Verify that ObservabilityError can be caught as AgentKitError.
    """
    err = ObservabilityError("Pipeline", "configure", "bad config")
    caught = False
    try:
        raise err
    except AgentKitError:
        caught = True

    assert caught is True, "ObservabilityError should be catchable as AgentKitError"
    return


def test_observability_error_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name ObservabilityError.
    """
    err = ObservabilityError("TestComponent", "testOp", "test message")
    repr_str = repr(err)
    has_class_name = "ObservabilityError" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_observability_error_repr_contains_component_name():
    """
        Verify that __repr__ includes the component name.
    """
    err = ObservabilityError("MyExporter", "export", "failed")
    repr_str = repr(err)
    has_component = "MyExporter" in repr_str
    assert has_component is True, "repr should contain the component name"
    return


def test_observability_error_repr_contains_operation_name():
    """
        Verify that __repr__ includes the operation name.
    """
    err = ObservabilityError("MyExporter", "flush", "failed")
    repr_str = repr(err)
    has_operation = "flush" in repr_str
    assert has_operation is True, "repr should contain the operation name"
    return


def test_observability_error_repr_contains_message():
    """
        Verify that __repr__ includes the error message.
    """
    err = ObservabilityError("MyExporter", "export", "connection refused")
    repr_str = repr(err)
    has_message = "connection refused" in repr_str
    assert has_message is True, "repr should contain the error message"
    return
