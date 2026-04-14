from datetime import datetime

from game_monitoring.monitoring.behavior_monitor import BehaviorMonitor
from game_monitoring.simulator.player_behavior import PlayerBehavior


def test_behavior_monitor_supports_parametrized_atomic_actions():
    """BehaviorMonitor 应保留动作参数并让规则引擎读取这些参数。"""
    monitor = BehaviorMonitor(recent_actions_window=3)

    monitor.add_atomic_action("player_1", "make_payment", {"amount": 100})
    monitor.add_atomic_action("player_1", "recruit_hero", {"rarity": "legendary"})
    triggered = monitor.add_atomic_action(
        "player_1",
        "complete_dungeon",
        {"status": "success", "difficulty": "hard"},
    )

    sequence = monitor.get_player_action_sequence("player_1")
    scenario_names = {item["scenario"] for item in triggered}

    assert sequence[-1]["params"] == {"status": "success", "difficulty": "hard"}
    assert "充值行为积极表现" in scenario_names
    assert "游戏成就积极表现" in scenario_names


def test_behavior_monitor_can_reanalyze_current_sequence():
    """BehaviorMonitor 应支持对当前序列做公开的重新分析，并缓存最近结果。"""
    monitor = BehaviorMonitor(recent_actions_window=3)

    monitor.add_atomic_action("player_1", "sell_item")
    monitor.add_atomic_action("player_1", "cancel_auto_renew")
    monitor.add_atomic_action("player_1", "post_account_for_sale")

    reanalyzed = monitor.analyze_current_sequence("player_1")

    assert any(item["scenario"] == "资产处理风险" for item in reanalyzed)
    assert monitor.get_triggered_scenarios("player_1") == reanalyzed


def test_behavior_monitor_add_behavior_preserves_legacy_threshold_trigger():
    """高层行为兼容入口仍应在达到阈值时返回 True。"""
    monitor = BehaviorMonitor(threshold=2)

    first = monitor.add_behavior(
        PlayerBehavior("player_1", datetime.now(), "突然不充了")
    )
    second = monitor.add_behavior(
        PlayerBehavior("player_1", datetime.now(), "玩家点击退出游戏")
    )

    assert first is False
    assert second is True


def test_behavior_monitor_negative_count_api_persists_per_player():
    """行为监控器应提供可持久复用的负面计数 API。"""
    monitor = BehaviorMonitor(threshold=2)

    assert monitor.get_negative_count("player_1") == 0
    assert monitor.increment_negative_count("player_1") == 1
    assert monitor.increment_negative_count("player_1") == 2
    assert monitor.get_negative_count("player_1") == 2

    monitor.reset_negative_count("player_1")

    assert monitor.get_negative_count("player_1") == 0


def test_behavior_monitor_add_atomic_action_records_behavior_history():
    """原子动作入口也应补充行为历史，保证服务层路径可观测。"""
    monitor = BehaviorMonitor()

    monitor.add_atomic_action("player_1", "sell_item")

    history = monitor.get_player_history("player_1")

    assert len(history) == 1
    assert history[0].action == "sell_item"
