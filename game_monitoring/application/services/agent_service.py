"""
Agent服务

职责:
- 协调Agent调用
- 处理异步执行
- 管理日志捕获
"""

from __future__ import annotations

import asyncio
import threading
from typing import Optional, Callable, List, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

from ...core.context import GameContext

if TYPE_CHECKING:
    from ...team.team_manager import GameMonitoringTeam


@dataclass
class InterventionResult:
    """干预结果"""
    player_id: str
    success: bool
    message: str
    logs: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class AgentService:
    """
    Agent服务

    封装Agent调用的复杂性
    """

    def __init__(
        self,
        game_context: GameContext,
        team_factory: Callable[[], GameMonitoringTeam] = None,
    ):
        self._context = game_context
        self._team_factory = team_factory

    async def trigger_intervention(
        self,
        player_id: str,
        on_log: Callable[[str], None] = None
    ) -> InterventionResult:
        """
        触发Agent干预

        Args:
            player_id: 玩家ID
            on_log: 日志回调函数

        Returns:
            干预结果
        """
        try:
            if self._team_factory:
                team = self._team_factory()
            else:
                # 从环境获取（兼容模式）
                team = None

            if not team:
                return InterventionResult(
                    player_id=player_id,
                    success=False,
                    message="Team未初始化"
                )

            # 直接调用（简化版本）
            await team.trigger_analysis_and_intervention(
                player_id,
                self._context.monitor
            )

            return InterventionResult(
                player_id=player_id,
                success=True,
                message="干预已触发"
            )

        except Exception as e:
            return InterventionResult(
                player_id=player_id,
                success=False,
                message=str(e)
            )

    async def generate_military_order(
        self,
        player_name: str,
        commander_order: str
    ) -> str:
        """生成军令"""
        # TODO: 集成军令Agent
        return f"为{player_name}生成的军令"


# 便捷工厂函数
def create_team_factory(container) -> Callable[[], GameMonitoringTeam]:
    """创建Team工厂"""
    def factory():
        # 这里可以从容器解析team配置
        # 暂时返回None，需要实际配置
        return None
    return factory
