from typing import Dict, Any, List
import json # 确保导入json，以便处理可能的序列化

def get_historical_baseline_with_deps(player_id: str) -> Dict[str, Any]:
    """
    获取指定玩家的综合状态信息（从context.py获取真实实例）
    
    Args:
        player_id: 玩家ID
        
    Returns:
        包含玩家综合状态信息的字典，便于LLM总结
    """
    from ..context import get_global_monitor, get_global_player_state_manager, is_context_initialized

    # 使用卫语句模式，在函数入口处检查依赖，确保代码健壮性
    if not is_context_initialized():
        print("⚠️ 全局上下文未初始化，无法获取玩家基线数据。")
        return {"error": "Context not initialized", "player_id": player_id}

    # 从context获取真实实例
    state_manager = get_global_player_state_manager()
    monitor = get_global_monitor()
    
    # 断言，帮助类型检查器并增加运行时安全性
    assert state_manager is not None
    assert monitor is not None

    # 获取玩家状态对象，这是正确的
    player_state = state_manager.get_player_state(player_id)
    
    # 获取完整的玩家行为历史
    full_behavior_history = monitor.get_player_history(player_id)
    recent_behaviors_objects = full_behavior_history[-10:]

    # --- 关键修正：将 PlayerBehavior 对象转换为可序列化的字典 ---
    recent_behaviors_dicts = [
        # 假设 PlayerBehavior 对象有 action, timestamp, details 等属性
        # 如果它有 .to_dict() 方法会更佳: b.to_dict()           
        {
            "action": b.action,
            "timestamp": b.timestamp.isoformat(),
            "result": b.result
        } 
        for b in recent_behaviors_objects
    ]
    
    # --- 关键修正：直接访问 PlayerState 的扁平化属性 ---
    baseline_data = {
        "player_id": player_id,
        # 使用转换后的字典列表
        "recent_behaviors": recent_behaviors_dicts,
        "current_emotion": {
            # 直接访问属性，并提供默认值
            "dominant_emotion": player_state.emotion or "正常",
            "confidence": player_state.emotion_confidence,
            "keywords": player_state.emotion_keywords
        },
        "churn_risk": {
            # 直接访问 churn_risk_... 属性
            "level": player_state.churn_risk_level or "低",
            "score": player_state.churn_risk_score,
            "factors": player_state.churn_risk_factors
        },
        "bot_detection": {
            # 直接访问 is_bot, bot_... 属性
            "is_bot": player_state.is_bot,
            "confidence": player_state.bot_confidence,
            "patterns": player_state.bot_patterns
        },
        "behavior_summary": {
            # 从 monitor 获取正确的行为总数
            "total_behaviors": len(full_behavior_history),
            "recent_activity_level": len(recent_behaviors_objects),
            # 从转换后的字典列表中获取最后一个活动
            "last_activity": recent_behaviors_dicts[-1] if recent_behaviors_dicts else None
        }
    }
    
    return baseline_data

def get_historical_baseline(player_id: str) -> Dict[str, Any]:
    """简化版基线数据获取，用于向后兼容"""
    return {
        "player_id": player_id,
        "emotion": {"current": "正常", "confidence": 0.5},
        "churn_risk": {"level": "低风险", "score": 0.2},
        "bot_detection": {"is_bot": False, "confidence": 0.1},
        "recent_behaviors": [],
        "note": "简化分析，需要完整依赖进行真实分析"
    }