"""
流失挽回Worker实现

负责评估玩家流失风险并制定挽回方案。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from autogen_core import MessageContext, RoutedAgent, rpc

from ..domain.messages import InterventionTask, WorkerResponse
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
        level = getattr(churn_risk, "level", None) or getattr(
            churn_risk, "risk_level", "低风险"
        )
        plans = {
            "高风险": {"actions": ["个性化优惠", "回归礼包", "VIP特权"], "priority": 3},
            "中风险": {"actions": ["回归礼包", "小额优惠"], "priority": 2},
            "低风险": {"actions": ["引导提示"], "priority": 1},
        }
        return plans.get(level, {"actions": [], "priority": 0})

    @rpc
    async def handle_intervention_task(
        self, message: InterventionTask, ctx: MessageContext
    ) -> WorkerResponse:
        """将干预任务转换为流失挽回响应。"""
        risk_level, risk_score = self._infer_risk(message)
        plan = self._create_retention_plan(SimpleNamespace(level=risk_level))
        validated = ChurnWorkerOutput.model_validate(
            {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "retention_plan": self._build_actions(plan["actions"]),
                "expected_effectiveness": max(0.0, risk_score - 0.1),
            }
        )

        return WorkerResponse(
            task_id=message.task_id,
            worker_type="churn",
            intervention_actions=validated.retention_plan,
            confidence=validated.risk_score,
            metadata={
                "risk_level": validated.risk_level,
                "priority": plan["priority"],
            },
        )

    @staticmethod
    def _build_actions(actions: list[str]) -> list[dict[str, Any]]:
        mapping = {
            "个性化优惠": {"action_type": "grant_reward", "reward": "personal_offer"},
            "回归礼包": {"action_type": "grant_reward", "reward": "return_bundle"},
            "VIP特权": {"action_type": "assign_support", "channel": "vip_retention"},
            "小额优惠": {"action_type": "send_email", "template": "discount_offer"},
            "引导提示": {"action_type": "send_email", "template": "guidance_tip"},
        }
        return [mapping[action] for action in actions if action in mapping]

    @staticmethod
    def _infer_risk(message: InterventionTask) -> tuple[str, float]:
        scenarios = " ".join(
            str(item.get("scenario", "")) for item in message.context["triggered_scenarios"]
        ).lower()
        history = " ".join(
            str(item.get("action", "")) for item in message.context["behavior_history"]
        ).lower()

        if any(keyword in scenarios or keyword in history for keyword in ("quit", "cancel", "negative", "uninstall", "sell")):
            return "高风险", 0.90
        if any(keyword in scenarios or keyword in history for keyword in ("inactive", "low_activity", "drop")):
            return "中风险", 0.65
        return "低风险", 0.35
