import json
from datetime import datetime

def assess_churn_risk_with_deps(player_id: str) -> str:
    """评估指定玩家的流失风险，并实时更新到玩家状态中。"""
    from ..context import get_global_monitor, get_global_player_state_manager, is_context_initialized
    
    # --- 修正点 1: 使用“卫语句”模式 ---
    # 在函数入口处立即检查依赖。如果未初始化，直接返回模拟/错误结果。
    if not is_context_initialized():
        print("⚠️ 全局上下文未初始化，使用模拟数据进行评估")
        # 这里的模拟逻辑应该完整并直接返回，不与后续真实逻辑混合
        risk_level = "无法评估"
        risk_score = 0.0
        risk_factors = ["上下文未初始化"]
        
        # 直接返回模拟结果的JSON
        return json.dumps({
            "player_id": player_id, 
            "risk_level": risk_level, 
            "risk_score": risk_score, 
            "key_factors": risk_factors
        }, ensure_ascii=False)

    # 如果代码能执行到这里，说明上下文已初始化，可以安全地获取和使用实例。
    # 这就从根本上避免了 "referenced before assignment" 错误。
    monitor = get_global_monitor()
    player_state_manager = get_global_player_state_manager()
    
    # 断言可以增加代码可读性和类型检查的安全性
    assert monitor is not None
    assert player_state_manager is not None

    behaviors = monitor.get_player_history(player_id)
    risk_factors, risk_score = [], 0.0
    
    for b in behaviors:
        # 使用 b.action 是正确的，因为 get_player_history 返回的是 PlayerBehavior 对象
        if "不充了" in b.action: 
            risk_score += 0.3
            risk_factors.append("停止充值")
        elif "退出" in b.action: 
            risk_score += 0.25
            risk_factors.append("频繁退出")
        elif "消极" in b.action: 
            risk_score += 0.2
            risk_factors.append("负面情绪")
    
    if risk_score >= 0.7: 
        risk_level = "高风险"
    elif risk_score >= 0.4: 
        risk_level = "中风险"
    else: 
        risk_level = "低风险"
    
    final_risk_score = min(risk_score, 1.0)

    # --- 修正点 2: 修复函数调用参数 ---
    # 将字典拆分为独立的参数，以匹配 update_churn_risk 方法的签名。
    player_state_manager.update_churn_risk(
        player_id=player_id,
        risk_level=risk_level,
        risk_score=final_risk_score,
        risk_factors=risk_factors,
        update_time=datetime.now()
    )
    print(f"✅ 已更新玩家 {player_id} 的流失风险为: {risk_level}")
    
    return json.dumps({
        "player_id": player_id, 
        "risk_level": risk_level, 
        "risk_score": final_risk_score, 
        "key_factors": risk_factors
    }, ensure_ascii=False)


def assess_churn_risk(player_id: str) -> str:
    """简化版流失风险评估，用于向后兼容"""
    import json
    return json.dumps({
        "player_id": player_id,
        "risk_level": "低风险",
        "risk_score": 0.2,
        "key_factors": ["简化分析"],
        "note": "需要完整依赖进行真实分析"
    }, ensure_ascii=False)