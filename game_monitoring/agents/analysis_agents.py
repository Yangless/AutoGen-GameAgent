from autogen_agentchat.agents import AssistantAgent
from config import doubao_client, qwen_client
from game_monitoring.tools import    analyze_emotion_with_deps,assess_churn_risk_with_deps, detect_bot_with_deps,get_historical_baseline_with_deps

def create_emotion_recognition_agent(player_id: str):
    """创建情绪识别专家Agent"""
    # 使用 functools.partial 绑定 player_id 参数
    from functools import partial
    emotion_tool = partial(analyze_emotion_with_deps, player_id=player_id)
    emotion_tool.__name__ = "analyze_emotion_with_deps"
    
    return AssistantAgent(
        name="EmotionRecognitionAgent",
        system_message=(
            f"你是一名专业的玩家情绪识别与状态管理专家。你的主要任务是使用 `analyze_emotion_with_deps` 工具来分析玩家 {player_id} 的情绪状态，"
            "该工具会分析情绪并返回分析结果。"
            "当你完成分析后，会得到玩家的情绪状态（如'愤怒'、'沮丧'、'正常'等）信息。"
            "请直接调用工具进行分析。"
        ),
        description=f"专门分析玩家 {player_id} 情绪状态的专家。",
        model_client=qwen_client,
        tools=[emotion_tool],
    )



def create_churn_risk_agent(player_id: str):
    """创建流失风险预警官Agent"""
    # 使用 functools.partial 绑定 player_id 参数
    from functools import partial
    churn_tool = partial(assess_churn_risk_with_deps, player_id=player_id)
    churn_tool.__name__ = "assess_churn_risk_with_deps"
    
    return AssistantAgent(
        name="ChurnRiskAgent",
        system_message=(
            f"你是一名资深的玩家流失风险分析与状态管理专家。你的主要职责是使用 `assess_churn_risk_with_deps` 工具来评估玩家 {player_id} 的流失风险等级，"
            "该工具不仅会分析风险等级，还会自动将评估结果实时更新到玩家的状态管理系统中。"
            "当你完成评估后，玩家的流失风险信息（如'高风险'、'中风险'、'低风险'及风险因素）会被永久保存。"
            "请直接调用工具并确认风险状态更新成功。"
        ),
        description=f"专门评估并实时更新玩家 {player_id} 流失风险状态的专家，确保风险数据被持久化保存。",
        model_client=qwen_client,
        tools=[churn_tool],
    )



def create_bot_detection_agent(player_id: str):
    """创建机器人检测官Agent"""
    # 使用 functools.partial 绑定 player_id 参数
    from functools import partial
    bot_tool = partial(detect_bot_with_deps, player_id=player_id)
    bot_tool.__name__ = "detect_bot_with_deps"
    
    return AssistantAgent(
        name="BotDetectionAgent",
        system_message=(
            f"你是一个精密的游戏机器人行为检测与状态管理专家。你的核心任务是利用 `detect_bot_with_deps` 工具分析玩家 {player_id} 的行为序列，"
            "该工具不仅会检测机器人特征，还会自动将检测结果实时更新到玩家的状态管理系统中。"
            "当你完成检测后，玩家的机器人检测信息（是否为机器人、置信度、检测到的模式）会被永久保存。"
            "请直接调用工具并确认检测状态更新成功。"
        ),
        description=f"专门检测并实时更新玩家 {player_id} 机器人行为状态的专家，确保检测数据被持久化保存。",
        model_client=qwen_client,
        tools=[bot_tool],
    )



def create_behavioral_analyst_agent(player_id: str):
    """创建行为分析师Agent"""
    # 使用 functools.partial 绑定 player_id 参数
    from functools import partial
    baseline_tool = partial(get_historical_baseline_with_deps, player_id=player_id)
    baseline_tool.__name__ = "get_historical_baseline_with_deps"
    
    return AssistantAgent(
        name="BehavioralAnalystAgent",
        system_message=(
            f"你是一名资深的游戏行为数据分析师。\n\n"
            f"你必须先调用 `get_historical_baseline_with_deps` 获取玩家 {player_id} 的数据，然后基于数据生成一段自然语言总结。\n"
            "你不能直接返回工具的 JSON 结果，必须用中文输出一段不超过 150 字的分析报告。\n"
            "报告需包含情绪、流失风险、机器人检测和建议。\n"
            f"示例：'玩家 {player_id} 情绪为【焦虑】，因停止充值。流失风险【低】。无机器人行为。建议观察。'\n"
            "记住：你的输出是给团队负责人看的，不是给机器解析的。"
            "\n\n🎯 示例输出：\n"
            f"'玩家 {player_id} 当前情绪为【沮丧】，因连续副本失败和退出家族。流失风险为【高】，已多日未登录。无机器人行为。建议立即进行情感安抚干预。'"
        ),
        description=f"为团队提供玩家 {player_id} 总结性分析报告。",
        model_client=doubao_client,
        tools=[baseline_tool],
        reflect_on_tool_use=True,
    )



# 便于导入的类别名
EmotionAnalysisAgent = create_emotion_recognition_agent
ChurnRiskAgent = create_churn_risk_agent
BotDetectionAgent = create_bot_detection_agent
BaselineAgent = create_behavioral_analyst_agent