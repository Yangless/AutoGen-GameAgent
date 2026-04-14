from game_monitoring.core.bootstrap import bootstrap_application
from game_monitoring.domain.messages import PlayerEvent, WorkerResponse


def test_end_to_end_intervention_flow():
    """端到端干预流程测试"""
    container = bootstrap_application(setup_global_context=False)

    event = PlayerEvent(
        player_id="test_player",
        triggered_scenarios=[{"scenario": "negative_behavior", "count": 3}],
        behavior_history=[
            {"action": "click_exit", "timestamp": "2026-04-13T10:00:00"},
            {"action": "negative_chat", "timestamp": "2026-04-13T10:01:00"},
        ],
        session_id="test_session_001",
    )

    orchestrator = container.resolve("OrchestratorAgent")
    tasks = orchestrator._generate_tasks(event)

    assert [task.task_type for task in tasks] == ["emotion", "churn", "behavior"]

    mock_results = [
        WorkerResponse(
            task_id=tasks[0].task_id,
            worker_type="emotion",
            intervention_actions=[{"action_type": "send_email"}],
            confidence=0.85,
            metadata={"emotion_type": "沮丧", "priority": 2},
        ),
        WorkerResponse(
            task_id=tasks[1].task_id,
            worker_type="churn",
            intervention_actions=[{"action_type": "grant_reward"}],
            confidence=0.90,
            metadata={"risk_level": "高风险", "priority": 3},
        ),
        WorkerResponse(
            task_id=tasks[2].task_id,
            worker_type="behavior",
            intervention_actions=[{"action_type": "assign_support"}],
            confidence=0.75,
            metadata={"is_bot": False, "priority": 1},
        ),
    ]

    final_decision = orchestrator._merge_results(mock_results)

    assert final_decision["worker_count"] == 3
    assert len(final_decision["final_actions"]) == 3
    assert 0.0 <= final_decision["overall_confidence"] <= 1.0
