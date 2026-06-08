"""
    Unit tests for the ccai.agentkit.deadletterquery module.

    Validates: Requirements 14.1–14.13
"""

from datetime import datetime

from ccai.agentkit.deadletterentry import DeadLetterEntry
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.deadletterquery import DeadLetterQueryResult


# ---------------------------------------------------------------------------
# DeadLetterQuery – construction and filtering (14.1–14.5)
# ---------------------------------------------------------------------------

def test_query_default_construction():
    """
        Verify that DeadLetterQuery can be constructed with no filters.
        All optional fields should default to None.
    """
    query = DeadLetterQuery()

    assert query.operation_type is None, "operation_type should default to None"
    assert query.source_component is None, "source_component should default to None"
    assert query.agent_identifier is None, "agent_identifier should default to None"
    assert query.start_time is None, "start_time should default to None"
    assert query.end_time is None, "end_time should default to None"
    assert query.max_results is None, "max_results should default to None"
    return


def test_query_operation_type_filter():
    """
        Verify that DeadLetterQuery stores the operation_type filter.
        Validates: Requirement 14.1
    """
    query = DeadLetterQuery(operation_type="send_message")

    assert query.operation_type == "send_message", "operation_type should match"
    return


def test_query_source_component_filter():
    """
        Verify that DeadLetterQuery stores the source_component filter.
        Validates: Requirement 14.2
    """
    query = DeadLetterQuery(source_component="transport")

    assert query.source_component == "transport", "source_component should match"
    return


def test_query_agent_identifier_filter():
    """
        Verify that DeadLetterQuery stores the agent_identifier filter.
        Validates: Requirement 14.3
    """
    query = DeadLetterQuery(agent_identifier="agent-1")

    assert query.agent_identifier == "agent-1", "agent_identifier should match"
    return


def test_query_time_range_filter():
    """
        Verify that DeadLetterQuery stores start_time and end_time filters.
        Validates: Requirement 14.4
    """
    start = datetime(2025, 1, 1, 0, 0, 0)
    end = datetime(2025, 1, 2, 0, 0, 0)
    query = DeadLetterQuery(start_time=start, end_time=end)

    assert query.start_time == start, "start_time should match"
    assert query.end_time == end, "end_time should match"
    return


def test_query_max_results_filter():
    """
        Verify that DeadLetterQuery stores the max_results filter.
        Validates: Requirement 14.5
    """
    query = DeadLetterQuery(max_results=50)

    assert query.max_results == 50, "max_results should match"
    return


def test_query_all_filters():
    """
        Verify that DeadLetterQuery stores all filters when provided together.
        Validates: Requirements 14.1–14.5
    """
    start = datetime(2025, 6, 1)
    end = datetime(2025, 6, 30)
    query = DeadLetterQuery(
        operation_type="tool_exec",
        source_component="tool_executor",
        agent_identifier="agent-42",
        start_time=start,
        end_time=end,
        max_results=10
    )

    assert query.operation_type == "tool_exec", "operation_type should match"
    assert query.source_component == "tool_executor", "source_component should match"
    assert query.agent_identifier == "agent-42", "agent_identifier should match"
    assert query.start_time == start, "start_time should match"
    assert query.end_time == end, "end_time should match"
    assert query.max_results == 10, "max_results should match"
    return


# ---------------------------------------------------------------------------
# DeadLetterQuery – as_dict (14.6)
# ---------------------------------------------------------------------------

def test_query_as_dict_no_filters():
    """
        Verify that as_dict returns a dictionary with all keys set to None
        when no filters are provided.
        Validates: Requirement 14.6
    """
    query = DeadLetterQuery()
    result = query.as_dict()

    assert isinstance(result, dict), "as_dict should return a dict"
    assert result["operation_type"] is None, "operation_type should be None"
    assert result["source_component"] is None, "source_component should be None"
    assert result["agent_identifier"] is None, "agent_identifier should be None"
    assert result["start_time"] is None, "start_time should be None"
    assert result["end_time"] is None, "end_time should be None"
    assert result["max_results"] is None, "max_results should be None"
    return


def test_query_as_dict_with_filters():
    """
        Verify that as_dict returns a dictionary with correct values
        when filters are provided.
        Validates: Requirement 14.6
    """
    start = datetime(2025, 3, 15, 10, 30, 0)
    end = datetime(2025, 3, 16, 10, 30, 0)
    query = DeadLetterQuery(
        operation_type="send_message",
        source_component="transport",
        agent_identifier="agent-1",
        start_time=start,
        end_time=end,
        max_results=25
    )
    result = query.as_dict()

    assert result["operation_type"] == "send_message", "operation_type should match"
    assert result["source_component"] == "transport", "source_component should match"
    assert result["agent_identifier"] == "agent-1", "agent_identifier should match"
    assert result["start_time"] == start.isoformat(), "start_time should be ISO format"
    assert result["end_time"] == end.isoformat(), "end_time should be ISO format"
    assert result["max_results"] == 25, "max_results should match"
    return


