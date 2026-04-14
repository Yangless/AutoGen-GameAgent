import json

import pytest

from game_monitoring.domain.schemas import EmotionWorkerOutput
from game_monitoring.infrastructure.validation.output_validator import OutputValidator


def test_extract_json_from_pure_json():
    """测试纯JSON提取"""
    validator = OutputValidator(EmotionWorkerOutput)
    json_text = (
        '{"emotion_type": "沮丧", "confidence": 0.85, '
        '"intervention_actions": [], "reason": "test"}'
    )

    result = validator._extract_json(json_text)

    assert result["emotion_type"] == "沮丧"
    assert result["confidence"] == 0.85


def test_extract_json_from_mixed_text():
    """测试混合文本中的JSON提取"""
    validator = OutputValidator(EmotionWorkerOutput)
    mixed_text = (
        '思考中... {"emotion_type": "沮丧", "confidence": 0.85, '
        '"intervention_actions": [], "reason": "test"} 然后执行...'
    )

    result = validator._extract_json(mixed_text)

    assert result["emotion_type"] == "沮丧"


def test_extract_json_invalid_raises():
    """测试无效JSON抛出异常"""
    validator = OutputValidator(EmotionWorkerOutput)

    with pytest.raises(json.JSONDecodeError):
        validator._extract_json("this is not json at all")
