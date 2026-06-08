"""
    Tests for the ccai.agentkit.platform.platformdetector module.

    Contains unit tests for PlatformDetector environment-based detection
    including AWS, Azure, GCP, LOCAL default, configuration hint override,
    multiple platform conflict, and repr/str output.

    Feature: cross-platform-runtime

    .. module:: ccai.tests.singlehost.agentkit.platform.test_platformdetector
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for PlatformDetector.
"""

import os

from ccai.agentkit.platform.errors import PlatformDetectionError
from ccai.agentkit.platform.platformdetector import PlatformDetector
from ccai.agentkit.platform.platformtype import PlatformType
from ccai.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# All cloud env vars that the detector checks, used for cleanup.
ALL_CLOUD_ENV_VARS = [
    "AWS_LAMBDA_FUNCTION_NAME", "AWS_EXECUTION_ENV", "AWS_REGION",
    "AZURE_FUNCTIONS_ENVIRONMENT", "WEBSITE_SITE_NAME", "AZURE_REGION",
    "GOOGLE_CLOUD_PROJECT", "FUNCTION_NAME", "GCP_REGION",
]


def _save_env_vars():
    """
        Saves the current values of all cloud env vars so they can be restored.
    """
    saved = {}
    for var_name in ALL_CLOUD_ENV_VARS:
        saved[var_name] = os.environ.get(var_name)
    return saved


def _restore_env_vars(saved):
    """
        Restores env vars to their saved values.
    """
    for var_name, value in saved.items():
        if value is not None:
            os.environ[var_name] = value
        elif var_name in os.environ:
            del os.environ[var_name]
    return


def _clear_all_cloud_env_vars():
    """
        Removes all cloud env vars from the environment.
    """
    for var_name in ALL_CLOUD_ENV_VARS:
        if var_name in os.environ:
            del os.environ[var_name]
    return


# ---------------------------------------------------------------------------
# AWS detection tests
# ---------------------------------------------------------------------------

def test_detect_aws_with_aws_env_vars():
    """
        Verify that PlatformDetector detects AWS when AWS env vars are set.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "my-function"
    os.environ["AWS_REGION"] = "us-east-1"

    try:
        detector = PlatformDetector()
        result = detector.detect()

        assert result is PlatformType.AWS, (
            "detect() should return PlatformType.AWS when AWS env vars are set, "
            "got: {!r}".format(result)
        )
    finally:
        _restore_env_vars(saved)

    return


# ---------------------------------------------------------------------------
# Azure detection tests
# ---------------------------------------------------------------------------

def test_detect_azure_with_azure_env_vars():
    """
        Verify that PlatformDetector detects Azure when Azure env vars are set.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    os.environ["AZURE_FUNCTIONS_ENVIRONMENT"] = "Production"
    os.environ["WEBSITE_SITE_NAME"] = "my-app"

    try:
        detector = PlatformDetector()
        result = detector.detect()

        assert result is PlatformType.AZURE, (
            "detect() should return PlatformType.AZURE when Azure env vars are set, "
            "got: {!r}".format(result)
        )
    finally:
        _restore_env_vars(saved)

    return


# ---------------------------------------------------------------------------
# GCP detection tests
# ---------------------------------------------------------------------------

def test_detect_gcp_with_gcp_env_vars():
    """
        Verify that PlatformDetector detects GCP when GCP env vars are set.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    os.environ["GOOGLE_CLOUD_PROJECT"] = "my-project"
    os.environ["GCP_REGION"] = "us-central1"

    try:
        detector = PlatformDetector()
        result = detector.detect()

        assert result is PlatformType.GCP, (
            "detect() should return PlatformType.GCP when GCP env vars are set, "
            "got: {!r}".format(result)
        )
    finally:
        _restore_env_vars(saved)

    return


# ---------------------------------------------------------------------------
# LOCAL default detection tests
# ---------------------------------------------------------------------------

def test_detect_local_when_no_cloud_vars_present():
    """
        Verify that PlatformDetector defaults to LOCAL when no cloud env vars
        are present.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    try:
        detector = PlatformDetector()
        result = detector.detect()

        assert result is PlatformType.LOCAL, (
            "detect() should return PlatformType.LOCAL when no cloud env vars are set, "
            "got: {!r}".format(result)
        )
    finally:
        _restore_env_vars(saved)

    return


# ---------------------------------------------------------------------------
# Configuration hint override tests
# ---------------------------------------------------------------------------

def test_detect_configuration_hint_overrides_environment():
    """
        Verify that a PlatformConfiguration hint overrides environment detection.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "my-function"

    try:
        mock_config = Mock()
        mock_config.configure(recursive=True)
        mock_config.mock_context().set_attribute("platform_type", PlatformType.GCP)

        detector = PlatformDetector()
        result = detector.detect(configuration=mock_config)

        assert result is PlatformType.GCP, (
            "detect() should return the configuration hint platform type, "
            "got: {!r}".format(result)
        )
    finally:
        _restore_env_vars(saved)

    return


# ---------------------------------------------------------------------------
# Multiple platform conflict tests
# ---------------------------------------------------------------------------

def test_detect_multiple_platforms_raises_platform_detection_error():
    """
        Verify that PlatformDetector raises PlatformDetectionError when
        multiple cloud platforms are detected simultaneously.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "my-function"
    os.environ["AZURE_FUNCTIONS_ENVIRONMENT"] = "Production"

    try:
        detector = PlatformDetector()

        caught = False
        error_message = ""
        try:
            detector.detect()
        except PlatformDetectionError as err:
            caught = True
            error_message = str(err)

        assert caught is True, (
            "detect() should raise PlatformDetectionError when multiple platforms detected"
        )
        assert "Multiple" in error_message or "multiple" in error_message, (
            "Error message should mention multiple platforms, got: {!r}".format(error_message)
        )
    finally:
        _restore_env_vars(saved)

    return


def test_detect_three_platforms_raises_platform_detection_error():
    """
        Verify that PlatformDetector raises PlatformDetectionError when
        all three cloud platforms are detected simultaneously.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["AZURE_REGION"] = "westus2"
    os.environ["GCP_REGION"] = "us-central1"

    try:
        detector = PlatformDetector()

        caught = False
        try:
            detector.detect()
        except PlatformDetectionError:
            caught = True

        assert caught is True, (
            "detect() should raise PlatformDetectionError when three platforms detected"
        )
    finally:
        _restore_env_vars(saved)

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name():
    """
        Verify that __repr__ includes the class name.
    """
    detector = PlatformDetector()

    repr_str = repr(detector)

    assert "PlatformDetector" in repr_str, (
        "repr should contain 'PlatformDetector', got: {!r}".format(repr_str)
    )
    return


def test_str_shows_none_before_detection():
    """
        Verify that __str__ shows 'none' before any detection has occurred.
    """
    detector = PlatformDetector()

    str_val = str(detector)

    assert "none" in str_val, (
        "str should contain 'none' before detection, got: {!r}".format(str_val)
    )
    return


def test_str_shows_detected_platform_after_detection():
    """
        Verify that __str__ shows the detected platform type after detection.
    """
    saved = _save_env_vars()
    _clear_all_cloud_env_vars()

    try:
        detector = PlatformDetector()
        detector.detect()

        str_val = str(detector)

        assert "local" in str_val, (
            "str should contain 'local' after detecting LOCAL, got: {!r}".format(str_val)
        )
    finally:
        _restore_env_vars(saved)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
