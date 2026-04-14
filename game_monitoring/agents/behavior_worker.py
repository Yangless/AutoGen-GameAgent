"""
行为管控Worker实现

负责检测异常行为并制定管控措施。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from autogen_core import MessageContext, RoutedAgent, rpc

from ..domain.messages import InterventionTask, WorkerResponse
from ..domain.schemas import BehaviorWorkerOutput
from ..infrastructure.validation.output_validator import OutputValidator


class BehaviorWorker(RoutedAgent):
    """行为管控Worker"""

    def __init__(self, model_client: Any, tools: list[Any]) -> None:
        super().__init__("Behavior管控Worker")
        self.model_client = model_client
        self.tools = tools
        self.validator = OutputValidator(BehaviorWorkerOutput, max_retries=3)

    def _decide_measures(self, bot_result: Any) -> list[str]:
        """根据检测结果决定管控措施。"""
        confidence = getattr(bot_result, "confidence", None)
        if confidence is None:
            confidence = getattr(bot_result, "bot_confidence", 0.0)

        if bot_result.is_bot and confidence > 0.8:
            return ["账号限制", "人工审核"]
        if bot_result.is_bot and confidence > 0.5:
            return ["行为警告", "密切监控"]
        return ["正常监控"]

    @rpc
    async def handle_intervention_task(
        self, message: InterventionTask, ctx: MessageContext
    ) -> WorkerResponse:
        """将干预任务转换为行为管控响应。"""
        is_bot, confidence, risk_tags = self._infer_behavior_risk(message)
        measures = self._decide_measures(
            SimpleNamespace(is_bot=is_bot, confidence=confidence)
        )
        validated = BehaviorWorkerOutput.model_validate(
            {
                "is_bot": is_bot,
                "bot_confidence": confidence,
                "control_measures": self._build_actions(measures),
                "risk_tags": risk_tags,
            }
        )

        return WorkerResponse(
            task_id=message.task_id,
            worker_type="behavior",
            intervention_actions=validated.control_measures,
            confidence=validated.bot_confidence,
            metadata={
                "is_bot": validated.is_bot,
                "priority": 4 if validated.is_bot else 1,
                "risk_tags": validated.risk_tags,
            },
        )

    @staticmethod
    def _build_actions(actions: list[str]) -> list[dict[str, Any]]:
        mapping = {
            "账号限制": {"action_type": "restrict_account"},
            "人工审核": {"action_type": "manual_review"},
            "行为警告": {"action_type": "send_warning"},
            "密切监控": {"action_type": "monitor_account"},
            "正常监控": {"action_type": "monitor_account"},
        }
        return [mapping[action] for action in actions if action in mapping]

    @staticmethod
    def _infer_behavior_risk(message: InterventionTask) -> tuple[bool, float, list[str]]:
        scenarios = [
            str(item.get("scenario", "")).lower()
            for item in message.context["triggered_scenarios"]
        ]
        history = [
            str(item.get("action", "")).lower()
            for item in message.context["behavior_history"]
        ]

        bot_like = any("bot" in scenario or "abnormal" in scenario for scenario in scenarios)
        repetitive = len(history) >= 8 and len(set(history)) <= 2
        is_bot = bot_like or repetitive
        confidence = 0.88 if is_bot else 0.20
        risk_tags = ["bot_suspected"] if is_bot else ["normal_activity"]
        return is_bot, confidence, risk_tags
