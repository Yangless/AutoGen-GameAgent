import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from game_monitoring.infrastructure.memory.memory_service import (
    LongTermMemory,
    MemoryService,
    ShortTermMemory,
)
from tests.unit.memory.test_memory_service import FakeRedis


def test_update_long_term_memory():
    """测试更新长期记忆"""
    service = MemoryService(client=FakeRedis())

    asyncio.run(
        service.update_long_term(
            session_id="session_123",
            summary="玩家情绪低落，已发送关怀邮件",
            key_events=[{"event_type": "intervention", "description": "发送关怀邮件"}],
        )
    )

    long_memory = asyncio.run(service.get_long_term("session_123"))

    assert isinstance(long_memory, LongTermMemory)
    assert "情绪低落" in long_memory.summary


def test_compress_history():
    """测试递归摘要压缩"""
    service = MemoryService(client=FakeRedis())

    llm_client = AsyncMock()
    llm_client.create = AsyncMock()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "玩家经历了情绪波动，已采取安抚措施。"
    llm_client.create.return_value = mock_response

    base_time = datetime.now()
    for i in range(5):
        asyncio.run(
            service.append_short_term(
                "session_123",
                ShortTermMemory(
                    session_id="session_123",
                    timestamp=base_time + timedelta(seconds=i),
                    role="user",
                    content=f"Message {i}",
                    metadata={"is_intervention": i == 4},
                ),
            )
        )

    asyncio.run(service.compress_history("session_123", llm_client))

    long_memory = asyncio.run(service.get_long_term("session_123"))

    assert long_memory is not None
    assert len(long_memory.summary) <= 200
    assert long_memory.key_events[0]["event_type"] == "intervention"
