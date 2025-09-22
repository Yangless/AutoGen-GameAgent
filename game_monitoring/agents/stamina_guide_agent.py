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
    "你的任务是检查玩家的库存，并根据他们的体力恢复物品提供个性化建议。"
    "请严格遵循以下步骤："
    "1. **必须**首先调用 `get_player_inventory_status()` 函数来获取玩家背包中体力恢复道具的状态。禁止凭空猜测玩家的库存。"
    "2. 分析上一步的返回结果，生成一条不超过30字的中文个性化建议，并将其赋值给字符串变量 `suggestion_guide`。例如：'体力不足啦！背包里还有5瓶药水，快去使用吧！'。"
    # "3. **必须**最后调用 `execute_personalized_guidance_popup(suggestion_guide=suggestion_guide)` 函数，将第二步生成的建议作为参数传入。"
    # "整个过程只能调用这两个函数，不要输出任何额外的解释或文本。"
         ),
        description="负责根据玩家背包信息提供体力恢复引导的智能体，具备背包分析和个性化引导能力。",
        model_client=doubao_client,
        tools=[
            get_player_inventory_status,
            # execute_personalized_guidance_popup
        ],
        reflect_on_tool_use=True,
    )

# 便于导入的类别名
StaminaGuideAgent = create_stamina_guide_agent