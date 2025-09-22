import json
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..context import get_player_info



def get_player_inventory_status(player_id: str) -> str:
    """
    获取玩家背包中的体力道具状态
    
    Args:
        player_id: 玩家ID
    
    Returns:
        玩家背包状态的JSON字符串
    """
    print(f"")
    print(f"  - 玩家ID: {player_id}")
    
    # 从context.py获取玩家数据
    player_info = get_player_info(player_id)
    if not player_info:
        # 如果找不到玩家信息，返回默认数据
        player_data = {
            "stamina_items": [],
            "current_stamina": 10,
            "max_stamina": 100,
            "vip_level": 0
        }
        print(f"  - 警告: 未找到玩家 {player_id} 的信息，使用默认数据")
    else:
        player_data = {
            "stamina_items": player_info.get("stamina_items", []),
            "current_stamina": player_info.get("current_stamina", 10),
            "max_stamina": player_info.get("max_stamina", 100),
            "vip_level": player_info.get("vip_level", 0)
        }
    
    # 分析道具状态
    total_recovery_potential = sum(item["recovery_amount"] * item["count"] for item in player_data["stamina_items"])
    expiring_soon_items = []
    
    current_time = datetime.now()
    for item in player_data["stamina_items"]:
        try:
            expire_time = datetime.fromisoformat(item["expire_time"])
            if expire_time <= current_time + timedelta(days=3):  # 3天内过期
                expiring_soon_items.append(item)
        except:
            pass
    
    result = {
        "player_id": player_id,
        "stamina_items": player_data["stamina_items"],
        "total_items_count": len(player_data["stamina_items"]),
      #  "total_recovery_potential": total_recovery_potential,
     #   "expiring_soon_items": expiring_soon_items,
    #    "query_time": datetime.now().isoformat(),
        "status": "success"
    }
    
    print(f"  - 当前体力: {player_data['current_stamina']}/{player_data['max_stamina']}")
    print(f"  - 体力道具数量: {len(player_data['stamina_items'])}")
    print(f"  - 总恢复潜力: {total_recovery_potential}")
    print(f"  - 即将过期道具: {len(expiring_soon_items)}")
    
    return json.dumps(result, ensure_ascii=False)

def execute_personalized_guidance_popup(suggestion: str) -> str:
    """
    模拟弹窗引导，将传入的个性化建议输出出来
    
    Args:
        suggestion: Agent生成的个性化建议
    
    Returns:
        执行成功返回 'success'
    """
    print(f"--- 个性化体力引导弹窗执行 -------")
    print(f"弹窗引导：{suggestion}")
    return "success"