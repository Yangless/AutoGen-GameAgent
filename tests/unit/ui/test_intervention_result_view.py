from datetime import datetime

from game_monitoring.ui.intervention_result_view import (
    format_intervention_result,
    store_intervention_result,
)


def test_store_intervention_result_keeps_latest_entries():
    history = []
    base_result = {
        "player_id": "player_1",
        "session_id": "player_1-abcd1234",
        "worker_count": 3,
        "overall_confidence": 0.82,
        "final_actions": [{"action_type": "grant_reward"}],
    }

    for index in range(12):
        history = store_intervention_result(
            history,
            {**base_result, "session_id": f"player_1-session-{index}"},
            captured_at=datetime(2026, 4, 14, 12, 0, index),
            limit=10,
        )

    assert len(history) == 10
    assert history[0]["session_id"] == "player_1-session-2"
    assert history[-1]["session_id"] == "player_1-session-11"


def test_format_intervention_result_returns_dashboard_friendly_summary():
    formatted = format_intervention_result(
        {
            "player_id": "player_1",
            "session_id": "player_1-abcd1234",
            "worker_count": 3,
            "overall_confidence": 0.82,
            "final_actions": [
                {"action_type": "grant_reward", "reward": "return_bundle"},
                {"action_type": "assign_support", "channel": "vip_support"},
            ],
        },
        captured_at=datetime(2026, 4, 14, 12, 34, 56),
    )

    assert formatted["player_id"] == "player_1"
    assert formatted["captured_at"] == "2026-04-14 12:34:56"
    assert formatted["worker_count"] == 3
    assert formatted["overall_confidence"] == 0.82
    assert formatted["action_labels"] == [
        "grant_reward",
        "assign_support",
    ]
