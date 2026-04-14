import asyncio
from types import SimpleNamespace

from game_monitoring.ui.dashboard_actions import process_atomic_action


class FakeCapture:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start_capture(self):
        self.started = True

    def stop_capture(self):
        self.stopped = True


class FakeRuleEngine:
    @staticmethod
    def get_emotion_type_from_scenarios(scenarios):
        assert scenarios == [
            {"scenario": "negative_behavior", "description": "negative flow"}
        ]
        return "negative"


class FakeMonitor:
    def __init__(self):
        self.threshold = 3
        self.rule_engine = FakeRuleEngine()
        self._negative_count = 2
        self.reset_calls = []

    def get_player_action_sequence(self, player_id):
        assert player_id == "player_1"
        return [{"action": "sell_item"}]

    def get_recent_actions_for_analysis(self, player_id):
        assert player_id == "player_1"
        return [{"action": "sell_item"}]

    def get_negative_count(self, player_id):
        assert player_id == "player_1"
        return self._negative_count

    def reset_negative_count(self, player_id):
        self.reset_calls.append(player_id)
        self._negative_count = 0


def test_process_atomic_action_records_sequence_and_triggers_intervention():
    action_result = SimpleNamespace(
        triggered_rules=[
            SimpleNamespace(scenario="negative_behavior", description="negative flow")
        ],
        should_intervene=True,
        current_negative_count=3,
    )

    class FakeActionService:
        async def process_action(self, player_id, action_name):
            assert player_id == "player_1"
            assert action_name == "sell_item"
            return action_result

    class FakeAgentService:
        async def trigger_intervention(self, player_id):
            assert player_id == "player_1"
            return SimpleNamespace(
                payload={"player_id": player_id, "final_actions": [{"action_type": "grant_reward"}]}
            )

    monitor = FakeMonitor()
    runtime = {
        "action_service": FakeActionService(),
        "agent_service": FakeAgentService(),
        "monitor": monitor,
    }
    session_state = {
        "action_sequence": [],
        "player_negative_counts": {},
        "team_analysis_capture": FakeCapture(),
    }
    behavior_logs = []
    agent_logs = []
    stored_results = []

    asyncio.run(
        process_atomic_action(
            session_state,
            runtime,
            "player_1",
            "sell_item",
            add_behavior_log=lambda player_id, action: behavior_logs.append((player_id, action)),
            add_agent_log=agent_logs.append,
            store_team_analysis_result=stored_results.append,
        )
    )

    assert session_state["action_sequence"][0]["action"] == "sell_item"
    assert session_state["player_negative_counts"]["player_1"] == 0
    assert stored_results == [
        {"player_id": "player_1", "final_actions": [{"action_type": "grant_reward"}]}
    ]
    assert monitor.reset_calls == ["player_1"]
    assert any("达到负面行为阈值" in message for message in agent_logs)
    assert behavior_logs == [("player_1", "sell_item")]

