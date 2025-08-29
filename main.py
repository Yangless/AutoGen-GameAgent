import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any
from functools import partial

# Autogen 相关的导入
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import MagenticOneGroupChat
# ！！！ 新增导入 Console UI ！！！
from autogen_agentchat.ui import Console

# 导入模型配置
from config import (
    custom_model_client, doubao_client, deepseek_client, qwen_client,
    settings, doubao_settings, deepseek_settings, qwen_settings
)


# --- 数据结构和模拟器 (保持不变) ---
# --- 1. 数据结构和模拟器 (保持不变) ---
class PlayerBehavior:
    def __init__(self, player_id: str, timestamp: datetime, action: str, result: str = "", metadata: Dict[str, Any] = None):
        self.player_id = player_id
        self.timestamp = timestamp
        self.action = action
        self.result = result
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"PlayerBehavior(id={self.player_id}, timestamp='{self.timestamp.isoformat()}', action='{self.action}')"

class PlayerBehaviorSimulator:
    def __init__(self):
        # 基础游戏行为场景
        self.basic_scenarios = ["玩家登陆游戏", "玩家打开副本", "玩家迁城", "玩家攻城", "玩家被玩家攻击", "玩家攻占土地", "玩家加入家族", "玩家加入国家", "玩家讨伐蛮族", "玩家打开招募英雄", "玩家跳转充值页面", "玩家打开世界频道"]
        
        # 积极情绪相关场景
        self.positive_scenarios = [
            "玩家成功通关困难副本", "玩家获得稀有装备", "玩家升级成功", "玩家完成成就", 
            "玩家在PVP中获胜", "玩家成功招募传说英雄", "玩家家族排名上升", "玩家获得每日奖励",
            "玩家参与活动获得大奖", "玩家解锁新地图", "玩家技能升级成功", "玩家建筑升级完成",
            "玩家在世界频道收到赞美", "玩家被邀请加入高级家族", "玩家充值获得额外奖励"
        ]
        
        # 消极情绪相关场景
        self.negative_scenarios = [
            "发布消极评论", "突然不充了", "不买月卡了", "抽卡频率变低", "玩家分解装备", 
            "玩家退出家族", "玩家退出登录", "玩家点击退出游戏", "玩家连续副本失败", 
            "玩家被其他玩家击败多次", "玩家抽卡连续未中", "玩家装备强化失败", 
            "玩家在世界频道发泄不满", "玩家长时间未登录", "玩家删除好友", 
            "玩家取消自动续费", "玩家投诉客服", "玩家评分游戏1星"
        ]
        
        # 流失风险相关场景
        self.churn_risk_scenarios = [
            "玩家连续3天未登录", "玩家游戏时长急剧下降", "玩家停止充值行为", 
            "玩家卸载游戏客户端", "玩家清空背包物品", "玩家转让账号询价",
            "玩家在论坛发布退游帖", "玩家关注竞品游戏", "玩家修改昵称为告别语",
            "玩家大量出售游戏道具", "玩家退出所有社交群组"
        ]
        
        # 机器人行为相关场景
        self.bot_scenarios = [
            "玩家操作频率异常高", "玩家24小时在线", "玩家行为模式过于规律", 
            "玩家响应时间异常快", "玩家重复执行相同操作", "玩家移动路径过于精确",
            "玩家从不参与社交互动", "玩家操作无人类特征", "玩家同时多开账号"
        ]
        
        # 合并所有场景
        self.player_scenarios = (self.basic_scenarios + self.positive_scenarios + 
                               self.negative_scenarios + self.churn_risk_scenarios + 
                               self.bot_scenarios)
    
    def generate_behavior(self, player_id: str) -> PlayerBehavior:
        action = random.choice(self.player_scenarios)
        return PlayerBehavior(player_id=player_id, timestamp=datetime.now(), action=action)
    
    def generate_targeted_behavior(self, player_id: str, behavior_type: str) -> PlayerBehavior:
        """生成特定类型的行为"""
        if behavior_type == "positive":
            action = random.choice(self.positive_scenarios)
        elif behavior_type == "negative":
            action = random.choice(self.negative_scenarios)
        elif behavior_type == "churn_risk":
            action = random.choice(self.churn_risk_scenarios)
        elif behavior_type == "bot":
            action = random.choice(self.bot_scenarios)
        else:
            action = random.choice(self.basic_scenarios)
        
        return PlayerBehavior(player_id=player_id, timestamp=datetime.now(), action=action)
    
    def generate_behavior_sequence(self, player_id: str, sequence_type: str) -> List[PlayerBehavior]:
        """生成反映真实玩家变化的行为序列"""
        behaviors = []
        
        if sequence_type == "frustrated_player":
            # 沮丧玩家：连续失败 -> 消极情绪 -> 退出
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家连续副本失败"),
                PlayerBehavior(player_id, datetime.now(), "玩家装备强化失败"),
                PlayerBehavior(player_id, datetime.now(), "发布消极评论"),
                PlayerBehavior(player_id, datetime.now(), "玩家在世界频道发泄不满"),
                PlayerBehavior(player_id, datetime.now(), "玩家点击退出游戏")
            ]
        
        elif sequence_type == "churn_risk_player":
            # 流失风险玩家：停止充值 -> 减少活动 -> 退出社交 -> 长期离线
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "突然不充了"),
                PlayerBehavior(player_id, datetime.now(), "不买月卡了"),
                PlayerBehavior(player_id, datetime.now(), "玩家游戏时长急剧下降"),
                PlayerBehavior(player_id, datetime.now(), "玩家退出家族"),
                PlayerBehavior(player_id, datetime.now(), "玩家连续3天未登录")
            ]
        
        elif sequence_type == "excited_player":
            # 兴奋玩家：获得成就 -> 积极参与 -> 增加投入
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家获得稀有装备"),
                PlayerBehavior(player_id, datetime.now(), "玩家成功通关困难副本"),
                PlayerBehavior(player_id, datetime.now(), "玩家在世界频道收到赞美"),
                PlayerBehavior(player_id, datetime.now(), "玩家跳转充值页面"),
                PlayerBehavior(player_id, datetime.now(), "玩家充值获得额外奖励")
            ]
        
        elif sequence_type == "bot_pattern":
            # 机器人模式：规律性操作
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家24小时在线"),
                PlayerBehavior(player_id, datetime.now(), "玩家操作频率异常高"),
                PlayerBehavior(player_id, datetime.now(), "玩家重复执行相同操作"),
                PlayerBehavior(player_id, datetime.now(), "玩家从不参与社交互动"),
                PlayerBehavior(player_id, datetime.now(), "玩家行为模式过于规律")
            ]
        
        elif sequence_type == "returning_player":
            # 回归玩家：长期离线 -> 重新登录 -> 探索变化
            behaviors = [
                PlayerBehavior(player_id, datetime.now(), "玩家长时间未登录"),
                PlayerBehavior(player_id, datetime.now(), "玩家登陆游戏"),
                PlayerBehavior(player_id, datetime.now(), "玩家开始点击游戏攻略"),
                PlayerBehavior(player_id, datetime.now(), "玩家解锁新地图"),
                PlayerBehavior(player_id, datetime.now(), "玩家参与活动获得大奖")
            ]
        
        return behaviors
    
    def generate_mock_dataset(self, dataset_type: str, num_players: int = 10) -> Dict[str, List[PlayerBehavior]]:
        """生成完整的mock数据集"""
        dataset = {}
        
        if dataset_type == "mixed_emotions":
            # 混合情绪数据集
            for i in range(num_players):
                player_id = f"player_{i+1}"
                emotion_type = random.choice(["frustrated_player", "excited_player", "churn_risk_player"])
                dataset[player_id] = self.generate_behavior_sequence(player_id, emotion_type)
        
        elif dataset_type == "churn_analysis":
            # 流失分析数据集
            for i in range(num_players):
                player_id = f"churn_player_{i+1}"
                dataset[player_id] = self.generate_behavior_sequence(player_id, "churn_risk_player")
        
        elif dataset_type == "bot_detection":
            # 机器人检测数据集
            for i in range(num_players):
                player_id = f"bot_player_{i+1}"
                dataset[player_id] = self.generate_behavior_sequence(player_id, "bot_pattern")
        
        elif dataset_type == "engagement_boost":
            # 参与度提升数据集
            for i in range(num_players):
                player_id = f"engage_player_{i+1}"
                # 混合沮丧和兴奋玩家，用于测试干预效果
                if i % 2 == 0:
                    dataset[player_id] = self.generate_behavior_sequence(player_id, "frustrated_player")
                else:
                    dataset[player_id] = self.generate_behavior_sequence(player_id, "excited_player")
        
        return dataset
    
    def load_mock_data_to_monitor(self, dataset: Dict[str, List[PlayerBehavior]], monitor_instance):
        """将mock数据加载到监控器中"""
        for player_id, behaviors in dataset.items():
            for behavior in behaviors:
                monitor_instance.add_behavior(behavior)
                time.sleep(0.1)  # 模拟时间间隔
        print(f"✅ 已加载 {len(dataset)} 个玩家的mock数据到监控系统")

