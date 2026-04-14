"""
Behavior Monitor V2 - 集成新规则引擎

兼容层：尽量保持与旧版相同接口
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..rules import RuleEngine, RuleRegistry
from ..core.context import GameContext
from ..simulator.player_behavior import PlayerBehavior


class BehaviorMonitorV2:
    """
    行为监控器 V2

    集成新规则引擎，同时保持与旧版接口兼容
    """

    def __init__(
        self,
        engine: RuleEngine = None,
        threshold: int = 3,
        max_sequence_length: int = 50,
        recent_actions_window: int = 3
    ):
        self._engine = engine or RuleEngine()
        self._threshold = threshold
        self._max_sequence_length = max_sequence_length
        self._recent_window = recent_actions_window

        # 数据存储
        self._player_sequences: Dict[str, List[Dict]] = {}
        self._behavior_history: List[PlayerBehavior] = []
        self._negative_counts: Dict[str, int] = {}

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def rule_engine(self) -> RuleEngine:
        return self._engine

    def add_atomic_action(
        self,
        player_id: str,
        action_name: str,
        params: Dict[str, Any] = None
    ) -> List[Dict]:
        """
        添加动作并分析

        保持与旧版接口兼容
        """
        # 初始化序列
        if player_id not in self._player_sequences:
            self._player_sequences[player_id] = []

        action_data = {
            'action': action_name,
            'params': params or {},
            'timestamp': datetime.now(),
            'player_id': player_id
        }

        self._player_sequences[player_id].append(action_data)

        # 限制长度
        if len(self._player_sequences[player_id]) > self._max_sequence_length:
            self._player_sequences[player_id] = self._player_sequences[player_id][-self._max_sequence_length:]

        # 同时添加到旧版兼容的behavior_history
        self._behavior_history.append(
            PlayerBehavior(
                player_id=player_id,
                timestamp=datetime.now(),
                action=action_name,
                result="success",
                metadata=params or {}
            )
        )

        # 规则分析
        actions = self._player_sequences[player_id]
        recent = actions[-self._recent_window:] if len(actions) >= self._recent_window else actions

        context = type('context', (), {
            'player_id': player_id,
            'actions': actions,
            'recent_actions': recent
        })

        results = self._engine.registry.execute_all(context)
        return [r.to_dict() for r in results if r.triggered]

    # 旧版兼容方法
    def add_behavior(self, behavior: PlayerBehavior) -> bool:
        """旧版接口 - 直接返回False，逻辑重用add_atomic_action"""
        return False

    def get_player_history(self, player_id: str) -> List[PlayerBehavior]:
        """获取玩家行为历史"""
        return [b for b in self._behavior_history if b.player_id == player_id]

    def get_player_action_sequence(self, player_id: str) -> List[Dict]:
        """获取动作序列"""
        return self._player_sequences.get(player_id, [])

    def clear_player_sequence(self, player_id: str) -> None:
        """清空序列"""
        if player_id in self._player_sequences:
            self._player_sequences[player_id] = []

    # 新增方法（V2）
    def get_negative_count(self, player_id: str) -> int:
        """获取负面计数"""
        return self._negative_counts.get(player_id, 0)

    def increment_negative_count(self, player_id: str) -> int:
        """增加负面计数"""
        self._negative_counts[player_id] = self._negative_counts.get(player_id, 0) + 1
        return self._negative_counts[player_id]

    def reset_negative_count(self, player_id: str) -> None:
        """重置负面计数"""
        self._negative_counts[player_id] = 0

    def get_emotion_from_rules(self, rules: List[Dict]) -> str:
        """从规则结果判断情绪"""
        return self._engine.get_emotion_from_rules(
            [type('obj', (), r) for r in rules]
        )
