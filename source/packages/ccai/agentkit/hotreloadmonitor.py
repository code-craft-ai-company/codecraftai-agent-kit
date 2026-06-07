"""
    Defines the HotReloadMonitor class that watches configuration sources
    for changes and triggers reload in the codecraftai-agent-kit framework.

    The HotReloadMonitor runs on a configurable polling interval defined
    by a HotReloadPolicy and notifies the ConfigurationManager of detected
    changes. It uses a daemon thread for background monitoring and stores
    file modification timestamps to detect changes.
"""

import logging
import os
import threading

from ccai.agentkit.configurationerrors import ConfigurationValidationError


class HotReloadMonitor:
    """
        Watches configuration sources for changes and triggers reload.
        Runs on a configurable polling interval and notifies the
        ConfigurationManager of detected changes.

        :param configuration_manager: The ConfigurationManager instance to
            notify when changes are detected.
        :param policy: The HotReloadPolicy defining monitoring behavior.
    """

    def __init__(self, configuration_manager, policy) -> None:
        self._configuration_manager = configuration_manager
        self._policy = policy
        self._is_active = False
        self._change_count = 0
        self._logger = logging.getLogger("ccai.agentkit.configuration")
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._file_timestamps = {}
        return

    @property
    def is_active(self) -> bool:
        """
            Whether the monitor is currently active and polling for changes.

            :returns: True if monitoring is active, False otherwise.
        """
        return self._is_active

    @property
    def change_count(self) -> int:
        """
            The number of configuration changes detected since the monitor
            was started.

            :returns: The count of detected changes.
        """
        return self._change_count

    def start(self) -> None:
        """
            Begins monitoring configured file paths and environment variables
            at the polling interval defined in the HotReloadPolicy.

            Sets is_active to True and starts a daemon background thread
            that polls file modification timestamps. When a file change is
            detected, calls configuration_manager.reload() and increments
            change_count. On reload failure (ConfigurationValidationError),
            logs WARNING and retains previous config.
        """
        if self._is_active is True:
            return

        self._is_active = True
        self._stop_event.clear()
        self._file_timestamps = self._capture_file_timestamps()

        self._logger.info(
            "Starting hot-reload monitor with polling interval %.1f seconds",
            self._policy.polling_interval
        )

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="hotreload-monitor",
            daemon=True
        )
        self._monitor_thread.start()
        return

    def stop(self) -> None:
        """
            Stops monitoring and releases resources. Sets is_active to False
            and stops the background thread.
        """
        if self._is_active is False:
            return

        self._is_active = False
        self._stop_event.set()

        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=self._policy.polling_interval * 2)
            self._monitor_thread = None

        self._logger.info("Stopped hot-reload monitor")
        return

    def _monitor_loop(self) -> None:
        """
            Background thread loop that polls for file changes at the
            configured polling interval. Exits when the stop event is set.
        """
        while self._stop_event.is_set() is False:
            stopped = self._stop_event.wait(timeout=self._policy.polling_interval)

            if stopped is True:
                break

            self._check_for_changes()

        return

    def _check_for_changes(self) -> None:
        """
            Checks all monitored files for modification timestamp changes.
            When a change is detected, triggers a reload on the
            ConfigurationManager and increments the change count.
        """
        current_timestamps = self._capture_file_timestamps()
        change_detected = False

        for file_path, current_mtime in current_timestamps.items():
            previous_mtime = self._file_timestamps.get(file_path)

            if previous_mtime is None:
                change_detected = True
            elif current_mtime != previous_mtime:
                change_detected = True

        for file_path in self._file_timestamps:
            if file_path not in current_timestamps:
                change_detected = True

        if change_detected is True:
            self._file_timestamps = current_timestamps
            self._trigger_reload()

        return

    def _trigger_reload(self) -> None:
        """
            Triggers a configuration reload on the ConfigurationManager.
            On success, increments the change count. On
            ConfigurationValidationError, logs a WARNING and retains the
            previous configuration.
        """
        try:
            self._configuration_manager.reload()
            self._change_count = self._change_count + 1
        except ConfigurationValidationError as validation_err:
            self._logger.warning(
                "Hot-reload failed due to configuration validation error: %s",
                str(validation_err)
            )
        except Exception as exc:
            self._logger.warning(
                "Hot-reload failed due to unexpected error: %s",
                str(exc)
            )

        return

    def _capture_file_timestamps(self) -> dict:
        """
            Captures the current modification timestamps for all monitored
            files defined in the policy.

            :returns: A dictionary mapping file path strings to their
                modification timestamps as floats.
        """
        timestamps = {}
        monitored_files = self._policy.monitored_files

        for file_path in monitored_files:
            if os.path.isfile(file_path) is True:
                mtime = os.path.getmtime(file_path)
                timestamps[file_path] = mtime

        return timestamps

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            monitoring status, and polling interval.

            :returns: A repr string for debugging.
        """
        repr_str = "HotReloadMonitor(is_active={}, polling_interval={})".format(
            self._is_active, self._policy.polling_interval
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the monitoring status,
            polling interval, and count of monitored files.

            :returns: A human-readable string.
        """
        monitored_count = len(self._policy.monitored_files)
        str_val = "HotReloadMonitor (is_active={}, polling_interval={}, monitored_files={})".format(
            self._is_active, self._policy.polling_interval, monitored_count
        )
        return str_val
