from datetime import datetime
from typing import Dict, List


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