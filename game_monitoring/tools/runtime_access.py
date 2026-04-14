"""工具层运行时依赖访问辅助函数。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.context import get_global_context


def is_context_initialized() -> bool:
    """检查核心全局上下文是否已初始化。"""
    return get_global_context() is not None


def get_monitor():
    """获取全局 monitor。"""
    context = get_global_context()
    return context.monitor if context else None


def get_player_state_manager():
    """获取全局状态管理器。"""
    context = get_global_context()
    return context.player_state_manager if context else None


def get_player_info(player_name: str) -> Optional[Dict[str, Any]]:
    """从玩家仓储获取玩家信息字典。"""
    context = get_global_context()
    if context is None or context.player_repository is None:
        return None

    entity = context.player_repository.get_by_name(player_name)
    if entity is None:
        return None

    return context.player_repository.to_dict(entity)


def get_players_info() -> Dict[str, Dict[str, Any]]:
    """获取所有玩家信息。"""
    context = get_global_context()
    if context is None or context.player_repository is None:
        return {}

    players_info: Dict[str, Dict[str, Any]] = {}
    for player_name in context.player_repository.get_all_names():
        entity = context.player_repository.get_by_name(player_name)
        if entity is not None:
            players_info[player_name] = context.player_repository.to_dict(entity)
    return players_info


def get_all_player_names() -> list[str]:
    """获取所有玩家名称。"""
    context = get_global_context()
    if context is None or context.player_repository is None:
        return []
    return context.player_repository.get_all_names()


def get_commander_order() -> str:
    """获取当前军令。"""
    context = get_global_context()
    if context is None or context.commander_order_repository is None:
        return ""
    return context.commander_order_repository.get_current_order()


def set_commander_order(order: str) -> None:
    """保存当前军令。"""
    context = get_global_context()
    if context is None or context.commander_order_repository is None:
        return
    context.commander_order_repository.save_order(order)
