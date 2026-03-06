"""
    Defines the ClearCacheAction for clearing cached data in a component.
"""

from automojo.agentkit.healthstatus import HealthStatus
from automojo.agentkit.selfhealingaction import SelfHealingAction
from automojo.agentkit.selfhealingresult import SelfHealingResult


class ClearCacheAction(SelfHealingAction):
    """
        Clears cached data in a specified component by invoking a callable.

        :param cache_clear_callable: A callable that clears the cache.
    """

    def __init__(self, cache_clear_callable) -> None:
        super().__init__(action_name="clear_cache")
        self._cache_clear_callable = cache_clear_callable
        return

    def heal(self, check_name: str, status: HealthStatus) -> SelfHealingResult:
        """
            Invokes the cache clear callable.

            :param check_name: Name of the health check that triggered healing.
            :param status: The HealthStatus that triggered the action.

            :returns: A SelfHealingResult indicating success or failure.
        """
        try:
            self._cache_clear_callable()
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
