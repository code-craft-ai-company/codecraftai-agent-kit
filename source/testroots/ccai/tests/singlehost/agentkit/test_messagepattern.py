"""
    Unit tests for the MessagePattern enum.

    Tests all enum values, from_string with valid and invalid inputs.

    Requirements: 5.1, 5.2, 5.3
"""

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.messagepattern import MessagePattern


# =========================================================================
# Enum value tests (Requirement 5.1)
# =========================================================================

def test_messagepattern_request_value():
    """
        Verify that the REQUEST member has the value 'REQUEST'.
    """
    assert MessagePattern.REQUEST.value == "REQUEST", \
        "REQUEST value should be 'REQUEST'"
    return


def test_messagepattern_response_value():
    """
        Verify that the RESPONSE member has the value 'RESPONSE'.
    """
    assert MessagePattern.RESPONSE.value == "RESPONSE", \
        "RESPONSE value should be 'RESPONSE'"
    return


def test_messagepattern_fire_and_forget_value():
    """
        Verify that the FIRE_AND_FORGET member has the value 'FIRE_AND_FORGET'.
    """
    assert MessagePattern.FIRE_AND_FORGET.value == "FIRE_AND_FORGET", \
        "FIRE_AND_FORGET value should be 'FIRE_AND_FORGET'"
    return


def test_messagepattern_event_value():
    """
        Verify that the EVENT member has the value 'EVENT'.
    """
    assert MessagePattern.EVENT.value == "EVENT", \
        "EVENT value should be 'EVENT'"
    return


def test_messagepattern_has_exactly_four_members():
    """
        Verify that the MessagePattern enum defines exactly four members.
    """
    members = list(MessagePattern)
    assert len(members) == 4, \
        "MessagePattern should have exactly 4 members, got {}".format(len(members))
    return


# =========================================================================
# from_string valid input tests (Requirement 5.2)
# =========================================================================

def test_from_string_request():
    """
        Verify that from_string returns REQUEST for 'REQUEST'.
    """
    result = MessagePattern.from_string("REQUEST")
    assert result is MessagePattern.REQUEST, \
        "from_string('REQUEST') should return MessagePattern.REQUEST"
    return


def test_from_string_response():
    """
        Verify that from_string returns RESPONSE for 'RESPONSE'.
    """
    result = MessagePattern.from_string("RESPONSE")
    assert result is MessagePattern.RESPONSE, \
        "from_string('RESPONSE') should return MessagePattern.RESPONSE"
    return


def test_from_string_fire_and_forget():
    """
        Verify that from_string returns FIRE_AND_FORGET for 'FIRE_AND_FORGET'.
    """
    result = MessagePattern.from_string("FIRE_AND_FORGET")
    assert result is MessagePattern.FIRE_AND_FORGET, \
        "from_string('FIRE_AND_FORGET') should return MessagePattern.FIRE_AND_FORGET"
    return


def test_from_string_event():
    """
        Verify that from_string returns EVENT for 'EVENT'.
    """
    result = MessagePattern.from_string("EVENT")
    assert result is MessagePattern.EVENT, \
        "from_string('EVENT') should return MessagePattern.EVENT"
    return


def test_from_string_case_insensitive():
    """
        Verify that from_string handles lowercase input by converting to uppercase.
    """
    result = MessagePattern.from_string("request")
    assert result is MessagePattern.REQUEST, \
        "from_string('request') should return MessagePattern.REQUEST (case-insensitive)"
    return


def test_from_string_mixed_case():
    """
        Verify that from_string handles mixed-case input.
    """
    result = MessagePattern.from_string("Fire_And_Forget")
    assert result is MessagePattern.FIRE_AND_FORGET, \
        "from_string('Fire_And_Forget') should return MessagePattern.FIRE_AND_FORGET"
    return


# =========================================================================
# from_string invalid input tests (Requirement 5.3)
# =========================================================================

def test_from_string_invalid_value_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an invalid value.
    """
    raised = False
    try:
        MessagePattern.from_string("INVALID")
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_string('INVALID') should raise SemanticError"
    return


def test_from_string_empty_string_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an empty string.
    """
    raised = False
    try:
        MessagePattern.from_string("")
    except SemanticError:
        raised = True

    assert raised is True, \
        "from_string('') should raise SemanticError"
    return


def test_from_string_error_message_includes_invalid_value():
    """
        Verify that the SemanticError message includes the invalid value.
    """
    error_message = ""
    try:
        MessagePattern.from_string("BOGUS")
    except SemanticError as err:
        error_message = str(err)

    assert "BOGUS" in error_message, \
        "Error message should include the invalid value 'BOGUS'"
    return


def test_from_string_error_message_lists_valid_values():
    """
        Verify that the SemanticError message lists the valid pattern values.
    """
    error_message = ""
    try:
        MessagePattern.from_string("UNKNOWN")
    except SemanticError as err:
        error_message = str(err)

    assert "REQUEST" in error_message, \
        "Error message should list 'REQUEST' as a valid value"
    assert "RESPONSE" in error_message, \
        "Error message should list 'RESPONSE' as a valid value"
    assert "FIRE_AND_FORGET" in error_message, \
        "Error message should list 'FIRE_AND_FORGET' as a valid value"
    assert "EVENT" in error_message, \
        "Error message should list 'EVENT' as a valid value"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
