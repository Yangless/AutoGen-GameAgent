from unittest.mock import MagicMock

from game_monitoring.agents.emotion_worker import EmotionWorker


def test_emotion_worker_decide_strategy():
    """测试情绪安抚策略决策"""
    worker = EmotionWorker(model_client=MagicMock(), tools=[])

    anger_emotion = MagicMock()
    anger_emotion.emotion = "愤怒"
    anger_emotion.confidence = 0.9

    anger_strategy = worker._decide_strategy(anger_emotion)

    assert anger_strategy["priority"] == "high"
    assert "专属客服" in anger_strategy["actions"]

    sad_emotion = MagicMock()
    sad_emotion.emotion = "沮丧"
    sad_emotion.confidence = 0.8

    sad_strategy = worker._decide_strategy(sad_emotion)

    assert sad_strategy["priority"] == "medium"
    assert "关怀邮件" in sad_strategy["actions"]
