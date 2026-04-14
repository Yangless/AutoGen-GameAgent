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
            getter = monitor.get_triggered_scenarios
            try:
                return getter(player_id)
            except TypeError:
                return getter()
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
