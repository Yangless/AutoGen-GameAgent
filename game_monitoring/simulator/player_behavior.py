# -*- coding: utf-8 -*-
"""
PlayerBehavior 数据结构
玩家行为数据的基础数据类
"""

from datetime import datetime
from typing import Dict, List, Any


class PlayerActionDefinitions:
    """
    一个用于定义和归类游戏中所有细粒度玩家动作的纲要类。

    这个类本身不包含任何处理逻辑或模拟功能。
    它的主要目的是提供一个清晰、结构化的参考，用于定义系统中存在哪些原子性的玩家行为。
    """
    def __init__(self):
        # 核心游戏动作 (Core Game Actions)
        self.core_game_actions = [
            "login(player_id)",
            "logout(player_id)",
            "enter_dungeon(dungeon_id, difficulty)",
            "complete_dungeon(dungeon_id, status)",
            "move_city(target_coordinates)",
            "attack_city(target_player_id)",
            "be_attacked(attacker_player_id)",
            "win_pvp(opponent_id)",
            "lose_pvp(opponent_id)",
            "occupy_land(land_id, land_type)",
            "attack_npc_tribe(tribe_id)",
            "recruit_hero(rarity)",
            "upgrade_building(building_id)",
            "upgrade_skill(skill_id, status)",
            "enhance_equipment(item_id, status)",
            "dismantle_equipment(item_id)",
            "unlock_achievement(achievement_id)",
            "unlock_map(map_id)"
        ]

        # 社交动作 (Social Actions)
        self.social_actions = [
            "join_family(family_id)",
            "leave_family(family_id)",
            "join_nation(nation_id)",
            "send_chat_message(channel, message_content)",
            "receive_chat_message(channel, sender_id, message_content)",
            "add_friend(friend_id)",
            "remove_friend(friend_id)",
            "receive_praise(sender_id)",
            "be_invited_to_family(family_id)"
        ]

        # 经济与充值动作 (Economic & Payment Actions)
        self.economic_actions = [
            "navigate_to_payment_page()",
            "make_payment(amount, product_id)",
            "buy_monthly_card()",
            "cancel_auto_renew()",
            "receive_daily_reward()",
            "receive_event_reward(event_id, reward_id)",
            "sell_item(item_id, quantity)",
            "clear_backpack()",
            "post_account_for_sale(price)"
        ]

        # 元数据与其他动作 (Metadata & Other Actions)
        self.meta_actions = [
            "submit_review(rating, comment)",
            "contact_support()",
            "change_nickname(new_name)",
            "click_exit_game_button()",
            "uninstall_game()"
        ]

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