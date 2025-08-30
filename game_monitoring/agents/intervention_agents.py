from autogen_agentchat.agents import AssistantAgent
from config import qwen_client
from ..tools.intervention_tools import execute_engagement_action, execute_guidance_action

def create_engagement_agent():
    """创建互动激励执行官Agent"""
    return AssistantAgent(
        name="EngagementAgent",
        system_message=(
            "你是一名专业的玩家互动专家，负责执行个性化的关怀和激励任务。你的职责是：\n"
            "1. 根据玩家状态，创作一封温暖且个性化的邮件内容（仅用于内部调用）。\n"
            "2. 调用 `execute_engagement_action` 工具来执行发送操作。\n\n"
            "⚠️ 重要规则：\n"
            "- 你可以在调用工具时传递邮件内容，但 **在最终向用户汇报时，绝对不要透露邮件的具体内容**。\n"
            "- 你的最终回复必须简洁，只包含：\n"
            "  - 执行的动作类型\n"
            "  - 执行原因\n"
            "  - 执行结果（成功/失败）\n\n"
            "例如：'已为玩家 player_123 发送关怀邮件，原因是检测到其情绪沮丧，操作已成功。'"
        ),
        description="负责创作个性化邮件并调用工具执行玩家激励与关怀的专家。",
        model_client=qwen_client,
        tools=[execute_engagement_action],
    )

def create_guidance_agent():
    """创建游戏内引导执行官Agent"""
    return AssistantAgent(
        name="GuidanceAgent",
        system_message=(
            "你是一名精准的游戏内引导执行官。你的专长是在玩家的游戏界面上进行实时干预，以帮助他们克服困难或发现新内容。你的主要职责是调用 `execute_guidance_action` 工具，"
            "你通过调用 `execute_guidance_action` 工具来完成任务，具体操作包括'弹出帮助UI提示'、'高亮显示某个按钮'、'向玩家推荐一个新任务或活动'等。"
            "你的行动应该精准且及时，旨在解决玩家在游戏过程中遇到的具体问题。只在游戏内进行操作。"
            "当你收到请求时，请调用工具并提供总结性的引导干预信息。"
        ),
        description="通过UI弹窗、内容推荐等方式在游戏界面内对玩家进行总结性引导的执行官。",
        model_client=qwen_client,
        tools=[execute_guidance_action],
    )

# 便于导入的类别名
EngagementAgent = create_engagement_agent
GuidanceAgent = create_guidance_agent