import asyncio
from unittest.mock import AsyncMock

from autogen_core import SingleThreadedAgentRuntime

from game_monitoring.domain.messages import PlayerEvent
from game_monitoring.team.team_manager import GameMonitoringTeamV2


def test_team_manager_v2_uses_orchestrator():
    """测试新TeamManager使用Orchestrator架构"""
    runtime = SingleThreadedAgentRuntime()

    team = GameMonitoringTeamV2(model_client=None, runtime=runtime)

    assert team.orchestrator_id.type == "orchestrator"
    assert team.orchestrator_id.key == "default"


def test_team_manager_v2_trigger_intervention():
    """测试触发干预流程"""

    class FakeMonitor:
        def get_triggered_scenarios(self):
            return [{"scenario": "negative_behavior"}]

        def get_behavior_history(self, player_id):
            assert player_id == "player_1"
            return [{"action": "quit_match"}]

    runtime = AsyncMock()
    runtime.send_message = AsyncMock(return_value={"status": "ok"})

    team = GameMonitoringTeamV2(model_client=None, runtime=runtime)

    result = asyncio.run(
        team.trigger_analysis_and_intervention("player_1", FakeMonitor())
    )

    assert result == {"status": "ok"}
    runtime.send_message.assert_awaited_once()

    event, recipient = runtime.send_message.await_args.args
    assert isinstance(event, PlayerEvent)
    assert event.player_id == "player_1"
    assert event.triggered_scenarios == [{"scenario": "negative_behavior"}]
    assert event.behavior_history == [{"action": "quit_match"}]
    assert event.session_id.startswith("player_1-")
    assert recipient == team.orchestrator_id