# --- 2. 监控器 (保持不变) ---
class BehaviorMonitor:
    def __init__(self, threshold: int = 1):
        self.threshold = threshold
        self.player_negative_counts = {}
        self.behavior_history: List[PlayerBehavior] = []
    
    def add_behavior(self, behavior: PlayerBehavior) -> bool:
        self.behavior_history.append(behavior)
        if behavior.action in ["发布消极评论", "突然不充了", "不买月卡了", "玩家点击退出游戏"]:
            self.player_negative_counts.setdefault(behavior.player_id, 0)
            self.player_negative_counts[behavior.player_id] += 1
            if self.player_negative_counts[behavior.player_id] >= self.threshold:
                # print(f"⚠️  触发监控阈值: 玩家 {behavior.player_id} 负面行为达到 {self.threshold} 次")
                print(f"⚠️  触发监控阈值: 玩家 {behavior.player_id} 行为触发")
                return True
        return False
    
    def get_player_history(self, player_id: str) -> List[PlayerBehavior]:
        return [b for b in self.behavior_history if b.player_id == player_id]

# --- 3. 玩家状态管理系统 ---
class PlayerState:
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.emotion = None
        self.emotion_confidence = 0.0
        self.emotion_keywords = []
        self.churn_risk_level = None
        self.churn_risk_score = 0.0
        self.churn_risk_factors = []
        self.is_bot = False
        self.bot_confidence = 0.0
        self.bot_patterns = []
        self.last_updated = datetime.now()
    
    def to_dict(self):
        return {
            "player_id": self.player_id,
            "emotion": self.emotion,
            "emotion_confidence": self.emotion_confidence,
            "emotion_keywords": self.emotion_keywords,
            "churn_risk_level": self.churn_risk_level,
            "churn_risk_score": self.churn_risk_score,
            "churn_risk_factors": self.churn_risk_factors,
            "is_bot": self.is_bot,
            "bot_confidence": self.bot_confidence,
            "bot_patterns": self.bot_patterns,
            "last_updated": self.last_updated.isoformat()
        }

