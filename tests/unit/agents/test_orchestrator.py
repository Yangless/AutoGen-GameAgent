from unittest.mock import MagicMock

from game_monitoring.agents.orchestrator import OrchestratorAgent
from game_monitoring.domain.messages import PlayerEvent, WorkerResponse


def test_orchestrator_generate_tasks():
    """测试任务生成"""
    orchestrator = OrchestratorAgent(
        model_client=MagicMock(),
        worker_types=["emotion_worker", "churn_worker", "behavior_worker"],
    )

    event = PlayerEvent(
        player_id="player_1",
        triggered_scenarios=[{"scenario": "negative_behavior"}],
        behavior_history=[{"event": "quit_match"}],
        session_id="session_123",
    )

    tasks = orchestrator._generate_tasks(event)

    assert len(tasks) == 3
    assert [task.task_type for task in tasks] == ["emotion", "churn", "behavior"]
    assert all(task.player_id == "player_1" for task in tasks)
    assert all(task.session_id == "session_123" for task in tasks)


def test_merge_results_prioritization():
    """测试结果合并优先级"""
    orchestrator = OrchestratorAgent(
        model_client=MagicMock(),
        worker_types=["emotion", "churn", "behavior"],
    )

    results = [
        WorkerResponse(
            task_id="1",
            worker_type="emotion",
            intervention_actions=[
                {"action_type": "send_email", "template": "gentle_follow_up"}
            ],
            confidence=0.8,
            metadata={"priority": 2},
        ),
        WorkerResponse(
            task_id="2",
            worker_type="churn",
            intervention_actions=[
                {"action_type": "send_email", "template": "vip_retention"},
                {"action_type": "grant_reward", "amount": 100},
            ],
            confidence=0.9,
            metadata={"priority": 3},
        ),
        WorkerResponse(
            task_id="3",
            worker_type="behavior",
            intervention_actions=[{"action_type": "assign_support"}],
            confidence=0.7,
            metadata={"priority": 1},
        ),
    ]

    merged = orchestrator._merge_results(results)

    assert merged["worker_count"] == 3
    assert merged["overall_confidence"] == 0.8
    assert merged["final_actions"] == [
        {"action_type": "send_email", "template": "vip_retention"},
        {"action_type": "grant_reward", "amount": 100},
        {"action_type": "assign_support"},
    ]
