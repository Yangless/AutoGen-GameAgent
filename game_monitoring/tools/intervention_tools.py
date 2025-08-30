import json
import random
from typing import Dict, Any

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