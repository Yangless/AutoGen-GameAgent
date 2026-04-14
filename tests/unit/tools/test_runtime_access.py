from game_monitoring.core.context import GameContext, set_global_context
from game_monitoring.infrastructure.repositories.memory_player_repository import (
    InMemoryCommanderOrderRepository,
    InMemoryPlayerRepository,
)
from game_monitoring.monitoring.behavior_monitor import BehaviorMonitor
from game_monitoring.monitoring.player_state import PlayerStateManager
from game_monitoring.tools.runtime_access import get_monitor, get_player_state_manager


def test_runtime_access_reads_monitor_and_state_manager_from_core_context():
    context = GameContext(
        monitor=BehaviorMonitor(),
        player_state_manager=PlayerStateManager(),
        player_repository=InMemoryPlayerRepository(),
        commander_order_repository=InMemoryCommanderOrderRepository(),
    )
    set_global_context(context)

    assert get_monitor() is context.monitor
    assert get_player_state_manager() is context.player_state_manager
