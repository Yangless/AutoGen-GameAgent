from __future__ import annotations

import asyncio
import uuid
from typing import Any

from autogen_core import AgentId, SingleThreadedAgentRuntime

from ..agents.behavior_worker import BehaviorWorker
from ..agents.churn_worker import ChurnWorker
from ..agents.emotion_worker import EmotionWorker
from ..agents.orchestrator import OrchestratorAgent
from ..domain.messages import PlayerEvent
from ..monitoring.behavior_monitor import BehaviorMonitor

_LEGACY_TEAM_IMPORT_ERROR: ModuleNotFoundError | None = None

try:
    from autogen_agentchat.teams import MagenticOneGroupChat
    from autogen_agentchat.ui import Console
    from config import doubao_client
    from ..agents.analysis_agents import (
        create_behavioral_analyst_agent,
        create_bot_detection_agent,
        create_churn_risk_agent,
        create_emotion_recognition_agent,
    )
    from ..agents.intervention_agents import (
        create_engagement_agent,
        create_guidance_agent,
    )
    from ..agents.military_order_agent import create_military_order_agent
except ModuleNotFoundError as exc:
    _LEGACY_TEAM_IMPORT_ERROR = exc
    MagenticOneGroupChat = None
    Console = None
    doubao_client = None


class GameMonitoringTeam:
    """游戏监控多智能体团队管理器。"""

    def __init__(self, model_client=None, player_id="default_player"):
        if _LEGACY_TEAM_IMPORT_ERROR is not None:
            raise ModuleNotFoundError(
                "GameMonitoringTeam requires autogen_agentchat and legacy team dependencies."
            ) from _LEGACY_TEAM_IMPORT_ERROR

        self.model_client = model_client or doubao_client
        self.player_id = player_id

        self.emotion_agent = create_emotion_recognition_agent(player_id)
        self.churn_agent = create_churn_risk_agent(player_id)
        self.bot_agent = create_bot_detection_agent(player_id)
        self.behavioral_analyst_agent = create_behavioral_analyst_agent(player_id)
        self.engagement_agent = create_engagement_agent()
        self.guidance_agent = create_guidance_agent()
        self.military_order_agent = create_military_order_agent()

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
            model_client=self.model_client,
        )

    async def trigger_analysis_and_intervention(
        self, player_id: str, monitor: BehaviorMonitor
    ):
        """触发对指定玩家的分析和干预。"""
        behaviors = monitor.get_player_history(player_id)
        behavior_summary = "\n".join(
            [f"- {b.timestamp.strftime('%H:%M:%S')}: {b.action}" for b in behaviors[-5:]]
        )

        task = f"""
        **紧急警报：玩家 {player_id} 行为异常，启动多智能体协作流程。**

        **背景信息:**
        - **触发原因:** 系统监测到玩家触发了高负面行为阈值。
        - **近期行为摘要 (最近5条):**
        {behavior_summary}

        **你的角色与任务:**
        你现在是这个多智能体团队的 **首席调度官 (Chief Orchestrator)**。你的职责是高效地协调团队中的各位专家Agent，对玩家进行全面的分析，并根据分析结果执行最恰当的干预措施。输出为中文。
        """

        print("\n" + "=" * 25 + " 团队实时动态 " + "=" * 23)
        await Console(self.analysis_team.run_stream(task=task))
        print("=" * 62 + "\n")

    async def generate_batch_military_orders(self, commander_order: str = None):
        """使用军令Agent批量生成多玩家个性化军令。"""
        print("\n🎯 启动军令Agent，批量生成个性化军令...")

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

        print("\n" + "=" * 25 + " 军令生成动态 " + "=" * 23)
        await Console(self.military_order_agent.run_stream(task=task))
        print("=" * 62 + "\n")


class GameMonitoringTeamV2:
    """新版团队管理器，使用 Orchestrator-Worker 架构。"""

    def __init__(self, model_client: Any, runtime: Any):
        self.model_client = model_client
        self.runtime = runtime
        self.orchestrator_id = AgentId("orchestrator", "default")
        self._worker_types = ["emotion_worker", "churn_worker", "behavior_worker"]
        self._runtime_initialized = False
        self._runtime_lock = asyncio.Lock()

    async def trigger_analysis_and_intervention(
        self, player_id: str, monitor: Any
    ) -> Any:
        """构造 PlayerEvent 并发送到 Orchestrator。"""
        await self._ensure_runtime_ready()
        event = PlayerEvent(
            player_id=player_id,
            triggered_scenarios=self._get_triggered_scenarios(monitor, player_id),
            behavior_history=self._get_behavior_history(monitor, player_id),
            session_id=self._generate_session_id(player_id),
        )

        return await self.runtime.send_message(event, self.orchestrator_id)

    async def close(self) -> None:
        """关闭 runtime。"""
        if (
            isinstance(self.runtime, SingleThreadedAgentRuntime)
            and self._runtime_initialized
        ):
            await self.runtime.stop()
            self._runtime_initialized = False

    def _generate_session_id(self, player_id: str) -> str:
        """生成 session ID。"""
        return f"{player_id}-{uuid.uuid4().hex[:8]}"

    async def _ensure_runtime_ready(self) -> None:
        """为真实 runtime 注册 orchestrator 和 workers。"""
        if not isinstance(self.runtime, SingleThreadedAgentRuntime):
            return

        if self._runtime_initialized:
            return

        async with self._runtime_lock:
            if self._runtime_initialized:
                return

            await OrchestratorAgent.register(
                self.runtime,
                "orchestrator",
                lambda: OrchestratorAgent(
                    model_client=self.model_client,
                    worker_types=self._worker_types,
                ),
            )
            await EmotionWorker.register(
                self.runtime,
                "emotion_worker",
                lambda: EmotionWorker(model_client=self.model_client, tools=[]),
            )
            await ChurnWorker.register(
                self.runtime,
                "churn_worker",
                lambda: ChurnWorker(model_client=self.model_client, tools=[]),
            )
            await BehaviorWorker.register(
                self.runtime,
                "behavior_worker",
                lambda: BehaviorWorker(model_client=self.model_client, tools=[]),
            )
            self.runtime.start()
            self._runtime_initialized = True

    @staticmethod
    def _get_triggered_scenarios(monitor: Any, player_id: str) -> list[dict[str, Any]]:
        if hasattr(monitor, "get_triggered_scenarios"):
            return monitor.get_triggered_scenarios()
        if hasattr(monitor, "get_recent_actions_for_analysis"):
            return monitor.get_recent_actions_for_analysis(player_id)
        return []

    @staticmethod
    def _get_behavior_history(monitor: Any, player_id: str) -> list[Any]:
        if hasattr(monitor, "get_behavior_history"):
            return monitor.get_behavior_history(player_id)
        if hasattr(monitor, "get_player_action_sequence"):
            return monitor.get_player_action_sequence(player_id)
        if hasattr(monitor, "get_player_history"):
            return monitor.get_player_history(player_id)
        return []
