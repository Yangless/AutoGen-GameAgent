# -*- coding: utf-8 -*-
"""
PlayerBehavior 数据结构
玩家行为数据的基础数据类
"""

from datetime import datetime
from typing import Dict, List, Any


class PlayerBehavior:
    """玩家行为数据类"""
    
    def __init__(self, player_id: str, timestamp: datetime, action: str, result: str = "", metadata: Dict[str, Any] = None):
        """
        初始化玩家行为数据
        
        Args:
            player_id: 玩家ID
            timestamp: 行为发生时间
            action: 行为动作描述
            result: 行为结果
            metadata: 额外的元数据
        """
        self.player_id = player_id
        self.timestamp = timestamp
        self.action = action
        self.result = result
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"PlayerBehavior(id={self.player_id}, timestamp='{self.timestamp.isoformat()}', action='{self.action}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'player_id': self.player_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'result': self.result,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerBehavior':
        """从字典创建PlayerBehavior实例"""
        return cls(
            player_id=data['player_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            action=data['action'],
            result=data.get('result', ''),
            metadata=data.get('metadata', {})
        )