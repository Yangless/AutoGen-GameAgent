"""
Agent服务

职责:
- 协调Agent调用
- 处理异步执行
- 管理日志捕获
"""

from __future__ import annotations

from typing import Optional, Callable, List, Protocol, Any
from dataclasses import dataclass, field
from datetime import datetime

from ...core.context import GameContext

@dataclass
class InterventionResult:
    """干预结果"""
    player_id: str
    success: bool
    message: str
    payload: Any = None
    logs: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class MonitoringTeam(Protocol):
    async def trigger_analysis_and_intervention(
        self, player_id: str, monitor: Any
    ) -> Any:
        ...


class AgentService:
    """
    Agent服务

    封装Agent调用的复杂性
    """

    def __init__(
        self,
        game_context: GameContext,
        team_factory: Optional[Callable[[], MonitoringTeam]] = None,
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
            payload = await team.trigger_analysis_and_intervention(
                player_id,
                self._context.monitor
            )

            return InterventionResult(
                player_id=player_id,
                success=True,
                message="干预已触发",
                payload=payload,
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
def create_team_factory(container) -> Callable[[], Optional[MonitoringTeam]]:
    """创建Team工厂"""
    from ...team.team_manager import GameMonitoringTeamV2

    def try_resolve(interface):
        try:
            return container.resolve(interface)
        except Exception:
            return None

    def factory():
        resolved_factory = try_resolve("team_factory")
        if callable(resolved_factory) and not hasattr(
            resolved_factory, "trigger_analysis_and_intervention"
        ):
            return resolved_factory()
        if resolved_factory is not None:
            return resolved_factory

        for interface in (GameMonitoringTeamV2, "team"):
            resolved = try_resolve(interface)
            if resolved is not None:
                return resolved

        return None

    return factory
