"""
    Declarative configuration for the memory system.

    Defines backend type, connection parameters, default scope, expiration
    policy, embedding provider settings, and credential references for
    an Agent's memory system.
"""

import json
import os

from typing import Optional

import yaml

from ccai.agentkit.errors import ConfigurationError
from ccai.agentkit.expirationpolicy import ExpirationPolicy
from ccai.agentkit.memoryscope import MemoryScope


class MemoryConfiguration:
    """
        Declarative configuration for the memory system. Defines backend type,
        connection parameters, default scope, expiration policy, and
        embedding provider settings.
    """

    def __init__(self, backend_type: str, connection_params: dict = None,
                 default_scope: MemoryScope = None,
                 expiration_policy: ExpirationPolicy = None,
                 embedding_settings: dict = None,
                 credential_names: list = None):
        """
            Constructs a MemoryConfiguration.

            :param backend_type: The memory backend type string (e.g. "inmemory", "file").
            :param connection_params: Optional backend-specific connection parameters.
            :param default_scope: Optional default MemoryScope. Defaults to AGENT.
            :param expiration_policy: Optional ExpirationPolicy.
            :param embedding_settings: Optional embedding provider settings dictionary.
            :param credential_names: Optional list of CredentialReference names.
        """
        self._backend_type = backend_type
        self._connection_params = dict(connection_params) if connection_params is not None else {}
        self._default_scope = default_scope if default_scope is not None else MemoryScope.AGENT
        self._expiration_policy = expiration_policy
        self._embedding_settings = dict(embedding_settings) if embedding_settings is not None else {}
        self._credential_names = list(credential_names) if credential_names is not None else []
        return

    @property
    def backend_type(self) -> str:
        """
            The memory backend type string.

            :returns: The backend type string.
        """
        return self._backend_type

    @property
    def connection_params(self) -> dict:
        """
            Backend-specific connection parameters as a defensive copy.

            :returns: A dictionary of connection parameters.
        """
        return dict(self._connection_params)

    @property
    def default_scope(self) -> MemoryScope:
        """
            The default MemoryScope for entries stored without an explicit scope.

            :returns: A MemoryScope value.
        """
        return self._default_scope

    @property
    def expiration_policy(self) -> Optional[ExpirationPolicy]:
        """
            The expiration policy, or None if not configured.

            :returns: An ExpirationPolicy instance or None.
        """
        return self._expiration_policy

    @property
    def embedding_settings(self) -> dict:
        """
            Embedding provider settings as a defensive copy.

            :returns: A dictionary of embedding settings.
        """
        return dict(self._embedding_settings)

    @property
    def credential_names(self) -> list:
        """
            CredentialReference names required by the backend as a defensive copy.

            :returns: A list of credential name strings.
        """
        return list(self._credential_names)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration,
            excluding resolved credential values.

            :returns: A dictionary with configuration fields.
        """
        rtnval = {
            "backend_type": self._backend_type,
            "connection_params": dict(self._connection_params),
            "default_scope": self._default_scope.value,
            "expiration_policy": self._expiration_policy.as_dict() if self._expiration_policy is not None else None,
            "embedding_settings": dict(self._embedding_settings),
            "credential_names": list(self._credential_names),
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the configuration,
            excluding resolved credential values.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryConfiguration":
        """
            Constructs a MemoryConfiguration from a dictionary.

            :param data: A dictionary with configuration fields.

            :returns: A MemoryConfiguration instance.
            :raises: ConfigurationError if required fields are missing.
        """
        if "backend_type" not in data or data["backend_type"] is None:
            errmsg = "The 'backend_type' field is required in MemoryConfiguration."
            raise ConfigurationError(errmsg)

        default_scope = MemoryScope.AGENT
        if "default_scope" in data and data["default_scope"] is not None:
            default_scope = MemoryScope.from_string(data["default_scope"])

        expiration_policy = None
        if "expiration_policy" in data and data["expiration_policy"] is not None:
            expiration_policy = ExpirationPolicy.from_dict(data["expiration_policy"])

        rtnval = cls(
            backend_type=data["backend_type"],
            connection_params=data.get("connection_params"),
            default_scope=default_scope,
            expiration_policy=expiration_policy,
            embedding_settings=data.get("embedding_settings"),
            credential_names=data.get("credential_names"),
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryConfiguration":
        """
            Deserializes a JSON string into a MemoryConfiguration instance.

            :param json_str: A JSON string.

            :returns: A MemoryConfiguration instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    @classmethod
    def from_json_file(cls, file_path: str) -> "MemoryConfiguration":
        """
            Loads a MemoryConfiguration from a JSON file.

            :param file_path: Path to the JSON file.

            :returns: A MemoryConfiguration instance.
            :raises: ConfigurationError if the file cannot be read.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                json_str = fh.read()
            rtnval = cls.from_json(json_str=json_str)
            return rtnval
        except ConfigurationError:
            raise
        except Exception as exc:
            errmsg = "Failed to load MemoryConfiguration from file {!r}.".format(file_path)
            raise ConfigurationError(errmsg) from exc

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "MemoryConfiguration":
        """
            Loads a MemoryConfiguration from a YAML file.

            :param file_path: Path to the YAML file.

            :returns: A MemoryConfiguration instance.
            :raises: ConfigurationError if the file cannot be read.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            rtnval = cls.from_dict(data)
            return rtnval
        except ConfigurationError:
            raise
        except Exception as exc:
            errmsg = "Failed to load MemoryConfiguration from YAML file {!r}.".format(file_path)
            raise ConfigurationError(errmsg) from exc

    def __repr__(self) -> str:
        rtnval = "{}(backend_type={!r}, default_scope={!r})".format(
            self.__class__.__name__, self._backend_type, self._default_scope.value
        )
        return rtnval

    def __str__(self) -> str:
        exp_str = str(self._expiration_policy) if self._expiration_policy is not None else "none"
        rtnval = "MemoryConfiguration: backend={}, scope={}, expiration={}".format(
            self._backend_type, self._default_scope.value, exp_str
        )
        return rtnval

    def __eq__(self, other) -> bool:
        if not isinstance(other, MemoryConfiguration):
            rtnval = False
            return rtnval
        rtnval = (
            self._backend_type == other._backend_type
            and self._connection_params == other._connection_params
            and self._default_scope == other._default_scope
            and self._expiration_policy == other._expiration_policy
            and self._embedding_settings == other._embedding_settings
            and self._credential_names == other._credential_names
        )
        return rtnval
