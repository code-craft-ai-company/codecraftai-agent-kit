"""
    .. module:: automojo.tests.singlehost.agentkit.test_memoryerrors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryStoreError and ContextWindowError exception classes.
"""

from automojo.agentkit.errors import AgentKitError
from automojo.agentkit.memoryerrors import ContextWindowError
from automojo.agentkit.memoryerrors import MemoryStoreError


# ---- MemoryStoreError Tests ----


def test_memory_store_error_inherits_from_agentkit_error():
    """
        Verify that MemoryStoreError inherits from AgentKitError.
    """
    err = MemoryStoreError(store_name="test-store", operation="store")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "MemoryStoreError should inherit from AgentKitError"
    return


def test_memory_store_error_store_name_property():
    """
        Verify that store_name property returns the correct value.
    """
    err = MemoryStoreError(store_name="my-store", operation="retrieve")
    store_name = err.store_name
    assert store_name == "my-store", "store_name should return the provided store name"
    return


def test_memory_store_error_operation_property():
    """
        Verify that operation property returns the correct value.
    """
    err = MemoryStoreError(store_name="my-store", operation="search")
    operation = err.operation
    assert operation == "search", "operation should return the provided operation"
    return


def test_memory_store_error_cause_is_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = MemoryStoreError(store_name="my-store", operation="store")
    cause = err.cause
    assert cause is None, "cause should be None when not provided"
    return


def test_memory_store_error_cause_preserves_exception():
    """
        Verify that cause property returns the provided cause exception.
    """
    original = IOError("disk full")
    err = MemoryStoreError(store_name="file-store", operation="store", cause=original)
    cause = err.cause
    assert cause is original, "cause should be the original exception"
    return


def test_memory_store_error_message_contains_store_name():
    """
        Verify that the error message contains the store name.
    """
    err = MemoryStoreError(store_name="agent-memory", operation="delete")
    message = err.message
    has_store_name = "agent-memory" in message
    assert has_store_name is True, "error message should contain the store name"
    return


def test_memory_store_error_message_contains_operation():
    """
        Verify that the error message contains the operation.
    """
    err = MemoryStoreError(store_name="my-store", operation="update")
    message = err.message
    has_operation = "update" in message
    assert has_operation is True, "error message should contain the operation"
    return


def test_memory_store_error_message_contains_cause_string():
    """
        Verify that the error message contains the cause string when provided.
    """
    original = ConnectionError("connection refused")
    err = MemoryStoreError(store_name="db-store", operation="store", cause=original)
    message = err.message
    has_cause = "connection refused" in message
    assert has_cause is True, "error message should contain the cause string"
    return


def test_memory_store_error_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    err = MemoryStoreError(store_name="repr-store", operation="search")
    repr_str = repr(err)
    has_class_name = "MemoryStoreError" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_memory_store_error_repr_contains_store_name():
    """
        Verify that __repr__ contains the store_name.
    """
    err = MemoryStoreError(store_name="repr-store", operation="search")
    repr_str = repr(err)
    has_store_name = "repr-store" in repr_str
    assert has_store_name is True, "repr should contain the store name"
    return


def test_memory_store_error_repr_contains_operation():
    """
        Verify that __repr__ contains the operation.
    """
    err = MemoryStoreError(store_name="repr-store", operation="search")
    repr_str = repr(err)
    has_operation = "search" in repr_str
    assert has_operation is True, "repr should contain the operation"
    return


def test_memory_store_error_catchable_as_agentkit_error():
    """
        Verify that MemoryStoreError can be caught as AgentKitError.
    """
    caught = False
    try:
        raise MemoryStoreError(store_name="catch-store", operation="clear")
    except AgentKitError:
        caught = True

    assert caught is True, "MemoryStoreError should be catchable as AgentKitError"
    return


# ---- ContextWindowError Tests ----


def test_context_window_error_inherits_from_agentkit_error():
    """
        Verify that ContextWindowError inherits from AgentKitError.
    """
    err = ContextWindowError(max_tokens=4096, strategy="FIFO", message="too many tokens")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "ContextWindowError should inherit from AgentKitError"
    return


def test_context_window_error_max_tokens_property():
    """
        Verify that max_tokens property returns the correct value.
    """
    err = ContextWindowError(max_tokens=8192, strategy="RELEVANCE", message="overflow")
    max_tokens = err.max_tokens
    assert max_tokens == 8192, "max_tokens should return the provided value"
    return


def test_context_window_error_strategy_property():
    """
        Verify that strategy property returns the correct value.
    """
    err = ContextWindowError(max_tokens=4096, strategy="SUMMARIZE", message="failed")
    strategy = err.strategy
    assert strategy == "SUMMARIZE", "strategy should return the provided value"
    return


def test_context_window_error_error_message_property():
    """
        Verify that error_message property returns the correct value.
    """
    err = ContextWindowError(max_tokens=4096, strategy="FIFO", message="cannot fit context")
    error_message = err.error_message
    assert error_message == "cannot fit context", "error_message should return the provided message"
    return


def test_context_window_error_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    err = ContextWindowError(max_tokens=4096, strategy="FIFO", message="test")
    repr_str = repr(err)
    has_class_name = "ContextWindowError" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_context_window_error_repr_contains_max_tokens():
    """
        Verify that __repr__ contains the max_tokens value.
    """
    err = ContextWindowError(max_tokens=4096, strategy="FIFO", message="test")
    repr_str = repr(err)
    has_max_tokens = "4096" in repr_str
    assert has_max_tokens is True, "repr should contain the max_tokens value"
    return


def test_context_window_error_repr_contains_strategy():
    """
        Verify that __repr__ contains the strategy.
    """
    err = ContextWindowError(max_tokens=4096, strategy="RELEVANCE", message="test")
    repr_str = repr(err)
    has_strategy = "RELEVANCE" in repr_str
    assert has_strategy is True, "repr should contain the strategy"
    return


def test_context_window_error_repr_contains_message():
    """
        Verify that __repr__ contains the error message.
    """
    err = ContextWindowError(max_tokens=4096, strategy="FIFO", message="context overflow")
    repr_str = repr(err)
    has_message = "context overflow" in repr_str
    assert has_message is True, "repr should contain the error message"
    return


def test_context_window_error_catchable_as_agentkit_error():
    """
        Verify that ContextWindowError can be caught as AgentKitError.
    """
    caught = False
    try:
        raise ContextWindowError(max_tokens=4096, strategy="FIFO", message="test catch")
    except AgentKitError:
        caught = True

    assert caught is True, "ContextWindowError should be catchable as AgentKitError"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
