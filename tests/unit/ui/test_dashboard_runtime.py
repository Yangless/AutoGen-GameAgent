from game_monitoring.domain.repositories.player_repository import PlayerRepository
from game_monitoring.infrastructure.repositories.memory_player_repository import (
    InMemoryCommanderOrderRepository,
)
from game_monitoring.ui.dashboard_runtime import (
    build_runtime_bundle,
    sync_player_profile,
)


def test_build_runtime_bundle_exposes_container_services_and_repositories():
    """Dashboard runtime 应从 bootstrap 容器暴露核心服务和仓储。"""
    runtime = build_runtime_bundle()

    assert runtime["container"] is not None
    assert runtime["context"] is not None
    assert runtime["monitor"] is runtime["context"].monitor
    assert runtime["player_state_manager"] is runtime["context"].player_state_manager
    assert runtime["player_repository"] is runtime["context"].player_repository
    assert runtime["commander_order_repository"] is runtime["context"].commander_order_repository


def test_sync_player_profile_updates_state_manager_and_repository():
    """Dashboard 更新玩家属性时应同步更新状态管理器和玩家仓储。"""
    runtime = build_runtime_bundle()

    sync_player_profile(
        runtime,
        "孤独的凤凰战士",
        display_name="孤独的凤凰战士",
        team_stamina=[10, 20, 30, 40],
        backpack_items=["面包"],
        team_levels=[30, 25, 20, 10],
        skill_levels=[6, 4, 2, 1],
        reserve_troops=12345,
    )

    state = runtime["player_state_manager"].get_player_state("孤独的凤凰战士")
    entity = runtime["player_repository"].get_by_name("孤独的凤凰战士")

    assert state.team_stamina == [10, 20, 30, 40]
    assert state.reserve_troops == 12345
    assert entity is not None
    assert entity.team_stamina == [10, 20, 30, 40]
    assert entity.backpack_items == ["面包"]
