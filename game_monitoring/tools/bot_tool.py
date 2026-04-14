import json
from typing import List
from datetime import datetime

def detect_bot_with_deps(player_id: str) -> str:
    """检测玩家机器人行为（带依赖版本）"""
    from .runtime_access import (
        get_monitor,
        get_player_state_manager,
        is_context_initialized,
    )
    
    print(f"🤖 正在检测玩家 {player_id} 的机器人行为...")
    
    monitor = get_monitor()
    player_state_manager = get_player_state_manager()
    
    if not is_context_initialized():
        print("⚠️ 全局上下文未初始化，使用模拟数据")
        behaviors = [
            {"action": "精确重复操作", "timestamp": "14:30:15"},
            {"action": "异常高频点击", "timestamp": "14:30:16"},
            {"action": "完美时间间隔", "timestamp": "14:30:17"}
        ]
    else:
        behavior_history = monitor.get_player_history(player_id)
        behaviors = [
            {"action": b.action, "timestamp": b.timestamp.strftime("%H:%M:%S")}
            for b in behavior_history[-20:]
        ]
        
    is_bot, confidence, patterns = False, 0.0, []
    
    if len(behaviors) > 10: 
        patterns.append("高频操作")
        confidence += 0.3
    
    # --- 关键修改在这里 ---
    # 将 b.action 改为 b['action']
    if len({b['action'] for b in behaviors}) < 3 and len(behaviors) > 5: 
        patterns.append("重复性行为")
        confidence += 0.4
        is_bot = True
    
    final_confidence = min(confidence, 1.0)
    
    analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if is_context_initialized():
        player_state_manager.update_bot_detection(player_id,  
                                                    is_bot,
                                                    round(final_confidence, 2),
                                                    patterns,
                                                    datetime.now()) 
        print(f"✅ 已更新玩家 {player_id} 的机器人检测状态: {'是机器人' if is_bot else '非机器人'}")
    else:
        print(f"📝 模拟更新玩家 {player_id} 的机器人检测状态: {'是机器人' if is_bot else '非机器人'}")
    
    return json.dumps({
        "player_id": player_id,
        "is_bot": is_bot,
        "confidence": round(final_confidence, 2),
        "detected_patterns": patterns,
        "analysis_time": analysis_time
    }, ensure_ascii=False)

def detect_bot(player_id: str) -> str:
    """简化版机器人检测，用于向后兼容"""
    import json
    return json.dumps({
        "player_id": player_id,
        "is_bot": False,
        "confidence": 0.1,
        "detected_patterns": ["简化分析"],
        "note": "需要完整依赖进行真实分析"
    }, ensure_ascii=False)
