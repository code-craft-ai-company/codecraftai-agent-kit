"""
    Defines the TransportHealthCheck for checking Transport connectivity.
"""

import time

from automojo.agentkit.healthcheck import HealthCheck
from automojo.agentkit.healthstatus import HealthStatus


class TransportHealthCheck(HealthCheck):
    """
        Checks Transport connection status.

        :param name: The health check name.
        :param transport: The transport instance to check.
        :param check_interval: The interval between checks in seconds.
    """

    def __init__(self, name: str, transport, check_interval: float = 30.0) -> None:
        super().__init__(name, check_interval)
        self._transport = transport
        return

    def check(self) -> HealthStatus:
        start = time.monotonic()
        try:
            is_connected = self._transport.is_connected
            elapsed = time.monotonic() - start
            if is_connected:
                return HealthStatus(self._name, "healthy", response_time=elapsed)
            else:
                return HealthStatus(self._name, "unhealthy", detail="not connected", response_time=elapsed)
        except Exception as exc:
            elapsed = time.monotonic() - start
            return HealthStatus(self._name, "unhealthy", detail=str(exc), response_time=elapsed)