class PlayerStateManager:
    def __init__(self):
        self.player_states: Dict[str, PlayerState] = {}
    
    def get_or_create_state(self, player_id: str) -> PlayerState:
        if player_id not in self.player_states:
            self.player_states[player_id] = PlayerState(player_id)
        return self.player_states[player_id]
    
    def update_emotion(self, player_id: str, emotion: str, confidence: float, keywords: List[str]):
        state = self.get_or_create_state(player_id)
        state.emotion = emotion
        state.emotion_confidence = confidence
        state.emotion_keywords = keywords
        state.last_updated = datetime.now()
    
    def update_churn_risk(self, player_id: str, risk_level: str, risk_score: float, risk_factors: List[str]):
        state = self.get_or_create_state(player_id)
        state.churn_risk_level = risk_level
        state.churn_risk_score = risk_score
        state.churn_risk_factors = risk_factors
        state.last_updated = datetime.now()
    
    def update_bot_detection(self, player_id: str, is_bot: bool, confidence: float, patterns: List[str]):
        state = self.get_or_create_state(player_id)
        state.is_bot = is_bot
        state.bot_confidence = confidence
        state.bot_patterns = patterns
        state.last_updated = datetime.now()
    
    def get_player_state(self, player_id: str) -> PlayerState:
        return self.get_or_create_state(player_id)

# --- 4. 共享的监控器和状态管理器实例 ---
# 创建一个所有分析工具函数都可以访问的全局监控器实例。
# 这确保了所有分析 Agent 都从同一个数据源获取信息。
monitor = BehaviorMonitor()
player_state_manager = PlayerStateManager()


# --- 4. 工具函数 (修改后) ---
# 函数签名被简化，不再接收 monitor 参数。
# 它们直接使用在上面定义的全局 monitor 实例。

