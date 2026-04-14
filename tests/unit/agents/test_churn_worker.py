from unittest.mock import MagicMock

from game_monitoring.agents.churn_worker import ChurnWorker


def test_churn_worker_decide_retention():
    """测试流失挽回决策"""
    worker = ChurnWorker(model_client=MagicMock(), tools=[])

    high_risk = MagicMock()
    high_risk.level = "高风险"
    high_risk.confidence = 0.85

    plan = worker._create_retention_plan(high_risk)

    assert plan["priority"] == 3
    assert "个性化优惠" in plan["actions"]
