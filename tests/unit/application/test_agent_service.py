import asyncio

from game_monitoring.application.services.agent_service import AgentService, create_team_factory
from game_monitoring.core.context import GameContext
from game_monitoring.application.services.agent_service import create_team_factory
from game_monitoring.core.container import DIContainer
from game_monitoring.monitoring.behavior_monitor import BehaviorMonitor
from game_monitoring.monitoring.player_state import PlayerStateManager
from game_monitoring.team.team_manager import GameMonitoringTeamV2


def test_create_team_factory_resolves_registered_v2_team():
    """AgentService 的 team factory 应能解析默认注册的 v2 Team。"""
    container = DIContainer()
    sentinel_team = object()
    container.register_instance(GameMonitoringTeamV2, sentinel_team)

    team_factory = create_team_factory(container)

    assert team_factory() is sentinel_team


def test_agent_service_returns_structured_payload_from_v2_team():
    """AgentService 应将 v2 team 的结构化结果返回给上层。"""
    context = GameContext(
        monitor=BehaviorMonitor(),
        player_state_manager=PlayerStateManager(),
    )

    class FakeTeam:
        async def trigger_analysis_and_intervention(self, player_id, monitor):
            assert player_id == "player_1"
            assert monitor is context.monitor
            return {
                "player_id": player_id,
                "final_actions": [{"action_type": "grant_reward"}],
            }

    service = AgentService(context, team_factory=lambda: FakeTeam())

    result = asyncio.run(service.trigger_intervention("player_1"))

    assert result.success is True
    assert result.payload == {
        "player_id": "player_1",
        "final_actions": [{"action_type": "grant_reward"}],
    }
