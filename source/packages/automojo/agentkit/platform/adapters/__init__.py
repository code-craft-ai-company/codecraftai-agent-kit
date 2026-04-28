"""
    automojo.agentkit.platform.adapters - Platform-specific adapter implementations.

    Provides the PlatformAdapter abstract base class and concrete adapter
    implementations for AWS, Azure, GCP, and local environments. Each
    adapter bundles compute, storage, and messaging service implementations
    for its target platform.

    .. module:: automojo.agentkit.platform.adapters
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Platform adapter base class and concrete implementations.
"""

from automojo.agentkit.platform.adapters.platformadapter import PlatformAdapter
from automojo.agentkit.platform.adapters.awsplatformadapter import AwsPlatformAdapter
from automojo.agentkit.platform.adapters.azureplatformadapter import AzurePlatformAdapter
from automojo.agentkit.platform.adapters.gcpplatformadapter import GcpPlatformAdapter
from automojo.agentkit.platform.adapters.localplatformadapter import LocalPlatformAdapter
