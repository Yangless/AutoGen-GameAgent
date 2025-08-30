import random
import time
from datetime import datetime
from typing import Dict, List

from .player_behavior import PlayerBehavior


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