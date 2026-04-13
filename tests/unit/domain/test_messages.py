# tests/unit/domain/test_messages.py
import pytest
from datetime import datetime
from game_monitoring.domain.messages import PlayerEvent, InterventionTask, WorkerResponse

def test_player_event_creation():
    """测试PlayerEvent消息创建"""
    event = PlayerEvent(
        player_id="player_1",
        triggered_scenarios=[{"scenario": "negative_behavior"}],
        behavior_history=[],
        session_id="session_123"
    )

    assert event.player_id == "player_1"
    assert event.session_id == "session_123"
    assert len(event.triggered_scenarios) == 1

def test_intervention_task_creation():
    """测试InterventionTask消息创建"""
    task = InterventionTask(
        task_id="task_001",
        player_id="player_1",
        session_id="session_123",
        task_type="emotion",
        context={"emotion": "沮丧"},
        timestamp=datetime.now()
    )

    assert task.task_id == "task_001"
    assert task.task_type == "emotion"

def test_worker_response_creation():
    """测试WorkerResponse消息创建"""
    response = WorkerResponse(
        task_id="task_001",
        worker_type="emotion",
        intervention_actions=[{"action_type": "send_email"}],
        confidence=0.85,
        metadata={"emotion_type": "沮丧"}
    )

    assert response.worker_type == "emotion"
    assert response.confidence == 0.85
