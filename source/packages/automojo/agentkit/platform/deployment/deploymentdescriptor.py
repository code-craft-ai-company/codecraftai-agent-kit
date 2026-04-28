"""
    Defines the DeploymentDescriptor class representing a declarative
    configuration object that defines how an agent is deployed on a
    specific platform. Contains compute, storage, messaging configuration,
    environment variables, and scaling parameters.

    Supports serialization to and from dictionary, JSON, and YAML
    representations.

    .. module:: automojo.agentkit.platform.deployment.deploymentdescriptor
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable deployment descriptor for platform deployments.
"""

import json

from typing import Any
from typing import Dict
from typing import Optional

import yaml

from automojo.agentkit.platform.platformtype import PlatformType


class DeploymentDescriptor:
    """
        Declarative configuration object defining how an agent is deployed
        on a specific platform, including compute, storage, messaging
        configuration, environment variables, and scaling parameters.

        All fields are exposed as read-only properties.

        :param name: The descriptor name string.
        :param target_platform: The target PlatformType value.
        :param compute_config: An optional compute configuration dictionary.
        :param storage_config: An optional storage configuration dictionary.
        :param messaging_config: An optional messaging configuration dictionary.
        :param environment_variables: An optional environment variables dictionary.
        :param scaling_parameters: An optional scaling parameters dictionary.
    """

    def __init__(self, name: str, target_platform: PlatformType,
                 compute_config: Optional[Dict[str, Any]] = None,
                 storage_config: Optional[Dict[str, Any]] = None,
                 messaging_config: Optional[Dict[str, Any]] = None,
                 environment_variables: Optional[Dict[str, str]] = None,
                 scaling_parameters: Optional[Dict[str, Any]] = None) -> None:
        self._name = name
        self._target_platform = target_platform
        self._compute_config = dict(compute_config) if compute_config is not None else {}
        self._storage_config = dict(storage_config) if storage_config is not None else {}
        self._messaging_config = dict(messaging_config) if messaging_config is not None else {}
        self._environment_variables = dict(environment_variables) if environment_variables is not None else {}
        self._scaling_parameters = dict(scaling_parameters) if scaling_parameters is not None else {}
        return

    @property
    def name(self) -> str:
        """
            The descriptor name string.

            :returns: The name string.
        """
        rtnval = self._name
        return rtnval

    @property
    def target_platform(self) -> PlatformType:
        """
            The target platform type.

            :returns: The PlatformType value.
        """
        rtnval = self._target_platform
        return rtnval

    @property
    def compute_config(self) -> dict:
        """
            A defensive copy of the compute configuration dictionary.

            :returns: A dictionary of compute configuration.
        """
        rtnval = dict(self._compute_config)
        return rtnval

    @property
    def storage_config(self) -> dict:
        """
            A defensive copy of the storage configuration dictionary.

            :returns: A dictionary of storage configuration.
        """
        rtnval = dict(self._storage_config)
        return rtnval

    @property
    def messaging_config(self) -> dict:
        """
            A defensive copy of the messaging configuration dictionary.

            :returns: A dictionary of messaging configuration.
        """
        rtnval = dict(self._messaging_config)
        return rtnval

    @property
    def environment_variables(self) -> dict:
        """
            A defensive copy of the environment variables dictionary.

            :returns: A dictionary of environment variables.
        """
        rtnval = dict(self._environment_variables)
        return rtnval

    @property
    def scaling_parameters(self) -> dict:
        """
            A defensive copy of the scaling parameters dictionary.

            :returns: A dictionary of scaling parameters.
        """
        rtnval = dict(self._scaling_parameters)
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the descriptor fields.

            :returns: A dictionary with all descriptor fields.
        """
        rtnval = {
            "name": self._name,
            "target_platform": self._target_platform.to_string(),
            "compute_config": dict(self._compute_config),
            "storage_config": dict(self._storage_config),
            "messaging_config": dict(self._messaging_config),
            "environment_variables": dict(self._environment_variables),
            "scaling_parameters": dict(self._scaling_parameters)
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the descriptor fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        rtnval = json.dumps(data, indent=2)
        return rtnval

    def to_yaml(self) -> str:
        """
            Returns a YAML string representation of the descriptor fields.

            :returns: A YAML string.
        """
        data = self.as_dict()
        rtnval = yaml.dump(data, default_flow_style=False)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "DeploymentDescriptor":
        """
            Constructs a DeploymentDescriptor from a dictionary.

            :param data: Dictionary containing descriptor fields.

            :returns: A DeploymentDescriptor instance.
        """
        platform_type = PlatformType.from_string(data["target_platform"])
        rtnval = cls(
            name=data["name"],
            target_platform=platform_type,
            compute_config=data.get("compute_config", {}),
            storage_config=data.get("storage_config", {}),
            messaging_config=data.get("messaging_config", {}),
            environment_variables=data.get("environment_variables", {}),
            scaling_parameters=data.get("scaling_parameters", {})
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "DeploymentDescriptor":
        """
            Deserializes a JSON string into a DeploymentDescriptor instance.

            :param json_str: A JSON string containing descriptor fields.

            :returns: A DeploymentDescriptor instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "DeploymentDescriptor":
        """
            Deserializes a YAML string into a DeploymentDescriptor instance.

            :param yaml_str: A YAML string containing descriptor fields.

            :returns: A DeploymentDescriptor instance.
        """
        data = yaml.safe_load(yaml_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            descriptor name, and target platform type.

            :returns: A repr string for debugging.
        """
        rtnval = "DeploymentDescriptor(name={}, target_platform={})".format(
            self._name, self._target_platform.to_string()
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the descriptor name,
            target platform type, and the scaling parameters.

            :returns: A human-readable string.
        """
        rtnval = "DeploymentDescriptor: name={}, platform={}, scaling={}".format(
            self._name, self._target_platform.to_string(), self._scaling_parameters
        )
        return rtnval
