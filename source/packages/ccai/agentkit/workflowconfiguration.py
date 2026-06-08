"""
    Defines the WorkflowConfiguration class for declarative workflow
    execution settings in the Workflow & Orchestration feature.

    A WorkflowConfiguration contains the maximum parallel workers,
    checkpoint interval, default approval timeout, and an optional
    default retry policy. The class provides JSON and YAML
    serialization and deserialization, including file-based loading
    with optional AppContext path resolution.

    Requirements: 17.1-17.16, 23.23, 23.24
"""

import json
import os

from typing import Optional

import yaml

from ccai.agentkit.errors import ConfigurationError


class WorkflowConfiguration:
    """
        Configuration object defining default workflow execution
        settings.

        A WorkflowConfiguration captures the maximum number of
        parallel workers, the checkpoint interval (number of steps
        between automatic checkpoints), the default approval timeout
        in seconds, and an optional default retry policy. All fields
        are exposed as read-only properties.

        Validation is performed at construction time:
        - max_parallel_workers must be >= 1
        - default_approval_timeout must be > 0

        :param max_parallel_workers: The maximum number of
            concurrently executing branches. Must be >= 1.
            Defaults to 4.
        :param checkpoint_interval: The number of steps between
            automatic checkpoints. Defaults to 1.
        :param default_approval_timeout: The default timeout in
            seconds for approval requests. Must be > 0.
            Defaults to 3600.0.
        :param default_retry_policy: An optional default retry
            policy for workflow steps. Defaults to None.

        :raises ConfigurationError: If max_parallel_workers < 1
            or default_approval_timeout <= 0.
    """

    def __init__(self, max_parallel_workers: int = 4,
                 checkpoint_interval: int = 1,
                 default_approval_timeout: float = 3600.0,
                 default_retry_policy=None) -> None:

        if max_parallel_workers < 1:
            errmsg = "The maximum parallel workers must be at least 1, got {}.".format(
                max_parallel_workers
            )
            raise ConfigurationError(errmsg)

        if default_approval_timeout <= 0:
            errmsg = "The default approval timeout must be a positive value, got {}.".format(
                default_approval_timeout
            )
            raise ConfigurationError(errmsg)

        self._max_parallel_workers = max_parallel_workers
        self._checkpoint_interval = checkpoint_interval
        self._default_approval_timeout = default_approval_timeout
        self._default_retry_policy = default_retry_policy
        return

    @property
    def max_parallel_workers(self) -> int:
        """
            The maximum number of concurrently executing branches.

            :returns: An integer >= 1.
        """
        return self._max_parallel_workers

    @property
    def checkpoint_interval(self) -> int:
        """
            The number of steps between automatic checkpoints.

            :returns: An integer representing the checkpoint interval.
        """
        return self._checkpoint_interval

    @property
    def default_approval_timeout(self) -> float:
        """
            The default timeout in seconds for approval requests.

            :returns: A positive float in seconds.
        """
        return self._default_approval_timeout

    @property
    def default_retry_policy(self):
        """
            The optional default retry policy for workflow steps.

            :returns: A retry policy object or None.
        """
        return self._default_retry_policy

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration.

            The default_retry_policy is included only when it is
            not None.

            :returns: A dictionary containing all configuration
                fields.
        """
        rtnval = {
            "max_parallel_workers": self._max_parallel_workers,
            "checkpoint_interval": self._checkpoint_interval,
            "default_approval_timeout": self._default_approval_timeout,
        }

        if self._default_retry_policy is not None:
            rtnval["default_retry_policy"] = self._default_retry_policy

        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the
            configuration.

            :returns: A JSON string containing all configuration
                fields.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    def to_yaml(self) -> str:
        """
            Returns a YAML string representation of the
            configuration.

            :returns: A YAML string containing all configuration
                fields.
        """
        data = self.as_dict()
        rtnval = yaml.dump(data, default_flow_style=False)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowConfiguration":
        """
            Constructs a WorkflowConfiguration from a dictionary.

            :param data: A dictionary containing configuration
                fields.

            :returns: A WorkflowConfiguration instance.
        """
        max_parallel_workers = data.get("max_parallel_workers", 4)
        checkpoint_interval = data.get("checkpoint_interval", 1)
        default_approval_timeout = data.get("default_approval_timeout", 3600.0)
        default_retry_policy = data.get("default_retry_policy", None)

        rtnval = cls(
            max_parallel_workers=max_parallel_workers,
            checkpoint_interval=checkpoint_interval,
            default_approval_timeout=default_approval_timeout,
            default_retry_policy=default_retry_policy
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowConfiguration":
        """
            Deserializes a JSON string into a WorkflowConfiguration
            instance.

            :param json_str: A JSON string containing configuration
                fields.

            :returns: A WorkflowConfiguration instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "WorkflowConfiguration":
        """
            Deserializes a YAML string into a WorkflowConfiguration
            instance.

            :param yaml_str: A YAML string containing configuration
                fields.

            :returns: A WorkflowConfiguration instance.
        """
        data = yaml.safe_load(yaml_str)
        rtnval = cls.from_dict(data)
        return rtnval

    @classmethod
    def from_json_file(cls, file_path: str,
                       app_context=None) -> "WorkflowConfiguration":
        """
            Loads a WorkflowConfiguration from a JSON file.

            When an app_context is provided, the file path is
            resolved relative to the AppContext directory.

            :param file_path: The path to the JSON configuration
                file.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A WorkflowConfiguration instance.
        """
        resolved_path = file_path

        if app_context is not None:
            base_dir = app_context.home_directory
            resolved_path = os.path.join(base_dir, file_path)

        with open(resolved_path, "r") as fh:
            json_str = fh.read()

        rtnval = cls.from_json(json_str)
        return rtnval

    @classmethod
    def from_yaml_file(cls, file_path: str,
                       app_context=None) -> "WorkflowConfiguration":
        """
            Loads a WorkflowConfiguration from a YAML file.

            When an app_context is provided, the file path is
            resolved relative to the AppContext directory.

            :param file_path: The path to the YAML configuration
                file.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A WorkflowConfiguration instance.
        """
        resolved_path = file_path

        if app_context is not None:
            base_dir = app_context.home_directory
            resolved_path = os.path.join(base_dir, file_path)

        with open(resolved_path, "r") as fh:
            yaml_str = fh.read()

        rtnval = cls.from_yaml(yaml_str)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, maximum parallel workers, and checkpoint
            interval.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(max_parallel_workers={}, checkpoint_interval={})".format(
            self.__class__.__name__, self._max_parallel_workers,
            self._checkpoint_interval
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the maximum
            parallel workers, checkpoint interval, and default
            approval timeout.

            :returns: A human-readable string describing the
                configuration.
        """
        str_val = (
            "WorkflowConfiguration: max_parallel_workers={}, "
            "checkpoint_interval={}, default_approval_timeout={}s"
        ).format(
            self._max_parallel_workers, self._checkpoint_interval,
            self._default_approval_timeout
        )
        return str_val
