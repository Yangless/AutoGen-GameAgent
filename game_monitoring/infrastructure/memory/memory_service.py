"""
Redis记忆服务

提供分层 Contextual Memory 的短期与长期记忆能力。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ShortTermMemory:
    """短期记忆：滑动窗口原始对话。"""

    session_id: str
    timestamp: datetime
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LongTermMemory:
    """长期记忆：递归摘要压缩。"""

    session_id: str
    summary: str
    key_events: list[dict[str, Any]]
    last_updated: datetime
    compression_ratio: float


class MemoryService:
    """Redis 记忆服务。"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        client: Any | None = None,
        short_term_window: int = 10,
    ) -> None:
        self.redis_url = redis_url
        self._client = client
        self.short_term_window = short_term_window

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                import redis
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "redis package is required when no memory client is injected"
                ) from exc
            self._client = redis.from_url(self.redis_url)
        return self._client

    async def append_short_term(
        self,
        session_id: str,
        memory: ShortTermMemory,
    ) -> None:
        """追加短期记忆。"""
        key = f"memory:session:{session_id}:short"
        serialized = self._serialize_short_term(memory)
        score = memory.timestamp.isoformat()

        self.client.zadd(key, {serialized: score})
        self.client.zremrangebyrank(key, 0, -self.short_term_window - 1)
        self.client.expire(key, 7 * 24 * 3600)

    async def get_short_term(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[ShortTermMemory]:
        """获取短期记忆。"""
        key = f"memory:session:{session_id}:short"
        limit = limit or self.short_term_window
        memories_data = self.client.zrange(key, -limit, -1)
        return [self._deserialize_short_term(data) for data in memories_data]

    async def update_long_term(
        self,
        session_id: str,
        summary: str,
        key_events: list[dict[str, Any]],
    ) -> None:
        """更新长期摘要。"""
        key = f"memory:session:{session_id}:long:summary"
        memory = LongTermMemory(
            session_id=session_id,
            summary=summary,
            key_events=key_events,
            last_updated=datetime.now(),
            compression_ratio=self._calculate_compression_ratio(summary, key_events),
        )
        self.client.set(key, self._serialize_long_term(memory))
        self.client.expire(key, 30 * 24 * 3600)

    async def get_long_term(self, session_id: str) -> LongTermMemory | None:
        """获取长期记忆。"""
        key = f"memory:session:{session_id}:long:summary"
        data = self.client.get(key)
        if data is None:
            return None
        return self._deserialize_long_term(data)

    async def compress_history(self, session_id: str, llm_client: Any) -> None:
        """递归摘要压缩。"""
        short_memories = await self.get_short_term(session_id)
        long_memory = await self.get_long_term(session_id)
        compression_prompt = self._build_compression_prompt(short_memories, long_memory)

        summary_response = await llm_client.create(
            messages=[{"role": "user", "content": compression_prompt}],
            temperature=0.3,
        )
        new_summary = summary_response.choices[0].message.content[:200]
        key_events = self._extract_key_events(short_memories)

        await self.update_long_term(session_id, new_summary, key_events)

    def _build_compression_prompt(
        self,
        short_memories: list[ShortTermMemory],
        long_memory: LongTermMemory | None,
    ) -> str:
        """构建摘要压缩提示。"""
        recent_dialog = "\n".join(
            [f"{memory.role}: {memory.content}" for memory in short_memories[-5:]]
        )
        existing_summary = long_memory.summary if long_memory else "无"

        return f"""
请将以下对话历史压缩为简洁摘要，保留关键事件因果链：

【现有摘要】
{existing_summary}

【最新对话】
{recent_dialog}

【要求】
1. 合并新旧摘要
2. 保留关键决策、情绪变化、干预结果
3. 去除冗余细节
4. 不超过200字

【压缩后的摘要】
"""

    def _extract_key_events(self, memories: list[ShortTermMemory]) -> list[dict[str, Any]]:
        """从记忆中提取关键事件。"""
        key_events = []
        for memory in memories:
            if memory.metadata.get("is_intervention"):
                key_events.append(
                    {
                        "timestamp": memory.timestamp.isoformat(),
                        "event_type": "intervention",
                        "description": memory.content[:100],
                    }
                )
        return key_events

    @staticmethod
    def _serialize_short_term(memory: ShortTermMemory) -> str:
        payload = {
            "session_id": memory.session_id,
            "timestamp": memory.timestamp.isoformat(),
            "role": memory.role,
            "content": memory.content,
            "metadata": memory.metadata,
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _deserialize_short_term(data: str | bytes) -> ShortTermMemory:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        payload = json.loads(data)
        payload["timestamp"] = datetime.fromisoformat(payload["timestamp"])
        return ShortTermMemory(**payload)

    @staticmethod
    def _serialize_long_term(memory: LongTermMemory) -> str:
        payload = {
            "session_id": memory.session_id,
            "summary": memory.summary,
            "key_events": memory.key_events,
            "last_updated": memory.last_updated.isoformat(),
            "compression_ratio": memory.compression_ratio,
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _deserialize_long_term(data: str | bytes) -> LongTermMemory:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        payload = json.loads(data)
        payload["last_updated"] = datetime.fromisoformat(payload["last_updated"])
        return LongTermMemory(**payload)

    @staticmethod
    def _calculate_compression_ratio(
        summary: str, key_events: list[dict[str, Any]]
    ) -> float:
        denominator = max(len(summary) + len(json.dumps(key_events, ensure_ascii=False)), 1)
        return round(len(summary) / denominator, 3)
