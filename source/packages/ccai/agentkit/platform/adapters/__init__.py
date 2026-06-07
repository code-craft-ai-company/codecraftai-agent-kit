"""
    ccai.agentkit.platform.adapters - Platform-specific adapter implementations.

    Provides the PlatformAdapter abstract base class and concrete adapter
    implementations for AWS, Azure, GCP, and local environments. Each
    adapter bundles compute, storage, and messaging service implementations
    for its target platform.

    .. module:: ccai.agentkit.platform.adapters
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Platform adapter base class and concrete implementations.
"""

from ccai.agentkit.platform.adapters.platformadapter import PlatformAdapter
from ccai.agentkit.platform.adapters.awsplatformadapter import AwsPlatformAdapter
from ccai.agentkit.platform.adapters.azureplatformadapter import AzurePlatformAdapter
from ccai.agentkit.platform.adapters.gcpplatformadapter import GcpPlatformAdapter
from ccai.agentkit.platform.adapters.localplatformadapter import LocalPlatformAdapter
