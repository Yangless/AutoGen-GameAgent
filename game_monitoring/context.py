"""全局上下文管理器

提供全局共享的 monitor 和 player_state_manager 实例，
供各个工具函数访问真实的行为监控和状态管理功能。
"""

from typing import Optional, Dict, Any, List
from .monitoring.behavior_monitor import BehaviorMonitor
from .monitoring.player_state import PlayerStateManager

# 全局实例
_monitor: Optional[BehaviorMonitor] = None
_player_state_manager: Optional[PlayerStateManager] = None

# 多玩家信息存储
_players_info: Dict[str, Dict[str, Any]] = {
    "龙傲天": {
        "player_name": "龙傲天",
        "team_stamina": [90, 120, 120, 120],
        "backpack_items": ["1个面包"],
        "team_levels": [50, 45, 40, 38],
        "skill_levels": [10, 8, 6, 1],
        "reserve_troops": 40000,
        "player_type": "高级玩家",
        "combat_preference": "主力攻城"
    },
    "叶良辰": {
        "player_name": "叶良辰",
        "team_stamina": [30, 30, 30, 90],
        "backpack_items": ["1个大面包", "2个辎重箱"],
        "team_levels": [45, 40, 30, 25],
        "skill_levels": [10, 8, 6, 1],
        "reserve_troops": 50000,
        "player_type": "中级玩家",
        "combat_preference": "支援作战"
    },
        "孤独的凤凰战士": {
        "player_name": "孤独的凤凰战士",
        "team_stamina": [25, 60, 90, 90],
        "backpack_items": ["1个小面包", "1个大面包"],
        "team_levels": [30, 25, 20, 10],
        "skill_levels": [6, 4, 2, 1],
        "reserve_troops": 10000,
        "player_type": "初级玩家",
        "combat_preference": "支援作战"
    }
}

# 指挥官总军令
_commander_order: str = """事件：今天（9月15号）早上10点，听信件指挥进行攻城！

配置：请每人至少派出4支部队，第1队主力需要能打12级地，第2队需要能打11级地，第3队需要能打8级地，第4队需要能打6级地；能打12级直接去前线（752，613），注意兵种克属，派遣过去并驻守城池xx，城池最大可募兵三万，队伍重伤后可原地花费铜币募兵，不要回去，加油守住这个城池。能打11级的队伍如果是国家队伍的话，也可以酌情考虑派往前线，若非国家队，提前派遣部队至将军雕像（732，767），不列颠文明的队伍到城池附近，提前转化为器械部队；需提醒一下在打城前将派遣的队伍进行再次分类，为精锐攻城，和拆耐久部分；其余队伍作为攻城拆迁队，在主力将城池精锐部队耗完后，发起攻城，拆除城池耐久。

介绍：集结等建好后发起，将军雕像S（已建成）使用【集结】或【派遣】进行快速行军前往，目不消耗体力和十气。"""

def set_global_monitor(monitor: BehaviorMonitor) -> None:
    """设置全局 monitor 实例"""
    global _monitor
    _monitor = monitor

def set_global_player_state_manager(player_state_manager: PlayerStateManager) -> None:
    """设置全局 player_state_manager 实例"""
    global _player_state_manager
    _player_state_manager = player_state_manager

def get_global_monitor() -> Optional[BehaviorMonitor]:
    """获取全局 monitor 实例"""
    return _monitor

def get_global_player_state_manager() -> Optional[PlayerStateManager]:
    """获取全局 player_state_manager 实例"""
    return _player_state_manager

def initialize_context(monitor: BehaviorMonitor, player_state_manager: PlayerStateManager) -> None:
    """初始化全局上下文"""
    set_global_monitor(monitor)
    set_global_player_state_manager(player_state_manager)
    print("✅ 全局上下文已初始化")

def is_context_initialized() -> bool:
    """检查全局上下文是否已初始化"""
    return _monitor is not None and _player_state_manager is not None

def get_players_info() -> Dict[str, Dict[str, Any]]:
    """获取所有玩家信息"""
    return _players_info

def get_player_info(player_name: str) -> Optional[Dict[str, Any]]:
    """获取指定玩家信息"""
    return _players_info.get(player_name)

def add_player_info(player_name: str, player_info: Dict[str, Any]) -> None:
    """添加玩家信息"""
    _players_info[player_name] = player_info

def get_commander_order() -> str:
    """获取指挥官总军令"""
    return _commander_order

def set_commander_order(order: str) -> None:
    """设置指挥官总军令"""
    global _commander_order
    _commander_order = order

def get_all_player_names() -> List[str]:
    """获取所有玩家姓名列表"""
    return list(_players_info.keys())