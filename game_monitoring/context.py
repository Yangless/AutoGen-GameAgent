"""全局上下文管理器

提供全局共享的 monitor 和 player_state_manager 实例，
供各个工具函数访问真实的行为监控和状态管理功能。
"""

from typing import Optional
from .monitoring.behavior_monitor import BehaviorMonitor
from .monitoring.player_state import PlayerStateManager

# 全局实例
_monitor: Optional[BehaviorMonitor] = None
_player_state_manager: Optional[PlayerStateManager] = None

def set_global_monitor(monitor: BehaviorMonitor) -> None:
    """设置全局 monitor 实例"""
    global _monitor
    _monitor = monitor

def set_global_player_state_manager(player_state_manager: PlayerStateManager) -> None:
    """设置全局 player_state_manager 实例"""
    global _player_state_manager
    _player_state_manager = player_state_manager

def get_global_monitor() -> Optional[BehaviorMonitor]:
    """获取全局 monitor 实例"""
    return _monitor

def get_global_player_state_manager() -> Optional[PlayerStateManager]:
    """获取全局 player_state_manager 实例"""
    return _player_state_manager

def initialize_context(monitor: BehaviorMonitor, player_state_manager: PlayerStateManager) -> None:
    """初始化全局上下文"""
    set_global_monitor(monitor)
    set_global_player_state_manager(player_state_manager)
    print("✅ 全局上下文已初始化")

def is_context_initialized() -> bool:
    """检查全局上下文是否已初始化"""
    return _monitor is not None and _player_state_manager is not None