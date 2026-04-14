import asyncio
from datetime import datetime, timedelta

from game_monitoring.infrastructure.memory.memory_service import (
    MemoryService,
    ShortTermMemory,
)


class FakeRedis:
    def __init__(self):
        self.sorted_sets = {}
        self.values = {}
        self.ttl = {}

    def zadd(self, key, mapping):
        bucket = self.sorted_sets.setdefault(key, [])
        for value, score in mapping.items():
            bucket.append((score, value))
        bucket.sort(key=lambda item: item[0])

    def zremrangebyrank(self, key, start, end):
        bucket = self.sorted_sets.get(key, [])
        if not bucket:
            return
        length = len(bucket)
        start = self._normalize_rank(start, length)
        end = self._normalize_rank(end, length)
        if end < start:
            return
        del bucket[start : end + 1]

    def zrange(self, key, start, end):
        bucket = self.sorted_sets.get(key, [])
        if not bucket:
            return []
        length = len(bucket)
        start = self._normalize_index(start, length)
        end = self._normalize_index(end, length)
        if end < start:
            return []
        return [value for _, value in bucket[start : end + 1]]

    def expire(self, key, seconds):
        self.ttl[key] = seconds

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    @staticmethod
    def _normalize_index(index, length):
        if index < 0:
            index = length + index
        if index < 0:
            return 0
        if index >= length:
            return length - 1
        return index

    @staticmethod
    def _normalize_rank(index, length):
        if index < 0:
            index = length + index
        if index < 0:
            return -1
        if index >= length:
            return length - 1
        return index


def test_append_short_term_memory():
    """测试追加短期记忆"""
    service = MemoryService(client=FakeRedis())

    memory = ShortTermMemory(
        session_id="session_123",
        timestamp=datetime.now(),
        role="user",
        content="玩家点击退出按钮",
    )

    asyncio.run(service.append_short_term("session_123", memory))

    stored = service.client.zrange("memory:session:session_123:short", 0, -1)
    assert len(stored) == 1
    assert service.client.ttl["memory:session:session_123:short"] == 7 * 24 * 3600


def test_get_short_term_memory():
    """测试获取短期记忆"""
    service = MemoryService(client=FakeRedis())
    base_time = datetime.now()

    for i in range(5):
        memory = ShortTermMemory(
            session_id="session_123",
            timestamp=base_time + timedelta(seconds=i),
            role="user",
            content=f"Message {i}",
        )
        asyncio.run(service.append_short_term("session_123", memory))

    memories = asyncio.run(service.get_short_term("session_123", limit=3))

    assert len(memories) == 3
    assert [memory.content for memory in memories] == [
        "Message 2",
        "Message 3",
        "Message 4",
    ]
