"""
行为管控Worker实现

负责检测异常行为并制定管控措施。
"""

from __future__ import annotations

from typing import Any

from autogen_core import RoutedAgent

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
        if bot_result.is_bot and bot_result.confidence > 0.8:
            return ["账号限制", "人工审核"]
        if bot_result.is_bot and bot_result.confidence > 0.5:
            return ["行为警告", "密切监控"]
        return ["正常监控"]
