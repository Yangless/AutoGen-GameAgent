import json
from typing import List
from datetime import datetime


def analyze_emotion_with_deps(player_id: str) -> str:
    """分析玩家情绪状态（带依赖版本）"""
    from ..context import get_global_monitor, get_global_player_state_manager, is_context_initialized
    
    print(f"🔍 正在分析玩家 {player_id} 的情绪状态...")
    
    # 获取全局实例
    monitor = get_global_monitor()
    player_state_manager = get_global_player_state_manager()
    
    if not is_context_initialized():
        print("⚠️ 全局上下文未初始化，使用模拟数据")
        # 模拟玩家行为数据
        behaviors = [
            type('Behavior', (), {"action": "连续死亡3次", "timestamp": "14:30:15"}),
            type('Behavior', (), {"action": "愤怒退出副本", "timestamp": "14:32:20"}),
            type('Behavior', (), {"action": "发送负面消息", "timestamp": "14:33:45"})
        ]
    else:
        # 获取真实的玩家行为历史数据
        behaviors = monitor.get_player_history(player_id)
    
    # 情绪分析权重系统
    emotion_scores = {
        "愤怒": 0.0,
        "沮丧": 0.0,
        "焦虑": 0.0,
        "兴奋": 0.0,
        "满足": 0.0,
        "无聊": 0.0,
        "好奇": 0.0,
        "正常": 0.5  # 基础分数
    }
    
    keywords = []
    
    for behavior in behaviors:
        action = behavior.action
        
        # 愤怒情绪触发因素
        if any(keyword in action for keyword in ["被玩家攻击", "装备强化失败", "抽卡连续未中", "被其他玩家击败"]):
            emotion_scores["愤怒"] += 0.3
            keywords.append("挫败体验")
        
        if any(keyword in action for keyword in ["投诉客服", "评分游戏1星", "在世界频道发泄不满"]):
            emotion_scores["愤怒"] += 0.4
            keywords.append("表达愤怒")
        
        # 沮丧情绪触发因素
        if any(keyword in action for keyword in ["连续副本失败", "发布消极评论", "退出家族", "删除好友"]):
            emotion_scores["沮丧"] += 0.35
            keywords.append("消极行为")
        
        if any(keyword in action for keyword in ["点击退出游戏", "长时间未登录", "游戏时长急剧下降"]):
            emotion_scores["沮丧"] += 0.25
            keywords.append("逃避行为")
        
        # 焦虑情绪触发因素
        if any(keyword in action for keyword in ["突然不充了", "不买月卡了", "取消自动续费"]):
            emotion_scores["焦虑"] += 0.3
            keywords.append("经济担忧")
        
        if any(keyword in action for keyword in ["关注竞品游戏", "转让账号询价", "在论坛发布退游帖"]):
            emotion_scores["焦虑"] += 0.25
            keywords.append("未来不确定")
        
        # 兴奋情绪触发因素
        if any(keyword in action for keyword in ["获得稀有装备", "成功通关困难副本", "成功招募传说英雄", "完成成就"]):
            emotion_scores["兴奋"] += 0.4
            keywords.append("重大成就")
        
        if any(keyword in action for keyword in ["在PVP中获胜", "参与活动获得大奖", "充值获得额外奖励"]):
            emotion_scores["兴奋"] += 0.3
            keywords.append("胜利体验")
        
        # 满足情绪触发因素
        if any(keyword in action for keyword in ["升级成功", "技能升级成功", "建筑升级完成", "获得每日奖励"]):
            emotion_scores["满足"] += 0.25
            keywords.append("稳定进步")
        
        if any(keyword in action for keyword in ["家族排名上升", "被邀请加入高级家族", "在世界频道收到赞美"]):
            emotion_scores["满足"] += 0.3
            keywords.append("社交认可")
        
        # 无聊情绪触发因素
        if any(keyword in action for keyword in ["重复执行相同操作", "24小时在线", "行为模式过于规律"]):
            emotion_scores["无聊"] += 0.2
            keywords.append("机械化行为")
        
        if any(keyword in action for keyword in ["分解装备", "清空背包物品", "大量出售游戏道具"]):
            emotion_scores["无聊"] += 0.15
            keywords.append("缺乏目标")
        
        # 好奇情绪触发因素
        if any(keyword in action for keyword in ["解锁新地图", "开始点击游戏攻略", "打开招募英雄"]):
            emotion_scores["好奇"] += 0.3
            keywords.append("探索欲望")
        
        if any(keyword in action for keyword in ["登陆游戏", "打开副本", "打开世界频道"]):
            emotion_scores["好奇"] += 0.1
            keywords.append("日常探索")
    
    # 确定主导情绪
    dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
    emotion = dominant_emotion[0]
    base_confidence = min(dominant_emotion[1], 1.0)
    
    # 根据行为数量调整置信度
    behavior_count = len(behaviors)
    if behavior_count == 0:
        emotion, confidence = "未知", 0.0
        keywords = ["无行为数据"]
    elif behavior_count < 3:
        confidence = base_confidence * 0.6  # 数据不足，降低置信度
    elif behavior_count < 5:
        confidence = base_confidence * 0.8
    else:
        confidence = base_confidence * 0.95  # 数据充足，高置信度
    
    # 去重关键词
    keywords = list(set(keywords)) if keywords else ["正常游戏"]
    
    # 更新玩家状态
    if is_context_initialized():
        # 使用真实的状态管理器        
        player_state_manager.update_emotion(player_id, 
                                            emotion,
                                            confidence,
                                            keywords,
                                            datetime.now())
        print(f"✅ 已更新玩家 {player_id} 的情绪状态: {emotion} (置信度: {confidence:.2f})")
    else:
        print(f"📝 模拟更新玩家 {player_id} 的情绪状态: {emotion} (置信度: {confidence:.2f})")
    
    return json.dumps({
        "player_id": player_id, 
        "emotion": emotion, 
        "confidence": round(confidence, 2), 
        "trigger_keywords": keywords,
        "emotion_scores": {k: round(v, 2) for k, v in emotion_scores.items() if v > 0}
    }, ensure_ascii=False)

def analyze_emotion(player_id: str) -> str:
    """简化版情绪分析，用于向后兼容"""
    # 直接调用带依赖的版本
    return analyze_emotion_with_deps(player_id)