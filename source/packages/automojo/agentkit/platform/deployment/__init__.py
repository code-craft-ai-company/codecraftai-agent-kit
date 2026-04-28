"""
    automojo.agentkit.platform.deployment - Deployment descriptor support.

    Provides the DeploymentDescriptor immutable configuration object,
    DeploymentDescriptorParser for reading descriptors from JSON/YAML/files,
    and DeploymentDescriptorPrinter for writing descriptors to JSON/YAML/files.

    .. module:: automojo.agentkit.platform.deployment
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Deployment descriptor, parser, and printer for platform deployments.
"""

from automojo.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from automojo.agentkit.platform.deployment.deploymentdescriptorparser import DeploymentDescriptorParser
from automojo.agentkit.platform.deployment.deploymentdescriptorprinter import DeploymentDescriptorPrinter
