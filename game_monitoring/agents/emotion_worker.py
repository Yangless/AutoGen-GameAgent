"""
情绪安抚Worker实现

负责分析玩家情绪状态并制定安抚策略。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from autogen_core import MessageContext, RoutedAgent, rpc

from ..domain.messages import InterventionTask, WorkerResponse
from ..domain.schemas import EmotionWorkerOutput
from ..infrastructure.validation.output_validator import OutputValidator


class EmotionWorker(RoutedAgent):
    """情绪安抚Worker"""

    def __init__(self, model_client: Any, tools: list[Any]) -> None:
        super().__init__("Emotion安抚Worker")
        self.model_client = model_client
        self.tools = tools
        self.validator = OutputValidator(EmotionWorkerOutput, max_retries=3)

    def _decide_strategy(self, emotion_result: Any) -> dict[str, Any]:
        """基于情绪类型决定干预策略。"""
        emotion = getattr(emotion_result, "emotion", None) or getattr(
            emotion_result, "emotion_type", "正常"
        )
        strategies = {
            "愤怒": {"priority": "high", "actions": ["专属客服", "补偿道具"]},
            "沮丧": {"priority": "medium", "actions": ["关怀邮件", "小额奖励"]},
            "焦虑": {"priority": "low", "actions": ["引导提示"]},
        }
        return strategies.get(
            emotion,
            {"priority": "low", "actions": []},
        )

    @rpc
    async def handle_intervention_task(
        self, message: InterventionTask, ctx: MessageContext
    ) -> WorkerResponse:
        """将干预任务转换为情绪 Worker 响应。"""
        emotion_type = self._infer_emotion(message)
        strategy = self._decide_strategy(SimpleNamespace(emotion=emotion_type))
        validated = EmotionWorkerOutput.model_validate(
            {
                "emotion_type": emotion_type,
                "confidence": self._emotion_confidence(emotion_type),
                "intervention_actions": self._build_actions(strategy["actions"]),
                "reason": "Derived from triggered scenarios and recent behavior history.",
            }
        )

        return WorkerResponse(
            task_id=message.task_id,
            worker_type="emotion",
            intervention_actions=validated.intervention_actions,
            confidence=validated.confidence,
            metadata={
                "emotion_type": validated.emotion_type,
                "priority": self._priority_value(strategy["priority"]),
            },
        )

    @staticmethod
    def _priority_value(priority: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 1)

    @staticmethod
    def _emotion_confidence(emotion_type: str) -> float:
        return {
            "愤怒": 0.92,
            "沮丧": 0.85,
            "焦虑": 0.75,
            "正常": 0.60,
        }.get(emotion_type, 0.60)

    @staticmethod
    def _build_actions(actions: list[str]) -> list[dict[str, Any]]:
        mapping = {
            "专属客服": {"action_type": "assign_support", "channel": "vip_support"},
            "补偿道具": {"action_type": "grant_reward", "reward": "compensation_pack"},
            "关怀邮件": {"action_type": "send_email", "template": "care_follow_up"},
            "小额奖励": {"action_type": "grant_reward", "reward": "small_bonus"},
            "引导提示": {"action_type": "send_email", "template": "guidance_tip"},
        }
        return [mapping[action] for action in actions if action in mapping]

    @staticmethod
    def _infer_emotion(message: InterventionTask) -> str:
        scenarios = " ".join(
            str(item.get("scenario", "")) for item in message.context["triggered_scenarios"]
        ).lower()
        history = " ".join(
            str(item.get("action", "")) for item in message.context["behavior_history"]
        ).lower()

        if any(keyword in scenarios or keyword in history for keyword in ("angry", "rage", "complaint")):
            return "愤怒"
        if any(keyword in scenarios or keyword in history for keyword in ("negative", "quit", "exit", "uninstall")):
            return "沮丧"
        if any(keyword in scenarios or keyword in history for keyword in ("anxious", "hesitate", "stuck")):
            return "焦虑"
        return "正常"
