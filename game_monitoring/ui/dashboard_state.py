"""Dashboard 状态同步辅助函数。"""

from typing import Any, MutableMapping


def clear_action_sequence(
    session_state: MutableMapping[str, Any], monitor: Any, player_id: str
) -> None:
    """同步清空 Dashboard 序列显示和 Monitor 中的玩家动作序列。"""
    session_state["action_sequence"] = []
    if monitor and hasattr(monitor, "clear_player_sequence"):
        monitor.clear_player_sequence(player_id)