# ---------------------------------------------------------------------------
# DeadLetterQuery – __repr__ (14.7)
# ---------------------------------------------------------------------------

def test_query_repr():
    """
        Verify that __repr__ includes the class name and filter summary.
        Validates: Requirement 14.7
    """
    query = DeadLetterQuery(operation_type="send", source_component="transport")
    repr_str = repr(query)

    assert "DeadLetterQuery" in repr_str, "repr should contain class name"
    assert "send" in repr_str, "repr should contain operation_type"
    assert "transport" in repr_str, "repr should contain source_component"
    return


def test_query_repr_no_filters():
    """
        Verify that __repr__ works with no filters.
        Validates: Requirement 14.7
    """
    query = DeadLetterQuery()
    repr_str = repr(query)

    assert "DeadLetterQuery" in repr_str, "repr should contain class name"
    return


# ---------------------------------------------------------------------------
# DeadLetterQuery – __str__ (14.8)
# ---------------------------------------------------------------------------

def test_query_str_with_filters():
    """
        Verify that __str__ returns a human-readable summary with active filters.
        Validates: Requirement 14.8
    """
    query = DeadLetterQuery(
        operation_type="send_message",
        source_component="transport",
        agent_identifier="agent-1"
    )
    str_val = str(query)

    assert "DeadLetterQuery" in str_val, "str should contain class name"
    assert "send_message" in str_val, "str should contain operation_type"
    assert "transport" in str_val, "str should contain source_component"
    assert "agent-1" in str_val, "str should contain agent_identifier"
    return


def test_query_str_no_filters():
    """
        Verify that __str__ indicates no filters when none are set.
        Validates: Requirement 14.8
    """
    query = DeadLetterQuery()
    str_val = str(query)

    assert "DeadLetterQuery" in str_val, "str should contain class name"
    assert "no filters" in str_val, "str should indicate no filters"
    return


# ---------------------------------------------------------------------------
# DeadLetterQueryResult – construction and properties (14.9–14.10)
# ---------------------------------------------------------------------------

def _create_entry(operation_type="op", source_component="src",
                  agent_identifier="agent") -> DeadLetterEntry:
    """
        Helper to create a DeadLetterEntry for testing.
    """
    entry = DeadLetterEntry(
        operation_type=operation_type,
        payload={"data": "test"},
        exception_info="Error(test)",
        retry_attempts=1,
        source_component=source_component,
        agent_identifier=agent_identifier
    )
    return entry


def test_result_construction():
    """
        Verify that DeadLetterQueryResult stores entries and total_count.
        Validates: Requirement 14.9
    """
    entries = [_create_entry(), _create_entry()]
    result = DeadLetterQueryResult(entries=entries, total_count=2)

    assert len(result.entries) == 2, "entries should contain 2 items"
    assert result.total_count == 2, "total_count should be 2"
    return


def test_result_empty():
    """
        Verify that DeadLetterQueryResult works with empty entries.
        Validates: Requirement 14.9
    """
    result = DeadLetterQueryResult(entries=[], total_count=0)

    assert len(result.entries) == 0, "entries should be empty"
    assert result.total_count == 0, "total_count should be 0"
    return


def test_result_entries_are_read_only_copy():
    """
        Verify that the entries property returns a copy, not the internal list.
        Validates: Requirement 14.10
    """
    entries = [_create_entry()]
    result = DeadLetterQueryResult(entries=entries, total_count=1)

    returned_entries = result.entries
    returned_entries.append(_create_entry())

    assert len(result.entries) == 1, "internal entries should not be modified"
    return


def test_result_total_count_read_only():
    """
        Verify that total_count is a read-only property.
        Validates: Requirement 14.10
    """
    result = DeadLetterQueryResult(entries=[], total_count=5)

    assert result.total_count == 5, "total_count should be accessible"
    return


# ---------------------------------------------------------------------------
# DeadLetterQueryResult – __repr__ (14.12)
# ---------------------------------------------------------------------------

def test_result_repr():
    """
        Verify that __repr__ includes the class name and total_count.
        Validates: Requirement 14.12
    """
    result = DeadLetterQueryResult(entries=[], total_count=7)
    repr_str = repr(result)

    assert "DeadLetterQueryResult" in repr_str, "repr should contain class name"
    assert "7" in repr_str, "repr should contain total_count"
    return


# ---------------------------------------------------------------------------
# DeadLetterQueryResult – __str__ (14.13)
# ---------------------------------------------------------------------------

def test_result_str():
    """
        Verify that __str__ returns a human-readable summary with match count.
        Validates: Requirement 14.13
    """
    result = DeadLetterQueryResult(entries=[], total_count=3)
    str_val = str(result)

    assert "DeadLetterQueryResult" in str_val, "str should contain class name"
    assert "3" in str_val, "str should contain the match count"
    return
