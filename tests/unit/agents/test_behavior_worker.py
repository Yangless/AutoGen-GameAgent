from unittest.mock import MagicMock

from game_monitoring.agents.behavior_worker import BehaviorWorker


def test_behavior_worker_decide_measures():
    """测试行为管控决策"""
    worker = BehaviorWorker(model_client=MagicMock(), tools=[])

    bot_result = MagicMock()
    bot_result.is_bot = True
    bot_result.confidence = 0.9

    measures = worker._decide_measures(bot_result)

    assert "账号限制" in measures
    assert "人工审核" in measures
