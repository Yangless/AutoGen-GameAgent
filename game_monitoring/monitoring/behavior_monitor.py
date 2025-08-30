from typing import List

from ..simulator.player_behavior import PlayerBehavior


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