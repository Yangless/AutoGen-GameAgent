"""
领域上下文

提供应用级别的上下文对象，替代全局变量

核心概念:
- SystemConfig: 系统配置
- GameContext: 游戏应用上下文，包含核心依赖
- PlayerContext: 玩家级上下文，针对特定玩家的便捷访问
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from ..monitoring.behavior_monitor import BehaviorMonitor
    from ..monitoring.player_state import PlayerStateManager
    from ..domain.repositories.player_repository import (
        CommanderOrderRepository,
        PlayerRepository,
    )


@dataclass(frozen=True)
class SystemConfig:
    """
    系统配置

    frozen=True 使配置不可变，确保线程安全
    """
    behavior_threshold: int = 3
    max_sequence_length: int = 50
    recent_actions_window: int = 3
    auto_reset_after_intervention: bool = True
    use_yaml_repository: bool = False
    players_config_path: str = "config/players.yaml"
    initial_players: Optional[Dict] = None


@dataclass
class PlayerSnapshot:
    """
    玩家状态快照

    用于分析和展示，不可变数据便于比较
    """
    player_id: str
    emotion: Optional[str] = None
    emotion_confidence: float = 0.0
    emotion_keywords: List[str] = field(default_factory=list)
    churn_risk_level: Optional[str] = None
    churn_risk_score: float = 0.0
    is_bot: bool = False
    bot_confidence: float = 0.0
    bot_patterns: List[str] = field(default_factory=list)
    team_stamina: Optional[List[int]] = None
    backpack_items: Optional[List[str]] = None
    team_levels: Optional[List[int]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class GameContext:
    """
    游戏应用上下文

    作为核心协调对象，提供系统级别的依赖访问。

    设计理念:
    - 显式依赖传递替代全局变量
    - 上下文不可变，方法返回新对象
    - 支持向下转换为特定玩家的上下文

    使用示例:
    ```python
    context = GameContext(
        monitor=monitor,
        player_state_manager=state_manager,
        config=config
    )

    # 获取玩家历史
    history = context.monitor.get_player_history("player_1")

    # 创建玩家上下文
    player_ctx = context.for_player("player_1")
    state = player_ctx.player_state  # 便捷访问
    ```
    """

    def __init__(
        self,
        monitor: 'BehaviorMonitor',
        player_state_manager: 'PlayerStateManager',
        config: Optional[SystemConfig] = None,
        player_repository: Optional['PlayerRepository'] = None,
        commander_order_repository: Optional['CommanderOrderRepository'] = None,
    ):
        self._monitor = monitor
        self._player_state_manager = player_state_manager
        self._config = config or SystemConfig()
        self._player_repository = player_repository
        self._commander_order_repository = commander_order_repository

    @property
    def monitor(self) -> 'BehaviorMonitor':
        """行为监控器"""
        return self._monitor

    @property
    def player_state_manager(self) -> 'PlayerStateManager':
        """玩家状态管理器"""
        return self._player_state_manager

    @property
    def config(self) -> SystemConfig:
        """系统配置"""
        return self._config

    @property
    def player_repository(self) -> Optional['PlayerRepository']:
        """玩家仓储。"""
        return self._player_repository

    @property
    def commander_order_repository(self) -> Optional['CommanderOrderRepository']:
        """军令仓储。"""
        return self._commander_order_repository

    def for_player(self, player_id: str) -> 'PlayerContext':
        """
        创建玩家级上下文

        Args:
            player_id: 玩家ID

        Returns:
            玩家上下文，提供最特定玩家的便捷访问
        """
        return PlayerContext(self, player_id)

    def get_player_snapshot(self, player_id: str) -> PlayerSnapshot:
        """
        获取玩家状态快照

        Args:
            player_id: 玩家ID

        Returns:
            当前状态的不可变快照
        """
        try:
            state = self._player_state_manager.get_player_state(player_id)
            return PlayerSnapshot(
                player_id=player_id,
                emotion=state.emotion,
                emotion_confidence=state.emotion_confidence or 0.0,
                emotion_keywords=getattr(state, 'emotion_keywords', []) or [],
                churn_risk_level=state.churn_risk_level,
                churn_risk_score=state.churn_risk_score or 0.0,
                is_bot=state.is_bot or False,
                bot_confidence=state.bot_confidence or 0.0,
                bot_patterns=getattr(state, 'bot_patterns', []) or [],
                team_stamina=getattr(state, 'team_stamina', None),
                backpack_items=getattr(state, 'backpack_items', None),
                team_levels=getattr(state, 'team_levels', None)
            )
        except Exception as e:
            # 返回空快照
            return PlayerSnapshot(player_id=player_id)

    def __repr__(self):
        return f"<GameContext monitor={type(self._monitor).__name__}>"


class PlayerContext:
    """
    玩家级上下文

    提供针对特定玩家的便捷访问

    使用示例:
    ```python
    player_ctx = game_context.for_player("player_1")

    # 访问玩家状态
    state = player_ctx.player_state

    # 获取历史
    history = player_ctx.get_action_history(limit=10)
    ```
    """

    def __init__(self, game_context: GameContext, player_id: str):
        self._game = game_context
        self._player_id = player_id

    @property
    def game_context(self) -> GameContext:
        """上一级游戏上下文"""
        return self._game

    @property
    def player_id(self) -> str:
        """当前玩家ID"""
        return self._player_id

    @property
    def player_state(self):
        """当前玩家状态"""
        return self._game.player_state_manager.get_player_state(self._player_id)

    def get_action_history(self, limit: int = None) -> List[Any]:
        """获取玩家动作历史"""
        history = self._game.monitor.get_player_history(self._player_id)
        if limit:
            return history[-limit:]
        return history

    def get_action_sequence(self) -> List[Dict[str, Any]]:
        """获取玩家动作序列"""
        return self._game.monitor.get_player_action_sequence(self._player_id)

    def get_negative_count(self) -> int:
        """获取当前负面行为计数"""
        # 从monitor获取 - 可能需要调整接口
        if hasattr(self._game.monitor, 'get_negative_count'):
            return self._game.monitor.get_negative_count(self._player_id)
        return 0

    def __repr__(self):
        return f"<PlayerContext player_id={self._player_id}>"


# ======== 兼容性层 ========
# 以下是临时全局变量，用于逐步迁移旧代码

_global_context: Optional[GameContext] = None


def set_global_context(context: GameContext) -> None:
    """
    设置全局上下文（兼容性）

    警告: 将逐步废弃，使用依赖注入

    在过渡期用于:
    1. 启动时设置全局上下文
    2. 旧代码通过get_global_context访问

    Args:
        context: 游戏上下文
    """
    global _global_context
    _global_context = context


def get_global_context() -> Optional[GameContext]:
    """
    获取全局上下文（兼容性）

    用于迁移期间的兼容
    新代码应使用依赖注入
    """
    return _global_context