# 分析类工具函数
def analyze_emotion(player_id: str) -> str:
    """分析指定玩家的情绪状态，并实时更新到玩家状态中。"""
    behaviors = monitor.get_player_history(player_id) # 直接使用全局 monitor
    
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
    
    # 实时更新玩家状态
    player_state_manager.update_emotion(player_id, emotion, confidence, keywords)
    print(f"📊 已更新玩家 {player_id} 的情绪状态: {emotion} (置信度: {confidence:.2f})")
    
    return json.dumps({
        "player_id": player_id, 
        "emotion": emotion, 
        "confidence": round(confidence, 2), 
        "trigger_keywords": keywords,
        "emotion_scores": {k: round(v, 2) for k, v in emotion_scores.items() if v > 0}
    }, ensure_ascii=False)

def assess_churn_risk(player_id: str) -> str:
    """评估指定玩家的流失风险，并实时更新到玩家状态中。"""
    behaviors = monitor.get_player_history(player_id) # 直接使用全局 monitor
    risk_factors, risk_score = [], 0.0
    for b in behaviors:
        if "不充了" in b.action: risk_score += 0.3; risk_factors.append("停止充值")
        elif "退出" in b.action: risk_score += 0.25; risk_factors.append("频繁退出")
        elif "消极" in b.action: risk_score += 0.2; risk_factors.append("负面情绪")
    if risk_score >= 0.7: risk_level = "高风险"
    elif risk_score >= 0.4: risk_level = "中风险"
    else: risk_level = "低风险"
    
    # 实时更新玩家状态
    final_risk_score = min(risk_score, 1.0)
    player_state_manager.update_churn_risk(player_id, risk_level, final_risk_score, risk_factors)
    print(f"⚠️ 已更新玩家 {player_id} 的流失风险: {risk_level} (风险分数: {final_risk_score})")
    
    return json.dumps({"player_id": player_id, "risk_level": risk_level, "risk_score": final_risk_score, "key_factors": risk_factors}, ensure_ascii=False)

def detect_bot(player_id: str) -> str:
    """检测指定玩家是否具有机器人行为特征，并实时更新到玩家状态中。"""
    behaviors = monitor.get_player_history(player_id) # 直接使用全局 monitor
    is_bot, confidence, patterns = False, 0.0, []
    if len(behaviors) > 10: patterns.append("高频操作"); confidence += 0.3
    if len({b.action for b in behaviors}) < 3 and len(behaviors) > 5: patterns.append("重复性行为"); confidence += 0.4; is_bot = True
    
    # 实时更新玩家状态
    final_confidence = min(confidence, 1.0)
    player_state_manager.update_bot_detection(player_id, is_bot, final_confidence, patterns)
    print(f"🤖 已更新玩家 {player_id} 的机器人检测结果: {'是机器人' if is_bot else '非机器人'} (置信度: {final_confidence})")
    
    return json.dumps({"player_id": player_id, "is_bot": is_bot, "confidence": final_confidence, "detected_patterns": patterns}, ensure_ascii=False)

def get_historical_baseline(player_id: str) -> str:
    """获取指定玩家的综合状态信息，并返回精简版，便于LLM总结。"""
    behaviors = monitor.get_player_history(player_id)
    player_state = player_state_manager.get_player_state(player_id)
    
    # 只保留最近3条行为用于上下文
    recent_actions = [
        {"timestamp": b.timestamp.strftime("%H:%M"), "action": b.action}
        for b in behaviors[-5:]
    ]

    summary_data = {
        "player_id": player_id,
        "recent_behaviors": recent_actions,
        "current_emotion": {
            "emotion": player_state.emotion,
            "confidence": round(player_state.emotion_confidence, 2),
            "keywords": player_state.emotion_keywords
        } if player_state.emotion else None,
        "churn_risk": {
            "level": player_state.churn_risk_level,
            "score": round(player_state.churn_risk_score, 2),
            "factors": player_state.churn_risk_factors
        } if player_state.churn_risk_level else None,
        "bot_detection": {
            "is_bot": player_state.is_bot,
            "confidence": round(player_state.bot_confidence, 2),
            "patterns": player_state.bot_patterns
        },
        "summary": {
            "total_behavior_count": len(behaviors),
            "last_updated": player_state.last_updated.isoformat(),
            "has_data": len(behaviors) > 0
        }
    }

    if not behaviors:
        summary_data["message"] = "未找到该玩家的行为记录"

    print(f"📊 玩家 {player_id} 的精简状态已生成，用于总结分析。")
    return json.dumps(summary_data, ensure_ascii=False)

