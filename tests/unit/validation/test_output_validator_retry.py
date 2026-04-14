import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from game_monitoring.domain.schemas import EmotionWorkerOutput
from game_monitoring.infrastructure.validation.output_validator import (
    OutputValidationError,
    OutputValidator,
)


def test_validate_output_with_retry_success():
    """测试重试成功场景"""
    validator = OutputValidator(EmotionWorkerOutput, max_retries=3)

    model_client = AsyncMock()
    model_client.create = AsyncMock()

    valid_response = MagicMock()
    valid_response.choices = [MagicMock()]
    valid_response.choices[0].message.content = (
        '{"emotion_type": "沮丧", "confidence": 0.85, '
        '"intervention_actions": [], "reason": "test"}'
    )

    model_client.create.return_value = valid_response

    result = asyncio.run(
        validator.validate_output("invalid json", model_client, temperature=0.7)
    )

    assert isinstance(result, EmotionWorkerOutput)
    assert result.emotion_type == "沮丧"
    assert model_client.create.call_count == 1


def test_validate_output_max_retries_exceeded():
    """测试超过最大重试次数"""
    validator = OutputValidator(EmotionWorkerOutput, max_retries=2)

    model_client = AsyncMock()
    model_client.create = AsyncMock()

    invalid_response = MagicMock()
    invalid_response.choices = [MagicMock()]
    invalid_response.choices[0].message.content = "always invalid"
    model_client.create.return_value = invalid_response

    with pytest.raises(OutputValidationError) as exc_info:
        asyncio.run(validator.validate_output("invalid", model_client))

    assert exc_info.value.retry_count == 2
