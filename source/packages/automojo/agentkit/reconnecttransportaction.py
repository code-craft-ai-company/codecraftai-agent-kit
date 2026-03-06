"""
    Defines the ReconnectTransportAction for reconnecting a Transport instance.
"""

from datetime import datetime

from automojo.agentkit.healthstatus import HealthStatus
from automojo.agentkit.selfhealingaction import SelfHealingAction
from automojo.agentkit.selfhealingresult import SelfHealingResult


class ReconnectTransportAction(SelfHealingAction):
    """
        Attempts to disconnect and reconnect a Transport instance.

        :param transport: The transport instance to reconnect.
    """

    def __init__(self, transport) -> None:
        super().__init__(action_name="reconnect_transport")
        self._transport = transport
        return

    def heal(self, check_name: str, status: HealthStatus) -> SelfHealingResult:
        """
            Disconnects and reconnects the transport.

            :param check_name: Name of the health check that triggered healing.
            :param status: The HealthStatus that triggered the action.

            :returns: A SelfHealingResult indicating success or failure.
        """
        try:
            self._transport.disconnect()
            self._transport.connect()
            result = SelfHealingResult(
                check_name=check_name,
                action_name=self._action_name,
                success=True
            )
            return result
        except Exception as exc:
            result = SelfHealingResult(
                check_name=check_name,
                action_name=self._action_name,
                success=False,
                error_message=str(exc)
            )
            return result
