"""
Orchestrator Agent实现

负责接收玩家事件、生成任务包、合并Worker结果。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from autogen_core import RoutedAgent

from ..domain.messages import InterventionTask, PlayerEvent, WorkerResponse


class OrchestratorAgent(RoutedAgent):
    """干预编排Agent"""

    def __init__(self, model_client: Any, worker_types: list[str]) -> None:
        super().__init__("Intervention orchestrator")
        self.model_client = model_client
        self.worker_types = worker_types

    def _generate_tasks(self, message: PlayerEvent) -> list[InterventionTask]:
        """基于配置的 worker 类型生成任务包。"""
        tasks = []
        for worker_type in self.worker_types:
            task_type = worker_type.removesuffix("_worker")
            task = InterventionTask(
                task_id=str(uuid.uuid4()),
                player_id=message.player_id,
                session_id=message.session_id,
                task_type=task_type,
                context={
                    "triggered_scenarios": message.triggered_scenarios,
                    "behavior_history": message.behavior_history,
                },
                timestamp=datetime.now(),
            )
            tasks.append(task)

        return tasks

    def _merge_results(self, results: list[WorkerResponse]) -> dict[str, Any]:
        """按优先级合并多个Worker结果并对动作去重。"""
        prioritized = sorted(
            results,
            key=lambda response: response.metadata.get("priority", 0),
            reverse=True,
        )

        unique_actions: dict[str, dict[str, Any]] = {}
        for response in prioritized:
            for action in response.intervention_actions:
                action_key = action.get("action_type")
                if action_key not in unique_actions:
                    unique_actions[action_key] = action

        avg_confidence = (
            sum(response.confidence for response in results) / len(results)
            if results
            else 0.0
        )
        avg_confidence = round(avg_confidence, 3)

        return {
            "final_actions": list(unique_actions.values()),
            "overall_confidence": avg_confidence,
            "worker_count": len(results),
            "timestamp": datetime.now().isoformat(),
        }