# --- 修改后的工具函数 ---
# 它现在是一个纯粹的执行器，不再生成内容

def execute_engagement_action(
    player_id: str, 
    action_type: str, 
    reason: str, 
    personalized_email_content: str  # 仍然接收内容用于日志/模拟
) -> str:
    """
    对指定玩家执行激励或安抚操作。
    此函数负责记录操作并模拟发送由Agent生成的个性化邮件。

    Args:
        player_id (str): 目标玩家的ID。
        action_type (str): 执行的动作类型 (e.g., 'emotional_care_with_reward').
        reason (str): 执行此操作的原因总结。
        personalized_email_content (str): 由EngagementAgent预先生成好的、完整的个性化邮件正文。
    """
    print(f"--- TOOL EXECUTION: execute_engagement_action ---")
    print(f"  - Player ID: {player_id}")
    print(f"  - Action Type: {action_type}")
    print(f"  - Reason: {reason}")
    # 可选：只打印前100字符
    print(f"  - Email Content (truncated): {personalized_email_content}...")

    # 模拟操作成功
    success = True  # 可以加入随机失败来测试鲁棒性
    
    if success:
        result_dict = {
            "status": "success",
            "message": f"Action '{action_type}' for player '{player_id}' executed successfully."
        }
    else:
        result_dict = {
            "status": "failed",
            "message": f"Failed to execute action for player {player_id} due to a system error."
        }
        
    return json.dumps(result_dict, ensure_ascii=False)

def execute_guidance_action(player_id: str, action_type: str, reason: str) -> str:
    """对指定玩家执行引导操作（如弹窗）。"""
    print(f"执行游戏内引导: 对玩家 {player_id} 进行 '{action_type}' 因为 '{reason}'")
    
    # 首先构造Python字典
    if random.choice([True, True]):
        result_dict = {
            "status": "success", 
            "action": action_type, 
            "player_id": player_id, 
            "reason": reason
        }
    else:
        result_dict = {
            "status": "failed", 
            "error": "玩家不在线", 
            "player_id": player_id
        }
        
    # 在最后返回时，统一使用 ensure_ascii=False 进行转换
    print("result_dict:", result_dict)
    return json.dumps(result_dict, ensure_ascii=False)

