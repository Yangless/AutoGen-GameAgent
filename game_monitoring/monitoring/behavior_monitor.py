from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..simulator.player_behavior import PlayerBehavior
from ..simulator.behavior_simulator import PlayerBehaviorRuleEngine


class BehaviorMonitor:
    def __init__(self, threshold: int = 3, max_sequence_length: int = 50, recent_actions_window: int = 3):
        """初始化行为监控器
        
        Args:
            threshold: 触发干预的负面行为阈值
            max_sequence_length: 最大序列长度
            recent_actions_window: 最近行为窗口大小（用于情景识别）
        """
        self.rule_engine = PlayerBehaviorRuleEngine()
        self.player_action_sequences = {}  # 存储每个玩家的动作序列
        self.behavior_history = []  # 存储所有行为历史
        self.threshold = threshold
        self.max_sequence_length = max_sequence_length
        self.recent_actions_window = recent_actions_window
    
    def add_behavior(self, behavior: PlayerBehavior) -> bool:
        """添加行为数据（保持向后兼容）"""
        self.behavior_history.append(behavior)
        # 移除阈值判断逻辑，该逻辑已前置到process_atomic_action中
        return False
    
    def add_atomic_action(self, player_id: str, action_name: str) -> List[Dict]:
        """添加原子动作到玩家序列并分析
        
        Args:
            player_id: 玩家ID
            action_name: 动作名称
            
        Returns:
            触发的场景列表
        """
        # 初始化玩家序列（如果不存在）
        if player_id not in self.player_action_sequences:
            self.player_action_sequences[player_id] = []
        
        # 创建动作数据
        action_data = {
            'action': action_name,
            'timestamp': datetime.now(),
            'player_id': player_id
        }
        
        # 添加到玩家序列
        self.player_action_sequences[player_id].append(action_data)
        
        # 限制序列长度
        if len(self.player_action_sequences[player_id]) > self.max_sequence_length:
            self.player_action_sequences[player_id] = self.player_action_sequences[player_id][-self.max_sequence_length:]
        
        # 获取最近的行为窗口用于情景识别
        current_sequence = self.player_action_sequences[player_id]
        recent_actions = current_sequence[-self.recent_actions_window:] if len(current_sequence) >= self.recent_actions_window else current_sequence
        
        # 输出调试信息
        print(f"\n=== 玩家 {player_id} 行为分析 ===")
        print(f"当前动作: {action_name}")
        print(f"完整动作序列 ({len(current_sequence)} 个): {[a['action'] for a in current_sequence]}")
        print(f"分析窗口 ({len(recent_actions)} 个): {[a['action'] for a in recent_actions]}")
        
        # 使用规则引擎分析最近行为窗口
        triggered_scenarios = self.rule_engine.analyze_action_sequence(player_id, recent_actions)
        
        # 输出触发的场景信息
        if triggered_scenarios:
            print(f"触发的场景 ({len(triggered_scenarios)} 个):")
            for i, scenario in enumerate(triggered_scenarios, 1):
                scenario_name = scenario.get('scenario', '未知场景')
                scenario_desc = scenario.get('description', '无描述')
                print(f"  {i}. {scenario_name}: {scenario_desc}")
        else:
            print("未触发任何场景")
        
        print(f"=== 分析完成 ===\n")
        
        return triggered_scenarios
    
    def get_recent_actions_for_analysis(self, player_id: str) -> List[Dict]:
        """获取用于分析的最近行为
        
        Args:
            player_id: 玩家ID
            
        Returns:
            最近的行为列表
        """
        if player_id not in self.player_action_sequences:
            return []
        
        current_sequence = self.player_action_sequences[player_id]
        return current_sequence[-self.recent_actions_window:] if len(current_sequence) >= self.recent_actions_window else current_sequence
    
    def get_player_history(self, player_id: str) -> List[PlayerBehavior]:
        """获取玩家行为历史"""
        return [b for b in self.behavior_history if b.player_id == player_id]
    
    def get_player_action_sequence(self, player_id: str) -> List[Dict[str, Any]]:
        """获取玩家当前动作序列"""
        return self.player_action_sequences.get(player_id, [])
    
    def clear_player_sequence(self, player_id: str):
        """清空玩家动作序列（用于测试或重置）"""
        if player_id in self.player_action_sequences:
            self.player_action_sequences[player_id] = []