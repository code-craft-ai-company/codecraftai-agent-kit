"""
    ccai.agentkit.platform.deployment - Deployment descriptor support.

    Provides the DeploymentDescriptor immutable configuration object,
    DeploymentDescriptorParser for reading descriptors from JSON/YAML/files,
    and DeploymentDescriptorPrinter for writing descriptors to JSON/YAML/files.

    .. module:: ccai.agentkit.platform.deployment
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Deployment descriptor, parser, and printer for platform deployments.
"""

from ccai.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from ccai.agentkit.platform.deployment.deploymentdescriptorparser import DeploymentDescriptorParser
from ccai.agentkit.platform.deployment.deploymentdescriptorprinter import DeploymentDescriptorPrinter