# --- 主系统类 (最终修正版) ---
class GamePlayerMonitoringSystem:
    def __init__(self, model_client=None):
        self.model_client = model_client or custom_model_client
        self.simulator = PlayerBehaviorSimulator()
        # 使用全局monitor实例，确保数据一致性
        self.monitor = monitor
                # --- 分析类工具Agent (Analysis Tool Agents) ---

        # 1. EmotionRecognitionAgent (情绪识别专家)
        self.emotion_agent = AssistantAgent(
            name="EmotionRecognitionAgent",
            system_message=(
                "你是一名专业的玩家情绪识别与状态管理专家。你的主要任务是使用 `analyze_emotion` 工具来分析玩家的情绪状态，"
                "该工具不仅会分析情绪，还会自动将分析结果实时更新到玩家的状态管理系统中。"
                "当你完成分析后，玩家的情绪状态（如'愤怒'、'沮丧'、'正常'等）会被永久保存，供其他系统组件使用。"
                "请直接调用工具并确认状态更新成功。"
            ),
            description="专门分析并实时更新玩家情绪状态的专家，确保情绪数据被持久化保存。",
            # model_client=self.model_client,
            # model_client=deepseek_client,
            model_client=qwen_client,
            tools=[analyze_emotion], # 直接绑定函数
        )
        
        # 2. ChurnRiskAgent (流失风险预警官)
        self.churn_agent = AssistantAgent(      
            name="ChurnRiskAgent",
            system_message=(
                "你是一名资深的玩家流失风险分析与状态管理专家。你的主要职责是使用 `assess_churn_risk` 工具来评估玩家的流失风险等级，"
                "该工具不仅会分析风险等级，还会自动将评估结果实时更新到玩家的状态管理系统中。"
                "当你完成评估后，玩家的流失风险信息（如'高风险'、'中风险'、'低风险'及风险因素）会被永久保存。"
                "请直接调用工具并确认风险状态更新成功。"
            ),
            description="专门评估并实时更新玩家流失风险状态的专家，确保风险数据被持久化保存。",
            model_client=qwen_client,
            tools=[assess_churn_risk], # 直接绑定函数
        )

        # 3. BotDetectionAgent (机器人检测官)
        self.bot_agent = AssistantAgent(
            name="BotDetectionAgent",
            system_message=(
                "你是一个精密的游戏机器人行为检测与状态管理专家。你的核心任务是利用 `detect_bot` 工具分析玩家的行为序列，"
                "该工具不仅会检测机器人特征，还会自动将检测结果实时更新到玩家的状态管理系统中。"
                "当你完成检测后，玩家的机器人检测信息（是否为机器人、置信度、检测到的模式）会被永久保存。"
                "请直接调用工具并确认检测状态更新成功。"
            ),
            description="专门检测并实时更新玩家机器人行为状态的专家，确保检测数据被持久化保存。",
            model_client=qwen_client,
            tools=[detect_bot], # 直接绑定函数
        )


        self.behavioral_analyst_agent = AssistantAgent(
            name="BehavioralAnalystAgent",
            system_message=(
              "你是一名资深的游戏行为数据分析师。\n\n"
"你必须先调用 `get_historical_baseline` 获取数据，然后基于数据生成一段自然语言总结。\n"
"你不能直接返回工具的 JSON 结果，必须用中文输出一段不超过 150 字的分析报告。\n"
"报告需包含情绪、流失风险、机器人检测和建议。\n"
"示例：'玩家 player_1 情绪为【焦虑】，因停止充值。流失风险【低】。无机器人行为。建议观察。'\n"
"记住：你的输出是给团队负责人看的，不是给机器解析的。"
                
                "🎯 示例输出：\n"
                "'玩家 player_123 当前情绪为【沮丧】，因连续副本失败和退出家族。流失风险为【高】，已多日未登录。无机器人行为。建议立即进行情感安抚干预。'"
            ),
            description="为团队提供玩家总结性分析报告。",
            model_client=doubao_client,
            tools=[get_historical_baseline],
            reflect_on_tool_use=True,
            
        )
        
        # --- 干预类工具Agent (Intervention Tool Agents) ---

        # 5. EngagementAgent (互动激励执行官) - 支持LLM生成个性化邮件
        self.engagement_agent = AssistantAgent(
            name="EngagementAgent",
            system_message=(
        "你是一名专业的玩家互动专家，负责执行个性化的关怀和激励任务。你的职责是：\n"
        "1. 根据玩家状态，创作一封温暖且个性化的邮件内容（仅用于内部调用）。\n"
        "2. 调用 `execute_engagement_action` 工具来执行发送操作。\n\n"
        "⚠️ 重要规则：\n"
        "- 你可以在调用工具时传递邮件内容，但 **在最终向用户汇报时，绝对不要透露邮件的具体内容**。\n"
        "- 你的最终回复必须简洁，只包含：\n"
        "  - 执行的动作类型\n"
        "  - 执行原因\n"
        "  - 执行结果（成功/失败）\n\n"
        "例如：'已为玩家 player_123 发送关怀邮件，原因是检测到其情绪沮丧，操作已成功。'"          
            ),
            description="负责创作个性化邮件并调用工具执行玩家激励与关怀的专家。",
            model_client=qwen_client,
            tools=[execute_engagement_action],
        )

        # 6. GuidanceAgent (游戏内引导执行官)
        self.guidance_agent = AssistantAgent(       
            name="GuidanceAgent",
            system_message=(
                "你是一名精准的游戏内引导执行官。你的专长是在玩家的游戏界面上进行实时干预，以帮助他们克服困难或发现新内容。你的主要职责是调用 `execute_guidance_action` 工具，"
                "你通过调用 `execute_guidance_action` 工具来完成任务，具体操作包括‘弹出帮助UI提示’、‘高亮显示某个按钮’、‘向玩家推荐一个新任务或活动’等。"
                "你的行动应该精准且及时，旨在解决玩家在游戏过程中遇到的具体问题。只在游戏内进行操作。"
                "当你收到请求时，请调用工具并提供总结性的引导干预信息。"  
            ),
            description="通过UI弹窗、内容推荐等方式在游戏界面内对玩家进行总结性引导的执行官。",
            model_client=qwen_client,
            tools=[execute_guidance_action],
        )

        # Agent团队定义
        self.analysis_team = MagenticOneGroupChat(
            [
                self.emotion_agent,
                self.churn_agent,
                self.bot_agent,
                self.behavioral_analyst_agent,
                self.engagement_agent,
                self.guidance_agent,
            ], 
            # model_client=self.model_client
            model_client=doubao_client
        )
        print("🎮 游戏玩家实时行为监控助手系统已初始化 (最终架构)")

    async def trigger_analysis_and_intervention(self, player_id: str):
        print(f"\n🤖 启动多智能体团队，为玩家 {player_id} 进行分析和干预...")
        behaviors = self.monitor.get_player_history(player_id)
        behavior_summary = "\n".join([f"- {b.timestamp.strftime('%H:%M:%S')}: {b.action}" for b in behaviors[-5:]])

        # task = f"""
        # 警报：玩家 {player_id} 触发了高负面行为阈值。
        # 该玩家最近的行为记录如下:
        # {behavior_summary}
        # 请你作为首席分析师，立即按以下步骤操作：
        # 1. 对该玩家进行全面的状态分析（情绪、流失风险、机器人行为）。
        # 2. 根据你的分析，决定一个最合适的干预方案。
        # 3. 执行该干预方案。
        # 4. 最后，将你的完整分析、决策和执行结果总结给我。
        # """
        task = f"""
        **紧急警报：玩家 {player_id} 行为异常，启动多智能体协作流程。**

        **背景信息:**
        - **触发原因:** 系统监测到玩家触发了高负面行为阈值。
        - **近期行为摘要 (最近5条):**
        {behavior_summary}

        **你的角色与任务:**
        你现在是这个多智能体团队的 **首席调度官 (Chief Orchestrator)**。你的职责是高效地协调团队中的各位专家Agent，对玩家进行全面的分析，并根据分析结果执行最恰当的干预措施。
        """


        # **请严格按照以下流程执行:**

        # **第一步：并行综合分析 (Parallel Analysis)**
        # 你必须 **立即并行启动** 以下三项独立的分析任务，将它们同时分派给对应的专家Agent。不要等待一个完成后再开始下一个：
        # 1.  **情绪状态分析:** 指派 `EmotionRecognitionAgent` 对玩家当前的情绪进行深入分析。
        # 2.  **流失风险评估:** 指派 `ChurnRiskAgent` 评估玩家的流失风险等级（例如：低、中、高）。
        # 3.  **机器人行为检测:** 指派 `BotDetectionAgent` 检查该玩家的行为模式，判断是否存在机器人脚本嫌疑。

        # **第二步：汇总诊断与决策 (Synthesize & Decide)**
        # 等待所有并行分析任务完成后，仔细审查由各个专家Agent返回的分析结果。基于这些多维度的信息，进行综合诊断并回答以下核心问题：
        # - 玩家当前面临的主要问题是什么？（例如：是因游戏挫败感导致的愤怒情绪？还是有高风险流失倾向的消极行为？或是可疑的自动化操作？）
        # - 基于你的诊断，什么是最优先需要解决的问题？

        # **第三步：选择并执行干预 (Select & Execute Intervention)**
        # 根据你在上一步的决策，从干预类Agent中 **选择一个最合适的** 来执行任务。
        # - 如果决策是安抚玩家情绪、提升参与度（如发放小额奖励、发送鼓励信息），请指令 `EngagementAgent` 执行。
        # - 如果决策是在游戏内提供帮助（如弹出引导提示、推荐相关攻略或活动），请指令 `GuidanceAgent` 执行。
            

        # **第四步：生成最终报告 (Final Report)**
        # 在干预措施执行完毕后，整合整个流程的信息，不要再调用agent tools，向我提交一份完整的最终报告。报告必须包含以下四个部分：
        # 1.  **[综合分析结果]**: 清晰列出情绪、流失风险和机器人检测三个方面的分析结论。
        # 2.  **[核心决策逻辑]**: 详细阐述你如何根据分析结果得出了最终的干预决策。
        # 3.  **[执行的干预措施]**: 明确说明哪个Agent被调用，以及它执行了什么具体操作。
        # 4.  **[预期目标]**: 简述本次干预期望达到的效果。
        # """


        # ！！！ 修正点 4：使用新的启动方式 ！！！
        # 使用 Console UI 以流式方式运行团队，实时查看过程
        print("\n" + "="*25 + " 团队实时动态 " + "="*23)
        await Console(self.analysis_team.run_stream(task=task))
        print("="*62 + "\n")

    async def simulate_monitoring_session(self, duration_seconds: int = 60, mode: str = "random", dataset_type: str = "mixed"):
        """
        模拟监控会话
        
        Args:
            duration_seconds: 会话持续时间（秒）
            mode: 数据生成模式 - "random" 随机生成 或 "preset" 预设序列
            dataset_type: 当mode="preset"时，指定数据集类型（"mixed", "negative", "positive"）
        """
        print(f"\n🚀 开始模拟监控会话 (持续 {duration_seconds} 秒, 模式: {mode})...")
        
        if mode == "random":
            # 随机生成模式
            players = [f"player_{random.randint(100, 999)}" for _ in range(5)]
            start_time = time.time()
            
            while time.time() - start_time < duration_seconds:
                player_id = random.choice(players)
                behavior = self.simulator.generate_behavior(player_id)
                print(f"📝 玩家行为: {player_id} - {behavior.action}")
                
                # 将生成的行为数据保存到monitor中
                if self.monitor.add_behavior(behavior):
                    await self.trigger_analysis_and_intervention(player_id)
                    self.monitor.player_negative_counts[player_id] = 0
                    print(f"🔄 已重置玩家 {player_id} 的负面行为计数")
                
                await asyncio.sleep(random.uniform(2, 4)) # 增加间隔以便观察
                
        elif mode == "preset":
            # 预设序列模式
            print(f"📦 加载预设数据集 (类型: {dataset_type})...")
            
            # 生成预设数据集
            dataset = self.simulator.generate_mock_dataset(dataset_type, num_players=5)
            print(f"✅ 已生成 {len(dataset)} 个玩家的行为数据")
            
            # 将数据加载到监控器中并触发分析
            for player_id, behaviors in dataset.items():
                print(f"\n👤 处理玩家: {player_id}")
                
                for behavior in behaviors:
                    print(f"📝 玩家行为: {player_id} - {behavior.action}")
                    
                    # 将行为数据保存到monitor中
                    if self.monitor.add_behavior(behavior):
                        await self.trigger_analysis_and_intervention(player_id)
                        self.monitor.player_negative_counts[player_id] = 0
                        print(f"🔄 已重置玩家 {player_id} 的负面行为计数")
                    
                    # 模拟实时处理间隔
                    await asyncio.sleep(1)
                    
        else:
            print(f"❌ 不支持的模式: {mode}，请使用 'random' 或 'preset'")
            return
        
        print("\n✅ 监控会话结束")

