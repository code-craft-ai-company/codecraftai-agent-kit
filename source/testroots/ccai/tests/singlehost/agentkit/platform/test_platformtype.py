"""
    Tests for the ccai.agentkit.platform.platformtype module.

    Contains unit tests for the PlatformType enumeration including
    from_string with valid and invalid values, to_string output,
    and enum member values.

    Feature: cross-platform-runtime

    .. module:: ccai.tests.singlehost.agentkit.platform.test_platformtype
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for PlatformType enum.
"""

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.platform.platformtype import PlatformType


# ---------------------------------------------------------------------------
# Enum member tests
# ---------------------------------------------------------------------------

def test_platform_type_defines_aws():
    """
        Verify that PlatformType defines an AWS member.
    """
    actual = PlatformType.AWS.value

    assert actual == "aws", (
        "PlatformType.AWS value should be 'aws', got: {!r}".format(actual)
    )
    return


def test_platform_type_defines_azure():
    """
        Verify that PlatformType defines an AZURE member.
    """
    actual = PlatformType.AZURE.value

    assert actual == "azure", (
        "PlatformType.AZURE value should be 'azure', got: {!r}".format(actual)
    )
    return


def test_platform_type_defines_gcp():
    """
        Verify that PlatformType defines a GCP member.
    """
    actual = PlatformType.GCP.value

    assert actual == "gcp", (
        "PlatformType.GCP value should be 'gcp', got: {!r}".format(actual)
    )
    return


def test_platform_type_defines_local():
    """
        Verify that PlatformType defines a LOCAL member.
    """
    actual = PlatformType.LOCAL.value

    assert actual == "local", (
        "PlatformType.LOCAL value should be 'local', got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# from_string tests — valid values
# ---------------------------------------------------------------------------

def test_from_string_lowercase_aws():
    """
        Verify that from_string accepts 'aws' and returns PlatformType.AWS.
    """
    result = PlatformType.from_string("aws")

    assert result is PlatformType.AWS, (
        "from_string('aws') should return PlatformType.AWS, got: {!r}".format(result)
    )
    return


def test_from_string_uppercase_aws():
    """
        Verify that from_string is case-insensitive for 'AWS'.
    """
    result = PlatformType.from_string("AWS")

    assert result is PlatformType.AWS, (
        "from_string('AWS') should return PlatformType.AWS, got: {!r}".format(result)
    )
    return


def test_from_string_mixed_case_azure():
    """
        Verify that from_string is case-insensitive for 'Azure'.
    """
    result = PlatformType.from_string("Azure")

    assert result is PlatformType.AZURE, (
        "from_string('Azure') should return PlatformType.AZURE, got: {!r}".format(result)
    )
    return


def test_from_string_gcp():
    """
        Verify that from_string accepts 'gcp' and returns PlatformType.GCP.
    """
    result = PlatformType.from_string("gcp")

    assert result is PlatformType.GCP, (
        "from_string('gcp') should return PlatformType.GCP, got: {!r}".format(result)
    )
    return


def test_from_string_local():
    """
        Verify that from_string accepts 'local' and returns PlatformType.LOCAL.
    """
    result = PlatformType.from_string("local")

    assert result is PlatformType.LOCAL, (
        "from_string('local') should return PlatformType.LOCAL, got: {!r}".format(result)
    )
    return


def test_from_string_with_whitespace():
    """
        Verify that from_string strips leading and trailing whitespace.
    """
    result = PlatformType.from_string("  gcp  ")

    assert result is PlatformType.GCP, (
        "from_string('  gcp  ') should return PlatformType.GCP, got: {!r}".format(result)
    )
    return


# ---------------------------------------------------------------------------
# from_string tests — invalid values
# ---------------------------------------------------------------------------

def test_from_string_invalid_value_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an invalid value.
    """
    caught = False
    try:
        PlatformType.from_string("invalid-platform")
    except SemanticError:
        caught = True

    assert caught is True, (
        "from_string('invalid-platform') should raise SemanticError"
    )
    return


def test_from_string_empty_string_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an empty string.
    """
    caught = False
    try:
        PlatformType.from_string("")
    except SemanticError:
        caught = True

    assert caught is True, (
        "from_string('') should raise SemanticError"
    )
    return


def test_from_string_semantic_error_mentions_invalid_value():
    """
        Verify that the SemanticError message identifies the invalid value.
    """
    error_message = ""
    try:
        PlatformType.from_string("bogus")
    except SemanticError as err:
        error_message = str(err)

    has_value = "bogus" in error_message

    assert has_value is True, (
        "SemanticError message should mention the invalid value 'bogus', "
        "got: {!r}".format(error_message)
    )
    return


# ---------------------------------------------------------------------------
# to_string tests
# ---------------------------------------------------------------------------

def test_to_string_aws_returns_lowercase():
    """
        Verify that to_string returns 'aws' for PlatformType.AWS.
    """
    result = PlatformType.AWS.to_string()

    assert result == "aws", (
        "to_string() should return 'aws', got: {!r}".format(result)
    )
    return


def test_to_string_azure_returns_lowercase():
    """
        Verify that to_string returns 'azure' for PlatformType.AZURE.
    """
    result = PlatformType.AZURE.to_string()

    assert result == "azure", (
        "to_string() should return 'azure', got: {!r}".format(result)
    )
    return


def test_to_string_gcp_returns_lowercase():
    """
        Verify that to_string returns 'gcp' for PlatformType.GCP.
    """
    result = PlatformType.GCP.to_string()

    assert result == "gcp", (
        "to_string() should return 'gcp', got: {!r}".format(result)
    )
    return


def test_to_string_local_returns_lowercase():
    """
        Verify that to_string returns 'local' for PlatformType.LOCAL.
    """
    result = PlatformType.LOCAL.to_string()

    assert result == "local", (
        "to_string() should return 'local', got: {!r}".format(result)
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
