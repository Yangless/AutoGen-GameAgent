import json

from game_monitoring.core.context import GameContext, set_global_context
from game_monitoring.infrastructure.repositories.memory_player_repository import (
    InMemoryCommanderOrderRepository,
    InMemoryPlayerRepository,
)
from game_monitoring.monitoring.behavior_monitor import BehaviorMonitor
from game_monitoring.monitoring.player_state import PlayerStateManager
from game_monitoring.tools.stamina_guide_tool import get_player_inventory_status


def test_stamina_guide_tool_reads_player_repository_from_global_context():
    """体力引导工具应从核心全局上下文的玩家仓储读取背包数据。"""
    repo = InMemoryPlayerRepository(
        {
            "测试玩家": {
                "player_name": "测试玩家",
                "current_stamina": 5,
                "max_stamina": 100,
                "vip_level": 2,
                "stamina_items": [
                    {
                        "item_id": "stamina_potion_small",
                        "name": "小体力药水",
                        "count": 3,
                        "recovery_amount": 20,
                        "expire_time": "2026-05-01T00:00:00",
                    }
                ],
            }
        }
    )
    context = GameContext(
        monitor=BehaviorMonitor(),
        player_state_manager=PlayerStateManager(),
        player_repository=repo,
        commander_order_repository=InMemoryCommanderOrderRepository(),
    )
    set_global_context(context)

    payload = json.loads(get_player_inventory_status("测试玩家"))

    assert payload["player_id"] == "测试玩家"
    assert payload["total_items_count"] == 1
    assert payload["stamina_items"][0]["name"] == "小体力药水"
