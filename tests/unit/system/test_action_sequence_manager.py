import asyncio
from unittest.mock import AsyncMock

from game_monitoring.monitoring.behavior_monitor import BehaviorMonitor
from game_monitoring.system.action_sequence_manager import ActionSequenceManager


class _FakeTeam:
    async def trigger_analysis_and_intervention(self, player_id, monitor):
        return {"player_id": player_id}


def test_action_sequence_manager_analyzes_current_sequence_with_public_monitor_api(monkeypatch):
    """动作序列管理器应通过 BehaviorMonitor 公共接口重新分析序列。"""
    monitor = BehaviorMonitor(recent_actions_window=3)
    manager = ActionSequenceManager(monitor, _FakeTeam())

    for action in ("sell_item", "cancel_auto_renew", "post_account_for_sale"):
        manager.ui.add_action_to_sequence(f"{action}()")
        monitor.add_atomic_action(manager.current_player_id, action)

    trigger = AsyncMock()
    monkeypatch.setattr(manager, "_trigger_agent_analysis", trigger)

    asyncio.run(manager._analyze_and_trigger_agents())

    trigger.assert_awaited_once()
    scenarios = trigger.await_args.args[0]
    assert any(item["scenario"] == "资产处理风险" for item in scenarios)


def test_action_sequence_manager_clear_current_sequence_resets_ui_and_monitor():
    """清空序列时应同时清空 UI 和 Monitor 中的状态。"""
    monitor = BehaviorMonitor()
    manager = ActionSequenceManager(monitor, _FakeTeam())

    manager.ui.add_action_to_sequence("sell_item()")
    monitor.add_atomic_action(manager.current_player_id, "sell_item")

    manager._clear_current_sequence()

    assert manager.ui.action_sequence == []
    assert monitor.get_player_action_sequence(manager.current_player_id) == []
