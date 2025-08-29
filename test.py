from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily


class ModelSettings:
    model_provider: str = "volces"  # 模型提供商类型
    model_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model_name: str = "ep-20250721140404-4bf2t"
    model_api_key: str = "8d8f08ce-ee01-4bcc-9142-ce10e05cf0c5"
    model_retry_count: int = 3
    model_retry_delay: int = 1
    model_timeout: int = 30

settings = ModelSettings()


custom_model_client = OpenAIChatCompletionClient(
    model=settings.model_name,
    base_url=settings.model_base_url,
    api_key=settings.model_api_key,
    # 其他参数的映射
    request_timeout=settings.model_timeout,
    # 注意：重试逻辑在AutoGen中通常由Agent或Client内部处理，
    # OpenAIChatCompletionClient 本身没有直接的 max_retries 参数，
    # 但可以通过更底层的配置或封装来实现。
    # 这里的参数名与LangChain略有不同。
        model_info={
        # 这些值需要根据你实际模型的支持情况来填写
        "json_output": True,       # 你的模型是否支持JSON模式？通常都支持
        "function_calling": True,  # 你的模型是否支持工具调用？通常都支持
        "vision": False,           # 你的模型是否支持图片输入？如果不支持就设为False
        "family": "openai",        # 声明它属于兼容OpenAI的家族
        "context_window": 262144,  # 如果你知道上下文窗口大小，可以加上
        "structured_output": True,
    }
)



# asyncio.run(main())
import asyncio
import json

# 从 autogen 库导入必要的模块
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
# 导入强大的网页浏览智能体
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

# --- 工具定义 ---

def get_simulated_player_data(player_id: str) -> str:
    """
    根据玩家ID返回一个模拟的玩家游戏数据。

    Args:
        player_id (str): 玩家的唯一标识符。

    Returns:
        str: 包含玩家模拟数据的JSON字符串。
    """
    mock_database = {
        "player_001": {"name": "Alice", "level": 99, "class": "Warrior", "hp": 1500, "attack": 250},
        "player_007": {"name": "Bob", "level": 85, "class": "Mage", "hp": 950, "mana": 3000},
        "player_123": {"name": "Charlie", "level": 92, "class": "Rogue", "hp": 1100, "agility": 280},
    }
    
    player_info = mock_database.get(player_id, {"error": "未找到该玩家"})
    return json.dumps(player_info, ensure_ascii=False)


async def main() -> None:
    # 1. 创建模型客户端
    model_client = custom_model_client
    # 2. 创建自定义智能体
    
    # 第一个智能体：网页冲浪者，负责所有需要在线查询的任务
    # 它内置了搜索、浏览、总结网页等多种工具，无需我们手动提供。
    web_surfer = MultimodalWebSurfer(
        name="Web_Surfer", # 给它一个清晰的名字
        model_client=model_client,
    )

    # 第二个智能体：游戏管理员 (保持不变)
    game_master = AssistantAgent(
        name="Game_Master",
        model_client=model_client,
        system_message="你是一个游戏管理员。你的职责是使用 get_simulated_player_data 工具来查询玩家信息。",
        tools=[get_simulated_player_data],
    )

    # 3. 将新的网页冲浪智能体和游戏管理员一起加入团队
    team = MagenticOneGroupChat(
        [web_surfer, game_master],  
        model_client=model_client,
    )

    # 4. 提出一个更适合网页搜索的复杂任务
    complex_task = (
        "你好团队！请帮我在线搜索一下，今天长沙温度是多少？"
        "另外，也请告诉我玩家 'player_123' 的详细游戏数据。"
    )

    # 5. 使用 Console UI 运行并观察协作过程
    try:
        # 5. 使用 Console UI 运行并观察协作过程
        await Console(team.run_stream(task=complex_task))
    finally:
        # 6. 在程序结束前，无论如何都要调用 close() 方法
        print("\n正在关闭 WebSurfer 资源...")
        await web_surfer.close()
        print("WebSurfer 已关闭。")


if __name__ == "__main__":
    asyncio.run(main())