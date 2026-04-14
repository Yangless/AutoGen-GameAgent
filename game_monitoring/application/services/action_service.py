"""
动作处理应用服务

职责:
- 处理玩家动作的核心业务逻辑
- 协调规则引擎和状态管理
- 决定是否需要干预
- 无UI依赖，纯业务逻辑
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum, auto
from datetime import datetime

from ...core.context import GameContext
from ...rules import RuleResult
from ...simulator.player_behavior import PlayerBehavior


class ActionResult(Enum):
    """动作处理结果类型"""
    SUCCESS = auto()
    RULE_TRIGGERED = auto()
    INTERVENTION_TRIGGERED = auto()
    ERROR = auto()


@dataclass
class ActionProcessingResult:
    """动作处理结果"""
    result: ActionResult
    player_id: str
    action_name: str
    message: str
    triggered_rules: List[RuleResult] = field(default_factory=list)
    should_intervene: bool = False
    current_negative_count: int = 0
    threshold: int = 3
    emotion_type: str = "neutral"
    action_sequence_length: int = 0


class ActionProcessingService:
    """
    动作处理服务

    核心协调器，负责:
    1. 记录动作到监控器
    2. 执行规则引擎分析
    3. 更新负面计数
    4. 判断干预条件

    使用示例:
    ```python
    service = ActionProcessingService(game_context)
    result = await service.process_action("player_1", "click_exit")

    if result.should_intervene:
        await agent_service.trigger_intervention(result.player_id)
    ```
    """

    def __init__(self, game_context: GameContext):
        self._context = game_context
        self._monitor = game_context.monitor

    async def process_action(
        self,
        player_id: str,
        action_name: str,
        action_params: Dict[str, Any] = None
    ) -> ActionProcessingResult:
        """
        处理玩家动作

        Args:
            player_id: 玩家ID
            action_name: 动作名称
            action_params: 可选参数

        Returns:
            处理结果，包含是否触发干预的标记
        """
        try:
            # 1. 添加到监控器
            triggered = self._monitor.add_atomic_action(
                player_id, action_name, action_params
            )

            # 2. 获取情绪类型
            emotion_type = "neutral"
            if triggered:
                emotion_type = self._get_emotion_from_rules(triggered)

            # 3. 更新负面计数
            should_intervene = False
            if emotion_type == "negative":
                current_count = self._increment_negative_count(player_id)
                should_intervene = current_count >= self._monitor.threshold
            else:
                current_count = self._get_negative_count(player_id)

            # 4. 获取序列长度
            sequence = self._monitor.get_player_action_sequence(player_id)

            return ActionProcessingResult(
                result=ActionResult.INTERVENTION_TRIGGERED if should_intervene else ActionResult.RULE_TRIGGERED if triggered else ActionResult.SUCCESS,
                player_id=player_id,
                action_name=action_name,
                message="处理完成",
                triggered_rules=[type('obj', (), r) for r in triggered],
                should_intervene=should_intervene,
                current_negative_count=current_count,
                threshold=self._monitor.threshold,
                emotion_type=emotion_type,
                action_sequence_length=len(sequence)
            )

        except Exception as e:
            return ActionProcessingResult(
                result=ActionResult.ERROR,
                player_id=player_id,
                action_name=action_name,
                message=f"错误: {str(e)}",
                triggered_rules=[],
                should_intervene=False
            )

    def _get_emotion_from_rules(self, rules: List[Dict]) -> str:
        """从规则结果推断情绪"""
        for rule in rules:
            scenario = rule.get('scenario', '')
            if any(kw in scenario for kw in ['失败', '风险', '退出', '攻击']):
                return "negative"
            if any(kw in scenario for kw in ['充值', '胜利', '成就']):
                return "positive"
            if '机器人' in scenario or '高频' in scenario:
                return "abnormal"
        return "neutral"

    def _increment_negative_count(self, player_id: str) -> int:
        """增加负面计数"""
        if hasattr(self._monitor, "increment_negative_count"):
            return self._monitor.increment_negative_count(player_id)
        return 0

    def _get_negative_count(self, player_id: str) -> int:
        """获取当前负面计数"""
        if hasattr(self._monitor, "get_negative_count"):
            return self._monitor.get_negative_count(player_id)
        return 0

    def reset_negative_count(self, player_id: str) -> None:
        """重置负面计数"""
        if hasattr(self._monitor, "reset_negative_count"):
            self._monitor.reset_negative_count(player_id)

    def get_info(self, player_id: str) -> Dict[str, Any]:
        """获取玩家处理信息"""
        return {
            'player_id': player_id,
            'negative_count': self._get_negative_count(player_id),
            'threshold': self._monitor.threshold,
            'sequence_length': len(self._monitor.get_player_action_sequence(player_id))
        }
