"""
情绪安抚Worker实现

负责分析玩家情绪状态并制定安抚策略。
"""

from __future__ import annotations

from typing import Any

from autogen_core import RoutedAgent

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
        strategies = {
            "愤怒": {"priority": "high", "actions": ["专属客服", "补偿道具"]},
            "沮丧": {"priority": "medium", "actions": ["关怀邮件", "小额奖励"]},
            "焦虑": {"priority": "low", "actions": ["引导提示"]},
        }
        return strategies.get(
            emotion_result.emotion,
            {"priority": "low", "actions": []},
        )
