from pkgutil import extend_path
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from config import doubao_client
from ..agents.analysis_agents import (
    create_emotion_recognition_agent,
    create_churn_risk_agent,
    create_bot_detection_agent,
    create_behavioral_analyst_agent
)
from ..agents.intervention_agents import (
    create_engagement_agent,
    create_guidance_agent
)
from ..agents.military_order_agent import (
    create_military_order_agent
)
from ..monitoring.behavior_monitor import BehaviorMonitor
from typing import List
import mlflow




class GameMonitoringTeam:
    """游戏监控多智能体团队管理器"""
    
    def __init__(self, model_client=None, player_id="default_player"):
        self.model_client = model_client or doubao_client
        self.player_id = player_id
        
        # 创建所有Agent，传递 player_id
        self.emotion_agent = create_emotion_recognition_agent(player_id)
        self.churn_agent = create_churn_risk_agent(player_id)
        self.bot_agent = create_bot_detection_agent(player_id)
        self.behavioral_analyst_agent = create_behavioral_analyst_agent(player_id)
        
        # 这些 Agent 不需要依赖
        self.engagement_agent = create_engagement_agent()
        self.guidance_agent = create_guidance_agent()
        
        # 创建军令Agent
        self.military_order_agent = create_military_order_agent()
        
        # 创建团队
        self.analysis_team = MagenticOneGroupChat(
            [
                self.emotion_agent,
                self.churn_agent,
                self.bot_agent,
                self.behavioral_analyst_agent,
                self.engagement_agent,
                self.guidance_agent,
                self.military_order_agent,
            ],
            model_client=self.model_client
        )
    # @mlflow.trace(name="[Main-Agent] Analysis Orchestrator", span_type="ORCHESTRATOR")
    async def trigger_analysis_and_intervention(self, player_id: str, monitor: BehaviorMonitor):
        """触发对指定玩家的分析和干预"""
        # print(f"\n🤖 启动多智能体团队，为玩家 {player_id} 进行分析和干预...")
        behaviors = monitor.get_player_history(player_id)
        behavior_summary = "\n".join([f"- {b.timestamp.strftime('%H:%M:%S')}: {b.action}" for b in behaviors[-5:]])

        task = f"""
        **紧急警报：玩家 {player_id} 行为异常，启动多智能体协作流程。**

        **背景信息:**
        - **触发原因:** 系统监测到玩家触发了高负面行为阈值。
        - **近期行为摘要 (最近5条):**
        {behavior_summary}

        **你的角色与任务:**
        你现在是这个多智能体团队的 **首席调度官 (Chief Orchestrator)**。你的职责是高效地协调团队中的各位专家Agent，对玩家进行全面的分析，并根据分析结果执行最恰当的干预措施。输出为中文。
        """
        # 使用 Console UI 以流式方式运行团队，实时查看过程
        print("\n" + "="*25 + " 团队实时动态 " + "="*23)
        
        await Console(self.analysis_team.run_stream(task=task))
        print("="*62 + "\n")
    
    async def generate_batch_military_orders(self, commander_order: str = None):
        """使用军令Agent批量生成多玩家个性化军令"""
        print(f"\n🎯 启动军令Agent，批量生成个性化军令...")
        
        task = f"""
        **军令生成任务：批量为多个玩家生成个性化军令**

        **指挥官总军令:**
        {commander_order if commander_order else "使用默认军令配置"}

        **你的任务:**
        1. 使用 `generate_batch_military_orders` 工具批量生成所有玩家的个性化军令
        2. 确保每个玩家的军令都基于其具体属性进行个性化定制
        3. 汇报生成结果，包括为哪些玩家生成了军令以及主要特点
        4. 不要在回复中透露军令的具体内容，只汇报生成状态和玩家能力摘要

        请立即开始执行批量军令生成任务。
        """
        
        print("\n" + "="*25 + " 军令生成动态 " + "="*23)
        await Console(self.military_order_agent.run_stream(task=task))
        print("="*62 + "\n")