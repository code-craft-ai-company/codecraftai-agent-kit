"""
    Defines the SelfHealingPolicy class for configuring self-healing
    behavior per health check.
"""

from ccai.agentkit.selfhealingaction import SelfHealingAction


class SelfHealingPolicy:
    """
        Immutable configuration object defining the self-healing behavior
        for a specific health check.

        :param check_name: The health check name this policy applies to.
        :param action: The SelfHealingAction to execute.
        :param max_attempts: Maximum healing attempts before cooldown.
        :param cooldown_interval: Seconds to wait after max attempts exhausted.
    """

    def __init__(self, check_name: str, action: SelfHealingAction,
                 max_attempts: int, cooldown_interval: float) -> None:
        self._check_name = check_name
        self._action = action
        self._max_attempts = max_attempts
        self._cooldown_interval = cooldown_interval
        return

    @property
    def check_name(self) -> str:
        return self._check_name

    @property
    def action(self) -> SelfHealingAction:
        return self._action

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    @property
    def cooldown_interval(self) -> float:
        return self._cooldown_interval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the policy fields.

            :returns: A dictionary of policy fields.
        """
        result = {
            "check_name": self._check_name,
            "action_name": self._action.action_name,
            "max_attempts": self._max_attempts,
            "cooldown_interval": self._cooldown_interval
        }
        return result

    def __repr__(self) -> str:
        return "SelfHealingPolicy(check_name={!r}, action={!r})".format(
            self._check_name, self._action.action_name
        )

    def __str__(self) -> str:
        return "SelfHealingPolicy check='{}', action='{}', max_attempts={}, cooldown={}s".format(
            self._check_name, self._action.action_name,
            self._max_attempts, self._cooldown_interval
        )
