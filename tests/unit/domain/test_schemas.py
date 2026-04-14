# tests/unit/domain/test_schemas.py
import pytest
from pydantic import ValidationError
from game_monitoring.domain.schemas import EmotionWorkerOutput, ChurnWorkerOutput, BehaviorWorkerOutput


def test_emotion_worker_output_validation():
    """测试情绪Worker输出验证"""
    valid_output = {
        "emotion_type": "沮丧",
        "confidence": 0.85,
        "intervention_actions": [{"action_type": "send_email"}],
        "reason": "玩家情绪低落"
    }

    result = EmotionWorkerOutput(**valid_output)
    assert result.emotion_type == "沮丧"
    assert result.confidence == 0.85

def test_emotion_worker_output_invalid_confidence():
    """测试无效置信度验证"""
    invalid_output = {
        "emotion_type": "沮丧",
        "confidence": 1.5,  # 超出范围
        "intervention_actions": [],
        "reason": "test"
    }

    with pytest.raises(ValidationError):
        EmotionWorkerOutput(**invalid_output)


def test_churn_worker_output_validation():
    """测试流失Worker输出验证"""
    valid_output = {
        "risk_level": "高风险",
        "risk_score": 0.92,
        "retention_plan": [{"action_type": "offer_discount"}],
        "expected_effectiveness": 0.78,
    }

    result = ChurnWorkerOutput(**valid_output)
    assert result.risk_level == "高风险"
    assert result.risk_score == 0.92


def test_churn_worker_output_invalid_risk_score():
    """测试无效流失评分验证"""
    invalid_output = {
        "risk_level": "中风险",
        "risk_score": -0.1,
        "retention_plan": [{"action_type": "send_coupon"}],
        "expected_effectiveness": 0.5,
    }

    with pytest.raises(ValidationError):
        ChurnWorkerOutput(**invalid_output)


def test_behavior_worker_output_validation():
    """测试行为Worker输出验证"""
    valid_output = {
        "is_bot": True,
        "bot_confidence": 0.97,
        "control_measures": [{"action_type": "flag_account"}],
        "risk_tags": ["automation", "abnormal_click_rate"],
    }

    result = BehaviorWorkerOutput(**valid_output)
    assert result.is_bot is True
    assert result.bot_confidence == 0.97


def test_behavior_worker_output_invalid_bot_confidence():
    """测试无效机器人置信度验证"""
    invalid_output = {
        "is_bot": False,
        "bot_confidence": 1.2,
        "control_measures": [],
        "risk_tags": [],
    }

    with pytest.raises(ValidationError):
        BehaviorWorkerOutput(**invalid_output)

def test_emotion_worker_output_invalid_action():
    """测试无效动作验证"""
    invalid_output = {
        "emotion_type": "沮丧",
        "confidence": 0.5,
        "intervention_actions": [{"action_type": "invalid_action"}],
        "reason": "test"
    }

    with pytest.raises(ValidationError):
        EmotionWorkerOutput(**invalid_output)
