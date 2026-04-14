"""
流失挽回Worker实现

负责评估玩家流失风险并制定挽回方案。
"""

from __future__ import annotations

from typing import Any

from autogen_core import RoutedAgent

from ..domain.schemas import ChurnWorkerOutput
from ..infrastructure.validation.output_validator import OutputValidator


class ChurnWorker(RoutedAgent):
    """流失挽回Worker"""

    def __init__(self, model_client: Any, tools: list[Any]) -> None:
        super().__init__("Churn挽回Worker")
        self.model_client = model_client
        self.tools = tools
        self.validator = OutputValidator(ChurnWorkerOutput, max_retries=3)

    def _create_retention_plan(self, churn_risk: Any) -> dict[str, Any]:
        """基于风险等级制定挽回计划。"""
        plans = {
            "高风险": {"actions": ["个性化优惠", "回归礼包", "VIP特权"], "priority": 3},
            "中风险": {"actions": ["回归礼包", "小额优惠"], "priority": 2},
            "低风险": {"actions": ["引导提示"], "priority": 1},
        }
        return plans.get(churn_risk.level, {"actions": [], "priority": 0})
