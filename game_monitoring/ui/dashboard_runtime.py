"""Dashboard 运行时辅助函数。"""

from __future__ import annotations

from typing import Any, Dict, Iterable

from ..application.services import ActionProcessingService, AgentService
from ..core import GameContext, bootstrap_application
from ..domain.repositories.player_repository import (
    CommanderOrderRepository,
    PlayerEntity,
    PlayerRepository,
)


def _seed_player_state_from_entity(runtime: Dict[str, Any], entity: PlayerEntity) -> None:
    state_manager = runtime["player_state_manager"]
    state_manager.update_player_attributes(
        entity.player_name,
        player_name=entity.player_name,
        team_stamina=entity.team_stamina,
        backpack_items=entity.backpack_items,
        team_levels=entity.team_levels,
        skill_levels=entity.skill_levels,
        reserve_troops=entity.reserve_troops,
    )


def build_runtime_bundle() -> Dict[str, Any]:
    """从 bootstrap 容器构建 Dashboard 运行时依赖。"""
    container = bootstrap_application()
    context = container.resolve(GameContext)
    player_repository = container.resolve(PlayerRepository)
    commander_order_repository = container.resolve(CommanderOrderRepository)

    runtime = {
        "container": container,
        "context": context,
        "monitor": context.monitor,
        "player_state_manager": context.player_state_manager,
        "action_service": container.resolve(ActionProcessingService),
        "agent_service": container.resolve(AgentService),
        "player_repository": player_repository,
        "commander_order_repository": commander_order_repository,
    }

    for player_name in player_repository.get_all_names():
        entity = player_repository.get_by_name(player_name)
        if entity is not None:
            _seed_player_state_from_entity(runtime, entity)

    return runtime


def sync_player_profile(
    runtime: Dict[str, Any],
    player_name: str,
    *,
    team_stamina: list[int],
    backpack_items: list[str],
    team_levels: list[int],
    skill_levels: list[int],
    reserve_troops: int,
    display_name: str | None = None,
) -> None:
    """同步更新玩家状态管理器和玩家仓储。"""
    resolved_name = display_name or player_name
    state_manager = runtime["player_state_manager"]
    repo = runtime["player_repository"]

    state_manager.update_player_attributes(
        player_name,
        player_name=resolved_name,
        team_stamina=team_stamina,
        backpack_items=backpack_items,
        team_levels=team_levels,
        skill_levels=skill_levels,
        reserve_troops=reserve_troops,
    )

    entity = repo.get_by_name(player_name) or PlayerEntity(player_name=player_name)
    entity.player_name = resolved_name
    entity.team_stamina = team_stamina
    entity.backpack_items = backpack_items
    entity.team_levels = team_levels
    entity.skill_levels = skill_levels
    entity.reserve_troops = reserve_troops
    repo.save(entity)


def get_player_names(runtime: Dict[str, Any]) -> list[str]:
    """获取可选玩家名列表。"""
    return runtime["player_repository"].get_all_names()


def get_commander_order(runtime: Dict[str, Any]) -> str:
    """获取当前军令。"""
    return runtime["commander_order_repository"].get_current_order()


def set_commander_order(runtime: Dict[str, Any], order: str) -> None:
    """保存当前军令。"""
    runtime["commander_order_repository"].save_order(order)