async def main(mode: str = "random", dataset_type: str = "mixed", duration: int = 60):
    """
    主函数
    
    Args:
        mode: 数据生成模式 - "random" 随机生成 或 "preset" 预设序列
        dataset_type: 当mode="preset"时，指定数据集类型（"mixed", "negative", "positive"）
        duration: 会话持续时间（秒）
    """
    print("=" * 50)
    print("🎮 游戏玩家实时行为监控助手")
    print("=" * 50)
    
    print(f"📋 运行参数:")
    print(f"   - 数据模式: {mode}")
    if mode == "preset":
        print(f"   - 数据集类型: {dataset_type}")
    print(f"   - 持续时间: {duration}秒")
    print("-" * 50)
    
    system = GamePlayerMonitoringSystem()
    await system.simulate_monitoring_session(duration_seconds=duration, mode=mode, dataset_type=dataset_type)
    print("\n🎯 系统演示完成!")

def run_demo():
    """
    演示函数，展示两种模式的使用
    """
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        dataset_type = sys.argv[2] if len(sys.argv) > 2 else "mixed"
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    else:
        # 默认演示随机模式
        mode = "random"
        dataset_type = "mixed"
        duration = 60
        
        print("\n💡 使用说明:")
        print("   python main.py [mode] [dataset_type] [duration]")
        print("   - mode: 'random' (随机生成) 或 'preset' (预设序列)")
        print("   - dataset_type: 'mixed', 'negative', 'positive' (仅preset模式)")
        print("   - duration: 持续时间（秒）")
        print("\n示例:")
        print("   python main.py random")
        print("   python main.py preset negative 30")
        print("   python main.py preset mixed 45")
        print()
    
    asyncio.run(main(mode, dataset_type, duration))

if __name__ == "__main__":
    run_demo()