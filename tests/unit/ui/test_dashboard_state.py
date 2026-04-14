from game_monitoring.monitoring.behavior_monitor import BehaviorMonitor
from game_monitoring.ui.dashboard_state import clear_action_sequence


def test_clear_action_sequence_resets_session_and_monitor():
    """Dashboard 清空动作序列时应同步清空 monitor 中的玩家序列。"""
    session_state = {"action_sequence": [{"action": "sell_item"}]}
    monitor = BehaviorMonitor()
    monitor.add_atomic_action("player_1", "sell_item")

    clear_action_sequence(session_state, monitor, "player_1")

    assert session_state["action_sequence"] == []
    assert monitor.get_player_action_sequence("player_1") == []
