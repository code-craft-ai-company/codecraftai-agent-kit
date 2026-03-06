"""
    Defines the MemoryStoreHealthCheck for checking MemoryStore availability.
"""

import time

from automojo.agentkit.healthcheck import HealthCheck
from automojo.agentkit.healthstatus import HealthStatus


class MemoryStoreHealthCheck(HealthCheck):
    """
        Checks MemoryStore availability via a lightweight read.

        :param name: The health check name.
        :param memory_store: The memory store instance to check.
        :param check_interval: The interval between checks in seconds.
    """

    def __init__(self, name: str, memory_store, check_interval: float = 30.0) -> None:
        super().__init__(name, check_interval)
        self._memory_store = memory_store
        return

    def check(self) -> HealthStatus:
        start = time.monotonic()
        try:
            self._memory_store.ping()
            elapsed = time.monotonic() - start
            return HealthStatus(self._name, "healthy", response_time=elapsed)
        except Exception as exc:
            elapsed = time.monotonic() - start
            return HealthStatus(self._name, "unhealthy", detail=str(exc), response_time=elapsed)
