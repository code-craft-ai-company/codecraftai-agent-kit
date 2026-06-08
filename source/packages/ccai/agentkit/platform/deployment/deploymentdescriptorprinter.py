"""
    Defines the DeploymentDescriptorPrinter class for formatting
    DeploymentDescriptor objects into JSON or YAML strings, or
    writing them to files with format detection from file extension.

    .. module:: ccai.agentkit.platform.deployment.deploymentdescriptorprinter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Printer for deployment descriptors to JSON/YAML/files.
"""

import logging
import os

from ccai.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from ccai.agentkit.platform.errors import DeploymentDescriptorError


logger = logging.getLogger("ccai.agentkit.platform.deployment")


class DeploymentDescriptorPrinter:
    """
        Formats DeploymentDescriptor objects into JSON or YAML strings
        or writes them to files.
    """

    def print_json(self, descriptor: DeploymentDescriptor) -> str:
        """
            Returns a JSON string representation of the descriptor.

            :param descriptor: The DeploymentDescriptor to format.

            :returns: A JSON string.
        """
        rtnval = descriptor.to_json()
        return rtnval

    def print_yaml(self, descriptor: DeploymentDescriptor) -> str:
        """
            Returns a YAML string representation of the descriptor.

            :param descriptor: The DeploymentDescriptor to format.

            :returns: A YAML string.
        """
        rtnval = descriptor.to_yaml()
        return rtnval

    def print_file(self, descriptor: DeploymentDescriptor,
                   file_path: str) -> None:
        """
            Writes the descriptor to a file in the format determined
            by the file extension.

            :param descriptor: The DeploymentDescriptor to write.
            :param file_path: Path to the output file.

            :raises: DeploymentDescriptorError
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".json":
            content = self.print_json(descriptor)
        elif ext in (".yaml", ".yml"):
            content = self.print_yaml(descriptor)
        else:
            err_msg_lines = [
                "Unrecognized file extension '{}'.".format(ext),
                "Supported extensions: .json, .yaml, .yml"
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise DeploymentDescriptorError(err_msg)

        try:
            with open(file_path, "w") as file_handle:
                file_handle.write(content)
        except (OSError, IOError) as exc:
            err_msg_lines = [
                "Failed to write deployment descriptor file."
            ]
            err_msg_lines.append("  File path: {!r}".format(file_path))
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise DeploymentDescriptorError(err_msg)

        logger.debug("Deployment descriptor written: name=%s, platform=%s",
                      descriptor.name, descriptor.target_platform.to_string())
        return

    def __repr__(self) -> str:
        """
            Returns a string representation including the class name.

            :returns: A repr string for debugging.
        """
        rtnval = "DeploymentDescriptorPrinter()"
        return rtnval
