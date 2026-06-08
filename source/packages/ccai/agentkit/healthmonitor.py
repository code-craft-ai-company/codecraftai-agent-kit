"""
    Defines the HealthMonitor class for periodic health check execution
    and self-healing in the Error Handling & Resilience feature.
"""

import logging
import time

from ccai.agentkit.healthcheckregistry import HealthCheckRegistry
from ccai.agentkit.healthstatus import HealthStatus
from ccai.agentkit.selfhealingresult import SelfHealingResult


class HealthMonitor:
    """
        Periodically executes registered HealthCheck instances and aggregates
        results into an overall agent health status. Triggers self-healing
        actions when unhealthy components are detected.

        :param health_check_registry: The HealthCheckRegistry to monitor.
        :param check_interval: Default interval between checks in seconds.
    """

    def __init__(self, health_check_registry: HealthCheckRegistry,
                 check_interval: float = 30.0) -> None:
        self._health_check_registry = health_check_registry
        self._check_interval = check_interval
        self._is_active = False
        self._latest_results = {}
        self._healing_policies = {}
        self._healing_attempt_counts = {}
        self._healing_cooldown_timestamps = {}
        self._logger = logging.getLogger("ccai.agentkit.resilience")
        return

    @property
    def is_active(self) -> bool:
        """
            Whether the monitor is actively running.

            :returns: Boolean indicating active state.
        """
        return self._is_active

    @property
    def latest_results(self) -> dict:
        """
            Returns the most recent HealthStatus for each registered check.

            :returns: Dictionary of check name to HealthStatus.
        """
        return dict(self._latest_results)

    @property
    def overall_status(self) -> str:
        """
            Returns the overall agent health status.

            Returns "healthy" when all checks are healthy, "degraded" when
            any is degraded but none unhealthy, "unhealthy" when any check
            is unhealthy. Returns "healthy" when no results exist.

            :returns: Overall status string.
        """
        if not self._latest_results:
            return "healthy"

        has_unhealthy = False
        has_degraded = False

        for status in self._latest_results.values():
            if status.status == "unhealthy":
                has_unhealthy = True
            elif status.status == "degraded":
                has_degraded = True

        if has_unhealthy:
            return "unhealthy"
        if has_degraded:
            return "degraded"
        return "healthy"

    def register_healing_policy(self, policy) -> None:
        """
            Registers a SelfHealingPolicy for a specific health check.

            :param policy: The SelfHealingPolicy to register.
        """
        self._healing_policies[policy.check_name] = policy
        return

    def start(self) -> None:
        """
            Marks the monitor as active. Actual periodic scheduling is
            handled externally (e.g., by the Agent lifecycle).
        """
        self._is_active = True
        return

    def stop(self) -> None:
        """
            Marks the monitor as inactive.
        """
        self._is_active = False
        return

    def check_now(self) -> dict:
        """
            Immediately executes all registered health checks, triggers
            self-healing for unhealthy checks, and returns the results.

            :returns: Dictionary of check name to HealthStatus.
        """
        results = {}
        checks = self._health_check_registry.list_all()

        for health_check in checks:
            check_name = health_check.name
            status = self._execute_check(health_check)
            results[check_name] = status
            self._latest_results[check_name] = status

            if status.status == "unhealthy":
                self._logger.warning(
                    "Health check '%s' is unhealthy: %s",
                    check_name, status.detail
                )
                self._attempt_healing(check_name, status)
            elif status.status == "degraded":
                self._logger.warning(
                    "Health check '%s' is degraded: %s",
                    check_name, status.detail
                )
            else:
                self._logger.debug(
                    "Health check '%s' is healthy", check_name
                )
                self._reset_healing_state(check_name)

        return results

    def _execute_check(self, health_check) -> HealthStatus:
        """
            Executes a single health check, catching exceptions as unhealthy.

            :param health_check: The HealthCheck to execute.

            :returns: A HealthStatus object.
        """
        try:
            status = health_check.check()
            return status
        except Exception as exc:
            self._logger.warning(
                "Health check '%s' raised exception: %s",
                health_check.name, exc
            )
            status = HealthStatus(
                check_name=health_check.name,
                status="unhealthy",
                detail="check raised exception: {}".format(str(exc))
            )
            return status

    def _attempt_healing(self, check_name: str, status: HealthStatus) -> None:
        """
            Attempts self-healing for an unhealthy check if a policy exists
            and attempt/cooldown limits allow it.

            :param check_name: The health check name.
            :param status: The unhealthy HealthStatus.
        """
        if check_name not in self._healing_policies:
            return

        policy = self._healing_policies[check_name]

        # Check cooldown
        cooldown_ts = self._healing_cooldown_timestamps.get(check_name)
        if cooldown_ts is not None:
            elapsed = time.monotonic() - cooldown_ts
            if elapsed < policy.cooldown_interval:
                self._logger.debug(
                    "Healing for '%s' in cooldown (%.1fs remaining)",
                    check_name, policy.cooldown_interval - elapsed
                )
                return

        # Check attempt count
        attempt_count = self._healing_attempt_counts.get(check_name, 0)
        if attempt_count >= policy.max_attempts:
            self._logger.debug(
                "Healing for '%s' reached max attempts (%d), entering cooldown",
                check_name, policy.max_attempts
            )
            self._healing_cooldown_timestamps[check_name] = time.monotonic()
            self._healing_attempt_counts[check_name] = 0
            return

        # Execute healing
        self._healing_attempt_counts[check_name] = attempt_count + 1
        healing_result = self._execute_healing(check_name, status, policy)

        self._logger.info(
            "Self-healing for '%s' with action '%s': success=%s",
            check_name, policy.action.action_name, healing_result.success
        )
        return

    def _execute_healing(self, check_name: str, status: HealthStatus,
                         policy) -> SelfHealingResult:
        """
            Executes the healing action, catching exceptions as failures.

            :param check_name: The health check name.
            :param status: The unhealthy HealthStatus.
            :param policy: The SelfHealingPolicy.

            :returns: A SelfHealingResult.
        """
        try:
            result = policy.action.heal(check_name, status)
            return result
        except Exception as exc:
            self._logger.warning(
                "Self-healing action '%s' for '%s' raised exception: %s",
                policy.action.action_name, check_name, exc
            )
            result = SelfHealingResult(
                check_name=check_name,
                action_name=policy.action.action_name,
                success=False,
                error_message=str(exc)
            )
            return result

    def _reset_healing_state(self, check_name: str) -> None:
        """
            Resets healing attempt count and cooldown for a check that
            has returned to healthy.

            :param check_name: The health check name.
        """
        if check_name in self._healing_attempt_counts:
            del self._healing_attempt_counts[check_name]
        if check_name in self._healing_cooldown_timestamps:
            del self._healing_cooldown_timestamps[check_name]
        return

    def __repr__(self) -> str:
        return "HealthMonitor(active={}, checks={})".format(
            self._is_active, self._health_check_registry.count
        )

    def __str__(self) -> str:
        return "HealthMonitor active={}, checks={}, overall={}".format(
            self._is_active, self._health_check_registry.count, self.overall_status
        )
