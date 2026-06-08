"""
    Defines the HotReloadPolicy class representing declarative hot-reload
    behavior settings for the codecraftai-agent-kit framework.

    A HotReloadPolicy contains a polling interval, a list of monitored file
    paths, an environment monitoring enabled flag, and an automatic reload
    enabled flag. The HotReloadMonitor uses a HotReloadPolicy to determine
    how and when to check for configuration changes.
"""

import json


class HotReloadPolicy:
    """
        Configuration object defining hot-reload behavior including polling
        interval, monitored file paths, and automatic reload settings.

        :param polling_interval: The polling interval in seconds as a float.
        :param monitored_files: A list of file path strings to monitor for changes.
        :param environment_monitoring_enabled: Whether environment variable monitoring is enabled.
        :param automatic_reload_enabled: Whether automatic reload is enabled when changes are detected.
    """

    def __init__(self, polling_interval: float = 5.0, monitored_files: list = None,
                 environment_monitoring_enabled: bool = False,
                 automatic_reload_enabled: bool = True) -> None:
        self._polling_interval = polling_interval

        if monitored_files is not None:
            self._monitored_files = list(monitored_files)
        else:
            self._monitored_files = []

        self._environment_monitoring_enabled = environment_monitoring_enabled
        self._automatic_reload_enabled = automatic_reload_enabled
        return

    @property
    def polling_interval(self) -> float:
        """
            The polling interval in seconds.

            :returns: The polling interval as a float.
        """
        return self._polling_interval

    @property
    def monitored_files(self) -> list:
        """
            A defensive copy of the list of monitored file paths.

            :returns: A list copy of the monitored file path strings.
        """
        monitored_copy = list(self._monitored_files)
        return monitored_copy

    @property
    def environment_monitoring_enabled(self) -> bool:
        """
            Whether environment variable monitoring is enabled.

            :returns: True if environment monitoring is enabled, False otherwise.
        """
        return self._environment_monitoring_enabled

    @property
    def automatic_reload_enabled(self) -> bool:
        """
            Whether automatic reload is enabled when changes are detected.

            :returns: True if automatic reload is enabled, False otherwise.
        """
        return self._automatic_reload_enabled

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the policy fields.

            :returns: A dictionary with polling_interval, monitored_files,
                environment_monitoring_enabled, and automatic_reload_enabled.
        """
        result = {
            "polling_interval": self._polling_interval,
            "monitored_files": list(self._monitored_files),
            "environment_monitoring_enabled": self._environment_monitoring_enabled,
            "automatic_reload_enabled": self._automatic_reload_enabled
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the policy fields.

            :returns: A JSON string containing all policy fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "HotReloadPolicy":
        """
            Constructs a HotReloadPolicy from a dictionary.

            :param data: A dictionary containing polling_interval, monitored_files,
                environment_monitoring_enabled, and automatic_reload_enabled.

            :returns: A HotReloadPolicy instance reconstructed from the dictionary.
        """
        polling_interval = data.get("polling_interval", 5.0)
        monitored_files = data.get("monitored_files", None)
        environment_monitoring_enabled = data.get("environment_monitoring_enabled", False)
        automatic_reload_enabled = data.get("automatic_reload_enabled", True)

        policy = cls(
            polling_interval=polling_interval,
            monitored_files=monitored_files,
            environment_monitoring_enabled=environment_monitoring_enabled,
            automatic_reload_enabled=automatic_reload_enabled
        )
        return policy

    @classmethod
    def from_json(cls, json_str: str) -> "HotReloadPolicy":
        """
            Deserializes a JSON string into a HotReloadPolicy instance.

            :param json_str: A JSON string containing policy fields.

            :returns: A HotReloadPolicy instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        policy = cls.from_dict(data)
        return policy

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            polling interval, and automatic reload enabled status.

            :returns: A repr string for debugging.
        """
        repr_str = "HotReloadPolicy(polling_interval={}, automatic_reload_enabled={})".format(
            self._polling_interval, self._automatic_reload_enabled
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the polling interval,
            monitored file count, and automatic reload enabled status.

            :returns: A human-readable string.
        """
        monitored_count = len(self._monitored_files)
        str_val = "HotReloadPolicy (polling_interval={}, monitored_files={}, automatic_reload_enabled={})".format(
            self._polling_interval, monitored_count, self._automatic_reload_enabled
        )
        return str_val
