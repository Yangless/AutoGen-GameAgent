from typing import List, Dict, Any
from datetime import datetime

from ..simulator.player_behavior import PlayerBehavior
from ..simulator.behavior_simulator import PlayerBehaviorRuleEngine


class BehaviorMonitor:
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.player_negative_counts = {}
        self.behavior_history: List[PlayerBehavior] = []
        # 新增：规则引擎和动作序列管理
        self.rule_engine = PlayerBehaviorRuleEngine()
        self.player_action_sequences: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_behavior(self, behavior: PlayerBehavior) -> bool:
        """添加行为数据（保持向后兼容）"""
        self.behavior_history.append(behavior)
        if behavior.action in ["发布消极评论", "突然不充了", "不买月卡了", "玩家点击退出游戏"]:
            self.player_negative_counts.setdefault(behavior.player_id, 0)
            self.player_negative_counts[behavior.player_id] += 1
            if self.player_negative_counts[behavior.player_id] >= self.threshold:
                print(f"⚠️  触发监控阈值: 玩家 {behavior.player_id} 行为触发")
                return True
        return False
    
    def add_atomic_action(self, player_id: str, action: str, params: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """添加原子动作到玩家序列，并使用规则引擎分析"""
        # 确保玩家有动作序列
        if player_id not in self.player_action_sequences:
            self.player_action_sequences[player_id] = []
            
        # 添加新动作
        action_data = {
            'action': action,
            'params': params or {},
            'timestamp': datetime.now(),
            'player_id': player_id
        }
        self.player_action_sequences[player_id].append(action_data)
        
        # 使用规则引擎分析当前序列
        triggered_scenarios = self._analyze_action_sequence(player_id)
        
        return triggered_scenarios
    
    def _analyze_action_sequence(self, player_id: str) -> List[Dict[str, str]]:
        """使用规则引擎分析玩家的动作序列"""
        if player_id not in self.player_action_sequences:
            return []
            
        actions = self.player_action_sequences[player_id]
        triggered_scenarios = []
        
        # 定义规则检查映射
        rules_to_check = [
            ('玩家流失风险', self._check_churn_risk, actions),
            ('游戏挫败情绪', self._check_frustration, actions),
            ('疑似机器人行为', self._check_bot_behavior, actions),
            ('高价值玩家行为', self._check_high_value_behavior, actions),
            ('社交活跃表现', self._check_social_activity, actions)
        ]
        
        for scenario_name, rule_func, action_data in rules_to_check:
            if rule_func(action_data):
                triggered_scenarios.append({
                    'scenario': scenario_name,
                    'player_id': player_id,
                    'trigger_reason': f'规则引擎检测到{scenario_name}相关行为模式'
                })
                
        return triggered_scenarios
    
    def _check_churn_risk(self, actions: List[Dict]) -> bool:
        """检查玩家流失风险"""
        # 批量出售物品 + 取消自动续费 + 点击退出游戏
        bulk_sell = self.rule_engine.check_bulk_item_sell(actions, 3)
        return (len(bulk_sell) > 0 or 
                any(a.get('action') == 'cancel_auto_renew' for a in actions) or
                any(a.get('action') == 'click_exit_game_button' for a in actions))
    
    def _check_frustration(self, actions: List[Dict]) -> bool:
        """检查游戏挫败情绪"""
        # 连续副本失败 + 多次PVP失败 + 连续招募失败
        dungeon_failures = self.rule_engine.check_consecutive_dungeon_failures(actions, 2)
        pvp_losses = self.rule_engine.check_multiple_pvp_losses(actions, 2)
        recruit_failures = self.rule_engine.check_consecutive_recruit_failures(actions, 3)
        return len(dungeon_failures) > 0 or len(pvp_losses) > 0 or len(recruit_failures) > 0
    
    def _check_bot_behavior(self, actions: List[Dict]) -> bool:
        """检查疑似机器人行为"""
        # 异常高频动作
        high_freq = self.rule_engine.check_abnormally_high_action_rate(actions, 1, 5)
        return len(high_freq) > 0
    
    def _check_high_value_behavior(self, actions: List[Dict]) -> bool:
        """检查高价值玩家行为"""
        # 传说英雄招募 + 充值行为 + 困难副本成功
        legendary_recruit = self.rule_engine.check_legendary_hero_recruitment(actions)
        hard_dungeon_success = self.rule_engine.check_successful_hard_dungeon_completion(actions)
        payment_actions = any(a.get('action') == 'make_payment' for a in actions)
        return len(legendary_recruit) > 0 or len(hard_dungeon_success) > 0 or payment_actions
    
    def _check_social_activity(self, actions: List[Dict]) -> bool:
        """检查社交活跃表现"""
        # 世界聊天 + 加入家族 + 添加好友
        world_chat = self.rule_engine.check_open_world_chat(actions)
        social_actions = any(a.get('action') in ['join_family', 'add_friend'] for a in actions)
        return len(world_chat) > 0 or social_actions
    
    def get_player_history(self, player_id: str) -> List[PlayerBehavior]:
        return [b for b in self.behavior_history if b.player_id == player_id]