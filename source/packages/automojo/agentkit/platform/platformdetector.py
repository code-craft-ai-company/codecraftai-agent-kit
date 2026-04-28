"""
    Defines the PlatformDetector class that inspects the runtime environment
    to determine which platform the agent is running on. Checks environment
    variables and optional configuration hints to return a PlatformType value.

    .. module:: automojo.agentkit.platform.platformdetector
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Environment-based platform detection returning PlatformType.
"""

import logging
import os

from automojo.agentkit.platform.errors import PlatformDetectionError
from automojo.agentkit.platform.platformtype import PlatformType


logger = logging.getLogger("automojo.agentkit.platform.detector")


class PlatformDetector:
    """
        Inspects the runtime environment to determine which platform the agent
        is running on. Checks environment variables and optional configuration
        hints to return a PlatformType value.
    """

    AWS_ENV_VARS = ("AWS_LAMBDA_FUNCTION_NAME", "AWS_EXECUTION_ENV", "AWS_REGION")
    AZURE_ENV_VARS = ("AZURE_FUNCTIONS_ENVIRONMENT", "WEBSITE_SITE_NAME", "AZURE_REGION")
    GCP_ENV_VARS = ("GOOGLE_CLOUD_PROJECT", "FUNCTION_NAME", "GCP_REGION")

    def __init__(self) -> None:
        self._last_detected = None
        return

    def detect(self, configuration=None) -> PlatformType:
        """
            Inspects the runtime environment and returns the detected PlatformType.

            When a configuration hint is provided with a non-None platform_type,
            the hint overrides environment-based detection.

            :param configuration: Optional PlatformConfiguration hint that
                overrides environment detection.

            :returns: The detected PlatformType value.
            :raises: PlatformDetectionError
        """
        if configuration is not None and configuration.platform_type is not None:
            detected = configuration.platform_type
            logger.info("Platform detected from configuration hint: %s", detected.to_string())
            self._last_detected = detected
            rtnval = detected
            return rtnval

        detected_platforms = []
        indicators = {}

        aws_found = self._check_env_vars(self.AWS_ENV_VARS)
        if len(aws_found) > 0:
            detected_platforms.append(PlatformType.AWS)
            indicators["aws"] = aws_found

        azure_found = self._check_env_vars(self.AZURE_ENV_VARS)
        if len(azure_found) > 0:
            detected_platforms.append(PlatformType.AZURE)
            indicators["azure"] = azure_found

        gcp_found = self._check_env_vars(self.GCP_ENV_VARS)
        if len(gcp_found) > 0:
            detected_platforms.append(PlatformType.GCP)
            indicators["gcp"] = gcp_found

        if len(detected_platforms) > 1:
            err_msg_lines = [
                "Multiple cloud platforms detected simultaneously.",
                "Conflicting indicators: {}".format(indicators)
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise PlatformDetectionError(err_msg)

        if len(detected_platforms) == 1:
            detected = detected_platforms[0]
        else:
            detected = PlatformType.LOCAL

        logger.info("Platform detected: %s, indicators: %s", detected.to_string(), indicators)
        self._last_detected = detected
        rtnval = detected
        return rtnval

    def _check_env_vars(self, var_names: tuple) -> list:
        """
            Checks which of the given environment variable names are present.

            :param var_names: Tuple of environment variable names to check.

            :returns: List of environment variable names that are set.
        """
        found = []
        for var_name in var_names:
            if os.environ.get(var_name) is not None:
                found.append(var_name)
        rtnval = found
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name.

            :returns: A repr string for debugging.
        """
        rtnval = "PlatformDetector()"
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the last detected
            platform type.

            :returns: A human-readable string.
        """
        last = self._last_detected.to_string() if self._last_detected is not None else "none"
        rtnval = "PlatformDetector(last_detected={})".format(last)
        return rtnval
