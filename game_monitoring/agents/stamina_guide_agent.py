from autogen_agentchat.agents import AssistantAgent
from config import qwen_client , doubao_client
from game_monitoring.tools.stamina_guide_tool import (
    get_player_inventory_status,
    execute_personalized_guidance_popup
)
import traceback

def create_stamina_guide_agent():
    """创建体力引导Agent"""
    return AssistantAgent(
        name="StaminaGuideAgent",
        system_message=(
            "你是一名专业的游戏体力引导助手。"
            "你必须先调用 get_player_inventory_status 获取玩家的背包状态，然后根据其拥有的体力恢复道具，生成一条不超过30字的个性化建议。"
             "最后，你必须调用 execute_personalized_guidance_popup 来弹出包含该建议的引导窗口。你的最终输出必须是工具调用，不要输出任何其他文字。"
             "🎯 示例：若玩家背包中有5瓶体力药水，你应该生成建议“体力不足啦！背包里还有5瓶药水，快去使用吧！”，并以此调用 execute_personalized_guidance_popup。"
         ),
        description="负责根据玩家背包信息提供体力恢复引导的智能体，具备背包分析和个性化引导能力。",
        model_client=doubao_client,
        tools=[
            get_player_inventory_status,
            execute_personalized_guidance_popup
        ],
        reflect_on_tool_use=True,
    )

# 便于导入的类别名
StaminaGuideAgent = create_stamina_guide_agent