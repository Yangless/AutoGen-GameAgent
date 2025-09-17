from datetime import datetime
from typing import Dict, List, Optional


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
        
        # 个性化推送相关属性
        self.player_name: Optional[str] = None  # 玩家姓名
        self.team_stamina: List[int] = [100, 100, 100, 100]  # 队伍体力，默认4个队伍
        self.backpack_items: List[str] = []  # 背包道具列表
        self.team_levels: List[int] = [1, 1, 1, 1]  # 阵容等级，默认4个队伍
        self.skill_levels: List[int] = [1, 1, 1, 1]  # 技能等级，默认4个技能
        self.reserve_troops: int = 0  # 预备兵数量
    
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
            "last_updated": self.last_updated.isoformat(),
            # 个性化推送相关属性
            "player_name": self.player_name,
            "team_stamina": self.team_stamina,
            "backpack_items": self.backpack_items,
            "team_levels": self.team_levels,
            "skill_levels": self.skill_levels,
            "reserve_troops": self.reserve_troops
        }


class PlayerStateManager:
    def __init__(self):
        self.player_states: Dict[str, PlayerState] = {}
    
    def get_or_create_state(self, player_id: str) -> PlayerState:
        if player_id not in self.player_states:
            self.player_states[player_id] = PlayerState(player_id)
        return self.player_states[player_id]
    
    def update_emotion(self, player_id: str, emotion: str, confidence: float, keywords: List[str], update_time: datetime):
        state = self.get_or_create_state(player_id)
        state.emotion = emotion
        state.emotion_confidence = confidence
        state.emotion_keywords = keywords
        state.last_updated = update_time
    
    def update_churn_risk(self, player_id: str, risk_level: str, risk_score: float, risk_factors: List[str], update_time: datetime):
        state = self.get_or_create_state(player_id)
        state.churn_risk_level = risk_level
        state.churn_risk_score = risk_score
        state.churn_risk_factors = risk_factors
        state.last_updated = update_time
    
    def update_bot_detection(self, player_id: str, is_bot: bool, confidence: float, patterns: List[str], analysis_time: datetime):
        state = self.get_or_create_state(player_id)
        state.is_bot = is_bot
        state.bot_confidence = confidence
        state.bot_patterns = patterns
        state.last_updated = analysis_time
    
    def get_player_state(self, player_id: str) -> PlayerState:
        return self.get_or_create_state(player_id)
    
    def update_player_attributes(self, player_id: str, player_name: str = None, 
                               team_stamina: List[int] = None, backpack_items: List[str] = None,
                               team_levels: List[int] = None, skill_levels: List[int] = None,
                               reserve_troops: int = None, update_time: datetime = None):
        """更新玩家的个性化推送相关属性"""
        state = self.get_or_create_state(player_id)
        
        if player_name is not None:
            state.player_name = player_name
        if team_stamina is not None:
            state.team_stamina = team_stamina
        if backpack_items is not None:
            state.backpack_items = backpack_items
        if team_levels is not None:
            state.team_levels = team_levels
        if skill_levels is not None:
            state.skill_levels = skill_levels
        if reserve_troops is not None:
            state.reserve_troops = reserve_troops
            
        state.last_updated = update_time or datetime.now()