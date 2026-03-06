"""
    Defines the CostTracker class for accumulating token usage and cost
    estimate records across multiple LLM requests.

    CostTracker provides totals and per-provider breakdowns of TokenUsage
    and CostEstimate records. It is a mutable accumulator owned by an Agent
    instance.
"""

from automojo.agentkit.tokenusage import TokenUsage
from automojo.agentkit.costestimate import CostEstimate


class CostTracker:
    """
        Accumulates TokenUsage and CostEstimate records across multiple
        LLM requests, providing totals and per-provider breakdowns.
    """

    def __init__(self) -> None:
        self._records = []
        return

    def record(self, provider_name: str, token_usage: TokenUsage,
               cost_estimate: CostEstimate) -> None:
        """
            Records a single LLM request's usage and cost.

            :param provider_name: The provider name for this record.
            :param token_usage: The TokenUsage for this request.
            :param cost_estimate: The CostEstimate for this request.
        """
        entry = {
            "provider_name": provider_name,
            "token_usage": token_usage,
            "cost_estimate": cost_estimate
        }
        self._records.append(entry)
        return

    @property
    def total_token_usage(self) -> TokenUsage:
        """
            Returns the total TokenUsage across all tracked requests.

            :returns: A TokenUsage with summed counts, or TokenUsage(0, 0, 0) if empty.
        """
        rtnval = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        for entry in self._records:
            rtnval = rtnval + entry["token_usage"]

        return rtnval

    @property
    def total_cost_estimate(self) -> CostEstimate:
        """
            Returns the total CostEstimate across all tracked requests.

            :returns: A CostEstimate with summed costs.
        """
        prompt_total = sum(e["cost_estimate"].prompt_cost for e in self._records)
        completion_total = sum(e["cost_estimate"].completion_cost for e in self._records)
        total = prompt_total + completion_total

        rtnval = CostEstimate(
            prompt_cost=prompt_total,
            completion_cost=completion_total,
            total_cost=total
        )
        return rtnval

    def per_provider_breakdown(self) -> dict:
        """
            Returns a per-provider breakdown of TokenUsage and CostEstimate totals.

            :returns: A dictionary keyed by provider name with token_usage
                and cost_estimate values.
        """
        breakdown = {}

        for entry in self._records:
            pname = entry["provider_name"]

            if pname not in breakdown:
                breakdown[pname] = {
                    "token_usage": TokenUsage(0, 0, 0),
                    "cost_estimate": CostEstimate(0.0, 0.0, 0.0)
                }

            breakdown[pname]["token_usage"] = breakdown[pname]["token_usage"] + entry["token_usage"]

            existing_cost = breakdown[pname]["cost_estimate"]
            new_prompt = existing_cost.prompt_cost + entry["cost_estimate"].prompt_cost
            new_completion = existing_cost.completion_cost + entry["cost_estimate"].completion_cost

            breakdown[pname]["cost_estimate"] = CostEstimate(
                prompt_cost=new_prompt,
                completion_cost=new_completion,
                total_cost=new_prompt + new_completion
            )

        rtnval = breakdown
        return rtnval

    @property
    def request_count(self) -> int:
        """
            The count of tracked requests.

            :returns: The number of recorded requests as an integer.
        """
        rtnval = len(self._records)
        return rtnval

    def reset(self) -> None:
        """
            Clears all accumulated records.
        """
        self._records = []
        return
